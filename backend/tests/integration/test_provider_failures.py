from app.services.answering import AnswerGenerationError, GeminiAnswerer


class FailingGeminiModels:
    def generate_content(self, **_kwargs):
        raise RuntimeError("provider unavailable")


class FailingGeminiClient:
    models = FailingGeminiModels()


def test_answer_provider_failure_is_converted_to_safe_generation_error():
    answerer = GeminiAnswerer(
        api_key="test-key",
        model_name="test-answer-model",
        client=FailingGeminiClient(),
    )

    try:
        answerer.answer("What is the deadline?", ["Approved policy context."])
    except AnswerGenerationError as error:
        assert "failed" in str(error).lower()
    else:
        raise AssertionError("provider failures must not produce an answer")