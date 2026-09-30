from pathlib import Path

from app.services.ingestion.pdf import parse_pdf

FIXTURE_DIRECTORY = Path(__file__).resolve().parents[2] / "fixtures" / "ingestion"


def test_pdf_parser_retains_text_and_page_locations():
    document = parse_pdf(FIXTURE_DIRECTORY / "policy.pdf")

    assert [block.content_kind for block in document.blocks] == [
        "heading",
        "paragraph",
        "table",
        "list",
        "sidebar",
        "callout",
    ]
    assert "Academic Calendar" in document.blocks[0].content_text
    assert "August 20" in document.blocks[2].content_text
    assert "Registrar" in document.blocks[4].content_text
    assert all("Page" in block.location_label for block in document.blocks)
    assert document.review_reason is None


def test_pdf_parser_marks_image_only_documents_for_review():
    document = parse_pdf(FIXTURE_DIRECTORY / "image-only.pdf")

    assert document.blocks == []
    assert document.review_reason is not None
    assert "image-only" in document.review_reason.lower()
