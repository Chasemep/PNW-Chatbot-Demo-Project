"""Pydantic schemas for approved sources and knowledge-base releases."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.base import ReleaseStatus, ReviewStatus, SourceType


def require_text(value: str) -> str:
    """Reject blank strings while preserving meaningful surrounding text."""

    normalized = value.strip()
    if not normalized:
        raise ValueError("value must not be blank")
    return normalized


class SourceCreate(BaseModel):
    """Manifest data required to register an approved source."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=500)
    source_url: str = Field(min_length=1)
    source_type: SourceType
    issuing_office: str = Field(min_length=1, max_length=255)
    publication_date: date | None = None
    reviewed_at: datetime
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    superseded_by: UUID | None = None
    is_active: bool = False

    _validate_text = field_validator("title", "source_url", "issuing_office")(
        require_text
    )

    @model_validator(mode="after")
    def validate_authority_invariants(self) -> "SourceCreate":
        """Reject source states that cannot become authoritative."""

        if (
            self.review_status is ReviewStatus.SUPERSEDED
            and self.superseded_by is None
        ):
            raise ValueError("superseded sources require superseded_by")
        if self.review_status is ReviewStatus.APPROVED and not self.is_active:
            raise ValueError("approved sources must be active")
        return self


class SourceRead(SourceCreate):
    """Persisted approved source returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class ReleaseRead(BaseModel):
    """Persisted knowledge-base release returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ReleaseStatus
    embedding_model: str = Field(min_length=1, max_length=255)
    embedding_dimension: int = Field(gt=0)
    started_at: datetime
    validated_at: datetime | None = None
    activated_at: datetime | None = None
    failure_summary: str | None = None
    created_at: datetime
    updated_at: datetime