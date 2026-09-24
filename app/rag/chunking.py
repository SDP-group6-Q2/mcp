"""Section-aware chunking. Pure functions: no I/O, no models.

Text is assigned to the manual's outline sections, then each section is split into chunks of roughly
TARGET_WORDS on line/sentence boundaries with a small overlap. Every chunk carries its section number,
title, breadcrumb path and page range, so an answer can cite "section 11.5.1.5, page 94".
"""

import re
from dataclasses import dataclass

from app.rag.pdf import OutlineEntry

# Bump when chunking changes, so existing indexes are rebuilt.
CHUNKER_VERSION = "1"

TARGET_WORDS = 200
MAX_WORDS = 280
MIN_CHUNK_WORDS = 12  # anything shorter is heading-only noise
_SHORT_LINE_CHARS = 45  # short lines (list items, table cells, headings) each stand alone
_SENTENCE_END = (".", "!", "?", ":", ";")


@dataclass(frozen=True)
class Section:
    number: str
    title: str
    level: int
    page: int
    path: str  # breadcrumb: "4 CLOSING MACHINE DESCRIPTION > 4.3 TECHNICAL DATA"


@dataclass(frozen=True)
class SectionText:
    section: Section | None  # None for text before the first bookmark
    text: str
    page_start: int  # 1-based
    page_end: int


@dataclass(frozen=True)
class Chunk:
    section_number: str
    section_title: str
    section_path: str
    page_start: int  # 1-based, as printed in a PDF viewer
    page_end: int
    content: str

    @property
    def embedding_text(self) -> str:
        """What gets embedded: the breadcrumb gives the chunk its context."""
        return f"{self.section_path}\n{self.content}" if self.section_path else self.content


def build_sections(outline: list[OutlineEntry]) -> list[Section]:
    """Outline entries in document order, each with its breadcrumb path."""
    sections: list[Section] = []
    stack: list[tuple[int, str]] = []  # (level, label)
    for entry in outline:
        label = f"{entry.number} {entry.title}".strip()
        while stack and stack[-1][0] >= entry.level:
            stack.pop()
        stack.append((entry.level, label))
        sections.append(
            Section(entry.number, entry.title, entry.level, entry.page, " > ".join(l for _, l in stack))
        )
    return sections


def _heading_offset(page_text: str, section: Section) -> int:
    """Offset of the section's heading line inside its page (0 if it isn't found)."""
    title_start = re.escape(" ".join(section.title.split())[:12])
    if not title_start:
        return 0
    number = rf"{re.escape(section.number)}\.?\s+" if section.number else ""
    pattern = re.compile(rf"^\s*{number}{title_start}", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(page_text)
    return match.start() if match else 0


def assign_sections(pages: list[str], sections: list[Section]) -> list[SectionText]:
    """Split the pages' text at the outline's heading positions.

    A section runs from its heading to the next heading in document order, so a parent section only
    holds the text before its first child. Emptied (table-of-contents) pages contribute nothing.
    """
    page_starts: list[int] = []
    offset = 0
    for text in pages:
        page_starts.append(offset)
        offset += len(text) + 1
    stream = "\n".join(pages)

    def page_of(position: int) -> int:
        page = 0
        for index, start in enumerate(page_starts):
            if start <= position:
                page = index
        return page

    positions: list[int] = []
    previous = 0
    for section in sections:
        page = min(section.page, len(pages) - 1)
        position = max(page_starts[page] + _heading_offset(pages[page], section), previous)
        positions.append(position)
        previous = position

    segments: list[SectionText] = []
    if not sections:
        return [SectionText(None, stream, 1, len(pages))] if stream.strip() else []
    if positions[0] > 0 and stream[: positions[0]].strip():
        segments.append(SectionText(None, stream[: positions[0]], 1, page_of(positions[0]) + 1))
    for index, section in enumerate(sections):
        end = positions[index + 1] if index + 1 < len(sections) else len(stream)
        text = stream[positions[index] : end]
        if text.strip():
            last = max(positions[index], end - 1)
            segments.append(
                SectionText(section, text, page_of(positions[index]) + 1, page_of(last) + 1)
            )
    return segments


def _units(text: str) -> list[str]:
    """Split text into units that shouldn't be cut: wrapped lines are joined into sentences, and short
    lines (list items, table cells) stay as separate units so tables aren't reflowed."""
    units: list[str] = []
    current: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        current.append(line)
        if line.endswith(_SENTENCE_END) or len(line) < _SHORT_LINE_CHARS:
            units.append(" ".join(current))
            current = []
    if current:
        units.append(" ".join(current))
    return units


def _split_long(unit: str, max_words: int) -> list[str]:
    words = unit.split()
    return [" ".join(words[i : i + max_words]) for i in range(0, len(words), max_words)]


def chunk_text(text: str, target_words: int = TARGET_WORDS, max_words: int = MAX_WORDS) -> list[str]:
    """Pack units into chunks of about target_words, carrying the last unit over as overlap."""
    units: list[str] = []
    for unit in _units(text):
        units.extend(_split_long(unit, max_words) if len(unit.split()) > max_words else [unit])

    chunks: list[str] = []
    current: list[str] = []
    words = 0
    for unit in units:
        unit_words = len(unit.split())
        if current and words + unit_words > target_words:
            chunks.append("\n".join(current))
            current = [current[-1]] if len(current[-1].split()) < target_words // 2 else []
            words = sum(len(u.split()) for u in current)
        current.append(unit)
        words += unit_words
    if current and (not chunks or "\n".join(current) != chunks[-1]):
        chunks.append("\n".join(current))
    return [c for c in chunks if len(c.split()) >= MIN_CHUNK_WORDS]


def chunk_manual(pages: list[str], outline: list[OutlineEntry]) -> list[Chunk]:
    """Chunks of one manual. `pages` must already be cleaned (see app.rag.pdf.searchable_pages)."""
    segments = assign_sections(pages, build_sections(outline))
    chunks: list[Chunk] = []
    for segment in segments:
        section = segment.section
        for content in chunk_text(segment.text):
            chunks.append(
                Chunk(
                    section_number=section.number if section else "",
                    section_title=section.title if section else "Front matter",
                    section_path=section.path if section else "Front matter",
                    page_start=segment.page_start,
                    page_end=segment.page_end,
                    content=content,
                )
            )
    return chunks
