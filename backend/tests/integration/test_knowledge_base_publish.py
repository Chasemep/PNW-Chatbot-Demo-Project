from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.models.base import Base, ReleaseStatus
from app.models.source import KnowledgeBaseRelease
from app.services.ingestion.publish import publish_release
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture
def database_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


def release(*, release_id, status: ReleaseStatus) -> KnowledgeBaseRelease:
    return KnowledgeBaseRelease(
        id=release_id,
        status=status,
        embedding_model="test-model",
        embedding_dimension=768,
        started_at=datetime.now(UTC),
    )


def test_publish_activates_validated_release_and_retires_prior_release(database_engine):
    previous_release_id = uuid4()
    candidate_release_id = uuid4()

    with Session(database_engine) as database:
        database.add_all(
            [
                release(release_id=previous_release_id, status=ReleaseStatus.ACTIVE),
                release(
                    release_id=candidate_release_id,
                    status=ReleaseStatus.VALIDATED,
                ),
            ]
        )
        database.commit()

        published_release = publish_release(database, candidate_release_id)
        database.commit()

        assert published_release.id == candidate_release_id
        assert published_release.status is ReleaseStatus.ACTIVE
        assert database.get(KnowledgeBaseRelease, previous_release_id).status is (
            ReleaseStatus.RETIRED
        )
        assert database.get(KnowledgeBaseRelease, candidate_release_id).activated_at


def test_rejected_release_does_not_change_the_active_release(database_engine):
    previous_release_id = uuid4()
    rejected_release_id = uuid4()

    with Session(database_engine) as database:
        database.add_all(
            [
                release(release_id=previous_release_id, status=ReleaseStatus.ACTIVE),
                release(release_id=rejected_release_id, status=ReleaseStatus.REJECTED),
            ]
        )
        database.commit()

        with pytest.raises(ValueError, match="validated"):
            publish_release(database, rejected_release_id)
        database.rollback()

        assert database.get(KnowledgeBaseRelease, previous_release_id).status is (
            ReleaseStatus.ACTIVE
        )
        assert database.get(KnowledgeBaseRelease, rejected_release_id).status is (
            ReleaseStatus.REJECTED
        )