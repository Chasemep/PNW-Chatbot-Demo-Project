"""Pinned embedding-provider integration and vector validation."""

from collections.abc import Sequence
from math import isfinite
from numbers import Real
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Provider interface whose declared model is pinned per release."""

    @property
    def model_name(self) -> str:
        """Return the provider model identifier."""

    def embed(self, texts: list[str]) -> Sequence[Sequence[Real]]:
        """Generate one embedding for every submitted text."""


def generate_embeddings(
    texts: list[str],
    *,
    provider: EmbeddingProvider,
    expected_model: str,
    expected_dimension: int,
) -> list[list[float]]:
    """Generate a complete compatible batch or return no vectors."""

    if not expected_model.strip():
        raise ValueError("expected_model must not be blank")
    if expected_dimension <= 0:
        raise ValueError("expected_dimension must be positive")
    if not all(text.strip() for text in texts):
        raise ValueError("embedding text must not be blank")
    if provider.model_name != expected_model:
        raise ValueError("embedding provider model does not match the pinned model")

    generated_vectors = provider.embed(texts)
    if provider.model_name != expected_model:
        raise ValueError("embedding provider model changed during generation")

    vectors = list(generated_vectors)
    validated_vectors = [
        _validate_vector(vector, expected_dimension) for vector in vectors
    ]
    if len(vectors) != len(texts):
        raise ValueError("embedding provider returned a partial batch")

    return validated_vectors


def _validate_vector(
    vector: Sequence[Real],
    expected_dimension: int,
) -> list[float]:
    if isinstance(vector, (str, bytes)) or len(vector) != expected_dimension:
        raise ValueError("embedding vector has the wrong dimension")

    values: list[float] = []
    for component in vector:
        if isinstance(component, bool) or not isinstance(component, Real):
            raise ValueError("embedding vector must contain finite numeric values")
        value = float(component)
        if not isfinite(value):
            raise ValueError("embedding vector must contain finite numeric values")
        values.append(value)
    return values
