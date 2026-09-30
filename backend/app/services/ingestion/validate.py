"""Validation gates for isolated knowledge-base releases."""

from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime
from math import isfinite
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.answer_log import AnswerCitation
from app.models.base import ReleaseStatus, ReviewStatus
from app.models.review_record import (
    PreparationValidation,
    ValidationStatus,
)
from app.models.source import ApprovedSource, KnowledgeBaseRelease
from app.models.source_chunk import SourceContentSegment

REQUIRED_GATES = (
    "metadata",
    "parse_completeness",
    "duplicate_or_empty_chunks",
    "approval",
    "vector",
    "retrieval_smoke",
    "citation_resolution",
)

SmokeQuestion = str | tuple[str, Sequence[str]]
Retriever = Callable[[Session, UUID, str], Iterable[SourceContentSegment]]


def validate_release(
    database: Session,
    release_id: UUID,
    *,
    smoke_questions: Sequence[SmokeQuestion] = (),
    retriever: Retriever | None = None,
) -> bool:
    """Run required quality gates and return whether a release can publish."""

    release = database.get(KnowledgeBaseRelease, release_id)
    if release is None:
        raise ValueError(f"knowledge-base release {release_id} does not exist")

    database.query(PreparationValidation).filter_by(release_id=release_id).delete(
        synchronize_session=False
    )

    chunks = (
        database.query(SourceContentSegment)
        .filter_by(release_id=release_id)
        .order_by(SourceContentSegment.chunk_index)
        .all()
    )
    source_ids = {chunk.source_id for chunk in chunks}
    sources = {
        source.id: source
        for source in database.query(ApprovedSource)
        .filter(ApprovedSource.id.in_(source_ids))
        .all()
    }

    results = [
        _metadata_gate(release),
        _parse_completeness_gate(chunks),
        _duplicate_or_empty_gate(chunks),
        _approval_gate(chunks, sources),
        _vector_gate(release, chunks),
        _retrieval_smoke_gate(
            database,
            release_id,
            chunks,
            smoke_questions,
            retriever,
        ),
        _citation_resolution_gate(database, release_id),
    ]
    database.add_all(
        PreparationValidation(
            release_id=release_id,
            check_name=check_name,
            status=status,
            measured_value=measured_value,
            details=details,
        )
        for check_name, status, measured_value, details in results
    )

    passed = all(status is ValidationStatus.PASSED for _, status, _, _ in results)
    if passed:
        release.status = ReleaseStatus.VALIDATED
        release.validated_at = datetime.now(UTC)
        release.failure_summary = None
    else:
        release.status = ReleaseStatus.REJECTED
        release.failure_summary = "; ".join(
            f"{check_name}: {details}"
            for check_name, status, _, details in results
            if status is ValidationStatus.FAILED
        )

    database.flush()
    return passed


def _metadata_gate(
    release: KnowledgeBaseRelease,
) -> tuple[str, ValidationStatus, str, str]:
    missing_fields = [
        field_name
        for field_name in ("embedding_model", "embedding_dimension", "started_at")
        if not getattr(release, field_name, None)
    ]
    if release.embedding_dimension <= 0:
        missing_fields.append("positive embedding_dimension")

    if missing_fields:
        return (
            "metadata",
            ValidationStatus.FAILED,
            "missing_or_invalid",
            f"Missing or invalid release metadata: {', '.join(missing_fields)}",
        )
    return (
        "metadata",
        ValidationStatus.PASSED,
        "complete",
        "Release metadata is complete.",
    )


def _parse_completeness_gate(
    chunks: list[SourceContentSegment],
) -> tuple[str, ValidationStatus, str, str]:
    if not chunks:
        return (
            "parse_completeness",
            ValidationStatus.FAILED,
            "0_chunks",
            "The release contains no parsed chunks.",
        )

    incomplete = [
        str(chunk.id)
        for chunk in chunks
        if not all(
            isinstance(value, str) and value.strip()
            for value in (
                chunk.content_text,
                chunk.structural_path,
                chunk.location_label,
                chunk.chunk_hash,
            )
        )
        or chunk.chunk_index < 0
    ]
    if incomplete:
        return (
            "parse_completeness",
            ValidationStatus.FAILED,
            f"{len(incomplete)}_incomplete",
            f"Chunks are missing required parsed metadata: {', '.join(incomplete)}",
        )
    return (
        "parse_completeness",
        ValidationStatus.PASSED,
        f"{len(chunks)}_chunks",
        "All chunks contain parsed content and structural provenance.",
    )


def _duplicate_or_empty_gate(
    chunks: list[SourceContentSegment],
) -> tuple[str, ValidationStatus, str, str]:
    hashes: dict[str, int] = {}
    empty_count = 0
    for chunk in chunks:
        if not isinstance(chunk.content_text, str) or not chunk.content_text.strip():
            empty_count += 1
        hashes[chunk.chunk_hash] = hashes.get(chunk.chunk_hash, 0) + 1

    duplicate_hashes = sorted(
        chunk_hash for chunk_hash, count in hashes.items() if count > 1
    )
    if empty_count or duplicate_hashes:
        problems = []
        if empty_count:
            problems.append(f"{empty_count} empty chunks")
        if duplicate_hashes:
            problems.append(f"duplicate hashes: {', '.join(duplicate_hashes)}")
        return (
            "duplicate_or_empty_chunks",
            ValidationStatus.FAILED,
            "failed",
            "; ".join(problems),
        )
    return (
        "duplicate_or_empty_chunks",
        ValidationStatus.PASSED,
        f"{len(chunks)}_unique_chunks",
        "Chunks are non-empty and have unique hashes.",
    )


