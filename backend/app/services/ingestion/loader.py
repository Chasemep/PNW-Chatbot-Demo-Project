"""Local and remote source loading with immutable content versions."""

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import cast
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen


class SourceLoadError(ValueError):
    """Raised when a source cannot be loaded safely."""


@dataclass(frozen=True, slots=True)
class LoadedSourceVersion:
    """Immutable source bytes and provenance captured for one preparation run."""

    original_location: str
    content: bytes
    content_hash: str
    fetched_at: datetime

    @property
    def byte_size(self) -> int:
        """Return the source byte count."""

        return len(self.content)


def load_source(
    location: str,
    *,
    source_root: Path | None = None,
    timeout_seconds: float = 30.0,
) -> LoadedSourceVersion:
    """Read a local file or HTTP(S) URL and produce an immutable version."""

    parsed_location = urlparse(location)
    if parsed_location.scheme in {"http", "https"}:
        content = _load_remote_source(location, timeout_seconds)
    elif parsed_location.scheme:
        raise SourceLoadError(f"unsupported source scheme: {parsed_location.scheme}")
    else:
        content = _load_local_source(location, source_root)

    return LoadedSourceVersion(
        original_location=location,
        content=content,
        content_hash=sha256(content).hexdigest(),
        fetched_at=datetime.now(UTC),
    )


def _load_local_source(location: str, source_root: Path | None) -> bytes:
    path = Path(location)
    if source_root is not None:
        root = source_root.resolve()
        path = (root / path).resolve()
        if not path.is_relative_to(root):
            raise SourceLoadError("local source is outside source_root")

    try:
        return path.read_bytes()
    except OSError as error:
        raise SourceLoadError(f"could not read local source: {path}") from error


def _load_remote_source(location: str, timeout_seconds: float) -> bytes:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")

    try:
        with urlopen(location, timeout=timeout_seconds) as response:  # noqa: S310
            return cast(bytes, response.read())
    except URLError as error:
        raise SourceLoadError("could not fetch remote source") from error
