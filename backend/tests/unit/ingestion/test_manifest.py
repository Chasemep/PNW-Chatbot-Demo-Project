from datetime import date

import pytest
from app.services.ingestion.manifest import validate_manifest


def valid_source(**overrides):
    values = {
        "source_key": "registration-calendar-2026",
        "title": "Registration Calendar",
        "location": "https://example.purdue.edu/registration/calendar",
        "source_type": "html",
        "issuing_office": "Registrar",
        "review_status": "approved",
        "effective_date": "2026-01-01",
        "reviewed_at": "2026-09-01T00:00:00Z",
    }
    values.update(overrides)
    return values


def test_manifest_accepts_complete_approved_source_metadata():
    sources = validate_manifest([valid_source()])

    assert len(sources) == 1
    assert sources[0].source_key == "registration-calendar-2026"
    assert sources[0].effective_date == date(2026, 1, 1)
    assert sources[0].reviewed_at.isoformat() == "2026-09-01T00:00:00+00:00"


def test_manifest_requires_canonical_url_for_local_source_file():
    with pytest.raises(ValueError, match="source_url"):
        validate_manifest([valid_source(location="StudentAbsencePolicy.html")])


def test_manifest_accepts_canonical_url_for_local_source_file():
    sources = validate_manifest(
        [
            valid_source(
                location="StudentAbsencePolicy.html",
                source_url="https://www.pnw.edu/dean-of-students/policies/student-absence-policy/",
            )
        ]
    )

    assert sources[0].source_url == (
        "https://www.pnw.edu/dean-of-students/policies/student-absence-policy/"
    )


def test_manifest_rejects_non_http_citation_url():
    with pytest.raises(ValueError, match="source_url"):
        validate_manifest([valid_source(source_url="StudentAbsencePolicy.html")])


@pytest.mark.parametrize(
    "field",
    [
        "source_key",
        "title",
        "location",
        "source_type",
        "issuing_office",
        "review_status",
        "effective_date",
        "reviewed_at",
    ],
)
def test_manifest_requires_each_source_metadata_field(field):
    source = valid_source()
    del source[field]

    with pytest.raises(ValueError, match=field):
        validate_manifest([source])


@pytest.mark.parametrize(
    "field, value",
    [
        ("source_key", "   "),
        ("title", "   "),
        ("location", "   "),
        ("source_url", "   "),
        ("issuing_office", "   "),
        ("source_type", "text"),
        ("review_status", "unverified"),
        ("effective_date", "not-a-date"),
        ("reviewed_at", "not-a-timestamp"),
    ],
)
def test_manifest_rejects_invalid_source_metadata(field, value):
    with pytest.raises(ValueError, match=field):
        validate_manifest([valid_source(**{field: value})])


def test_manifest_rejects_duplicate_canonical_source_keys():
    with pytest.raises(ValueError, match="source_key"):
        validate_manifest(
            [
                valid_source(),
                valid_source(title="Replacement Registration Calendar"),
            ]
        )
