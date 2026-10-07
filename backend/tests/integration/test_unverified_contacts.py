from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy.orm import Session, sessionmaker

OFFICIAL_DIRECTORY_URL = "https://www.pnw.edu/academic-and-administrative-offices/"


def test_unverified_contact_uses_official_directory_fallback(
    contact_api: tuple[TestClient, sessionmaker[Session]],
    monkeypatch: MonkeyPatch,
):
    client, _session_factory = contact_api
    monkeypatch.setattr(
        "app.api.routes.chat._retrieve_chunks",
        lambda *_args: [],
    )

    response = client.post(
        "/api/chat",
        json={"question": "Who can help me with a campus parking ticket?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["response_type"] == "safe_referral"
    assert payload["citations"] == []
    assert payload["referral"]["contact_url"] == OFFICIAL_DIRECTORY_URL
    assert "verify" in payload["answer"].lower()
