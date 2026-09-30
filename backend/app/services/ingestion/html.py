"""HTML parsing into ordered, structure-aware blocks."""

from pathlib import Path

from bs4 import BeautifulSoup, Tag
from bs4.element import AttributeValueList, NavigableString

from app.models.base import ContentKind
from app.services.ingestion.parser import ParsedDocument, StructuralBlock

_HEADING_TAGS = {f"h{level}" for level in range(1, 7)}


def parse_html(path: Path) -> ParsedDocument:
    """Parse HTML headings, paragraphs, lists, tables, sidebars, and callouts."""

    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    root = soup.body or soup
    headings: list[str] = []
    blocks: list[StructuralBlock] = []

    def append_block(kind: ContentKind, text: str) -> None:
        if kind in {ContentKind.TABLE, ContentKind.LIST}:
            normalized = "\n".join(
                " ".join(line.split()) for line in text.splitlines() if line.strip()
            )
        else:
            normalized = " ".join(text.split())
        if not normalized:
            return
        blocks.append(
            StructuralBlock(
                content_kind=kind,
                content_text=normalized,
                structural_path=" > ".join(headings) or "Document",
                location_label=f"HTML element {len(blocks) + 1}",
                ordinal=len(blocks),
            )
        )

    def visit(node: Tag) -> None:
        for child in node.children:
            if isinstance(child, NavigableString) or not isinstance(child, Tag):
                continue

            name = child.name.lower()
            if name in _HEADING_TAGS:
                level = int(name[1])
                text = child.get_text(" ", strip=True)
                if text:
                    del headings[level - 1 :]
                    headings.append(text)
                    append_block(ContentKind.HEADING, text)
            elif name in {"ul", "ol"}:
                items = [
                    item.get_text(" ", strip=True)
                    for item in child.find_all("li", recursive=False)
                ]
                append_block(ContentKind.LIST, "\n".join(items))
            elif name == "table":
                if child.find("table") is not None:
                    visit(child)
                    continue
                rows = [
                    " | ".join(
                        cell.get_text(" ", strip=True)
                        for cell in row.find_all(["th", "td"], recursive=False)
                    )
                    for row in child.find_all("tr")
                ]
                append_block(ContentKind.TABLE, "\n".join(row for row in rows if row))
            elif _has_class(child, "sidebar") or name == "aside":
                append_block(ContentKind.SIDEBAR, _non_heading_text(child))
            elif _has_class(child, "callout"):
                append_block(ContentKind.CALLOUT, child.get_text(" ", strip=True))
            elif name == "p":
                append_block(ContentKind.PARAGRAPH, child.get_text(" ", strip=True))
            else:
                visit(child)

    visit(root)
    return ParsedDocument(blocks=blocks)


def _has_class(node: Tag, class_name: str) -> bool:
    """Return whether a tag declares an exact semantic class."""

    classes = node.get("class")
    return isinstance(classes, AttributeValueList) and class_name in classes


def _non_heading_text(node: Tag) -> str:
    """Extract visually separated text without duplicating sidebar headings."""

    text_nodes = [
        text.strip()
        for text in node.find_all(string=True)
        if text.strip()
        and not (text.parent and text.parent.name.lower() in _HEADING_TAGS)
    ]
    return " ".join(text_nodes)
