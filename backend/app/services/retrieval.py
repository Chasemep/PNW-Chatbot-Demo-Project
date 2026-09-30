"""Queries for source chunks eligible to support student answers."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import ReleaseStatus, ReviewStatus
from app.models.source import ApprovedSource, KnowledgeBaseRelease
from app.models.source_chunk import SourceContentSegment


def retrieve_active_chunks(
    database: Session,
    *,
    limit: int = 10,
    query_embedding: Sequence[float] | None = None,
    student_type: str | None = None,
    term: str | None = None,
    campus: str | None = None,
    program: str | None = None,
    policy_category: str | None = None,
) -> list[SourceContentSegment]:
    """Return authoritative chunks, optionally ranked by semantic similarity.

    Metadata filter arguments are accepted as the retrieval contract evolves;
    the current schema only has source authority metadata, so unsupported
    dimensions are intentionally not guessed or applied to free-form text.
    """

    if limit < 1:
        raise ValueError("limit must be at least 1")

    statement = (
        select(SourceContentSegment)
        .join(ApprovedSource, SourceContentSegment.source_id == ApprovedSource.id)
        .join(
            KnowledgeBaseRelease,
            SourceContentSegment.release_id == KnowledgeBaseRelease.id,
        )
        .where(
            KnowledgeBaseRelease.status == ReleaseStatus.ACTIVE,
            ApprovedSource.review_status == ReviewStatus.APPROVED,
            ApprovedSource.is_active.is_(True),
            ApprovedSource.superseded_by.is_(None),
        )
    )
    if query_embedding is not None:
        if not query_embedding:
            raise ValueError("query_embedding must not be empty")
        statement = statement.order_by(
            SourceContentSegment.embedding.cosine_distance(query_embedding),
            SourceContentSegment.id,
        )
    else:
        statement = statement.order_by(
            SourceContentSegment.chunk_index,
            SourceContentSegment.id,
        )
    statement = statement.limit(limit)
    return list(database.scalars(statement))
