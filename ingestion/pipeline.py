import json
from pathlib import Path
from loguru import logger
from ingestion.extractors.pdf_extractor import extract_text_from_pdf
from ingestion.extractors.table_extractor import extract_tables_from_pdf
from ingestion.chunkers.text_chunker import chunk_pages, chunk_table
from vectorstore.chroma_store import ChromaStore

# Registre des sources
SOURCES = [
    {
        "filename": "RGPH5_preliminaire_2023.pdf",
        "source_id": "rgph5_preliminaire",
        "institution": "ANSD",
        "report_name": "RGPH-5 Rapport Préliminaire",
        "year": 2023,
        "topics": ["population", "démographie", "habitat", "régions"],
        "url": "https://www.ansd.sn"
    },
    {
        "filename": "RGPH5_economie_2024.pdf",
        "source_id": "rgph5_economie",
        "institution": "ANSD",
        "report_name": "RGPH-5 Chapitre Économie",
        "year": 2024,
        "topics": ["emploi", "activité économique", "chômage", "régions"],
        "url": "https://www.ansd.sn"
    },
    {
        "filename": "EHCVM_2021_2022.pdf",
        "source_id": "ehcvm_2021",
        "institution": "ANSD",
        "report_name": "EHCVM 2021-2022",
        "year": 2022,
        "topics": ["pauvreté", "conditions de vie", "inégalités", "ménages"],
        "url": "https://www.ansd.sn"
    },
    {
        "filename": "SES_2022_2023.pdf",
        "source_id": "ses_2022_2023",
        "institution": "ANSD",
        "report_name": "Situation Économique et Sociale 2022-2023",
        "year": 2023,
        "topics": ["économie", "social", "santé", "éducation", "agriculture"],
        "url": "https://www.ansd.sn"
    },
]


def run_ingestion(raw_dir: str = "./data/raw"):
    store = ChromaStore()
    raw_path = Path(raw_dir)

    for source in SOURCES:
        pdf_path = raw_path / source["filename"]
        if not pdf_path.exists():
            logger.warning(f"PDF manquant : {pdf_path}")
            continue

        logger.info(f"Ingestion de {source['filename']}...")

        # Extraction texte
        extracted = extract_text_from_pdf(str(pdf_path))

        # Extraction tableaux
        tables = extract_tables_from_pdf(str(pdf_path))

        # Metadata de la source (sans filename)
        meta = {k: v for k, v in source.items() if k != "filename"}

        # Chunking texte
        text_chunks = chunk_pages(extracted["pages"], meta)

        # Chunking tableaux
        table_chunks = [chunk_table(t, meta) for t in tables]

        all_chunks = text_chunks + table_chunks
        logger.info(f"  → {len(text_chunks)} chunks texte + "
                    f"{len(table_chunks)} chunks tableau")

        # Indexation
        store.add_chunks(all_chunks)
        logger.success(f"  ✓ {source['source_id']} indexé")

    logger.success(f"Ingestion terminée. "
                   f"{store.collection.count()} chunks au total.")


if __name__ == "__main__":
    run_ingestion()
