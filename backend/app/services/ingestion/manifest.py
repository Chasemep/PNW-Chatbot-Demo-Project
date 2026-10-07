"""Validation for operator-supplied approved-source manifests."""

from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    field_validator,
    model_validator,
)

from app.models.base import ReviewStatus, SourceType


class ManifestSource(BaseModel):
    """One source declared in an approved-source manifest."""

    model_config = ConfigDict(str_strip_whitespace=True)

    source_key: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=500)
    location: str = Field(min_length=1)
    source_url: str | None = Field(default=None, min_length=1)
    source_type: SourceType
    issuing_office: str = Field(min_length=1, max_length=255)
    review_status: ReviewStatus
    effective_date: date
    reviewed_at: datetime

    @field_validator("source_key", "title", "location", "source_url", "issuing_office")
    @classmethod
    def require_text(cls, value: str | None) -> str | None:
        """Reject blank identifiers and source metadata."""

        if value is not None and not value:
            raise ValueError("value must not be blank")
        return value

    @field_validator("source_url")
    @classmethod
    def require_http_source_url(cls, value: str | None) -> str | None:
        """Ensure browser-facing citation URLs use HTTP(S)."""

        if value is None:
            return None
        parsed_url = urlparse(value)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("source_url must be an absolute HTTP(S) URL")
        return value

    @model_validator(mode="after")
    def require_canonical_url_for_local_source(self) -> "ManifestSource":
        """Require a public citation target when ingestion reads a local file."""

        parsed_location = urlparse(self.location)
        if parsed_location.scheme not in {"http", "https"} and self.source_url is None:
            raise ValueError("source_url is required when location is a local file")
        return self

    @field_validator("reviewed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        """Require an offset so review timestamps remain unambiguous."""

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("reviewed_at must include a timezone")
        return value


def validate_manifest(payload: Any) -> list[ManifestSource]:
    """Validate manifest records and reject duplicate canonical identities."""

    sources = TypeAdapter(list[ManifestSource]).validate_python(payload)
    source_keys = [source.source_key for source in sources]
    if len(set(source_keys)) != len(source_keys):
        raise ValueError("manifest contains duplicate source_key values")
    return sources
