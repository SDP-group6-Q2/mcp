from app.rag.chunking import assign_sections, build_sections, chunk_manual, chunk_text
from app.rag.pdf import OutlineEntry

OUTLINE = [
    OutlineEntry("11", "MAINTENANCE", 0, 1),
    OutlineEntry("11.5", "SCHEDULED MAINTENANCE", 1, 1),
    OutlineEntry("11.5.1", "EVERY 6000 WORKING HOURS", 2, 2),
    OutlineEntry("12", "SPARE PARTS", 0, 3),
]
LONG = "\n".join(f"Step {i}: lubricate the springs and check the clearance of the spindle pads carefully." for i in range(40))
PAGES = [
    "Cover page with the machine identification and edition details for this manual.",
    "11 MAINTENANCE\nGeneral maintenance rules apply to every operation on the closing machine described here.\n"
    "11.5 SCHEDULED MAINTENANCE\nScheduled maintenance keeps the machine in working order over the years of use.",
    "11.5.1 EVERY 6000 WORKING HOURS\nOverhaul the closure heads replacing the wear components as indicated in the table.",
    "12 SPARE PARTS\nSpare parts can be ordered from the AROL technical service quoting the serial number.",
]


def test_breadcrumb_paths():
    paths = [s.path for s in build_sections(OUTLINE)]
    assert paths[2] == "11 MAINTENANCE > 11.5 SCHEDULED MAINTENANCE > 11.5.1 EVERY 6000 WORKING HOURS"
    assert paths[3] == "12 SPARE PARTS"


def test_two_sections_starting_on_one_page_are_split_at_their_headings():
    segments = assign_sections(PAGES, build_sections(OUTLINE))
    by_number = {s.section.number: s for s in segments if s.section}
    assert "Scheduled maintenance keeps" not in by_number["11"].text
    assert "Scheduled maintenance keeps" in by_number["11.5"].text
    assert by_number["11.5.1"].page_start == 3 and by_number["12"].page_start == 4
    assert segments[0].section is None and "Cover page" in segments[0].text


def test_chunks_carry_section_and_pages():
    chunks = chunk_manual(PAGES, OUTLINE)
    spare = next(c for c in chunks if c.section_number == "12")
    assert spare.page_start == 4 and "serial number" in spare.content
    assert spare.embedding_text.startswith("12 SPARE PARTS\n")
    front = chunks[0]
    assert front.section_title == "Front matter"


def test_long_section_is_split_with_overlap_and_within_max_words():
    chunks = chunk_text(LONG)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 280 for c in chunks)
    # the last unit of a chunk opens the next one
    last_unit = chunks[0].splitlines()[-1]
    assert chunks[1].startswith(last_unit)


def test_table_like_short_lines_are_not_reflowed():
    text = "OPERATION AIM NOTES\nCheck of the head control\nspindles.\nCheck the clearance of the spindle pads. See sub-chapter 11.5.2.1 page 96."
    chunk = chunk_text(text)[0]
    assert chunk.splitlines()[0] == "OPERATION AIM NOTES"


def test_heading_only_noise_is_dropped():
    assert chunk_text("4.4.4.1 OPERATOR") == []


def test_no_outline_falls_back_to_one_section_of_everything():
    chunks = chunk_manual(PAGES, [])
    assert chunks and all(c.section_title == "Front matter" for c in chunks)
