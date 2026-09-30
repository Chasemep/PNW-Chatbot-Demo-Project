"""Parsing issue and knowledge-base validation audit models."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import ModelBase


class ParsingIssueType(StrEnum):
    """Types of source problems requiring review."""

    PARSE_FAILURE = "parse_failure"
    INACCESSIBLE_SOURCE = "inaccessible_source"
    CONFLICTING_METADATA = "conflicting_metadata"
    INVALID_FORMAT = "invalid_format"
    MISSING_STRUCTURE = "missing_structure"


class ParsingReviewStatus(StrEnum):
    """Review states for a parsing issue."""

    PENDING = "pending"
    REVIEWED = "reviewed"
    REJECTED = "rejected"
    ACCEPTED_WITH_WARNING = "accepted_with_warning"


class ValidationStatus(StrEnum):
    """Outcome states for a preparation validation check."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class ParsingReviewRecord(ModelBase):
    """A reviewable parsing or source-access problem."""

    __tablename__ = "parsing_review_records"
    __table_args__ = (
        CheckConstraint(
            "length(trim(issue_details)) > 0",
            name="ck_parsing_review_records_issue_details_nonempty",
        ),
    )

    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("approved_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )
    issue_type: Mapped[ParsingIssueType] = mapped_column(
        Enum(
            ParsingIssueType,
            name="parsing_issue_type",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    issue_details: Mapped[str] = mapped_column(Text, nullable=False)
    review_status: Mapped[ParsingReviewStatus] = mapped_column(
        Enum(
            ParsingReviewStatus,
            name="parsing_review_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        default=ParsingReviewStatus.PENDING,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)


class PreparationValidation(ModelBase):
    """A named quality gate result for a knowledge-base release."""

    __tablename__ = "preparation_validations"
    __table_args__ = (
        CheckConstraint(
            "length(trim(check_name)) > 0",
            name="ck_preparation_validations_check_name_nonempty",
        ),
        CheckConstraint(
            "length(trim(measured_value)) > 0",
            name="ck_preparation_validations_measured_value_nonempty",
        ),
        CheckConstraint(
            "length(trim(details)) > 0",
            name="ck_preparation_validations_details_nonempty",
        ),
    )

    release_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_base_releases.id", ondelete="CASCADE"),
        nullable=False,
    )
    check_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ValidationStatus] = mapped_column(
        Enum(
            ValidationStatus,
            name="validation_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )
    measured_value: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
    )