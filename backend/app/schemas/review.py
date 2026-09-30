"""Pydantic schemas for ingestion review and validation records."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.review_record import (
    ParsingIssueType,
    ParsingReviewStatus,
    ValidationStatus,
)


def require_review_text(value: str) -> str:
    """Reject blank review diagnostics."""

    normalized = value.strip()
    if not normalized:
        raise ValueError("value must not be blank")
    return normalized


class ParsingReviewRead(BaseModel):
    """A source parsing issue returned for operator review."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    issue_type: ParsingIssueType
    issue_details: str = Field(min_length=1)
    review_status: ParsingReviewStatus
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    _validate_issue_details = field_validator("issue_details")(require_review_text)


class PreparationValidationRead(BaseModel):
    """A knowledge-base quality-gate result returned in a release report."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    release_id: UUID
    check_name: str = Field(min_length=1, max_length=255)
    status: ValidationStatus
    measured_value: str = Field(min_length=1, max_length=255)
    details: str = Field(min_length=1)
    created_at: datetime
    updated_at: datetime

    _validate_text = field_validator("check_name", "measured_value", "details")(
        require_review_text
    )

class SafeReferralRead(BaseModel):
    """Client-safe escalation details for unreliable answers."""

    office_name: str = Field(min_length=1, max_length=255)
    referral_reason: str = Field(min_length=1)
    contact_url: str | None = None

    _validate_text = field_validator("office_name", "referral_reason")(
        require_review_text
    )