"""Shared structural block types and source parser dispatch."""

from dataclasses import dataclass
from pathlib import Path

from app.models.base import ContentKind


@dataclass(frozen=True, slots=True)
class StructuralBlock:
    """A meaningful ordered portion of a parsed source."""

    content_kind: ContentKind
    content_text: str
    structural_path: str
    location_label: str
    ordinal: int

    def __post_init__(self) -> None:
        """Reject blocks that cannot be traced or retrieved."""

        if not self.content_text.strip():
            raise ValueError("content_text must not be blank")
        if not self.structural_path.strip():
            raise ValueError("structural_path must not be blank")
        if not self.location_label.strip():
            raise ValueError("location_label must not be blank")
        if self.ordinal < 0:
            raise ValueError("ordinal must not be negative")


@dataclass(slots=True)
class ParsedDocument:
    """Ordered parser output plus a review signal for unreliable extraction."""

    blocks: list[StructuralBlock]
    review_reason: str | None = None


def parse_source(path: Path) -> ParsedDocument:
    """Dispatch a local source to its format-specific parser."""

    suffix = path.suffix.lower()
    if suffix in {".html", ".htm"}:
        from app.services.ingestion.html import parse_html

        return parse_html(path)
    if suffix == ".pdf":
        from app.services.ingestion.pdf import parse_pdf

        return parse_pdf(path)
    if suffix == ".docx":
        from app.services.ingestion.docx import parse_docx

        return parse_docx(path)
    raise ValueError(f"unsupported source format: {suffix or 'no extension'}")
