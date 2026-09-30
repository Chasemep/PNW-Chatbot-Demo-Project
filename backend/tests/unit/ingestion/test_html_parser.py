from pathlib import Path

from app.services.ingestion.html import parse_html

FIXTURE = (
    Path(__file__).resolve().parents[2] / "fixtures" / "ingestion" / "policy.html"
)


def test_html_parser_preserves_ordered_structural_content():
    document = parse_html(FIXTURE)

    assert [block.content_kind for block in document.blocks] == [
        "heading",
        "paragraph",
        "heading",
        "list",
        "table",
        "sidebar",
        "callout",
    ]
    assert [block.content_text for block in document.blocks[:3]] == [
        "Academic Calendar",
        "The calendar lists important student deadlines.",
        "Registration",
    ]
    assert "Review course availability." in document.blocks[3].content_text
    assert "Submit registration before the deadline." in document.blocks[3].content_text
    assert "Term" in document.blocks[4].content_text
    assert "August 20" in document.blocks[4].content_text
    assert document.blocks[3].structural_path == "Academic Calendar > Registration"
    assert all(block.location_label for block in document.blocks)


def test_html_parser_retains_sidebar_and_callout_text():
    document = parse_html(FIXTURE)

    assert document.blocks[5].content_text == "Contact the Registrar."
    assert (
        document.blocks[6].content_text
        == "Important: Deadlines are subject to change."
    )
