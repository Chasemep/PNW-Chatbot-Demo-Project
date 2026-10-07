"""Safe, shared error responses for the FastAPI application."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ApplicationError(Exception):
    """Base error with a client-safe message and explicit HTTP status."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "The request could not be completed."


class BadRequestError(ApplicationError):
    """Report an invalid request without exposing internal validation details."""

    status_code = status.HTTP_400_BAD_REQUEST
    message = "The request could not be processed."


class NotFoundError(ApplicationError):
    """Report a missing resource."""

    status_code = status.HTTP_404_NOT_FOUND
    message = "The requested resource was not found."


class ServiceUnavailableError(ApplicationError):
    """Report an unavailable dependency without exposing provider details."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    message = "The service is temporarily unavailable. Please try again later."


def _error_response(status_code: int, message: str) -> JSONResponse:
    """Create the standard client-safe error response."""

    return JSONResponse(status_code=status_code, content={"detail": message})


def register_error_handlers(app: FastAPI) -> None:
    """Register handlers that log safely and return non-success HTTP responses."""

    @app.exception_handler(ApplicationError)
    async def handle_application_error(
        request: Request, error: ApplicationError
    ) -> JSONResponse:
        logger.warning(
            "Application error type=%s path=%s",
            type(error).__name__,
            request.url.path,
        )
        return _error_response(error.status_code, error.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        logger.warning(
            "Request validation failed path=%s error_count=%d",
            request.url.path,
            len(error.errors()),
        )
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "The request contains invalid data.",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request, error: Exception
    ) -> JSONResponse:
        logger.error(
            "Unhandled request error type=%s path=%s",
            type(error).__name__,
            request.url.path,
            exc_info=error,
        )
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An unexpected error occurred.",
        )
