from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List

def chunk_pages(pages: list[dict], source_metadata: dict) -> list[dict]:
    """
    Chunke les pages extraites avec métadonnées.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        separators=["\n\n", "\n", ".", " "]
    )

    chunks = []
    for page in pages:
        if not page["text"].strip():
            continue

        texts = splitter.split_text(page["text"])
        for j, text in enumerate(texts):
            chunks.append({
                "text": text,
                "page_number": page["page_number"],
                "chunk_index": j,
                "ocr": bool(page.get("ocr", False)),
                **source_metadata  # institution, report_name, year, etc.
            })

    return chunks


def chunk_table(table: dict, source_metadata: dict) -> dict:
    """
    Un tableau = 1 chunk avec son contexte complet.
    """
    text = f"[TABLEAU — Page {table['page']}]\n\n{table['markdown']}"
    return {
        "text": text,
        "page_number": table["page"],
        "chunk_index": f"table_{table['table_index']}",
        "is_table": True,
        **source_metadata
    }
