"""Unit tests for the PDF text extraction / OCR fallback decision logic.

These are hermetic: pdfplumber and the OCR path are both mocked, so no PDF
file and no Tesseract binary are needed. They pin the decision table in
``extract_text_from_pdf`` — in particular that OCR never replaces richer
text extracted by pdfplumber.
"""

from unittest.mock import MagicMock

import pytest

from ingestion.chunkers.text_chunker import chunk_pages
from ingestion.extractors import pdf_extractor
from ingestion.extractors.pdf_extractor import OCR_MIN_CHARS, extract_text_from_pdf

PDF = "/nonexistent/report.pdf"


@pytest.fixture(autouse=True)
def reset_ocr_cache():
    """_ocr_available() memoises into a module global; clear it per test."""
    pdf_extractor._ocr_ready = None
    yield
    pdf_extractor._ocr_ready = None


def fake_pdf(monkeypatch, page_texts):
    """Make pdfplumber.open yield pages returning ``page_texts``."""
    pages = []
    for text in page_texts:
        page = MagicMock()
        page.extract_text.return_value = text
        pages.append(page)

    doc = MagicMock()
    doc.pages = pages
    ctx = MagicMock()
    ctx.__enter__.return_value = doc
    ctx.__exit__.return_value = False
    monkeypatch.setattr(pdf_extractor.pdfplumber, "open", lambda _path: ctx)
    return pages


def fake_ocr(monkeypatch, result):
    """Replace _ocr_page. ``result`` is a str or a callable(page_index)."""
    calls = []

    def _ocr(_pdf_path, index):
        calls.append(index)
        return result(index) if callable(result) else result

    monkeypatch.setattr(pdf_extractor, "_ocr_page", _ocr)
    return calls


def text_of(length, char="a"):
    return char * length


# ── OCR trigger threshold ─────────────────────────────────────────────────────


def test_rich_page_never_triggers_ocr(monkeypatch):
    fake_pdf(monkeypatch, [text_of(OCR_MIN_CHARS + 50)])
    calls = fake_ocr(monkeypatch, text_of(9999))

    result = extract_text_from_pdf(PDF)

    assert calls == [], "OCR must not run on a page that already has text"
    assert result["pages"][0]["ocr"] is False


def test_page_exactly_at_threshold_does_not_trigger_ocr(monkeypatch):
    fake_pdf(monkeypatch, [text_of(OCR_MIN_CHARS)])
    calls = fake_ocr(monkeypatch, text_of(9999))

    extract_text_from_pdf(PDF)

    assert calls == [], "threshold is strict: len(text) < OCR_MIN_CHARS"


def test_page_below_threshold_triggers_ocr(monkeypatch):
    fake_pdf(monkeypatch, [text_of(OCR_MIN_CHARS - 1)])
    calls = fake_ocr(monkeypatch, "")

    extract_text_from_pdf(PDF)

    assert calls == [0]


# ── The regression this module exists for ─────────────────────────────────────


def test_ocr_discarded_when_it_recovers_less(monkeypatch):
    """Chart/table pages: Tesseract returns less than pdfplumber.

    The previous implementation overwrote unconditionally and destroyed text.
    """
    original = text_of(153)
    fake_pdf(monkeypatch, [original])
    fake_ocr(monkeypatch, text_of(150, "b"))

    page = extract_text_from_pdf(PDF)["pages"][0]

    assert page["text"] == original
    assert page["ocr"] is False


def test_ocr_discarded_when_equal_length(monkeypatch):
    original = text_of(120)
    fake_pdf(monkeypatch, [original])
    fake_ocr(monkeypatch, text_of(120, "b"))

    page = extract_text_from_pdf(PDF)["pages"][0]

    assert page["text"] == original, "ties go to pdfplumber"
    assert page["ocr"] is False


def test_ocr_kept_when_it_recovers_more(monkeypatch):
    recovered = text_of(259, "b")
    fake_pdf(monkeypatch, [text_of(128)])
    fake_ocr(monkeypatch, recovered)

    page = extract_text_from_pdf(PDF)["pages"][0]

    assert page["text"] == recovered
    assert page["ocr"] is True


# ── Empty pages ───────────────────────────────────────────────────────────────


def test_blank_page_with_nothing_to_recover_stays_empty(monkeypatch):
    fake_pdf(monkeypatch, [""])
    fake_ocr(monkeypatch, "")

    page = extract_text_from_pdf(PDF)["pages"][0]

    assert page["text"] == ""
    assert page["ocr"] is False
    assert page["char_count"] == 0


