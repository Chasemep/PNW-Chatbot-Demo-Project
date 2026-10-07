"""Grounded answer generation through the server-side Gemini API."""

import re
from collections.abc import Sequence
from time import sleep
from typing import Any

from google import genai

from app.core.config import get_settings
from app.models.base import ContentKind, ResponseType
from app.models.source_chunk import SourceContentSegment
from app.schemas.chat import ChatResponse, CitationResponse, ReferralResponse


class AnswerGenerationError(RuntimeError):
    """Raised when Gemini cannot produce a usable grounded answer."""


_CONFLICT_TOPIC_MARKERS = ("deadline", "date", "requirement")
_TABLE_ROW_PATTERN = re.compile(r"^(?P<date>.+?)\s*\|\s*(?P<label>.+)$")
_INDIVIDUALIZED_QUESTION_PATTERN = re.compile(
    r"\b(?:my|me|i am|i'm|will i|can i|do i|am i)\b.{0,100}"
    r"\b(?:eligible|qualify|exception|circumstances|situation|case|"
    r"forgive|waive|appeal|my tuition)\b",
    re.IGNORECASE,
)
_GEMINI_ANSWER_MAX_RETRIES = 3
_GEMINI_UNAVAILABLE_BACKOFF_SECONDS = 2
_GEMINI_ANSWER_MAX_RETRY_DELAY_SECONDS = 40
_CONTACT_QUESTION_MARKERS = (
    "contact",
    "who can help",
    "who handles",
    "where can i get help",
)
_ANSWER_REFUSAL_MARKERS = (
    "cannot provide a reliable answer",
    "cannot provide reliable information",
    "cannot answer reliably",
    "cannot verify this information",
    "can't provide a reliable answer",
    "unable to provide a reliable answer",
)


def is_contact_question(question: str) -> bool:
    """Identify requests for an office or contact rather than policy guidance."""

    normalized = question.casefold()
    return any(marker in normalized for marker in _CONTACT_QUESTION_MARKERS)


def detect_ambiguity(question: str, student_type: str) -> str | None:
    """Request only student context needed to distinguish policy rules."""

    normalized = question.lower()
    context_sensitive_terms = ("academic standing", "grade appeal", "financial aid")
    if student_type == "unknown" and any(
        term in normalized for term in context_sensitive_terms
    ):
        return "Are you an undergraduate or graduate student?"
    return None


def assess_answer_safety(
    question: str,
    chunks: Sequence[SourceContentSegment],
) -> str | None:
    """Return a safe-failure reason when retrieved evidence is unreliable."""

    if not chunks:
        return "No approved source supports this question."
    if _INDIVIDUALIZED_QUESTION_PATTERN.search(question):
        return (
            "I cannot make an individualized decision. Contact the responsible "
            "university office for case-specific guidance."
        )
    if _has_conflicting_dates(question, chunks):
        return "The approved sources contain potentially conflicting policy details."
    return None


def _has_conflicting_dates(
    question: str,
    chunks: Sequence[SourceContentSegment],
) -> bool:
    """Flag only genuine date conflicts: the same labeled event with different dates."""

    if not any(marker in question.lower() for marker in _CONFLICT_TOPIC_MARKERS):
        return False

    return _has_conflicting_table_rows(chunks)


def _has_conflicting_table_rows(chunks: Sequence[SourceContentSegment]) -> bool:
    """Flag table rows where the same labeled event has different dates."""

    dates_by_label: dict[str, set[str]] = {}
    for chunk in chunks:
        if chunk.content_kind is not ContentKind.TABLE:
            continue
        for line in chunk.content_text.splitlines():
            match = _TABLE_ROW_PATTERN.match(line.strip())
            if not match:
                continue
            date_value = match.group("date").strip().lower()
            label = match.group("label").strip().lower()
            if not any(character.isdigit() for character in date_value):
                continue
            dates_by_label.setdefault(label, set()).add(date_value)

    return any(len(values) > 1 for values in dates_by_label.values())


