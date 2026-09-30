"""Question, answer, citation, and safe-referral audit models."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import ModelBase, ResponseType, StudentType


class StudentQuestion(ModelBase):
    """A student's submitted natural-language question."""

    __tablename__ = "student_questions"
    __table_args__ = (
        CheckConstraint(
            "length(trim(raw_text)) > 0",
            name="ck_student_questions_raw_text_nonempty",
        ),
    )

    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    student_type: Mapped[StudentType] = mapped_column(
        Enum(
            StudentType,
            name="student_type",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        default=StudentType.UNKNOWN,
    )
    asked_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class GroundedAnswer(ModelBase):
    """A response produced from retrieved policy context."""

    __tablename__ = "grounded_answers"
    __table_args__ = (
        CheckConstraint(
            "length(trim(answer_text)) > 0",
            name="ck_grounded_answers_answer_text_nonempty",
        ),
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_grounded_answers_confidence_range",
        ),
    )

    question_id: Mapped[UUID] = mapped_column(
        ForeignKey("student_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    response_type: Mapped[ResponseType] = mapped_column(
        Enum(
            ResponseType,
            name="response_type",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )


class AnswerCitation(ModelBase):
    """A source-backed citation attached to a grounded answer."""

    __tablename__ = "answer_citations"
    __table_args__ = (
        CheckConstraint(
            "length(trim(source_url)) > 0",
            name="ck_answer_citations_source_url_nonempty",
        ),
        CheckConstraint(
            "length(trim(citation_text)) > 0",
            name="ck_answer_citations_citation_text_nonempty",
        ),
    )

    answer_id: Mapped[UUID] = mapped_column(
        ForeignKey("grounded_answers.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("approved_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )
    chunk_id: Mapped[UUID] = mapped_column(
        ForeignKey("source_content_segments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    citation_text: Mapped[str] = mapped_column(Text, nullable=False)


class SafeReferral(ModelBase):
    """A verified office or directory referral for an answer."""

    __tablename__ = "safe_referrals"
    __table_args__ = (
        UniqueConstraint("answer_id", name="uq_safe_referrals_answer_id"),
        CheckConstraint(
            "length(trim(office_name)) > 0",
            name="ck_safe_referrals_office_name_nonempty",
        ),
        CheckConstraint(
            "length(trim(referral_reason)) > 0",
            name="ck_safe_referrals_reason_nonempty",
        ),
        CheckConstraint(
            "length(trim(contact_url)) > 0",
            name="ck_safe_referrals_contact_url_nonempty",
        ),
    )

    answer_id: Mapped[UUID] = mapped_column(
        ForeignKey("grounded_answers.id", ondelete="CASCADE"),
        nullable=False,
    )
    office_name: Mapped[str] = mapped_column(String(255), nullable=False)
    referral_reason: Mapped[str] = mapped_column(Text, nullable=False)
    contact_url: Mapped[str] = mapped_column(Text, nullable=False)