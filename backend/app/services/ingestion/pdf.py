"""PDF parsing into page-located structural blocks."""

from pathlib import Path

from pypdf import PdfReader

from app.models.base import ContentKind
from app.services.ingestion.parser import ParsedDocument, StructuralBlock


def parse_pdf(path: Path) -> ParsedDocument:
    """Extract reliable PDF text and flag image-only documents for review."""

    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    if not any(text.strip() for text in pages):
        return ParsedDocument(
            blocks=[],
            review_reason="Image-only PDF has no extractable text.",
        )

    blocks: list[StructuralBlock] = []
    heading_path = "Document"
    for page_number, page_text in enumerate(pages, start=1):
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]
        index = 0
        while index < len(lines):
            line = lines[index]
            kind = ContentKind.PARAGRAPH
            text = line

            if page_number == 1 and not blocks:
                kind = ContentKind.HEADING
                heading_path = line
            elif line.startswith("SIDEBAR:"):
                kind = ContentKind.SIDEBAR
                text = line.removeprefix("SIDEBAR:").strip()
            elif line.startswith("CALLOUT:"):
                kind = ContentKind.CALLOUT
                text = line.removeprefix("CALLOUT:").strip()
            elif "|" in line:
                kind = ContentKind.TABLE
                table_rows = [line]
                index += 1
                while index < len(lines) and "|" in lines[index]:
                    table_rows.append(lines[index])
                    index += 1
                text = "\n".join(table_rows)
                index -= 1
            elif line.startswith(("- ", "* ")):
                kind = ContentKind.LIST
                list_items = [line[2:]]
                index += 1
                while index < len(lines) and lines[index].startswith(("- ", "* ")):
                    list_items.append(lines[index][2:])
                    index += 1
                text = "\n".join(list_items)
                index -= 1

            blocks.append(
                StructuralBlock(
                    content_kind=kind,
                    content_text=text,
                    structural_path=heading_path,
                    location_label=f"Page {page_number}",
                    ordinal=len(blocks),
                )
            )
            index += 1

    return ParsedDocument(blocks=blocks)
