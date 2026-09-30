from pathlib import Path

import pytest
from app.services.ingestion.docx import parse_docx

FIXTURE_DIRECTORY = Path(__file__).resolve().parents[2] / "fixtures" / "ingestion"


@pytest.mark.parametrize("filename", ["policy.docx", "policy.doc"])
def test_docx_parser_retains_hierarchy_and_structural_content(filename):
    document = parse_docx(FIXTURE_DIRECTORY / filename)

    assert [block.content_kind for block in document.blocks] == [
        "heading",
        "paragraph",
        "heading",
        "list",
        "table",
        "sidebar",
        "callout",
    ]
    assert document.blocks[3].structural_path == "Academic Calendar > Registration"
    assert "Submit registration before the deadline." in document.blocks[3].content_text
    assert "Fall" in document.blocks[4].content_text
    assert "Contact the Registrar." == document.blocks[5].content_text
    assert "Deadlines are subject to change." in document.blocks[6].content_text
    assert all(block.location_label for block in document.blocks)
