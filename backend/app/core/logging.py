"""Structured application logging configuration."""

import json
import logging
import logging.config
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings


class JsonFormatter(logging.Formatter):
    """Format log records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure consistent structured logging for the backend process."""

    settings = get_settings()
    level = settings.log_level.upper()
    if level not in logging._nameToLevel:
        level = "INFO"

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

def log_grounding_event(
    event: str,
    *,
    response_type: str,
    citation_count: int = 0,
    failure_reason: str | None = None,
) -> None:
    """Emit structured grounding and provider-failure metadata without secrets."""

    logging.getLogger("purdue.grounding").info(
        "grounding_event=%s response_type=%s citation_count=%d failure_reason=%s",
        event,
        response_type,
        citation_count,
        failure_reason or "none",
    )