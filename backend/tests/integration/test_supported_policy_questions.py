import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("question", "student_type"),
    [
        ("What is the deadline to add a class?", "undergraduate"),
        ("How do I drop a class?", "undergraduate"),
        ("What counts as good academic standing?", "graduate"),
        ("How do I appeal a grade?", "undergraduate"),
        ("When is the financial aid deadline?", "undergraduate"),
        ("How do I register for classes?", "graduate"),
        ("Who should I contact about registration?", "unknown"),
    ],
)
def test_supported_policy_question_returns_grounded_citation(
    question: str,
    student_type: str,
) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"question": question, "student_type": student_type},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["response_type"] == "direct_answer"
    assert payload["answer"]
    assert payload["citations"]
    assert all(
        citation["source_url"] and citation["citation_text"]
        for citation in payload["citations"]
    )


def test_supported_question_preserves_student_type_distinctions() -> None:
    question = "What are the academic standing requirements?"

    with TestClient(app) as client:
        undergraduate_response = client.post(
            "/api/chat",
            json={"question": question, "student_type": "undergraduate"},
        )
        graduate_response = client.post(
            "/api/chat",
            json={"question": question, "student_type": "graduate"},
        )

    assert undergraduate_response.status_code == 200
    assert graduate_response.status_code == 200
    assert undergraduate_response.json()["citations"]
    assert graduate_response.json()["citations"]
