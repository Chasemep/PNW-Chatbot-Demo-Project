from uuid import uuid4

from app.models.base import ContentKind
from app.models.source_chunk import SourceContentSegment
from app.services.answering import (
    AnswerGenerationError,
    GeminiAnswerer,
    assess_answer_safety,
)


def chunk(
    *,
    content_text: str,
    structural_path: str,
    content_kind: ContentKind = ContentKind.PARAGRAPH,
) -> SourceContentSegment:
    return SourceContentSegment(
        source_id=uuid4(),
        release_id=uuid4(),
        chunk_index=0,
        content_text=content_text,
        structural_path=structural_path,
        content_kind=content_kind,
        location_label="Section 1",
        chunk_hash=f"hash-{uuid4()}",
        embedding=[0.0] * 768,
    )


def test_distinct_prose_chunks_about_different_terms_are_not_flagged_as_conflicting():
    chunks = [
        chunk(
            content_text="Fall term add/drop deadline is Aug 20.",
            structural_path="Registration > Fall",
        ),
        chunk(
            content_text="Spring term add/drop deadline is Jan 10.",
            structural_path="Registration > Spring",
        ),
    ]

    assert assess_answer_safety("What is the deadline to drop a class?", chunks) is None


def test_prose_chunks_mentioning_multiple_dates_in_one_section_are_not_flagged():
    chunks = [
        chunk(
            content_text="The semester begins Aug 20; the add/drop deadline is Aug 25.",
            structural_path="Registration > Fall",
        ),
        chunk(
            content_text="The add/drop deadline is Aug 25.",
            structural_path="Registration > Fall",
        ),
    ]

    assert assess_answer_safety("What is the deadline to drop a class?", chunks) is None


def test_questions_without_conflict_markers_are_not_checked_for_date_conflicts():
    chunks = [
        chunk(
            content_text="Contact the Registrar at registrar@pnw.edu.",
            structural_path="Contacts > Registrar",
        ),
        chunk(
            content_text="Contact the Registrar office in person.",
            structural_path="Contacts > Registrar",
        ),
    ]

    assert assess_answer_safety("Who do I contact about registration?", chunks) is None


def test_table_rows_for_distinct_events_are_not_flagged_as_conflicting():
    chunks = [
        chunk(
            content_text=(
                "Date | Event\n"
                "8/24/2026 | Fall 2026 Classes Begin\n"
                "8/28/2026 (4:00 PM) | Final Payment Deadline for Fall 2026"
            ),
            structural_path="Refund and Withdrawal Schedule > Fall 2026",
            content_kind=ContentKind.TABLE,
        )
    ]

    assert assess_answer_safety("What is the deadline to drop a class?", chunks) is None


def test_table_rows_with_the_same_event_label_and_different_dates_are_flagged():
    chunks = [
        chunk(
            content_text="Date | Event\n8/28/2026 | Last Day to Drop a Class",
            structural_path="Refund and Withdrawal Schedule > Fall 2026",
            content_kind=ContentKind.TABLE,
        ),
        chunk(
            content_text="Date | Event\n9/2/2026 | Last Day to Drop a Class",
            structural_path="Refund and Withdrawal Schedule > Fall 2026",
            content_kind=ContentKind.TABLE,
        ),
    ]

    reason = assess_answer_safety("What is the deadline to drop a class?", chunks)
    assert reason is not None
    assert "conflicting" in reason.lower()


def test_answerer_retries_quota_error_using_provider_retry_hint(monkeypatch):
    class RateLimitError(RuntimeError):
        code = 429

    class Models:
        calls = 0

        def generate_content(self, *, model, contents):
            self.calls += 1
            assert model == "gemini-3.6-flash"
            assert "Approved context" in contents
            if self.calls == 1:
                raise RateLimitError("RESOURCE_EXHAUSTED; retry in 0.25s")
            return type("Response", (), {"text": "Use the approved schedule."})()

    class Client:
        models = Models()

    pauses = []
    monkeypatch.setattr("app.services.answering.sleep", pauses.append)
    answerer = GeminiAnswerer(
        api_key="test-key",
        model_name="gemini-3.6-flash",
        client=Client(),
    )

    answer = answerer.answer("What is the deadline?", ["Approved policy context."])

    assert answer == "Use the approved schedule."
    assert Client.models.calls == 2
    assert pauses == [1.25]


def test_answerer_does_not_wait_past_the_request_retry_budget(monkeypatch):
    class RateLimitError(RuntimeError):
        code = 429

    class Models:
        def generate_content(self, **_kwargs):
            raise RateLimitError("RESOURCE_EXHAUSTED; retry in 60s")

    class Client:
        models = Models()

    pauses = []
    monkeypatch.setattr("app.services.answering.sleep", pauses.append)
    answerer = GeminiAnswerer(
        api_key="test-key",
        model_name="gemini-3.6-flash",
        client=Client(),
    )

    try:
        answerer.answer("What is the deadline?", ["Approved policy context."])
    except AnswerGenerationError as error:
        assert "code=429" in str(error)
    else:
        raise AssertionError("long quota waits must fail promptly")

    assert pauses == []
