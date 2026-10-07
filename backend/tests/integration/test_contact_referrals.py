from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.models.base import ContentKind, ReleaseStatus, ReviewStatus, SourceType
from app.models.source import ApprovedSource, KnowledgeBaseRelease
from app.models.source_chunk import SourceContentSegment
from app.services.answering import GeminiAnswerer
from app.services.ingestion.gemini_embed import GeminiEmbeddingProvider
from app.services.referral import extract_contact_metadata
from sqlalchemy.orm import sessionmaker

CONTACT_CASES = [
    (
        "Who should I contact about registration?",
        "Registrar",
        "https://www.pnw.edu/registrar/",
        "For registration questions, contact the Registrar. Official contact page: https://www.pnw.edu/registrar/",
    ),
    (
        "Who should I contact about financial aid?",
        "Financial Aid Office",
        "https://www.pnw.edu/financial-aid/",
        "For financial aid questions, contact the Financial Aid Office. "
        "Official contact page: https://www.pnw.edu/financial-aid/",
    ),
    (
        "Who should I contact about academic standing?",
        "Academic Affairs",
        "https://www.pnw.edu/academic-affairs/",
        "For academic standing questions, contact Academic Affairs. "
        "Official contact page: https://www.pnw.edu/academic-affairs/",
    ),
    (
        "Who should I contact about a grade appeal?",
        "Academic Affairs",
        "https://www.pnw.edu/academic-affairs/",
        "For grade appeal questions, contact Academic Affairs. Official contact page: https://www.pnw.edu/academic-affairs/",
    ),
    (
        "Who should I contact about adding or dropping a class?",
        "Registrar",
        "https://www.pnw.edu/registrar/",
        "For class add or drop questions, contact the Registrar. Official contact page: https://www.pnw.edu/registrar/",
    ),
]


def seed_contact_source(session_factory: sessionmaker, content_text: str) -> None:
    release_id = uuid4()
    source_id = uuid4()
    with session_factory() as database:
        database.add_all(
            [
                KnowledgeBaseRelease(
                    id=release_id,
                    status=ReleaseStatus.ACTIVE,
                    embedding_model="test-model",
                    embedding_dimension=768,
                    started_at=datetime.now(UTC),
                ),
                ApprovedSource(
                    id=source_id,
                    title="Official Contact Directory",
                    source_url="https://www.pnw.edu/academic-and-administrative-offices/",
                    source_type=SourceType.WEBPAGE,
                    issuing_office="Purdue Northwest",
                    reviewed_at=datetime.now(UTC),
                    review_status=ReviewStatus.APPROVED,
                    is_active=True,
                ),
            ]
        )
        database.flush()
        database.add(
            SourceContentSegment(
                source_id=source_id,
                release_id=release_id,
                chunk_index=0,
                content_text=content_text,
                source_snippet=content_text,
                embedding=[0.0] * 768,
                structural_path="Contact directory",
                content_kind=ContentKind.PARAGRAPH,
                location_label="Office contacts",
                chunk_hash=f"contact-{source_id}",
            )
        )
        database.commit()


def install_test_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    class NoEmbeddingProvider:
        def embed(self, _texts):
            raise RuntimeError("Embedding is disabled in this test")

    class TestAnswerer:
        def answer(self, _question, context):
            return " ".join(context)

    monkeypatch.setattr(
        GeminiEmbeddingProvider,
        "from_settings",
        classmethod(lambda _cls: NoEmbeddingProvider()),
    )
    monkeypatch.setattr(
        GeminiAnswerer,
        "from_settings",
        classmethod(lambda _cls: TestAnswerer()),
    )


@pytest.mark.parametrize(
    "question, expected_office, expected_url, approved_contact_text",
    CONTACT_CASES,
)
def test_contact_question_returns_source_grounded_office_referral(
    contact_api,
    monkeypatch: pytest.MonkeyPatch,
    question: str,
    expected_office: str,
    expected_url: str,
    approved_contact_text: str,
):
    client, session_factory = contact_api
    install_test_providers(monkeypatch)
    seed_contact_source(session_factory, approved_contact_text)

    response = client.post(
        "/api/chat",
        json={"question": question, "student_type": "undergraduate"},
    )

    assert response.status_code == 200
    payload = response.json()
    referral = payload["referral"]
    assert referral is not None, "contact questions should include a referral"
    assert referral["office_name"] == expected_office
    assert referral["contact_url"] == expected_url
    assert referral["referral_reason"]
    assert payload["citations"]


def test_contact_metadata_includes_verified_email_and_phone():
    contact = extract_contact_metadata(
        "For registration, contact the Registrar at registrar@pnw.edu or "
        "219-555-0123. Official contact page: https://www.pnw.edu/registrar/"
    )

    assert contact is not None
    assert contact.office_name == "Registrar"
    assert contact.contact_email == "registrar@pnw.edu"
    assert contact.contact_phone == "219-555-0123"
    assert contact.contact_url == "https://www.pnw.edu/registrar/"
