from math import nan

import pytest
from app.services.ingestion.embed import generate_embeddings
from app.services.ingestion.gemini_embed import (
    GeminiEmbeddingError,
    GeminiEmbeddingProvider,
)


class FakeEmbeddingProvider:
    def __init__(self, model_name: str, vectors: list[list[float]]) -> None:
        self.model_name = model_name
        self.vectors = vectors

    def embed(self, texts: list[str]) -> list[list[float]]:
        assert texts
        return self.vectors


def test_embedding_provider_returns_complete_pinned_compatible_vectors():
    provider = FakeEmbeddingProvider(
        model_name="test-embedding-v1",
        vectors=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
    )

    embeddings = generate_embeddings(
        ["first source chunk", "second source chunk"],
        provider=provider,
        expected_model="test-embedding-v1",
        expected_dimension=3,
    )

    assert embeddings == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


@pytest.mark.parametrize(
    "provider, expected_model, expected_dimension, match",
    [
        (
            FakeEmbeddingProvider("new-model", [[0.1, 0.2, 0.3]]),
            "pinned-model",
            3,
            "model",
        ),
        (
            FakeEmbeddingProvider("pinned-model", [[0.1, 0.2]]),
            "pinned-model",
            3,
            "dimension",
        ),
        (
            FakeEmbeddingProvider("pinned-model", [[0.1, nan, 0.3]]),
            "pinned-model",
            3,
            "finite",
        ),
        (
            FakeEmbeddingProvider("pinned-model", [[0.1, 0.2, 0.3]]),
            "pinned-model",
            3,
            "partial",
        ),
    ],
)
def test_embedding_provider_rejects_incompatible_or_partial_batches(
    provider,
    expected_model,
    expected_dimension,
    match,
):
    with pytest.raises(ValueError, match=match):
        generate_embeddings(
            ["first source chunk", "second source chunk"],
            provider=provider,
            expected_model=expected_model,
            expected_dimension=expected_dimension,
        )


class FakeGeminiModels:
    def __init__(self, response=None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    def embed_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class FakeGeminiClient:
    def __init__(self, models: FakeGeminiModels) -> None:
        self.models = models


class FakeEmbedding:
    def __init__(self, values: list[float] | None) -> None:
        self.values = values


class FakeEmbeddingResponse:
    def __init__(self, embeddings) -> None:
        self.embeddings = embeddings


def test_gemini_provider_maps_embeddings_and_pins_request_configuration():
    models = FakeGeminiModels(
        FakeEmbeddingResponse(
            [FakeEmbedding([0.1, 0.2, 0.3]), FakeEmbedding([0.4, 0.5, 0.6])]
        )
    )
    provider = GeminiEmbeddingProvider(
        api_key="test-key",
        model_name="gemini-embedding-test",
        dimension=3,
        client=FakeGeminiClient(models),
    )

    assert provider.embed(["first", "second"]) == [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]
    assert models.calls == [
        {
            "model": "gemini-embedding-test",
            "contents": ["first", "second"],
            "config": {"output_dimensionality": 3},
        }
    ]


def test_gemini_provider_converts_quota_or_api_failures_to_provider_errors():
    models = FakeGeminiModels(error=RuntimeError("quota exhausted"))
    provider = GeminiEmbeddingProvider(
        api_key="test-key",
        model_name="gemini-embedding-test",
        dimension=3,
        client=FakeGeminiClient(models),
    )

    with pytest.raises(GeminiEmbeddingError, match="quota"):
        provider.embed(["source text"])


def test_gemini_provider_rejects_incomplete_responses():
    models = FakeGeminiModels(FakeEmbeddingResponse([FakeEmbedding(None)]))
    provider = GeminiEmbeddingProvider(
        api_key="test-key",
        model_name="gemini-embedding-test",
        dimension=3,
        client=FakeGeminiClient(models),
    )

    with pytest.raises(GeminiEmbeddingError, match="without values"):
        provider.embed(["source text"])
