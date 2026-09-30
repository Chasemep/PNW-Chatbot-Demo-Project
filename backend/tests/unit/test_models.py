from datetime import UTC, datetime
from math import nan
from uuid import uuid4

import pytest
from app.models.answer_log import GroundedAnswer, StudentQuestion
from app.models.base import Base, ContentKind, ReleaseStatus, ResponseType
from app.models.review_record import (
    ParsingIssueType,
    ParsingReviewRecord,
    PreparationValidation,
    ValidationStatus,
)
from app.models.source import ApprovedSource, KnowledgeBaseRelease
from app.models.source_chunk import SourceContentSegment
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
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


def approved_source(**overrides):
    values = {
        "title": "Registration Calendar",
        "source_url": "https://example.edu/registration",
        "source_type": "webpage",
        "issuing_office": "Registrar",
        "reviewed_at": datetime.now(UTC),
        "review_status": "approved",
        "is_active": True,
    }
    values.update(overrides)
    return ApprovedSource(**values)


def release(**overrides):
    values = {
        "status": ReleaseStatus.PREPARING,
        "embedding_model": "test-embedding-model",
        "embedding_dimension": 768,
        "started_at": datetime.now(UTC),
    }
    values.update(overrides)
    return KnowledgeBaseRelease(**values)


def chunk(source_id, release_id, **overrides):
    values = {
        "source_id": source_id,
        "release_id": release_id,
        "chunk_index": 0,
        "content_text": "Students may add or drop classes during the published period.",
        "structural_path": "Registration > Add/drop",
        "content_kind": ContentKind.PARAGRAPH,
        "location_label": "Page 2",
        "chunk_hash": "chunk-hash",
        "embedding": [0.0] * 768,
    }
    values.update(overrides)
    return SourceContentSegment(**values)


def test_models_expose_expected_shared_tables(database_engine):
    expected_tables = {
        "approved_sources",
        "knowledge_base_releases",
        "source_content_segments",
        "student_questions",
        "grounded_answers",
        "answer_citations",
        "safe_referrals",
        "parsing_review_records",
        "preparation_validations",
    }
    assert expected_tables <= set(Base.metadata.tables)


def test_source_and_release_constraints(database_engine):
    with Session(database_engine) as database:
        database.add(approved_source())
        database.commit()

        database.add(approved_source(review_status="superseded"))
        with pytest.raises(IntegrityError):
            database.commit()
        database.rollback()

        database.add(approved_source(is_active=False))
        with pytest.raises(IntegrityError):
            database.commit()
        database.rollback()

        database.add_all(
            [
                release(status=ReleaseStatus.ACTIVE),
                release(status=ReleaseStatus.ACTIVE),
            ]
        )
        with pytest.raises(IntegrityError):
            database.commit()


def test_source_chunk_rejects_invalid_embeddings(database_engine):
    with pytest.raises(ValueError, match="768 dimensions"):
        chunk(uuid4(), uuid4(), embedding=[0.0])

    with pytest.raises(ValueError, match="finite"):
        chunk(uuid4(), uuid4(), embedding=[nan] * 768)


def test_audit_models_require_meaningful_values(database_engine):
    with Session(database_engine) as database:
        source = approved_source()
        knowledge_base_release = release()
        question = StudentQuestion(raw_text="What is the deadline?")
        database.add_all([source, knowledge_base_release, question])
        database.flush()
        database.add(
            GroundedAnswer(
                question_id=question.id,
                answer_text="The deadline is listed in the calendar.",
                confidence_score=0.9,
                response_type=ResponseType.DIRECT_ANSWER,
            )
        )
        database.add(
            ParsingReviewRecord(
                source_id=source.id,
                issue_type=ParsingIssueType.PARSE_FAILURE,
                issue_details="Text could not be extracted.",
            )
        )
        database.add(
            PreparationValidation(
                release_id=knowledge_base_release.id,
                check_name="metadata",
                status=ValidationStatus.PASSED,
                measured_value="1",
                details="All metadata is valid.",
            )
        )
        database.flush()

        database.add(StudentQuestion(raw_text="   "))
        with pytest.raises(IntegrityError):
            database.flush()
