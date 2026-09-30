"""Google Gemini embedding provider for source and query vectors."""

from collections.abc import Sequence
from numbers import Real
from time import sleep
from typing import Any

from google import genai

from app.core.config import get_settings

GEMINI_BATCH_SIZE = 25
GEMINI_BATCH_INTERVAL_SECONDS = 12


class GeminiEmbeddingError(RuntimeError):
    """Raised when Gemini cannot generate a complete embedding batch."""


class GeminiEmbeddingProvider:
    """Generate pinned embeddings through the Google Gemini API."""

    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        dimension: int,
        client: Any | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Gemini embedding API key must not be blank")
        if not model_name.strip():
            raise ValueError("Gemini embedding model must not be blank")
        if dimension <= 0:
            raise ValueError("Gemini embedding dimension must be positive")

        self._model_name = model_name
        self._dimension = dimension
        self._client = client or genai.Client(api_key=api_key)

    @classmethod
    def from_settings(cls) -> "GeminiEmbeddingProvider":
        """Build a provider from server-side application settings."""

        settings = get_settings()
        api_key = settings.gemini_api_key or settings.embedding_api_key
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be configured for embeddings")
        if not settings.embedding_model:
            raise ValueError("EMBEDDING_MODEL must be configured for embeddings")
        return cls(
            api_key=api_key,
            model_name=settings.embedding_model,
            dimension=settings.embedding_dimension,
        )

    @property
    def model_name(self) -> str:
        """Return the pinned Gemini embedding model identifier."""

        return self._model_name

    def embed(self, texts: list[str]) -> Sequence[Sequence[Real]]:
        """Generate one validated-by-the-pipeline vector for every text."""

        if not texts:
            return []
        if not all(text.strip() for text in texts):
            raise ValueError("embedding text must not be blank")

        vectors: list[Sequence[Real]] = []
        for start in range(0, len(texts), GEMINI_BATCH_SIZE):
            if start:
                sleep(GEMINI_BATCH_INTERVAL_SECONDS)
            batch = texts[start : start + GEMINI_BATCH_SIZE]
            try:
                response = self._client.models.embed_content(
                    model=self._model_name,
                    contents=batch,
                    config={"output_dimensionality": self._dimension},
                )
            except Exception as error:
                raise GeminiEmbeddingError(
                    "Gemini embedding request failed; check API key, model, and quota"
                ) from error

            embeddings = response.embeddings
            if embeddings is None or len(embeddings) != len(batch):
                raise GeminiEmbeddingError(
                    "Gemini returned an incomplete embedding batch"
                )
            batch_vectors = [embedding.values for embedding in embeddings]
            if any(vector is None for vector in batch_vectors):
                raise GeminiEmbeddingError(
                    "Gemini returned an embedding without values"
                )
            vectors.extend(batch_vectors)  # type: ignore[arg-type]
        return vectors