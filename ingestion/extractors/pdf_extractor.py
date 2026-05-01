import pdfplumber
import fitz  # PyMuPDF
from pathlib import Path
from loguru import logger

def extract_text_from_pdf(pdf_path: str) -> dict:
    """
    Extrait le texte d'un PDF.
    Stratégie : pdfplumber en premier, OCR en fallback si texte < 200 chars.
    """
    path = Path(pdf_path)
    result = {
        "source_path": str(path),
        "filename": path.name,
        "pages": []
    }

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""

            # Fallback OCR si page scannée
            if len(text.strip()) < 200:
                logger.warning(f"Page {i+1} pauvre en texte → OCR")
                text = _ocr_page(pdf_path, i)

            result["pages"].append({
                "page_number": i + 1,
                "text": text.strip(),
                "char_count": len(text)
            })

    logger.info(f"Extrait {len(result['pages'])} pages de {path.name}")
    return result


def _ocr_page(pdf_path: str, page_index: int) -> str:
    """OCR d'une page via pytesseract."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        images = convert_from_path(pdf_path, first_page=page_index+1,
                                   last_page=page_index+1, dpi=200)
        return pytesseract.image_to_string(images[0], lang='fra')
    except Exception as e:
        logger.error(f"OCR échoué page {page_index+1}: {e}")
        return ""