def _approval_gate(
    chunks: list[SourceContentSegment],
    sources: dict[UUID, ApprovedSource],
) -> tuple[str, ValidationStatus, str, str]:
    unauthorized = []
    for chunk in chunks:
        source = sources.get(chunk.source_id)
        if (
            source is None
            or source.review_status is not ReviewStatus.APPROVED
            or not source.is_active
            or source.superseded_by is not None
        ):
            unauthorized.append(str(chunk.id))

    if unauthorized:
        return (
            "approval",
            ValidationStatus.FAILED,
            f"{len(unauthorized)}_unauthorized_chunks",
            "Chunks reference unapproved or inactive sources: "
            f"{', '.join(unauthorized)}",
        )
    return (
        "approval",
        ValidationStatus.PASSED,
        f"{len(chunks)}_approved_chunks",
        "All chunks reference active approved sources.",
    )


def _vector_gate(
    release: KnowledgeBaseRelease,
    chunks: list[SourceContentSegment],
) -> tuple[str, ValidationStatus, str, str]:
    invalid = []
    for chunk in chunks:
        vector = chunk.embedding
        if not _is_valid_vector(vector, release.embedding_dimension):
            invalid.append(str(chunk.id))

    if invalid:
        return (
            "vector",
            ValidationStatus.FAILED,
            f"{len(invalid)}_invalid_vectors",
            f"Chunks have invalid vectors: {', '.join(invalid)}",
        )
    return (
        "vector",
        ValidationStatus.PASSED,
        f"{len(chunks)}_valid_vectors",
        "All vectors match the release dimension and contain finite values.",
    )


def _is_valid_vector(value: Any, expected_dimension: int) -> bool:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        return False
    try:
        vector = list(value)
    except TypeError:
        return False
    return len(vector) == expected_dimension and all(
        isinstance(component, (int, float)) and isfinite(component)
        for component in vector
    )


def _retrieval_smoke_gate(
    database: Session,
    release_id: UUID,
    chunks: list[SourceContentSegment],
    smoke_questions: Sequence[SmokeQuestion],
    retriever: Retriever | None,
) -> tuple[str, ValidationStatus, str, str]:
    if not smoke_questions:
        return (
            "retrieval_smoke",
            ValidationStatus.PASSED,
            "0_questions",
            "No retrieval smoke questions were configured.",
        )

    failures = []
    for question in smoke_questions:
        question_text, expected_terms = _smoke_question_parts(question)
        if not question_text:
            failures.append("empty question")
            continue

        matches = list(
            retriever(database, release_id, question_text)
            if retriever is not None
            else _lexical_smoke_matches(chunks, question_text)
        )
        if not matches:
            failures.append(f"no results for {question_text!r}")
            continue

        if expected_terms and not any(
            _contains_term(chunk.content_text, expected_terms) for chunk in matches
        ):
            failures.append(f"expected terms not found for {question_text!r}")

    if failures:
        return (
            "retrieval_smoke",
            ValidationStatus.FAILED,
            f"{len(failures)}_failed_questions",
            "; ".join(failures),
        )
    return (
        "retrieval_smoke",
        ValidationStatus.PASSED,
        f"{len(smoke_questions)}_passed_questions",
        "All retrieval smoke questions returned relevant chunks.",
    )


def _citation_resolution_gate(
    database: Session,
    release_id: UUID,
) -> tuple[str, ValidationStatus, str, str]:
    citations = (
        database.query(AnswerCitation)
        .join(
            SourceContentSegment,
            AnswerCitation.chunk_id == SourceContentSegment.id,
        )
        .filter(SourceContentSegment.release_id == release_id)
        .all()
    )
    if not citations:
        return (
            "citation_resolution",
            ValidationStatus.PASSED,
            "0_citations",
            "No citations were present for this release.",
        )

    chunks = {
        chunk.id: chunk
        for chunk in database.query(SourceContentSegment)
        .filter(SourceContentSegment.release_id == release_id)
        .all()
    }
    sources = {
        source.id: source
        for source in database.query(ApprovedSource)
        .filter(ApprovedSource.id.in_({citation.source_id for citation in citations}))
        .all()
    }
    failures = []
    for citation in citations:
        chunk = chunks.get(citation.chunk_id)
        source = sources.get(citation.source_id)
        if (
            chunk is None
            or source is None
            or chunk.source_id != citation.source_id
            or source.source_url != citation.source_url
            or not citation.citation_text.strip()
        ):
            failures.append(str(citation.id))

    if failures:
        return (
            "citation_resolution",
            ValidationStatus.FAILED,
            f"{len(failures)}_unresolved_citations",
            f"Citations do not resolve to their source chunks: {', '.join(failures)}",
        )
    return (
        "citation_resolution",
        ValidationStatus.PASSED,
        f"{len(citations)}_resolved_citations",
        "All citations resolve to source chunks and canonical source URLs.",
    )


def _smoke_question_parts(
    question: SmokeQuestion,
) -> tuple[str, Sequence[str]]:
    if isinstance(question, tuple):
        return question[0].strip(), question[1]
    return question.strip(), ()


def _lexical_smoke_matches(
    chunks: Sequence[SourceContentSegment],
    question: str,
) -> list[SourceContentSegment]:
    terms = _terms(question)
    return [chunk for chunk in chunks if terms.intersection(_terms(chunk.content_text))]


def _contains_term(text: str, expected_terms: Sequence[str]) -> bool:
    normalized_text = _terms(text)
    return any(_terms(term).intersection(normalized_text) for term in expected_terms)


def _terms(text: str) -> set[str]:
    return {
        term
        for term in "".join(
            character.lower() if character.isalnum() else " " for character in text
        ).split()
        if len(term) > 2
    }