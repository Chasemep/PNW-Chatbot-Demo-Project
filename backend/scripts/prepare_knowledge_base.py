"""Prepare an isolated knowledge-base release from an approved manifest."""

import argparse
import importlib
import json
import os
import sys
import tempfile
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.base import ReleaseStatus, SourceType  # noqa: E402
from app.models.review_record import (  # noqa: E402
    ParsingIssueType,
    ParsingReviewRecord,
    PreparationValidation,
)
from app.models.source import ApprovedSource, KnowledgeBaseRelease  # noqa: E402
from app.models.source_chunk import SourceContentSegment  # noqa: E402
from app.services.ingestion.chunk import chunk_blocks  # noqa: E402
from app.services.ingestion.embed import (  # noqa: E402
    EmbeddingProvider,
    generate_embeddings,
)
from app.services.ingestion.gemini_embed import (  # noqa: E402
    GeminiEmbeddingProvider,
)
from app.services.ingestion.loader import SourceLoadError, load_source  # noqa: E402
from app.services.ingestion.manifest import (  # noqa: E402
    ManifestSource,
    validate_manifest,
)
from app.services.ingestion.metrics import (  # noqa: E402
    PreparationMetrics,
    summarize_validations,
)
from app.services.ingestion.normalize import normalize_blocks  # noqa: E402
from app.services.ingestion.parser import parse_source  # noqa: E402
from app.services.ingestion.publish import publish_release  # noqa: E402
from app.services.ingestion.validate import validate_release  # noqa: E402

