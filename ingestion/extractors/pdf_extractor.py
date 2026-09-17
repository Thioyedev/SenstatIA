import pdfplumber
from pathlib import Path
from loguru import logger

OCR_MIN_CHARS = 200
OCR_DPI = 200
OCR_LANG = "fra"

_ocr_ready: bool | None = None


def _ocr_available() -> bool:
    """Vérifie la chaîne OCR une seule fois : un binaire manquant doit être
    signalé explicitement, pas avalé page par page."""
    global _ocr_ready
    if _ocr_ready is None:
        try:
            import pytesseract
            from pdf2image import convert_from_path  # noqa: F401

            pytesseract.get_tesseract_version()
            _ocr_ready = True
        except Exception as e:
            logger.error(
                f"OCR indisponible ({e}) — les pages scannées resteront vides. "
                f"Installer: brew install tesseract tesseract-lang poppler"
            )
            _ocr_ready = False
    return _ocr_ready


def extract_text_from_pdf(pdf_path: str) -> dict:
    """
    Extrait le texte d'un PDF.
    Stratégie : pdfplumber en premier, OCR en fallback si texte < OCR_MIN_CHARS.
    """
    path = Path(pdf_path)
    result = {
        "source_path": str(path),
        "filename": path.name,
        "pages": []
    }

    ocr_pages = 0
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = (page.extract_text() or "").strip()
            ocr_used = False

            if len(text) < OCR_MIN_CHARS:
                ocr_text = _ocr_page(pdf_path, i).strip()
                # On ne garde l'OCR que s'il récupère davantage : sur les pages
                # partiellement extraites, il rend souvent moins que pdfplumber
                # et l'écraser détruisait du texte valide.
                if len(ocr_text) > len(text):
                    text = ocr_text
                    ocr_used = True
                    ocr_pages += 1

            result["pages"].append({
                "page_number": i + 1,
                "text": text,
                "char_count": len(text),
                "ocr": ocr_used,
            })

    logger.info(
        f"Extrait {len(result['pages'])} pages de {path.name} "
        f"({ocr_pages} via OCR)"
    )
    return result


def _ocr_page(pdf_path: str, page_index: int) -> str:
    """OCR d'une page via pytesseract. Rendu page par page pour ne pas charger
    un rapport de 600 pages en images."""
    if not _ocr_available():
        return ""
    try:
        from pdf2image import convert_from_path
        import pytesseract

        images = convert_from_path(
            pdf_path, first_page=page_index + 1, last_page=page_index + 1,
            dpi=OCR_DPI,
        )
        return pytesseract.image_to_string(images[0], lang=OCR_LANG)
    except Exception as e:
        logger.error(f"OCR échoué page {page_index+1}: {e}")
        return ""
