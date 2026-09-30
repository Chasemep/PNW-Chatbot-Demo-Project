"""Citation construction for retrieved authoritative source chunks."""

from app.models.source import ApprovedSource
from app.models.source_chunk import SourceContentSegment
from app.schemas.chat import CitationResponse


def build_citations(
    chunks: list[SourceContentSegment],
    sources: dict,
) -> list[CitationResponse]:
    """Build source citations without inventing provenance."""

    citations: list[CitationResponse] = []
    for chunk in chunks:
        source: ApprovedSource | None = sources.get(chunk.source_id)
        if source is None:
            continue
        citations.append(
            CitationResponse(
                source_id=source.id,
                source_url=source.source_url,
                citation_text=chunk.source_snippet or chunk.content_text,
            )
        )
    return citations