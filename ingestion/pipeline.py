"""
Ingestion pipeline — driven entirely by data/sources.json.

Every source entry in sources.json defines its own pipeline type:
  pdf_text     → text extraction (pdfplumber + OCR fallback) + chunking
  pdf_colpali  → visual page embeddings via ColPali (for scanned PDFs)
  api_imf      → IMF WEO REST API
  api_ilostat  → ILO ILOSTAT REST API
  api_faostat  → FAO FAOSTAT REST API
  api_worldbank→ World Bank Open Data API
  xlsx         → Excel/CSV download → tabular chunks

Usage:
  python ingestion/pipeline.py                    # ingest all pending
  python ingestion/pipeline.py --id ansd_neer     # ingest one source
  python ingestion/pipeline.py --force            # re-ingest already-indexed
  python ingestion/pipeline.py --dry-run          # print plan, no writes
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

SOURCES_FILE = Path(__file__).parent.parent / "data" / "sources.json"
RAW_DIR = Path(os.getenv("DATA_RAW_DIR", "./data/raw"))


# ── Sources registry ──────────────────────────────────────────────────────────

def load_sources() -> list[dict]:
    with open(SOURCES_FILE) as f:
        return json.load(f)


def save_sources(sources: list[dict]):
    with open(SOURCES_FILE, "w") as f:
        json.dump(sources, f, ensure_ascii=False, indent=2)


def mark_indexed(sources: list[dict], source_id: str, edition_label: str | None = None):
    """Update status → indexed and set indexed_at in sources.json."""
    for s in sources:
        if s["id"] != source_id:
            continue
        if edition_label and "editions" in s:
            for ed in s["editions"]:
                if ed["label"] == edition_label:
                    ed["status"] = "indexed"
                    break
            # Mark parent indexed only when all editions are done
            if all(ed.get("status") == "indexed" for ed in s["editions"]):
                s["status"] = "indexed"
                s["indexed_at"] = datetime.now(timezone.utc).isoformat()
        else:
            s["status"] = "indexed"
            s["indexed_at"] = datetime.now(timezone.utc).isoformat()
        break
    save_sources(sources)


# ── Auto-download ─────────────────────────────────────────────────────────────

def _download(url: str, dest: Path, filetype: str = "pdf"):
    """Download a file if it doesn't exist locally."""
    if dest.exists():
        logger.debug(f"Already exists: {dest.name}")
        return
    logger.info(f"Downloading {dest.name} from {url[:80]}…")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    import subprocess
    result = subprocess.run(
        ["curl", "-L", "-s", "-o", str(dest),
         "-A", "Mozilla/5.0 SenStat/1.0",
         "--retry", "3", "--retry-delay", "2",
         url],
        capture_output=True, timeout=120,
    )
    if result.returncode != 0 or not dest.exists() or dest.stat().st_size < 1024:
        dest.unlink(missing_ok=True)
        raise RuntimeError(f"curl failed (rc={result.returncode}): {result.stderr.decode()[:200]}")
    if filetype == "pdf":
        magic = dest.read_bytes()[:4]
        if magic != b"%PDF":
            dest.unlink()
            raise RuntimeError(f"Downloaded file is not a PDF (got: {magic!r}) — URL may require browser auth or JS")
    logger.success(f"Downloaded: {dest.name} ({dest.stat().st_size // 1024} KB)")


# ── XLSX pipeline ─────────────────────────────────────────────────────────────

def _ingest_xlsx(source: dict, store) -> int:
    """Download XLSX, extract all sheets as text chunks."""
    import openpyxl

    dest = RAW_DIR / source["filename"]
    if source.get("direct_url"):
        _download(source["direct_url"], dest, filetype="xlsx")

    if not dest.exists():
        logger.warning(f"XLSX not found: {dest}")
        return 0

    wb = openpyxl.load_workbook(dest, read_only=True, data_only=True)
    meta = _base_meta(source)
    chunks = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = []
        for row in ws.iter_rows(values_only=True):
            cells = [str(c) if c is not None else "" for c in row]
            if any(cells):
                rows.append(" | ".join(cells))
        if not rows:
            continue

        text = f"{source['name']} — Feuille: {sheet_name}\n" + "\n".join(rows[:300])
        chunks.append({**meta, "text": text, "page_number": 0,
                       "chunk_index": len(chunks), "is_table": True})

    store.add_chunks(chunks)
    logger.success(f"XLSX {source['id']}: {len(chunks)} sheet chunks indexed")
    return len(chunks)


