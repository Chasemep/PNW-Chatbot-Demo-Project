"""Bounded, dependency-isolated latency and preparation performance checks."""

import json
import math
import subprocess
import sys
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from app.models.base import ContentKind, ReleaseStatus, ReviewStatus, SourceType
from app.models.source import ApprovedSource, KnowledgeBaseRelease
from app.models.source_chunk import SourceContentSegment
from app.services.answering import GeminiAnswerer
from app.services.ingestion.gemini_embed import GeminiEmbeddingProvider
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _p95(samples: list[float]) -> float:
    ordered_samples = sorted(samples)
    index = max(0, math.ceil(0.95 * len(ordered_samples)) - 1)
    return ordered_samples[index]


def test_chat_response_p95_stays_within_five_seconds(
    contact_api: tuple[TestClient, sessionmaker[Session]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, session_factory = contact_api
    release_id = uuid4()
    source_id = uuid4()
    with session_factory() as database:
        database.add_all(
            [
                KnowledgeBaseRelease(
                    id=release_id,
                    status=ReleaseStatus.ACTIVE,
                    embedding_model="test-model",
                    embedding_dimension=768,
                    started_at=datetime.now(UTC),
                ),
                ApprovedSource(
                    id=source_id,
                    title="Registration Policy",
                    source_url="https://www.pnw.edu/registrar/",
                    source_type=SourceType.WEBPAGE,
                    issuing_office="Registrar",
                    reviewed_at=datetime.now(UTC),
                    review_status=ReviewStatus.APPROVED,
                    is_active=True,
                ),
            ]
        )
        database.flush()
        database.add(
            SourceContentSegment(
                source_id=source_id,
                release_id=release_id,
                chunk_index=0,
                content_text=(
                    "Students may register for classes during the open period."
                ),
                source_snippet="Register during the open period.",
                embedding=[0.0] * 768,
                structural_path="Registration > Open period",
                content_kind=ContentKind.PARAGRAPH,
                location_label="Open period",
                chunk_hash=f"performance-{source_id}",
            )
        )
        database.commit()

    class NoEmbeddingProvider:
        def embed(self, _texts: list[str]) -> Sequence[Sequence[float]]:
            raise RuntimeError("Performance test uses deterministic local retrieval")

    class LocalAnswerer:
        def answer(self, _question: str, _context: Sequence[str]) -> str:
            return "Registration is available during the published open period."

    monkeypatch.setattr(
        GeminiEmbeddingProvider,
        "from_settings",
        classmethod(lambda _cls: NoEmbeddingProvider()),
    )
    monkeypatch.setattr(
        GeminiAnswerer,
        "from_settings",
        classmethod(lambda _cls: LocalAnswerer()),
    )

    samples = []
    for _ in range(20):
        started_at = time.perf_counter()
        response = client.post(
            "/api/chat",
            json={"question": "When can I register for classes?"},
        )
        samples.append(time.perf_counter() - started_at)
        assert response.status_code == 200
        assert response.json()["citations"]

    assert _p95(samples) < 5.0


def test_local_source_preparation_dry_run_stays_bounded() -> None:
    command = [
        sys.executable,
        "scripts/prepare_knowledge_base.py",
        "--manifest",
        "documents/approved-sources.json",
        "--source-root",
        "documents/sources",
        "--release-label",
        "performance-dry-run",
        "--dry-run",
    ]
    started_at = time.perf_counter()
    result = subprocess.run(
        command,
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    elapsed = time.perf_counter() - started_at

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "dry_run"
    assert report["source_counts"]["prepared"] == report["source_counts"]["declared"]
    assert report["source_counts"]["failed"] == 0
    assert report["chunk_count"] > 0
    assert elapsed < 15.0
