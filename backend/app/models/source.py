"""Approved source and knowledge-base release models."""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import (
    ModelBase,
    ReleaseStatus,
    ReviewStatus,
    SourceType,
)


class ApprovedSource(ModelBase):
    """A Purdue Northwest source eligible for controlled ingestion."""

    __tablename__ = "approved_sources"
    __table_args__ = (
        CheckConstraint(
            "review_status != 'superseded' OR superseded_by IS NOT NULL",
            name="ck_approved_sources_superseded_by_required",
        ),
        CheckConstraint(
            "review_status != 'approved' OR is_active",
            name="ck_approved_sources_approved_must_be_active",
        ),
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(
            SourceType,
            name="source_type",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    issuing_office: Mapped[str] = mapped_column(String(255), nullable=False)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(nullable=False)
    review_status: Mapped[ReviewStatus] = mapped_column(
        Enum(
            ReviewStatus,
            name="review_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        default=ReviewStatus.PENDING_REVIEW,
    )
    superseded_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("approved_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class KnowledgeBaseRelease(ModelBase):
    """An isolated, validated release of searchable source content."""

    __tablename__ = "knowledge_base_releases"
    __table_args__ = (
        Index(
            "uq_knowledge_base_releases_one_active",
            "status",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
    )

    status: Mapped[ReleaseStatus] = mapped_column(
        Enum(
            ReleaseStatus,
            name="release_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        default=ReleaseStatus.PREPARING,
    )
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(nullable=False)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    validated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    failure_summary: Mapped[str | None] = mapped_column(Text, nullable=True)