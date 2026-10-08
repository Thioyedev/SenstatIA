"""Integration test for the OCR fallback against a real Tesseract.

The unit tests in tests/unit/test_extractors.py mock both pdfplumber and the
OCR path, so they pin the decision logic but never prove the toolchain works.
This module builds a PDF holding the three page types the real corpus contains
— a native text layer, an image-only scan, and a blank page — then runs the
genuine pdfplumber + Tesseract + poppler chain over it.

Skipped rather than failed when the toolchain is absent, so the suite stays
runnable on a machine or CI image without Tesseract.
"""

import shutil
from pathlib import Path

import pdfplumber
import pytest

from ingestion.chunkers.text_chunker import chunk_pages
from ingestion.extractors.pdf_extractor import OCR_MIN_CHARS, extract_text_from_pdf

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

SCANNED_LINES = [
    "Republique du Senegal",
    "Agence Nationale de la Statistique et de la Demographie",
    "Tableau 3.1 - Population par region",
    "Dakar 4 043 057 habitants",
    "Thies 2 077 758 habitants",
    "Taux de pauvrete national 37,8 pour cent",
]

NATIVE_MARKER = "Produit interieur brut du Senegal en 2023"

NATIVE_PAGE = 1
SCANNED_PAGE = 2
BLANK_PAGE = 3


def _missing_requirement():
    """Return why this module cannot run, or None if it can."""
    if shutil.which("tesseract") is None:
        return "tesseract binary not on PATH"
    if shutil.which("pdftoppm") is None:
        return "poppler (pdftoppm) not on PATH"
    try:
        import pytesseract

        if "fra" not in pytesseract.get_languages():
            return "tesseract French language data (fra) not installed"
    except Exception as exc:
        return f"pytesseract unusable: {exc}"
    if not any(Path(f).exists() for f in FONT_CANDIDATES):
        return "no TrueType font available to render the scanned page"
    return None


pytestmark = pytest.mark.skipif(
    _missing_requirement() is not None,
    reason=_missing_requirement() or "",
)


def _render_scanned_image(width=1700, height=2200):
    """Draw text into a bitmap. The result carries no text layer at all."""
    from PIL import Image, ImageDraw, ImageFont

    font_path = next(f for f in FONT_CANDIDATES if Path(f).exists())
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, 44)

    y = 200
    for line in SCANNED_LINES:
        draw.text((160, y), line, fill="black", font=font)
        y += 110
    return image


@pytest.fixture(scope="module")
def mixed_pdf(tmp_path_factory):
    """A three-page PDF: native text, image-only scan, blank."""
    import fitz
    from PIL import Image  # noqa: F401

    out_dir = tmp_path_factory.mktemp("ocr")
    png = out_dir / "scan.png"
    _render_scanned_image().save(png)

    doc = fitz.open()

    native = doc.new_page(width=595, height=842)
    native.insert_text((72, 120), NATIVE_MARKER, fontsize=13)
    native.insert_text(
        (72, 150),
        "La croissance reelle atteint 4,3 pour cent selon la DPEE.",
        fontsize=13,
    )
    # Push the native page well past OCR_MIN_CHARS so it cannot trip the fallback
    for i in range(12):
        native.insert_text(
            (72, 190 + i * 18),
            f"Ligne {i} du rapport, presente pour depasser le seuil de caracteres.",
            fontsize=12,
        )

    scanned = doc.new_page(width=595, height=842)
    scanned.insert_image(scanned.rect, filename=str(png))

    doc.new_page(width=595, height=842)  # blank

    path = out_dir / "mixed.pdf"
    doc.save(str(path))
    doc.close()
    return str(path)


@pytest.fixture(scope="module")
def extracted(mixed_pdf):
    return extract_text_from_pdf(mixed_pdf)


def page(extracted, number):
    return extracted["pages"][number - 1]


# ── Fixture integrity ─────────────────────────────────────────────────────────


def test_scanned_page_has_no_text_layer(mixed_pdf):
    """Guards the fixture itself.

    If a future PIL or PyMuPDF started emitting a text layer here, every OCR
    assertion below would still pass while testing nothing.
    """
    with pdfplumber.open(mixed_pdf) as pdf:
        target = pdf.pages[SCANNED_PAGE - 1]
        assert (target.extract_text() or "").strip() == ""
        assert target.images, "the scanned page must actually carry an image"


def test_native_page_has_a_text_layer(mixed_pdf):
    with pdfplumber.open(mixed_pdf) as pdf:
        text = pdf.pages[NATIVE_PAGE - 1].extract_text() or ""
    assert len(text.strip()) >= OCR_MIN_CHARS


# ── The real chain ────────────────────────────────────────────────────────────


def test_scanned_page_is_recovered_by_tesseract(extracted):
    scanned = page(extracted, SCANNED_PAGE)

    assert scanned["ocr"] is True
    assert scanned["char_count"] > 0


def test_recovered_text_carries_the_page_content(extracted):
    text = page(extracted, SCANNED_PAGE)["text"].lower()

    assert "senegal" in text
    assert "population" in text
    assert "dakar" in text


def test_recovered_text_keeps_the_figures(extracted):
    """Statistics are the payload; OCR that drops digits is useless here."""
    digits = page(extracted, SCANNED_PAGE)["text"].replace(" ", "")

    assert "4043057" in digits, "Dakar population lost in OCR"
    assert "37,8" in digits, "poverty rate lost in OCR"


def test_native_page_keeps_its_own_text(extracted):
    native = page(extracted, NATIVE_PAGE)

    assert native["ocr"] is False
    assert NATIVE_MARKER in native["text"]


def test_blank_page_recovers_nothing(extracted):
    """Mirrors the 55 blank pages in Rapport-def-RGPH-5.pdf."""
    blank = page(extracted, BLANK_PAGE)

    assert blank["text"] == ""
    assert blank["ocr"] is False
    assert blank["char_count"] == 0


def test_only_the_scanned_page_is_flagged(extracted):
    flags = [p["ocr"] for p in extracted["pages"]]

    assert flags == [False, True, False]


def test_char_counts_match_retained_text(extracted):
    for p in extracted["pages"]:
        assert p["char_count"] == len(p["text"])


# ── Through to chunk metadata ─────────────────────────────────────────────────


def test_ocr_provenance_survives_chunking(extracted):
    chunks = chunk_pages(extracted["pages"], {"institution": "ANSD", "year": 2023})

    assert chunks, "expected at least one chunk"
    ocr_pages = {c["page_number"] for c in chunks if c["ocr"]}
    assert ocr_pages == {SCANNED_PAGE}
    assert all(c["institution"] == "ANSD" for c in chunks)


def test_blank_page_produces_no_chunks(extracted):
    chunks = chunk_pages(extracted["pages"], {"institution": "ANSD"})

    assert BLANK_PAGE not in {c["page_number"] for c in chunks}
