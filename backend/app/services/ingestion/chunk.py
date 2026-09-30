"""Deterministic, structure-aware chunks for source retrieval."""

from dataclasses import dataclass
from hashlib import sha256

from app.models.base import ContentKind
from app.services.ingestion.parser import StructuralBlock


@dataclass(frozen=True, slots=True)
class Chunk:
    """A bounded, traceable unit of source content ready for embedding."""

    content_text: str
    structural_path: str
    location_label: str
    content_kind: ContentKind
    ordinal: int
    chunk_hash: str


def chunk_blocks(
    blocks: list[StructuralBlock],
    *,
    source_version_hash: str,
    max_characters: int,
) -> list[Chunk]:
    """Create deterministic chunks without splitting semantic table/list rows."""

    if not source_version_hash.strip():
        raise ValueError("source_version_hash must not be blank")
    if max_characters <= 0:
        raise ValueError("max_characters must be positive")

    chunks: list[Chunk] = []
    heading_context: str | None = None

    for block in blocks:
        if block.content_kind is ContentKind.HEADING:
            heading_context = block.content_text

        prefix = _context_prefix(
            heading_context,
            block.content_text,
            block.content_kind,
        )
        units = _semantic_units(block)
        if block.content_kind is ContentKind.TABLE:
            packed_chunks = _pack_table_rows(units, prefix, max_characters)
        else:
            packed_chunks = _pack_units(units, prefix, max_characters)
        for block_chunk_index, content_text in enumerate(packed_chunks):
            chunk_kind = (
                block.content_kind
                if block_chunk_index == 0
                else ContentKind.CONTINUATION
            )
            ordinal = len(chunks)
            chunks.append(
                Chunk(
                    content_text=content_text,
                    structural_path=block.structural_path,
                    location_label=block.location_label,
                    content_kind=chunk_kind,
                    ordinal=ordinal,
                    chunk_hash=_chunk_hash(
                        source_version_hash=source_version_hash,
                        structural_path=block.structural_path,
                        location_label=block.location_label,
                        content_kind=chunk_kind,
                        ordinal=ordinal,
                        content_text=content_text,
                    ),
                )
            )

    return chunks


def _context_prefix(
    heading_context: str | None,
    content_text: str,
    content_kind: ContentKind,
) -> str:
    if (
        content_kind is ContentKind.HEADING
        or heading_context is None
        or content_text.startswith(heading_context)
    ):
        return ""
    return f"{heading_context}\n"


def _semantic_units(block: StructuralBlock) -> list[str]:
    if block.content_kind in {ContentKind.TABLE, ContentKind.LIST}:
        return block.content_text.splitlines()
    return _split_paragraph(block.content_text)


def _split_paragraph(content_text: str) -> list[str]:
    """Split ordinary prose at words, retaining all characters semantically."""

    words = content_text.split()
    if not words:
        raise ValueError("content_text must contain at least one word")
    return words


def _pack_units(
    units: list[str],
    prefix: str,
    max_characters: int,
) -> list[str]:
    if not units:
        raise ValueError("content_text must contain at least one semantic unit")

    packed_chunks: list[str] = []
    current_units: list[str] = []
    separator = "\n" if len(units) > 1 else " "

    for unit in units:
        candidate_units = [*current_units, unit]
        candidate = _with_prefix(prefix, separator.join(candidate_units))
        if len(candidate) <= max_characters:
            current_units = candidate_units
            continue

        if not current_units:
            raise ValueError("semantic unit exceeds max_characters")
        packed_chunks.append(_with_prefix(prefix, separator.join(current_units)))
        if len(_with_prefix(prefix, unit)) > max_characters:
            raise ValueError("semantic unit exceeds max_characters")
        current_units = [unit]

    packed_chunks.append(_with_prefix(prefix, separator.join(current_units)))
    return packed_chunks


def _pack_table_rows(
    rows: list[str],
    prefix: str,
    max_characters: int,
) -> list[str]:
    """Pack complete table rows while repeating the column-context row."""

    if not rows:
        raise ValueError("table content must contain at least one row")

    column_context = rows[0]
    context_prefix = _with_prefix(prefix, f"{column_context}\n")
    if len(context_prefix) > max_characters:
        raise ValueError("table column context exceeds max_characters")

    packed_chunks: list[str] = []
    current_rows: list[str] = []
    for row in rows[1:]:
        candidate_rows = [*current_rows, row]
        candidate = _with_prefix(
            context_prefix,
            "\n".join(candidate_rows),
        )
        if len(candidate) <= max_characters:
            current_rows = candidate_rows
            continue

        if not current_rows:
            raise ValueError("table row exceeds max_characters")
        packed_chunks.append(
            _with_prefix(context_prefix, "\n".join(current_rows))
        )
        current_rows = [row]
        if len(_with_prefix(context_prefix, row)) > max_characters:
            raise ValueError("table row exceeds max_characters")

    if current_rows:
        packed_chunks.append(
            _with_prefix(context_prefix, "\n".join(current_rows))
        )
    else:
        packed_chunks.append(context_prefix)
    return packed_chunks


def _with_prefix(prefix: str, content_text: str) -> str:
    return f"{prefix}{content_text}"


def _chunk_hash(
    *,
    source_version_hash: str,
    structural_path: str,
    location_label: str,
    content_kind: ContentKind,
    ordinal: int,
    content_text: str,
) -> str:
    """Hash every retrieval-relevant field with unambiguous separators."""

    fields = (
        source_version_hash,
        structural_path,
        location_label,
        content_kind.value,
        str(ordinal),
        content_text,
    )
    return sha256("\x1f".join(fields).encode()).hexdigest()
