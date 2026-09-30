from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.models.base import ReleaseStatus, ResponseType, ReviewStatus, SourceType
from app.schemas.chat import ChatRequest, ChatResponse, CitationResponse
from app.schemas.review import ParsingReviewRead
from app.schemas.source import ReleaseRead, SourceCreate
from pydantic import ValidationError


def source_payload(**overrides):
    values = {
        "title": "Registration Calendar",
        "source_url": "https://example.edu/registration",
        "source_type": SourceType.WEBPAGE,
        "issuing_office": "Registrar",
        "reviewed_at": datetime.now(UTC),
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize("field", ["title", "source_url", "issuing_office"])
def test_source_schema_rejects_blank_required_text(field):
    with pytest.raises(ValidationError):
        SourceCreate(**source_payload(**{field: "   "}))


def test_source_schema_enforces_authority_invariants():
    with pytest.raises(ValidationError, match="superseded_by"):
        SourceCreate(
            **source_payload(
                review_status=ReviewStatus.SUPERSEDED,
                is_active=False,
            )
        )

    with pytest.raises(ValidationError, match="active"):
        SourceCreate(
            **source_payload(
                review_status=ReviewStatus.APPROVED,
                is_active=False,
            )
        )


def test_release_schema_requires_positive_embedding_dimension():
    with pytest.raises(ValidationError):
        ReleaseRead(
            id=uuid4(),
            status=ReleaseStatus.ACTIVE,
            embedding_model="test-model",
            embedding_dimension=0,
            started_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


def test_chat_schema_requires_direct_answer_citation():
    with pytest.raises(ValidationError, match="citation"):
        ChatResponse(
            answer="The deadline is listed in the academic calendar.",
            response_type=ResponseType.DIRECT_ANSWER,
        )

    response = ChatResponse(
        answer="The deadline is listed in the academic calendar.",
        response_type=ResponseType.DIRECT_ANSWER,
        citations=[
            CitationResponse(
                source_id=uuid4(),
                source_url="https://example.edu/calendar",
                citation_text="Academic calendar",
            )
        ],
    )
    assert response.citations[0].citation_text == "Academic calendar"


def test_chat_request_and_review_schema_reject_blank_content():
    with pytest.raises(ValidationError):
        ChatRequest(question="   ")

    with pytest.raises(ValidationError):
        ParsingReviewRead(
            id=uuid4(),
            source_id=uuid4(),
            issue_type="parse_failure",
            issue_details="   ",
            review_status="pending",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
