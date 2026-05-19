"""
ColPali image-based PDF indexer.

Converts each PDF page to an image, embeds it with ColQwen2 (multi-vector patch
embeddings), and stores the result in Qdrant with multi-vector configuration.
This eliminates the text-extraction + OCR pipeline for scanned ANSD reports:
every page is retrieved visually, regardless of whether it has selectable text.

Requirements:
    pip install colpali-engine pdf2image pillow
    Qdrant server >= 1.10 (multivector support)

Usage:
    from ingestion.colpali_indexer import ColPaliIndexer
    indexer = ColPaliIndexer()
    indexer.index_pdf("data/raw/ansd_rgph5.pdf", source_id="rgph5", institution="ANSD")
"""
import os
from pathlib import Path
from typing import Optional

import torch
from loguru import logger
from pdf2image import convert_from_path
from PIL import Image
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    MatchValue,
    MultiVectorConfig,
    MultiVectorComparator,
    PointStruct,
    Prefetch,
    VectorParams,
)

try:
    from colpali_engine.models import ColQwen2, ColQwen2Processor
    _COLPALI_AVAILABLE = True
except ImportError:
    _COLPALI_AVAILABLE = False

COLPALI_COLLECTION = os.getenv("QDRANT_COLPALI_COLLECTION", "senstat_colpali")
COLPALI_MODEL = "vidore/colqwen2-v1.0"
PATCH_DIM = 128  # ColQwen2 patch embedding dimension
DPI = 150        # Resolution for PDF → image conversion (balance quality vs speed)


class ColPaliIndexer:
    """
    Index PDF documents via visual page embeddings (ColQwen2 multi-vector).

    Each PDF page becomes a set of patch-level vectors stored in Qdrant.
    Retrieval scores pages using late-interaction (MaxSim across query patches).
    """

    def __init__(self):
        if not _COLPALI_AVAILABLE:
            raise ImportError(
                "colpali-engine not installed — run: pip install colpali-engine"
            )

        self._device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        logger.info(f"ColPali device: {self._device}")

        self._model = ColQwen2.from_pretrained(
            COLPALI_MODEL,
            torch_dtype=torch.bfloat16,
            device_map=self._device,
        ).eval()
        self._processor = ColQwen2Processor.from_pretrained(COLPALI_MODEL)

        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")
        if url:
            self._client = QdrantClient(url=url, api_key=api_key)
        else:
            path = os.getenv("QDRANT_PATH", "./data/qdrant")
            self._client = QdrantClient(path=path)

        self._ensure_collection()

    # ── Collection ───────────────────────────────────────────────────────────

    def _ensure_collection(self):
        existing = {c.name for c in self._client.get_collections().collections}
        if COLPALI_COLLECTION not in existing:
            self._client.create_collection(
                collection_name=COLPALI_COLLECTION,
                vectors_config={
                    "colpali": VectorParams(
                        size=PATCH_DIM,
                        distance=Distance.COSINE,
                        multivector_config=MultiVectorConfig(
                            comparator=MultiVectorComparator.MAX_SIM
                        ),
                    )
                },
            )
            logger.info(f"Created ColPali collection '{COLPALI_COLLECTION}'")

    # ── Embedding ────────────────────────────────────────────────────────────

    def _embed_pages(self, images: list[Image.Image]) -> list[list[list[float]]]:
        """Return patch vectors for each page: shape (n_pages, n_patches, dim)."""
        batch_inputs = self._processor.process_images(images).to(self._device)
        with torch.no_grad():
            embeddings = self._model(**batch_inputs)
        return embeddings.cpu().float().tolist()

    def _embed_query(self, query: str) -> list[list[float]]:
        """Return patch vectors for a text query."""
        batch = self._processor.process_queries([query]).to(self._device)
        with torch.no_grad():
            embeddings = self._model(**batch)
        return embeddings[0].cpu().float().tolist()

    # ── Indexing ─────────────────────────────────────────────────────────────

    def index_pdf(
        self,
        pdf_path: str,
        source_id: str,
        institution: str,
        report_name: str = "",
        year: Optional[int] = None,
        batch_size: int = 8,
    ):
        """
        Convert PDF pages to images, embed with ColQwen2, upsert to Qdrant.
        Safe to re-run — point IDs are stable (source_id + page_number).
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        logger.info(f"Converting {path.name} to images at {DPI} DPI…")
        images = convert_from_path(str(path), dpi=DPI)
        total = len(images)
        logger.info(f"  → {total} pages")

        for start in range(0, total, batch_size):
            batch_imgs = images[start: start + batch_size]
            page_vecs = self._embed_pages(batch_imgs)

            points = []
            for i, vecs in enumerate(page_vecs):
                page_num = start + i + 1
                point_id = _stable_id(source_id, page_num)
                points.append(PointStruct(
                    id=point_id,
                    vector={"colpali": vecs},
                    payload={
                        "source_id": source_id,
                        "institution": institution,
                        "report_name": report_name or path.stem,
                        "page_number": page_num,
                        "year": year,
                        "pdf_path": str(path),
                    },
                ))

            self._client.upsert(collection_name=COLPALI_COLLECTION, points=points)
            logger.info(f"  Indexed pages {start + 1}–{start + len(batch_imgs)}/{total}")

        logger.info(f"ColPali indexing complete: {total} pages from {path.name}")

    # ── Retrieval ────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        n_results: int = 5,
        source_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Retrieve pages most relevant to query using MaxSim late-interaction.
        Returns list of dicts with source metadata + page_number + score.
        """
        query_vecs = self._embed_query(query)
        qdrant_filter = (
            Filter(must=[FieldCondition(key="source_id", match=MatchValue(value=source_id))])
            if source_id else None
        )

        results = self._client.query_points(
            collection_name=COLPALI_COLLECTION,
            query=query_vecs,
            using="colpali",
            limit=n_results,
            filter=qdrant_filter,
            with_payload=True,
        )

        chunks = []
        for r in results.points:
            payload = dict(r.payload or {})
            chunks.append({
                "text": f"[Visual page — {payload.get('report_name', '')} p.{payload.get('page_number', '?')}]",
                "score": r.score,
                **payload,
            })

        return chunks


# ── Utilities ────────────────────────────────────────────────────────────────

def _stable_id(source_id: str, page_num: int) -> str:
    """UUID stable across re-ingestion runs."""
    import hashlib
    import uuid
    digest = hashlib.sha256(f"{source_id}:{page_num}".encode()).hexdigest()[:32]
    return str(uuid.UUID(digest))
