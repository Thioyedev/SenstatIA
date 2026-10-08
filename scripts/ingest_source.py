"""Ingest a single source by source_id. Usage: python scripts/ingest_source.py rgph5_preliminaire"""

from dotenv import load_dotenv

load_dotenv()

import sys
from pathlib import Path

from loguru import logger

from ingestion.chunkers.text_chunker import chunk_pages, chunk_table
from ingestion.extractors.pdf_extractor import extract_text_from_pdf
from ingestion.extractors.table_extractor import extract_tables_from_pdf
from ingestion.pipeline import SOURCES
from vectorstore.chroma_store import ChromaStore


def ingest_one(source_id: str, raw_dir: str = "./data/raw"):
    source = next((s for s in SOURCES if s["source_id"] == source_id), None)
    if not source:
        logger.error(
            f"Unknown source_id: {source_id}. Available: {[s['source_id'] for s in SOURCES]}"
        )
        sys.exit(1)

    pdf_path = Path(raw_dir) / source["filename"]
    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        sys.exit(1)

    store = ChromaStore()
    meta = {k: v for k, v in source.items() if k != "filename"}

    extracted = extract_text_from_pdf(str(pdf_path))
    tables = extract_tables_from_pdf(str(pdf_path))
    text_chunks = chunk_pages(extracted["pages"], meta)
    table_chunks = [chunk_table(t, meta) for t in tables]
    all_chunks = text_chunks + table_chunks

    store.add_chunks(all_chunks)
    logger.success(f"Indexed {len(all_chunks)} chunks for {source_id}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest_source.py <source_id>")
        sys.exit(1)
    ingest_one(sys.argv[1])
