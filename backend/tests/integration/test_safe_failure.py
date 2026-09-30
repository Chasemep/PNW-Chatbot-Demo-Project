from app.main import app
from fastapi.testclient import TestClient


def test_unsupported_question_returns_safe_referral_without_citations():
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"question": "Can I receive a personal policy exception?"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["response_type"] == "safe_referral"
    assert payload["citations"] == []
    assert payload["referral"]["office_name"]


def test_context_sensitive_question_requests_student_type():
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"question": "What are the academic standing requirements?"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["response_type"] == "clarification_needed"
    assert payload["clarification_prompt"]
    assert payload["citations"] == []