class GeminiAnswerer:
    """Generate answers using only caller-supplied retrieved context."""

    def __init__(self, *, api_key: str, model_name: str, client: Any | None = None):
        if not api_key.strip():
            raise ValueError("Gemini answer API key must not be blank")
        if not model_name.strip():
            raise ValueError("Gemini answer model must not be blank")
        self._model_name = model_name
        self._api_key = api_key
        self._client = client or genai.Client(api_key=api_key)

    @classmethod
    def from_settings(cls) -> "GeminiAnswerer":
        settings = get_settings()
        if not settings.gemini_api_key or not settings.gemini_model:
            raise ValueError("GEMINI_API_KEY and GEMINI_MODEL must be configured")
        return cls(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model,
        )

    def answer(
        self,
        question: str,
        context: Sequence[str],
    ) -> str:
        """Return a concise answer constrained to retrieved context."""

        if not question.strip() or not context:
            raise ValueError("question and retrieved context are required")
        prompt = (
            "Answer only from the approved context below. If the context does "
            "not support an answer, say that you cannot provide a reliable answer. "
            "Do not invent policy, dates, exceptions, or contacts.\n\n"
            f"Question: {question.strip()}\n\n"
            "Approved context:\n"
            + "\n\n".join(context)
        )
        response = self._generate_content(prompt)
        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise AnswerGenerationError("Gemini returned an empty answer")
        return text.strip()

    def _generate_content(self, prompt: str) -> Any:
        for attempt in range(_GEMINI_ANSWER_MAX_RETRIES + 1):
            try:
                return self._client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                )
            except Exception as error:
                error_details = str(error)
                error_code = getattr(error, "code", None)
                retry_after = _retry_after_seconds(error_details)
                is_rate_limited = (
                    error_code == 429
                    or "RESOURCE_EXHAUSTED" in error_details
                    or "quota exceeded" in error_details.lower()
                )
                is_unavailable = (
                    error_code in (500, 503)
                    or "UNAVAILABLE" in error_details
                    or "overloaded" in error_details.lower()
                )
                if is_unavailable and attempt < _GEMINI_ANSWER_MAX_RETRIES:
                    sleep(_GEMINI_UNAVAILABLE_BACKOFF_SECONDS * (attempt + 1))
                    continue
                if (
                    is_rate_limited
                    and retry_after is not None
                    and retry_after <= _GEMINI_ANSWER_MAX_RETRY_DELAY_SECONDS
                    and attempt < _GEMINI_ANSWER_MAX_RETRIES
                ):
                    sleep(retry_after + 1)
                    continue

                error_details = error_details.replace(self._api_key, "[REDACTED]")
                raise AnswerGenerationError(
                    "Gemini answer request failed "
                    f"(code={error_code}): {error_details[:500]}"
                ) from error
        raise AnswerGenerationError("Gemini answer request failed after retries")


def _retry_after_seconds(error_details: str) -> float | None:
    """Extract Gemini's textual retry hint for quota/rate-limit responses."""

    match = re.search(r"retry in ([0-9]+(?:\.[0-9]+)?)s", error_details, re.IGNORECASE)
    return float(match.group(1)) if match else None


def build_grounded_response(
    *,
    answer: str,
    citations: list[CitationResponse],
    referral: ReferralResponse | None = None,
) -> ChatResponse:
    """Create a direct response only when citations exist and the model answered."""

    if not citations:
        raise AnswerGenerationError("grounded answers require citations")
    normalized_answer = answer.casefold()
    if any(marker in normalized_answer for marker in _ANSWER_REFUSAL_MARKERS):
        raise AnswerGenerationError("model could not provide a reliable answer")
    return ChatResponse(
        answer=answer,
        response_type=ResponseType.DIRECT_ANSWER,
        citations=citations,
        referral=referral,
    )