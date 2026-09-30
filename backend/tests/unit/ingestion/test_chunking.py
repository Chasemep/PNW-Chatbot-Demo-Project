import pytest
from app.models.base import ContentKind
from app.services.ingestion.chunk import chunk_blocks
from app.services.ingestion.normalize import normalize_blocks
from app.services.ingestion.parser import StructuralBlock


def block(
    content_kind: ContentKind,
    content_text: str,
    ordinal: int,
) -> StructuralBlock:
    return StructuralBlock(
        content_kind=content_kind,
        content_text=content_text,
        structural_path="Academic Calendar > Registration",
        location_label=f"Section {ordinal}",
        ordinal=ordinal,
    )


def test_normalization_preserves_structural_relationships():
    normalized = normalize_blocks(
        [
            block(
                ContentKind.TABLE,
                "Term   | Deadline\nFall | August 20",
                0,
            ),
            block(
                ContentKind.LIST,
                "Review availability.\nSubmit registration.",
                1,
            ),
        ]
    )

    assert [item.content_kind for item in normalized] == [
        ContentKind.TABLE,
        ContentKind.LIST,
    ]
    assert normalized[0].content_text == "Term | Deadline\nFall | August 20"
    assert normalized[1].content_text == "Review availability.\nSubmit registration."
    assert [item.structural_path for item in normalized] == [
        "Academic Calendar > Registration",
        "Academic Calendar > Registration",
    ]


def test_chunking_is_deterministic_bounded_and_traceable():
    blocks = normalize_blocks(
        [
            block(ContentKind.HEADING, "Academic Calendar", 0),
            block(
                ContentKind.PARAGRAPH,
                "Students must submit registration before the published deadline.",
                1,
            ),
            block(
                ContentKind.TABLE,
                "Term | Deadline\nFall | August 20",
                2,
            ),
        ]
    )

    first_run = chunk_blocks(
        blocks,
        source_version_hash="source-version-hash",
        max_characters=100,
    )
    second_run = chunk_blocks(
        blocks,
        source_version_hash="source-version-hash",
        max_characters=100,
    )

    assert [chunk.chunk_hash for chunk in first_run] == [
        chunk.chunk_hash for chunk in second_run
    ]
    assert [chunk.content_text for chunk in first_run] == [
        chunk.content_text for chunk in second_run
    ]
    assert all(len(chunk.content_text) <= 100 for chunk in first_run)
    assert all(
        chunk.structural_path == "Academic Calendar > Registration"
        for chunk in first_run
    )
    assert any(chunk.content_kind is ContentKind.TABLE for chunk in first_run)
    assert [chunk.ordinal for chunk in first_run] == list(range(len(first_run)))


def test_oversized_tables_split_between_rows_with_repeated_column_context():
    chunks = chunk_blocks(
        normalize_blocks(
            [
                block(
                    ContentKind.TABLE,
                    (
                        "Term | Deadline\nFall | August 20\n"
                        "Spring | January 10\nSummer | May 15"
                    ),
                    0,
                )
            ]
        ),
        source_version_hash="table-source",
        max_characters=45,
    )

    assert len(chunks) == 3
    assert all(len(chunk.content_text) <= 45 for chunk in chunks)
    assert all(
        chunk.content_text.startswith("Term | Deadline\n") for chunk in chunks
    )
    assert [chunk.content_text.splitlines()[1] for chunk in chunks] == [
        "Fall | August 20",
        "Spring | January 10",
        "Summer | May 15",
    ]
    assert chunks[0].content_kind is ContentKind.TABLE
    assert all(chunk.content_kind is ContentKind.CONTINUATION for chunk in chunks[1:])


def test_individually_oversized_table_rows_are_rejected_without_truncation():
    with pytest.raises(ValueError, match="table row exceeds"):
        chunk_blocks(
            normalize_blocks(
                [
                    block(
                        ContentKind.TABLE,
                        "Term | Deadline\nFall | " + "very long " * 20,
                        0,
                    )
                ]
            ),
            source_version_hash="table-source",
            max_characters=45,
        )
