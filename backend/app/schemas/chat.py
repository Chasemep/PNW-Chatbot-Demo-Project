"""Pydantic schemas for the student chat API."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.base import ResponseType, StudentType


def require_question(value: str) -> str:
    """Reject blank questions while normalizing surrounding whitespace."""

    normalized = value.strip()
    if not normalized:
        raise ValueError("question must not be blank")
    return normalized


def require_response_text(value: str) -> str:
    """Reject blank response and citation text."""

    normalized = value.strip()
    if not normalized:
        raise ValueError("value must not be blank")
    return normalized


class ChatRequest(BaseModel):
    """Student question submitted to the chat endpoint."""

    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(min_length=1)
    student_type: StudentType = StudentType.UNKNOWN

    _validate_question = field_validator("question")(require_question)


class CitationResponse(BaseModel):
    """Approved source citation included with a chat response."""

    source_id: UUID
    source_url: str = Field(min_length=1)
    citation_text: str = Field(min_length=1)

    _validate_text = field_validator("source_url", "citation_text")(
        require_response_text
    )


class ReferralResponse(BaseModel):
    """Verified office or directory referral included with a chat response."""

    office_name: str = Field(min_length=1)
    referral_reason: str = Field(min_length=1)
    contact_url: str | None = Field(default=None, min_length=1)

    _validate_text = field_validator("office_name", "referral_reason")(
        require_response_text
    )
    _validate_contact_url = field_validator("contact_url")(
        lambda value: require_response_text(value) if value is not None else value
    )


class ChatResponse(BaseModel):
    """Grounded answer, clarification, or safe referral returned to a student."""

    model_config = ConfigDict(str_strip_whitespace=True)

    answer: str = Field(min_length=1)
    response_type: ResponseType
    citations: list[CitationResponse] = Field(default_factory=list)
    referral: ReferralResponse | None = None
    clarification_prompt: str | None = Field(default=None, min_length=1)

    _validate_text = field_validator("answer", "clarification_prompt")(
        lambda value: require_response_text(value) if value is not None else value
    )

    @model_validator(mode="after")
    def validate_response_requirements(self) -> "ChatResponse":
        """Require the supporting data appropriate for each response type."""

        if self.response_type is ResponseType.DIRECT_ANSWER and not self.citations:
            raise ValueError("direct answers require at least one citation")
        if (
            self.response_type is ResponseType.CLARIFICATION_NEEDED
            and not self.clarification_prompt
        ):
            raise ValueError("clarification responses require a prompt")
        if self.response_type is ResponseType.SAFE_REFERRAL and self.referral is None:
            raise ValueError("safe referrals require referral details")
        return self