# ── PDF text pipeline ─────────────────────────────────────────────────────────

def _ingest_pdf_text(source: dict, edition: dict | None, store) -> int:
    """Standard PDF pipeline: text extraction + chunking."""
    from ingestion.chunkers.text_chunker import chunk_pages, chunk_table
    from ingestion.extractors.pdf_extractor import extract_text_from_pdf
    from ingestion.extractors.table_extractor import extract_tables_from_pdf

    entry = edition or source
    filename = entry.get("filename") or source.get("filename")
    if not filename:
        logger.warning(f"No filename for {source['id']} / {entry.get('label', '')}")
        return 0

    pdf_path = RAW_DIR / filename
    if not pdf_path.exists() and entry.get("direct_url"):
        _download(entry["direct_url"], pdf_path)
    if not pdf_path.exists():
        logger.warning(f"PDF not found: {pdf_path} — skipping")
        return 0

    meta = _base_meta(source, edition)
    extracted = extract_text_from_pdf(str(pdf_path))
    tables = extract_tables_from_pdf(str(pdf_path))

    text_chunks = chunk_pages(extracted["pages"], meta)
    table_chunks = [chunk_table(t, meta) for t in tables]
    all_chunks = text_chunks + table_chunks

    store.add_chunks(all_chunks)
    edition_tag = f"/{edition['label']}" if edition else ""
    logger.success(
        f"{source['id']}{edition_tag}: "
        f"{len(text_chunks)} text + {len(table_chunks)} table chunks"
    )
    return len(all_chunks)


# ── PDF ColPali pipeline ──────────────────────────────────────────────────────

def _ingest_pdf_colpali(source: dict, edition: dict | None) -> int:
    """Visual PDF pipeline: page images → ColQwen2 → Qdrant multivector."""
    from ingestion.colpali_indexer import ColPaliIndexer

    entry = edition or source
    filename = entry.get("filename") or source.get("filename")
    if not filename:
        logger.warning(f"No filename for ColPali source {source['id']}")
        return 0

    pdf_path = RAW_DIR / filename
    if not pdf_path.exists() and entry.get("direct_url"):
        _download(entry["direct_url"], pdf_path)
    if not pdf_path.exists():
        logger.warning(f"PDF not found for ColPali: {pdf_path}")
        return 0

    indexer = ColPaliIndexer()
    indexer.index_pdf(
        pdf_path=str(pdf_path),
        source_id=source["id"],
        institution=source["institution"],
        report_name=source["name"] + (f" {edition['label']}" if edition else ""),
        year=entry.get("year") or source.get("year"),
    )
    # Page count is handled inside ColPaliIndexer
    return 1  # signal success


# ── API pipelines ─────────────────────────────────────────────────────────────

def _ingest_api(source: dict, store) -> int:
    pipeline = source["pipeline"]

    if pipeline == "api_imf":
        from ingestion.api_fetchers.imf_weo import fetch_imf_weo
        chunks = fetch_imf_weo(source)
    elif pipeline == "api_ilostat":
        from ingestion.api_fetchers.ilostat import fetch_ilostat
        chunks = fetch_ilostat(source)
    elif pipeline == "api_faostat":
        from ingestion.api_fetchers.faostat import fetch_faostat
        chunks = fetch_faostat(source)
    elif pipeline == "api_worldbank":
        from ingestion.api_fetchers.worldbank import fetch_worldbank
        chunks = fetch_worldbank(source)
    else:
        logger.warning(f"Unknown API pipeline: {pipeline}")
        return 0

    if chunks:
        store.add_chunks(chunks)
        logger.success(f"{source['id']}: {len(chunks)} API chunks indexed")
    return len(chunks)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _base_meta(source: dict, edition: dict | None = None) -> dict:
    entry = edition or source
    return {
        "source_id": source["id"],
        "institution": source["institution"],
        "report_name": (
            f"{source['name']} {edition['label']}" if edition else source["name"]
        ),
        "year": entry.get("year") or source.get("year"),
        "url": source.get("url", ""),
        "edition": edition["label"] if edition else None,
    }


