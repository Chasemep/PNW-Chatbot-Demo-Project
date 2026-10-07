"""Student chat API route."""

import logging
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import DatabaseSession
from app.core.logging import log_grounding_event
from app.models.answer_log import (
    AnswerCitation,
    GroundedAnswer,
    SafeReferral,
    StudentQuestion,
)
from app.models.base import ResponseType
from app.models.source import ApprovedSource
from app.models.source_chunk import SourceContentSegment
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.answering import (
    AnswerGenerationError,
    GeminiAnswerer,
    assess_answer_safety,
    build_grounded_response,
    detect_ambiguity,
    is_contact_question,
)
from app.services.citation import build_citations
from app.services.ingestion.gemini_embed import GeminiEmbeddingProvider
from app.services.referral import build_contact_referral, select_verified_referral
from app.services.retrieval import retrieve_active_chunks

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, database: DatabaseSession) -> ChatResponse:
    """Return a grounded answer, clarification, or safe referral."""

    question = StudentQuestion(
        raw_text=request.question,
        student_type=request.student_type,
    )
    database.add(question)
    database.flush()

    clarification_prompt = detect_ambiguity(
        request.question,
        request.student_type.value,
    )
    if clarification_prompt:
        response = ChatResponse(
            answer="I need one detail before I can identify the applicable policy.",
            response_type=ResponseType.CLARIFICATION_NEEDED,
            clarification_prompt=clarification_prompt,
        )
        _persist_answer(database, question.id, response)
        database.commit()
        log_grounding_event(
            "clarification", response_type=response.response_type.value
        )
        return response

    chunks = _retrieve_chunks(database, request)
    contact_question = is_contact_question(request.question)
    contact_referral = (
        build_contact_referral(request.question, chunks) if contact_question else None
    )
    safety_reason = assess_answer_safety(request.question, chunks)
    if contact_question and contact_referral is None:
        safety_reason = (
            "I cannot verify current contact details from approved sources. "
            "Use the official Purdue Northwest directory to locate the "
            "appropriate office."
        )
    if safety_reason:
        response = _safe_referral_response(
            safety_reason,
            request.question,
        )
        _persist_answer(database, question.id, response)
        database.commit()
        log_grounding_event(
            "safe_referral",
            response_type=response.response_type.value,
            failure_reason=safety_reason,
        )
        return response

    sources = {
        source.id: source
        for source in database.scalars(
            select(ApprovedSource).where(
                ApprovedSource.id.in_({chunk.source_id for chunk in chunks})
            )
        )
    }
    citations = build_citations(chunks, sources)
    try:
        answer = GeminiAnswerer.from_settings().answer(
            request.question,
            [chunk.content_text for chunk in chunks],
        )
        response = build_grounded_response(
            answer=answer,
            citations=citations,
            referral=contact_referral,
        )
    except (AnswerGenerationError, ValueError) as error:
        logging.getLogger("purdue.grounding").error("answer_failed: %s", error)
        response = _safe_referral_response(
            "I could not verify a reliable answer right now. Please contact the "
            "responsible university office.",
            request.question,
        )
    log_grounding_event(
        "answer_generated",
        response_type=response.response_type.value,
        citation_count=len(response.citations),
    )

    _persist_answer(database, question.id, response, chunks, sources)
    database.commit()
    return response


def _retrieve_chunks(
    database: Session,
    request: ChatRequest,
) -> list[SourceContentSegment]:
    try:
        query_vector = [
            float(value)
            for value in GeminiEmbeddingProvider.from_settings().embed(
                [request.question]
            )[0]
        ]
    except Exception:
        query_vector = None
    return retrieve_active_chunks(
        database,
        query_embedding=query_vector,
        student_type=request.student_type.value,
    )


def _safe_referral_response(reason: str, question: str) -> ChatResponse:
    return ChatResponse(
        answer=reason,
        response_type=ResponseType.SAFE_REFERRAL,
        referral=select_verified_referral(question),
    )


def _persist_answer(
    database: Session,
    question_id: UUID,
    response: ChatResponse,
    chunks: list[SourceContentSegment] | None = None,
    sources: dict[UUID, ApprovedSource] | None = None,
) -> None:
    answer = GroundedAnswer(
        question_id=question_id,
        answer_text=response.answer,
        confidence_score=(
            1.0 if response.response_type is ResponseType.DIRECT_ANSWER else 0.0
        ),
        response_type=response.response_type,
    )
    database.add(answer)
    database.flush()
    if response.response_type is not ResponseType.DIRECT_ANSWER:
        if response.referral is not None:
            database.add(
                SafeReferral(
                    answer_id=answer.id,
                    office_name=response.referral.office_name,
                    referral_reason=response.referral.referral_reason,
                    contact_url=response.referral.contact_url or "https://www.pnw.edu/",
                )
            )
        return
    for chunk in chunks or []:
        source = (sources or {}).get(chunk.source_id)
        if source is not None:
            database.add(
                AnswerCitation(
                    answer_id=answer.id,
                    source_id=source.id,
                    chunk_id=chunk.id,
                    source_url=source.source_url,
                    citation_text=chunk.source_snippet or chunk.content_text,
                )
            )