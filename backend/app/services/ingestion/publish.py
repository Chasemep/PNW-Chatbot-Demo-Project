"""Database publishing primitives for knowledge-base releases."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.base import ReleaseStatus
from app.models.source import KnowledgeBaseRelease

HNSW_INDEX_NAME = "ix_source_content_segments_embedding_hnsw"


def create_hnsw_index(database: Session) -> None:
    """Create the pgvector HNSW index used for cosine similarity retrieval."""

    if database.bind is None or database.bind.dialect.name != "postgresql":
        raise RuntimeError("the HNSW index requires a PostgreSQL database")

    database.execute(
        text(
            f"CREATE INDEX IF NOT EXISTS {HNSW_INDEX_NAME} "
            "ON source_content_segments USING hnsw "
            "(embedding vector_cosine_ops)"
        )
    )


def publish_release(database: Session, release_id: UUID) -> KnowledgeBaseRelease:
    """Activate a validated release and retire the currently active release.

    The caller owns the surrounding transaction and must commit or roll it back.
    """

    candidate = database.scalar(
        select(KnowledgeBaseRelease)
        .where(KnowledgeBaseRelease.id == release_id)
        .with_for_update()
    )
    if candidate is None:
        raise ValueError(f"knowledge-base release {release_id} does not exist")
    if candidate.status is not ReleaseStatus.VALIDATED:
        raise ValueError("only validated releases can be published")

    active_releases = list(
        database.scalars(
            select(KnowledgeBaseRelease)
            .where(KnowledgeBaseRelease.status == ReleaseStatus.ACTIVE)
            .with_for_update()
        )
    )
    for active_release in active_releases:
        active_release.status = ReleaseStatus.RETIRED
    database.flush()

    candidate.status = ReleaseStatus.ACTIVE
    candidate.activated_at = datetime.now(UTC)
    database.flush()
    return candidate