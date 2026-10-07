"""Opt-in smoke tests against a running Docker Compose deployment."""

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

import pytest
from scripts.prepare_knowledge_base import prepare_knowledge_base

CHATBOT_URL = os.getenv("CHATBOT_E2E_URL")


@pytest.mark.skipif(
    not CHATBOT_URL,
    reason="set CHATBOT_E2E_URL to the running frontend URL to run Docker smoke tests",
)
def test_docker_stack_serves_ui_sources_and_chat_api() -> None:
    assert CHATBOT_URL is not None
    base_url = CHATBOT_URL.rstrip("/")

    with urlopen(f"{base_url}/", timeout=5) as response:
        html = response.read().decode("utf-8")
        assert response.status == 200
        assert '<div id="root"></div>' in html

    with urlopen(f"{base_url}/api/sources", timeout=5) as response:
        sources = json.loads(response.read())
        assert response.status == 200
        assert isinstance(sources, list)

    request = Request(
        f"{base_url}/api/chat",
        data=json.dumps(
            {
                "question": "I need an individualized financial aid decision. "
                "Who should I contact?",
                "student_type": "undergraduate",
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read())

    assert response.status == 200
    assert payload["response_type"] in {
        "direct_answer",
        "clarification_needed",
        "safe_referral",
    }
    assert isinstance(payload["answer"], str) and payload["answer"].strip()
    assert isinstance(payload["citations"], list)


def test_dry_run_reports_an_inaccessible_source_without_writing_database(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "sources"
    source_root.mkdir()
    manifest_path = tmp_path / "approved-sources.json"
    manifest_path.write_text(
        json.dumps(
            [
                {
                    "source_key": "inaccessible-source",
                    "title": "Unavailable source",
                    "location": "missing.html",
                    "source_url": "https://www.pnw.edu/example-policy/",
                    "source_type": "html",
                    "issuing_office": "Registrar",
                    "review_status": "approved",
                    "effective_date": "2026-01-01",
                    "reviewed_at": "2026-10-01T00:00:00Z",
                }
            ]
        ),
        encoding="utf-8",
    )

    report = prepare_knowledge_base(
        manifest_path=manifest_path,
        release_label="inaccessible-source-test",
        source_root=source_root,
        dry_run=True,
    )

    assert report["status"] == "dry_run"
    assert report["source_counts"] == {
        "declared": 1,
        "prepared": 0,
        "failed": 1,
        "excluded": 0,
    }
    assert report["failed_sources"][0]["source_key"] == "inaccessible-source"
    assert "could not read local source" in report["failed_sources"][0]["error"]


def test_unchanged_source_dry_runs_have_deterministic_chunk_counts() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    first_report = prepare_knowledge_base(
        manifest_path=backend_root / "documents/approved-sources.json",
        release_label="determinism-smoke",
        source_root=backend_root / "documents/sources",
        dry_run=True,
    )
    second_report = prepare_knowledge_base(
        manifest_path=backend_root / "documents/approved-sources.json",
        release_label="determinism-smoke",
        source_root=backend_root / "documents/sources",
        dry_run=True,
    )

    assert first_report["source_counts"] == second_report["source_counts"]
    assert first_report["chunk_count"] == second_report["chunk_count"]
    assert first_report["failed_sources"] == second_report["failed_sources"] == []
