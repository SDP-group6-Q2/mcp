"""PDF parsing for the manuals: page text, the outline (bookmarks) and page cleaning.

The manuals carry a full numbered outline, which gives real section boundaries, and every page
repeats boilerplate (ownership notice, page header) and some pages are tables of contents. Both would
pollute embeddings and crowd out real content, so they are removed here.
"""

import io
import re
from collections import Counter
from dataclasses import dataclass

from pypdf import PdfReader

# A line is boilerplate when its normalised form appears on at least this share of the pages.
BOILERPLATE_PAGE_SHARE = 0.4
_MAX_BOILERPLATE_LINE_CHARS = 200

_HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$", re.DOTALL)
# Page numbers (arabic or roman) at either end of a running header/footer line, with or without a space.
_LEADING_PAGE_MARKER_RE = re.compile(r"^\s*(?:\d+\s*(?=[A-Z])|[IVXLC]{1,6}\s+(?=[A-Z]))")
_TRAILING_PAGE_MARKER_RE = re.compile(r"\s+(?:\d+|[IVXLC]{1,6})\s*$")
_DOT_LEADER_RE = re.compile(r"\.{5,}")


@dataclass(frozen=True)
class OutlineEntry:
    number: str  # "11.5.1.5", or "" for an unnumbered bookmark
    title: str
    level: int
    page: int  # 0-based index of the page the bookmark points at


@dataclass(frozen=True)
class ParsedPdf:
    pages: list[str]
    outline: list[OutlineEntry]


def _split_heading(raw: str) -> tuple[str, str]:
    """'11.5.1.5\\tEVERY 6000 WORKING HOURS' -> ('11.5.1.5', 'EVERY 6000 WORKING HOURS')."""
    match = _HEADING_RE.match(raw.strip())
    if match:
        return match.group(1), " ".join(match.group(2).split())
    return "", " ".join(raw.split())


def _walk_outline(reader: PdfReader, items: list, level: int = 0) -> list[OutlineEntry]:
    entries: list[OutlineEntry] = []
    for item in items:
        if isinstance(item, list):
            entries.extend(_walk_outline(reader, item, level + 1))
            continue
        try:
            page = reader.get_destination_page_number(item)
        except Exception:
            continue
        if page is None or page < 0:
            continue
        number, title = _split_heading(item.title or "")
        if number or title:
            entries.append(OutlineEntry(number, title, level, page))
    return entries


def parse_pdf(data: bytes) -> ParsedPdf:
    reader = PdfReader(io.BytesIO(data))
    pages = [(page.extract_text() or "") for page in reader.pages]
    try:
        outline = _walk_outline(reader, reader.outline)
    except Exception:
        outline = []
    return ParsedPdf(pages, outline)


def _normalise(line: str) -> str:
    """Line key for boilerplate counting: page numbers/roman numerals at the start don't matter."""
    key = _LEADING_PAGE_MARKER_RE.sub("", line.strip())
    return _TRAILING_PAGE_MARKER_RE.sub("", key)


def strip_boilerplate(pages: list[str]) -> list[str]:
    """Drop lines that repeat across most pages (ownership notices, running headers and footers)."""
    if not pages:
        return pages
    counts: Counter[str] = Counter()
    for page in pages:
        counts.update({_normalise(line) for line in page.splitlines() if line.strip()})
    threshold = max(2, BOILERPLATE_PAGE_SHARE * len(pages))
    repeated = {
        key for key, count in counts.items() if count >= threshold and len(key) <= _MAX_BOILERPLATE_LINE_CHARS
    }
    return [
        "\n".join(
            line for line in page.splitlines() if line.strip() and _normalise(line) not in repeated
        )
        for page in pages
    ]


def is_toc_page(text: str) -> bool:
    """Tables of contents are dominated by dotted-leader lines ('8.3 INSTALLATION ......... 34')."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    dotted = sum(1 for line in lines if _DOT_LEADER_RE.search(line))
    return dotted >= 8 or (dotted >= 4 and dotted / len(lines) >= 0.4)


def searchable_pages(pages: list[str]) -> list[str]:
    """Pages with boilerplate removed; table-of-contents pages are emptied (page numbers are kept)."""
    cleaned = strip_boilerplate(pages)
    return ["" if is_toc_page(page) else page for page in cleaned]
