from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.models.base import (
    Base,
    ContentKind,
    ReleaseStatus,
    ReviewStatus,
    SourceType,
)
from app.models.source import ApprovedSource, KnowledgeBaseRelease
from app.models.source_chunk import SourceContentSegment
from app.services.retrieval import retrieve_active_chunks
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


def source(
    *,
    source_id,
    review_status: ReviewStatus = ReviewStatus.APPROVED,
    is_active: bool = True,
    superseded_by=None,
) -> ApprovedSource:
    return ApprovedSource(
        id=source_id,
        title=f"Source {source_id}",
        source_url=f"https://example.edu/{source_id}",
        source_type=SourceType.WEBPAGE,
        issuing_office="Registrar",
        reviewed_at=datetime.now(UTC),
        review_status=review_status,
        is_active=is_active,
        superseded_by=superseded_by,
    )


def chunk(*, source_id, release_id, chunk_index: int) -> SourceContentSegment:
    return SourceContentSegment(
        source_id=source_id,
        release_id=release_id,
        chunk_index=chunk_index,
        content_text="Official policy text.",
        structural_path="Policy",
        content_kind=ContentKind.PARAGRAPH,
        location_label="Section 1",
        chunk_hash=f"{source_id}-{release_id}-{chunk_index}",
        embedding=[0.0] * 768,
    )


def release(*, release_id, status: ReleaseStatus) -> KnowledgeBaseRelease:
    return KnowledgeBaseRelease(
        id=release_id,
        status=status,
        embedding_model="test-model",
        embedding_dimension=768,
        started_at=datetime.now(UTC),
    )


def test_retrieval_returns_only_authoritative_active_release_chunks(
    database_engine,
):
    current_source_id = uuid4()
    active_release_id = uuid4()
    retired_release_id = uuid4()

    with Session(database_engine) as database:
        database.add_all(
            [
                release(release_id=active_release_id, status=ReleaseStatus.ACTIVE),
                release(release_id=retired_release_id, status=ReleaseStatus.RETIRED),
                source(source_id=current_source_id),
                source(
                    source_id=uuid4(),
                    superseded_by=current_source_id,
                ),
                source(
                    source_id=uuid4(),
                    review_status=ReviewStatus.PENDING_REVIEW,
                    is_active=False,
                ),
            ]
        )
        database.flush()

        sources = database.query(ApprovedSource).all()
        current_source = next(
            stored_source
            for stored_source in sources
            if stored_source.id == current_source_id
        )
        superseded_source = next(
            stored_source
            for stored_source in sources
            if stored_source.superseded_by == current_source_id
        )
        pending_source = next(
            stored_source
            for stored_source in sources
            if stored_source.review_status == ReviewStatus.PENDING_REVIEW
        )
        database.add_all(
            [
                chunk(
                    source_id=current_source.id,
                    release_id=active_release_id,
                    chunk_index=1,
                ),
                chunk(
                    source_id=superseded_source.id,
                    release_id=active_release_id,
                    chunk_index=2,
                ),
                chunk(
                    source_id=pending_source.id,
                    release_id=active_release_id,
                    chunk_index=3,
                ),
                chunk(
                    source_id=current_source.id,
                    release_id=retired_release_id,
                    chunk_index=4,
                ),
            ]
        )
        database.commit()

        chunks = retrieve_active_chunks(database)

    assert [result.chunk_index for result in chunks] == [1]
    assert chunks[0].source_id == current_source_id


def test_retrieval_orders_results_and_rejects_invalid_limits(database_engine):
    source_id = uuid4()
    release_id = uuid4()

    with Session(database_engine) as database:
        database.add_all(
            [
                release(release_id=release_id, status=ReleaseStatus.ACTIVE),
                source(source_id=source_id),
                chunk(source_id=source_id, release_id=release_id, chunk_index=2),
                chunk(source_id=source_id, release_id=release_id, chunk_index=1),
            ]
        )
        database.commit()

        assert [
            result.chunk_index for result in retrieve_active_chunks(database, limit=1)
        ] == [1]
        with pytest.raises(ValueError, match="at least 1"):
            retrieve_active_chunks(database, limit=0)
