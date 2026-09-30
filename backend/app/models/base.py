"""Shared SQLAlchemy model types and database-enforced conventions."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import get_settings


class SourceType(StrEnum):
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    WEBPAGE = "webpage"


class ReviewStatus(StrEnum):
    APPROVED = "approved"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ReleaseStatus(StrEnum):
    PREPARING = "preparing"
    VALIDATED = "validated"
    ACTIVE = "active"
    REJECTED = "rejected"
    RETIRED = "retired"


class ParseStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    INCOMPLETE = "incomplete"


class ContentKind(StrEnum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    LIST = "list"
    SIDEBAR = "sidebar"
    CALLOUT = "callout"
    CONTINUATION = "continuation"


class StudentType(StrEnum):
    UNDERGRADUATE = "undergraduate"
    GRADUATE = "graduate"
    UNKNOWN = "unknown"


class ResponseType(StrEnum):
    DIRECT_ANSWER = "direct_answer"
    CLARIFICATION_NEEDED = "clarification_needed"
    SAFE_REFERRAL = "safe_referral"


class Base(DeclarativeBase):
    """Base class for all application database models."""


class UUIDPrimaryKeyMixin:
    """Provide a generated UUID primary key."""

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )


class TimestampMixin:
    """Provide timezone-aware creation and update timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class ModelBase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Abstract base combining identity and audit columns."""

    __abstract__ = True


embedding_vector_type = VECTOR(get_settings().embedding_dimension)