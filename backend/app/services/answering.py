"""Grounded answer generation through the server-side Gemini API."""

from collections.abc import Sequence
from typing import Any

from google import genai

from app.core.config import get_settings
from app.models.base import ResponseType
from app.models.source_chunk import SourceContentSegment
from app.schemas.chat import ChatResponse


class AnswerGenerationError(RuntimeError):
    """Raised when Gemini cannot produce a usable grounded answer."""


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
    if len(chunks) > 1:
        normalized = {chunk.content_text.strip().lower() for chunk in chunks}
        if len(normalized) > 1 and any(
            marker in question.lower() for marker in ("deadline", "date", "requirement")
        ):
            return (
                "The approved sources contain potentially conflicting policy details."
            )
    return None


class GeminiAnswerer:
    """Generate answers using only caller-supplied retrieved context."""

    def __init__(self, *, api_key: str, model_name: str, client: Any | None = None):
        if not api_key.strip():
            raise ValueError("Gemini answer API key must not be blank")
        if not model_name.strip():
            raise ValueError("Gemini answer model must not be blank")
        self._model_name = model_name
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
        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )
        except Exception as error:
            raise AnswerGenerationError("Gemini answer request failed") from error
        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise AnswerGenerationError("Gemini returned an empty answer")
        return text.strip()


def build_grounded_response(
    *,
    answer: str,
    citations,
) -> ChatResponse:
    """Create a direct response only when citations exist."""

    if not citations:
        raise AnswerGenerationError("grounded answers require citations")
    return ChatResponse(
        answer=answer,
        response_type=ResponseType.DIRECT_ANSWER,
        citations=citations,
    )