def test_scanned_page_is_recovered_by_ocr(monkeypatch):
    fake_pdf(monkeypatch, [None])  # pdfplumber returns None on an image-only page
    fake_ocr(monkeypatch, "Tableau 3.1 — Population par region")

    page = extract_text_from_pdf(PDF)["pages"][0]

    assert page["text"].startswith("Tableau 3.1")
    assert page["ocr"] is True


def test_whitespace_only_page_is_treated_as_empty(monkeypatch):
    fake_pdf(monkeypatch, ["   \n\t  "])
    fake_ocr(monkeypatch, "")

    page = extract_text_from_pdf(PDF)["pages"][0]

    assert page["text"] == ""
    assert page["char_count"] == 0


# ── Result shape ──────────────────────────────────────────────────────────────


def test_char_count_matches_retained_text(monkeypatch):
    fake_pdf(monkeypatch, [text_of(10), text_of(300)])
    fake_ocr(monkeypatch, text_of(80, "b"))

    for page in extract_text_from_pdf(PDF)["pages"]:
        assert page["char_count"] == len(page["text"])


def test_page_numbers_are_one_based_and_ordered(monkeypatch):
    fake_pdf(monkeypatch, [text_of(300)] * 3)
    fake_ocr(monkeypatch, "")

    pages = extract_text_from_pdf(PDF)["pages"]

    assert [p["page_number"] for p in pages] == [1, 2, 3]


def test_ocr_runs_only_on_low_text_pages(monkeypatch):
    fake_pdf(monkeypatch, [text_of(300), text_of(10), text_of(300), ""])
    calls = fake_ocr(monkeypatch, "")

    extract_text_from_pdf(PDF)

    assert calls == [1, 3], "only the low-text pages should be rendered"


def test_filename_is_reported(monkeypatch):
    fake_pdf(monkeypatch, [text_of(300)])
    fake_ocr(monkeypatch, "")

    assert extract_text_from_pdf(PDF)["filename"] == "report.pdf"


# ── Toolchain availability ────────────────────────────────────────────────────


def test_missing_tesseract_is_reported_not_swallowed(monkeypatch):
    import pytesseract

    def boom():
        raise OSError("tesseract is not installed")

    monkeypatch.setattr(pytesseract, "get_tesseract_version", boom)

    assert pdf_extractor._ocr_available() is False


def test_availability_is_checked_once(monkeypatch):
    import pytesseract

    calls = []

    def counted():
        calls.append(1)
        return "5.5.2"

    monkeypatch.setattr(pytesseract, "get_tesseract_version", counted)

    for _ in range(4):
        assert pdf_extractor._ocr_available() is True

    assert len(calls) == 1, "toolchain probe must be memoised"


def test_ocr_page_skips_render_when_toolchain_missing(monkeypatch):
    import pdf2image

    monkeypatch.setattr(pdf_extractor, "_ocr_available", lambda: False)
    monkeypatch.setattr(
        pdf2image,
        "convert_from_path",
        lambda *a, **k: pytest.fail("must not render without a toolchain"),
    )

    assert pdf_extractor._ocr_page(PDF, 0) == ""


def test_render_failure_returns_empty_string(monkeypatch):
    import pdf2image

    def boom(*_args, **_kwargs):
        raise RuntimeError("poppler: Unable to find pdftoppm")

    monkeypatch.setattr(pdf_extractor, "_ocr_available", lambda: True)
    monkeypatch.setattr(pdf2image, "convert_from_path", boom)

    assert pdf_extractor._ocr_page(PDF, 0) == ""


def test_failing_ocr_leaves_pdfplumber_text_intact(monkeypatch):
    """A broken OCR toolchain must degrade, not delete."""
    import pdf2image

    original = text_of(150)
    fake_pdf(monkeypatch, [original])
    monkeypatch.setattr(pdf_extractor, "_ocr_available", lambda: True)
    monkeypatch.setattr(
        pdf2image,
        "convert_from_path",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("render failed")),
    )

    page = extract_text_from_pdf(PDF)["pages"][0]

    assert page["text"] == original
    assert page["ocr"] is False


# ── Metadata propagation ──────────────────────────────────────────────────────


def test_ocr_flag_reaches_chunk_metadata():
    pages = [
        {"page_number": 1, "text": "scanned content", "char_count": 15, "ocr": True},
        {"page_number": 2, "text": "native content", "char_count": 14, "ocr": False},
    ]

    chunks = chunk_pages(pages, {"institution": "ANSD"})

    by_page = {c["page_number"]: c["ocr"] for c in chunks}
    assert by_page == {1: True, 2: False}


def test_chunk_ocr_flag_defaults_to_false_for_legacy_pages():
    """Pages produced before the ocr key existed must still chunk."""
    chunks = chunk_pages(
        [{"page_number": 1, "text": "legacy", "char_count": 6}],
        {"institution": "ANSD"},
    )

    assert chunks[0]["ocr"] is False
