"""add HNSW index for source embeddings

Revision ID: 7e4d1b8c2f10
Revises: 0012d9958515
Create Date: 2026-09-28
"""

from collections.abc import Sequence

from alembic import op

revision: str = "7e4d1b8c2f10"
down_revision: str | Sequence[str] | None = "0012d9958515"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the approximate nearest-neighbor index for cosine retrieval."""

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_source_content_segments_embedding_hnsw "
        "ON source_content_segments USING hnsw "
        "(embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Remove the source embedding index."""

    op.execute(
        "DROP INDEX IF EXISTS ix_source_content_segments_embedding_hnsw"
    )