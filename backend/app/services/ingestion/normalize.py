"""Canonical normalization for parsed structural source blocks."""

import re
import unicodedata

from app.services.ingestion.parser import StructuralBlock

_INLINE_WHITESPACE = re.compile(r"[^\S\r\n]+")
_UNVERIFIABLE_CHARACTERS = frozenset({"\ufffd"})


def normalize_blocks(blocks: list[StructuralBlock]) -> list[StructuralBlock]:
    """Return canonical, traceable blocks suitable for deterministic chunking."""

    normalized_blocks: list[StructuralBlock] = []
    for block in blocks:
        content_text = _normalize_content(block.content_text)
        if not content_text:
            raise ValueError("content_text must not be empty after normalization")
        if any(character in content_text for character in _UNVERIFIABLE_CHARACTERS):
            raise ValueError("content_text contains unverifiable extraction characters")

        normalized_blocks.append(
            StructuralBlock(
                content_kind=block.content_kind,
                content_text=content_text,
                structural_path=_normalize_metadata(
                    block.structural_path,
                    "structural_path",
                ),
                location_label=_normalize_metadata(
                    block.location_label,
                    "location_label",
                ),
                ordinal=block.ordinal,
            )
        )

    return normalized_blocks


def _normalize_content(value: str) -> str:
    """Canonicalize text without flattening table rows or list items."""

    canonical_value = unicodedata.normalize("NFC", value).replace("\r\n", "\n")
    canonical_value = canonical_value.replace("\r", "\n")
    return "\n".join(
        _INLINE_WHITESPACE.sub(" ", line).strip()
        for line in canonical_value.split("\n")
    ).strip()


def _normalize_metadata(value: str, field_name: str) -> str:
    """Canonicalize required provenance metadata."""

    normalized_value = _INLINE_WHITESPACE.sub(
        " ",
        unicodedata.normalize("NFC", value),
    ).strip()
    if not normalized_value:
        raise ValueError(f"{field_name} must not be empty after normalization")
    return normalized_value
