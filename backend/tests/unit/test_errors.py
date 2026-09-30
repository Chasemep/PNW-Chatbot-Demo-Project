from app.core.errors import (
    BadRequestError,
    ServiceUnavailableError,
    register_error_handlers,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


def create_client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/bad-request")
    def bad_request() -> None:
        raise BadRequestError()

    @app.get("/unavailable")
    def unavailable() -> None:
        raise ServiceUnavailableError()

    @app.get("/unexpected")
    def unexpected() -> None:
        raise RuntimeError("database password=not-for-client")

    return TestClient(app, raise_server_exceptions=False)


def test_application_error_returns_safe_client_message() -> None:
    response = create_client().get("/bad-request")

    assert response.status_code == 400
    assert response.json() == {"detail": "The request could not be processed."}


def test_unavailable_dependency_returns_non_success_response() -> None:
    response = create_client().get("/unavailable")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "The service is temporarily unavailable. Please try again later."
    }


def test_unexpected_error_does_not_expose_its_details() -> None:
    response = create_client().get("/unexpected")

    assert response.status_code == 500
    assert response.json() == {"detail": "An unexpected error occurred."}
    assert "password" not in response.text
