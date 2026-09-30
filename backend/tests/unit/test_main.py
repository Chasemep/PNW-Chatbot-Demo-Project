from app.main import app
from fastapi.testclient import TestClient


def test_application_exposes_configured_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert app.title == "Purdue Policy Chatbot"
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_application_allows_public_chat_cors_preflight() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/api/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