MAX_CHUNK_CHARACTERS = 1200


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for knowledge-base preparation."""

    parser = argparse.ArgumentParser(
        description="Prepare an approved PostgreSQL + pgvector knowledge-base release."
    )
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="JSON file containing approved source metadata.",
    )
    parser.add_argument(
        "--release-label",
        required=True,
        help="Human-readable label for this preparation run.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Root directory for local source paths in the manifest.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Parse and chunk sources without embeddings, database writes, "
            "or activation."
        ),
    )
    parser.add_argument(
        "--activate",
        action="store_true",
        help="Activate the release after all validation gates pass.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run preparation and print a JSON release report."""

    arguments = build_parser().parse_args(argv)
    try:
        report = prepare_knowledge_base(
            manifest_path=arguments.manifest,
            release_label=arguments.release_label,
            source_root=arguments.source_root,
            dry_run=arguments.dry_run,
            activate=arguments.activate,
        )
    except (OSError, RuntimeError, SourceLoadError, ValueError) as error:
        print(f"knowledge-base preparation failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


def prepare_knowledge_base(
    *,
    manifest_path: Path,
    release_label: str,
    source_root: Path | None = None,
    dry_run: bool = False,
    activate: bool = False,
    embedder: EmbeddingProvider | None = None,
) -> dict[str, Any]:
    """Prepare a release and return an operator-readable report."""

    if not release_label.strip():
        raise ValueError("release_label must not be blank")
    if activate and dry_run:
        raise ValueError("--activate cannot be combined with --dry-run")

    manifest = _read_manifest(manifest_path)
    settings = get_settings()
    metrics = PreparationMetrics(declared_sources=len(manifest))
    prepared_sources: dict[str, tuple[ManifestSource, list[Any], str]] = {}
    failed_sources: list[dict[str, str]] = []

    for source in manifest:
        try:
            blocks, content_hash = _prepare_source(source, source_root)
            prepared_sources[source.source_key] = (source, blocks, content_hash)
        except (OSError, SourceLoadError, ValueError) as error:
            failed_sources.append(
                {"source_key": source.source_key, "error": str(error)}
            )

    metrics.prepared_sources = len(prepared_sources)
    metrics.failed_sources = len(failed_sources)
    metrics.excluded_sources = sum(
        source.review_status.value != "approved" for source in manifest
    )

    chunk_count = sum(
        len(
            chunk_blocks(
                normalize_blocks(blocks),
                source_version_hash=content_hash,
                max_characters=MAX_CHUNK_CHARACTERS,
            )
        )
        for _, blocks, content_hash in prepared_sources.values()
    )
    metrics.chunks_created = chunk_count
    metrics.finish()
    report: dict[str, Any] = {
        "release_label": release_label,
        "status": "dry_run" if dry_run else "preparing",
        "release_id": None,
        "source_counts": {
            "declared": len(manifest),
            "prepared": len(prepared_sources),
            "failed": len(failed_sources),
            "excluded": sum(
                source.review_status.value != "approved" for source in manifest
            ),
        },
        "chunk_count": chunk_count,
        "failed_sources": failed_sources,
        "active_release_id_before": None,
        "active_release_id_after": None,
        "metrics": metrics.as_dict(),
        "diagnostics": {
            "failed_sources": failed_sources,
            "validation": "not_run",
        },
    }
    if dry_run:
        return report
    if embedder is None:
        embedder = _load_configured_embedder()
    metrics.embedding_model = embedder.model_name
    metrics.embedding_dimension = settings.embedding_dimension

    with SessionLocal() as database:
        try:
            active_release = database.query(KnowledgeBaseRelease).filter_by(
                status=ReleaseStatus.ACTIVE
            ).one_or_none()
            report["active_release_id_before"] = (
                str(active_release.id) if active_release else None
            )
            release = KnowledgeBaseRelease(
                status=ReleaseStatus.PREPARING,
                embedding_model=embedder.model_name,
                embedding_dimension=settings.embedding_dimension,
                started_at=datetime.now(UTC),
            )
            database.add(release)
            database.flush()
            report["release_id"] = str(release.id)

            for source in manifest:
                stored_source = ApprovedSource(
                    title=source.title,
                    source_url=source.location,
                    source_type=source.source_type,
                    issuing_office=source.issuing_office,
                    publication_date=source.effective_date,
                    reviewed_at=source.reviewed_at,
                    review_status=source.review_status,
                    is_active=source.review_status.value == "approved",
                )
                database.add(stored_source)
                database.flush()

                if source.source_key not in prepared_sources:
                    failure = next(
                        failure
                        for failure in failed_sources
                        if failure["source_key"] == source.source_key
                    )
                    database.add(
                        ParsingReviewRecord(
                            source_id=stored_source.id,
                            issue_type=ParsingIssueType.PARSE_FAILURE,
                            issue_details=failure["error"],
                        )
                    )
                    continue
                if source.review_status.value != "approved":
                    continue

                _, blocks, content_hash = prepared_sources[source.source_key]
                chunks = chunk_blocks(
                    normalize_blocks(blocks),
                    source_version_hash=content_hash,
                    max_characters=MAX_CHUNK_CHARACTERS,
                )
                vectors = generate_embeddings(
                    [chunk.content_text for chunk in chunks],
                    provider=embedder,
                    expected_model=embedder.model_name,
                    expected_dimension=settings.embedding_dimension,
                )
                metrics.embeddings_generated += len(vectors)
                database.add_all(
                    SourceContentSegment(
                        source_id=stored_source.id,
                        release_id=release.id,
                        chunk_index=chunk.ordinal,
                        content_text=chunk.content_text,
                        source_snippet=chunk.content_text,
                        embedding=vector,
                        structural_path=chunk.structural_path,
                        content_kind=chunk.content_kind,
                        location_label=chunk.location_label,
                        chunk_hash=chunk.chunk_hash,
                    )
                    for chunk, vector in zip(chunks, vectors, strict=True)
                )

            database.flush()
            is_valid = validate_release(database, release.id)
            validations = database.query(PreparationValidation).filter_by(
                release_id=release.id
            ).all()
            report["diagnostics"]["validation"] = summarize_validations(validations)
            metrics.finish()
            report["metrics"] = metrics.as_dict()
            report["diagnostics"]["failure_summary"] = release.failure_summary
            if not is_valid:
                database.commit()
                report["status"] = "rejected"
                return report
            if activate:
                publish_release(database, release.id)
                report["status"] = "active"
            else:
                report["status"] = "validated"
            database.commit()
            report["active_release_id_after"] = str(
                release.id if activate else active_release.id
            ) if (release.id if activate else active_release) else None
            return report
        except Exception:
            database.rollback()
            raise


def _read_manifest(manifest_path: Path) -> list[ManifestSource]:
    with manifest_path.open(encoding="utf-8") as manifest_file:
        return validate_manifest(json.load(manifest_file))


def _prepare_source(
    source: ManifestSource,
    source_root: Path | None,
) -> tuple[list[Any], str]:
    loaded = load_source(source.location, source_root=source_root)
    suffix = Path(source.location).suffix.lower() or {
        SourceType.HTML: ".html",
        SourceType.PDF: ".pdf",
        SourceType.DOCX: ".docx",
        SourceType.WEBPAGE: ".html",
    }[source.source_type]
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary:
            temporary.write(loaded.content)
            temporary_path = Path(temporary.name)
        parsed = parse_source(temporary_path)
        if parsed.review_reason:
            raise ValueError(parsed.review_reason)
        return parsed.blocks, loaded.content_hash
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _load_configured_embedder() -> EmbeddingProvider:
    provider_path = os.getenv("EMBEDDING_PROVIDER")
    if provider_path == "google-gemini":
        return GeminiEmbeddingProvider.from_settings()
    if not provider_path or ":" not in provider_path:
        raise RuntimeError(
            "non-dry-run preparation requires EMBEDDING_PROVIDER=module:factory"
        )
    module_name, factory_name = provider_path.split(":", maxsplit=1)
    provider_factory: Callable[[], EmbeddingProvider] = getattr(
        importlib.import_module(module_name), factory_name
    )
    return provider_factory()


if __name__ == "__main__":
    raise SystemExit(main())