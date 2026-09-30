from uuid import UUID

from app.main import app
from fastapi.testclient import TestClient


def test_chat_returns_a_cited_direct_answer_for_a_supported_question() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={
                "question": "What is the deadline to drop a class?",
                "student_type": "undergraduate",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"]
    assert payload["response_type"] == "direct_answer"
    assert payload["citations"]
    citation = payload["citations"][0]
    UUID(citation["source_id"])
    assert citation["source_url"]
    assert citation["citation_text"]


def test_chat_returns_a_safe_referral_when_the_question_is_unsupported() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"question": "Can I get a personal exception to this policy?"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"]
    assert payload["response_type"] == "safe_referral"
    assert payload["referral"]["office_name"]
    assert payload["referral"]["referral_reason"]
    assert payload["citations"] == []


def test_chat_rejects_blank_questions_and_unknown_student_types() -> None:
    with TestClient(app) as client:
        blank_question = client.post("/api/chat", json={"question": "   "})
        invalid_student_type = client.post(
            "/api/chat",
            json={
                "question": "What is the registration deadline?",
                "student_type": "nonexistent",
            },
        )

    assert blank_question.status_code == 422
    assert invalid_student_type.status_code == 422