from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.models.answer_log import AnswerCitation, GroundedAnswer, StudentQuestion
from app.models.base import (
    Base,
    ContentKind,
    ReleaseStatus,
    ReviewStatus,
    SourceType,
)
from app.models.review_record import PreparationValidation, ValidationStatus
from app.models.source import ApprovedSource, KnowledgeBaseRelease
from app.models.source_chunk import SourceContentSegment
from app.services.ingestion.validate import validate_release
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session


@pytest.fixture
def database_engine():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


def release(*, release_id) -> KnowledgeBaseRelease:
    return KnowledgeBaseRelease(
        id=release_id,
        status=ReleaseStatus.PREPARING,
        embedding_model="test-model",
        embedding_dimension=768,
        started_at=datetime.now(UTC),
    )


def source(*, source_id, review_status: ReviewStatus = ReviewStatus.APPROVED):
    return ApprovedSource(
        id=source_id,
        title="Registration Calendar",
        source_url="https://example.edu/registration",
        source_type=SourceType.WEBPAGE,
        issuing_office="Registrar",
        reviewed_at=datetime.now(UTC),
        review_status=review_status,
        is_active=review_status is ReviewStatus.APPROVED,
    )


def chunk(*, source_id, release_id, chunk_hash: str) -> SourceContentSegment:
    return SourceContentSegment(
        source_id=source_id,
        release_id=release_id,
        chunk_index=0,
        content_text="Students may add or drop a class before the deadline.",
        structural_path="Registration > Deadlines",
        content_kind=ContentKind.PARAGRAPH,
        location_label="Registration deadlines",
        chunk_hash=chunk_hash,
        embedding=[0.0] * 768,
    )


def test_validation_records_passing_required_gates_for_a_valid_release(database_engine):
    release_id = uuid4()
    source_id = uuid4()

    with Session(database_engine) as database:
        database.add_all(
            [
                release(release_id=release_id),
                source(source_id=source_id),
                chunk(
                    source_id=source_id,
                    release_id=release_id,
                    chunk_hash="registration-deadline",
                ),
            ]
        )
        database.commit()

        assert validate_release(database, release_id) is True

        validations = database.query(PreparationValidation).filter_by(
            release_id=release_id
        )
        assert {validation.check_name for validation in validations} >= {
            "metadata",
            "parse_completeness",
            "duplicate_or_empty_chunks",
            "approval",
            "vector",
        }
        assert all(
            validation.status is ValidationStatus.PASSED for validation in validations
        )


def test_validation_rejects_unapproved_sources_and_duplicate_chunks(database_engine):
    release_id = uuid4()
    approved_source_id = uuid4()
    unapproved_source_id = uuid4()

    with Session(database_engine) as database:
        database.add_all(
            [
                release(release_id=release_id),
                source(source_id=approved_source_id),
                source(
                    source_id=unapproved_source_id,
                    review_status=ReviewStatus.PENDING_REVIEW,
                ),
                chunk(
                    source_id=approved_source_id,
                    release_id=release_id,
                    chunk_hash="duplicate-policy-text",
                ),
                chunk(
                    source_id=unapproved_source_id,
                    release_id=release_id,
                    chunk_hash="duplicate-policy-text",
                ),
            ]
        )
        database.commit()

        assert validate_release(database, release_id) is False

        failed_gates = {
            validation.check_name
            for validation in database.query(PreparationValidation).filter_by(
                release_id=release_id,
                status=ValidationStatus.FAILED,
            )
        }
        assert {"approval", "duplicate_or_empty_chunks"} <= failed_gates


def test_validation_runs_retrieval_smoke_questions(database_engine):
    release_id = uuid4()
    source_id = uuid4()

    with Session(database_engine) as database:
        database.add_all(
            [
                release(release_id=release_id),
                source(source_id=source_id),
                chunk(
                    source_id=source_id,
                    release_id=release_id,
                    chunk_hash="registration-deadline",
                ),
            ]
        )
        database.commit()

        assert validate_release(
            database,
            release_id,
            smoke_questions=[("When can I add or drop a class?", ["deadline"])],
        ) is True

        smoke_validation = database.query(PreparationValidation).filter_by(
            release_id=release_id,
            check_name="retrieval_smoke",
        ).one()
        assert smoke_validation.measured_value == "1_passed_questions"


def test_validation_rejects_citations_that_do_not_match_their_source_chunk(
    database_engine,
):
    release_id = uuid4()
    source_id = uuid4()
    question_id = uuid4()
    answer_id = uuid4()

    with Session(database_engine) as database:
        database.add_all(
            [
                release(release_id=release_id),
                source(source_id=source_id),
                chunk(
                    source_id=source_id,
                    release_id=release_id,
                    chunk_hash="registration-deadline",
                ),
                StudentQuestion(
                    id=question_id,
                    raw_text="When can I add a class?",
                    asked_at=datetime.now(UTC),
                ),
            ]
        )
        database.flush()
        database.add(
            GroundedAnswer(
                id=answer_id,
                question_id=question_id,
                answer_text="See the registration deadline.",
                confidence_score=0.9,
                response_type="direct_answer",
            )
        )
        database.flush()
        stored_chunk = database.query(SourceContentSegment).one()
        database.add(
            AnswerCitation(
                answer_id=answer_id,
                source_id=source_id,
                chunk_id=stored_chunk.id,
                source_url="https://wrong.example.edu/source",
                citation_text="Registration deadline",
            )
        )
        database.commit()

        assert validate_release(database, release_id) is False

        citation_validation = database.query(PreparationValidation).filter_by(
            release_id=release_id,
            check_name="citation_resolution",
        ).one()
        assert citation_validation.status is ValidationStatus.FAILED