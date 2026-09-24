from app.rag.pdf import is_toc_page, searchable_pages, strip_boilerplate

NOTICE = "AROL S.p.A. - teaching copy, Politecnico di Torino. Do not redistribute."


def _pages(n: int) -> list[str]:
    return [f"{i + 1}THIS MANUAL IS PROPERTY OF AROL S.p.A.. ANY REPRODUCTION IS PROHIBITED.\nBody of page {i}.\n{NOTICE}" for i in range(n)]


def test_boilerplate_removed_even_with_glued_or_trailing_page_numbers():
    pages = _pages(9) + ["THIS MANUAL IS PROPERTY OF AROL S.p.A.. ANY REPRODUCTION IS PROHIBITED. 35\nBody of page 9.\n" + NOTICE]
    cleaned = strip_boilerplate(pages)
    assert all("PROPERTY OF AROL" not in page and "teaching copy" not in page for page in cleaned)
    assert cleaned[3] == "Body of page 3."


def test_rare_lines_survive():
    pages = _pages(9) + ["A one-off warning line.\nBody"]
    assert "A one-off warning line." in strip_boilerplate(pages)[9]


def test_toc_detection():
    toc = "\n".join(f"8.{i} SOME CHAPTER TITLE ............ {30 + i}" for i in range(12))
    assert is_toc_page(toc)
    assert not is_toc_page("Check the clearance of the spindle pads.\nSee sub-chapter 11.5.2.1 page 96.")
    assert not is_toc_page("")


def test_toc_pages_are_emptied_but_page_count_is_kept():
    toc = "\n".join(f"{i} CHAPTER ............ {i}" for i in range(12))
    pages = searchable_pages(["Front page text", toc, "Real content here"] + ["filler"] * 3)
    assert len(pages) == 6 and pages[1] == "" and pages[2] == "Real content here"