def _get_store():
    if os.getenv("USE_QDRANT", "false").lower() == "true":
        from vectorstore.qdrant_store import QdrantStore
        return QdrantStore()
    from vectorstore.chroma_store import ChromaStore
    return ChromaStore()


def _should_skip(source: dict, edition: dict | None, force: bool) -> bool:
    entry = edition or source
    if entry.get("status") == "excluded":
        return True  # always skip excluded sources, even with --force
    return entry.get("status") == "indexed" and not force


# ── Main orchestrator ─────────────────────────────────────────────────────────

def run_ingestion(
    source_id: str | None = None,
    force: bool = False,
    dry_run: bool = False,
    raw_dir: str | None = None,
):
    global RAW_DIR
    if raw_dir:
        RAW_DIR = Path(raw_dir)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    all_sources = load_sources()
    if source_id:
        sources = [s for s in all_sources if s["id"] == source_id]
        if not sources:
            logger.error(f"Source '{source_id}' not found in sources.json")
            sys.exit(1)
    else:
        sources = all_sources

    store = None if dry_run else _get_store()
    total_chunks = 0

    for source in sources:
        pipeline = source.get("pipeline", "pdf_text")
        editions = source.get("editions")

        # ── API and XLSX sources (no editions) ─────────────────────────────
        if pipeline.startswith("api_") or pipeline == "xlsx":
            if _should_skip(source, None, force):
                logger.info(f"Skip {source['id']} (already indexed)")
                continue
            if dry_run:
                logger.info(f"[dry-run] Would ingest {source['id']} via {pipeline}")
                continue
            try:
                n = _ingest_xlsx(source, store) if pipeline == "xlsx" else _ingest_api(source, store)
            except Exception as e:
                logger.error(f"SKIP {source['id']}: {e}")
                continue
            if n:
                total_chunks += n
                mark_indexed(all_sources, source["id"])

        # ── PDF sources with editions ───────────────────────────────────────
        elif editions:
            for edition in editions:
                if _should_skip(source, edition, force):
                    logger.info(f"Skip {source['id']}/{edition['label']} (indexed)")
                    continue
                if dry_run:
                    logger.info(f"[dry-run] Would ingest {source['id']}/{edition['label']} via {pipeline}")
                    continue
                try:
                    n = (_ingest_pdf_colpali(source, edition) if pipeline == "pdf_colpali"
                         else _ingest_pdf_text(source, edition, store))
                except Exception as e:
                    logger.error(f"SKIP {source['id']}/{edition['label']}: {e}")
                    continue
                if n:
                    total_chunks += n
                    mark_indexed(all_sources, source["id"], edition["label"])

        # ── Single PDF sources ──────────────────────────────────────────────
        else:
            if _should_skip(source, None, force):
                logger.info(f"Skip {source['id']} (already indexed)")
                continue
            if dry_run:
                logger.info(f"[dry-run] Would ingest {source['id']} via {pipeline}")
                continue
            try:
                n = (_ingest_pdf_colpali(source, None) if pipeline == "pdf_colpali"
                     else _ingest_pdf_text(source, None, store))
            except Exception as e:
                logger.error(f"SKIP {source['id']}: {e}")
                continue
            if n:
                total_chunks += n
                mark_indexed(all_sources, source["id"])

    if not dry_run:
        logger.success(f"Ingestion complete — {total_chunks} new chunks indexed")
    else:
        logger.info("Dry-run complete — no data written")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SenStat ingestion pipeline")
    parser.add_argument("--id", dest="source_id", help="Ingest a single source by ID")
    parser.add_argument("--force", action="store_true", help="Re-ingest already-indexed sources")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing")
    parser.add_argument("--raw-dir", help="Override DATA_RAW_DIR")
    args = parser.parse_args()

    run_ingestion(
        source_id=args.source_id,
        force=args.force,
        dry_run=args.dry_run,
        raw_dir=args.raw_dir,
    )
