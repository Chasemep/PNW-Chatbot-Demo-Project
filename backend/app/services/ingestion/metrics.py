"""Metrics and diagnostics for knowledge-base preparation runs."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.models.review_record import PreparationValidation


@dataclass
class PreparationMetrics:
    """Operator-facing counters and timing for one preparation run."""

    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    declared_sources: int = 0
    prepared_sources: int = 0
    failed_sources: int = 0
    excluded_sources: int = 0
    chunks_created: int = 0
    embeddings_generated: int = 0
    embedding_model: str | None = None
    embedding_dimension: int | None = None

    def finish(self) -> None:
        """Record completion time for the preparation run."""

        self.completed_at = datetime.now(UTC)

    def as_dict(self) -> dict[str, Any]:
        """Return JSON-serializable metrics."""

        completed_at = self.completed_at or datetime.now(UTC)
        return {
            "started_at": self.started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": round(
                (completed_at - self.started_at).total_seconds(),
                3,
            ),
            "sources": {
                "declared": self.declared_sources,
                "prepared": self.prepared_sources,
                "failed": self.failed_sources,
                "excluded": self.excluded_sources,
            },
            "chunks_created": self.chunks_created,
            "embeddings_generated": self.embeddings_generated,
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedding_dimension,
        }


def summarize_validations(
    validations: list[PreparationValidation],
) -> dict[str, Any]:
    """Summarize persisted release gates and preserve their diagnostics."""

    return {
        "total": len(validations),
        "passed": sum(
            validation.status.value == "passed" for validation in validations
        ),
        "failed": sum(
            validation.status.value == "failed" for validation in validations
        ),
        "warnings": sum(
            validation.status.value == "warning" for validation in validations
        ),
        "checks": [
            {
                "name": validation.check_name,
                "status": validation.status.value,
                "measured_value": validation.measured_value,
                "details": validation.details,
            }
            for validation in validations
        ],
    }