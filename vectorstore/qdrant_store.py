"""
Qdrant vector store: dense + BM42 sparse hybrid search with native RRF fusion.
Replaces the ChromaDB + BM25 sidecar with a single store.

The dense embedder defaults to the same sentence-transformers model as ChromaStore
(EMBEDDING_MODEL), so USE_QDRANT switches the storage, not the embedding. Set
QDRANT_DENSE_EMBEDDER=voyage to use voyage-3-large instead (paid API).

Usage:
    export QDRANT_URL=https://...qdrant.io   # or omit for local disk store
    export QDRANT_API_KEY=...
    export USE_QDRANT=true
    export QDRANT_DENSE_EMBEDDER=voyage      # optional, needs VOYAGE_API_KEY
"""

import hashlib
import os
import uuid

from fastembed import SparseTextEmbedding
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    MatchAny,
    MatchValue,
    PointStruct,
    Prefetch,
    SparseIndexParams,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

try:
    import voyageai

    _VOYAGE_AVAILABLE = True
except ImportError:
    _VOYAGE_AVAILABLE = False

COLLECTION = os.getenv("QDRANT_COLLECTION", "senstat")
SPARSE_MODEL = "Qdrant/bm42-all-minilm-l6-v2-attentions"
VOYAGE_MODEL = "voyage-3-large"
VOYAGE_DIM = 1024

# Payload field recording which model embedded a point. Points written before it
# existed carry none, and were all embedded with Voyage.
EMBEDDER_KEY = "dense_embedder"
LEGACY_EMBEDDER = VOYAGE_MODEL


def _chunk_uuid(text: str) -> str:
    """Stable UUID from chunk text for idempotent upserts."""
    digest = hashlib.sha256(text.encode()).hexdigest()[:32]
    return str(uuid.UUID(digest))


def _build_filter(where: dict) -> Filter:
    conditions = []
    for key, value in where.items():
        if isinstance(value, dict) and "$in" in value:
            conditions.append(FieldCondition(key=key, match=MatchAny(any=value["$in"])))
        else:
            conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
    return Filter(must=conditions)


def _point_to_chunk(point) -> dict:
    payload = dict(point.payload or {})
    text = payload.pop("text", "")
    payload.pop(EMBEDDER_KEY, None)
    return {"text": text, "score": point.score, **payload}


class QdrantStore:
    """
    Hybrid Qdrant store: dense vectors (local model or Voyage) + BM42 sparse vectors.
    Native RRF fusion replaces the BM25 sidecar in retrieval_agent.py.
    """

    def __init__(self):
        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")

        if url:
            self._client = QdrantClient(url=url, api_key=api_key)
            logger.info(f"QdrantStore → cloud at {url}")
        else:
            path = os.getenv("QDRANT_PATH", "./data/qdrant")
            self._client = QdrantClient(path=path)
            logger.info(f"QdrantStore → local disk at {path}")

        embedder = os.getenv("QDRANT_DENSE_EMBEDDER", "local")
        self._voyage = None
        self._local = None
        if embedder == "voyage":
            if not _VOYAGE_AVAILABLE:
                raise ImportError("voyageai package required — pip install voyageai")
            self._voyage = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
            self._embedder_name = VOYAGE_MODEL
            self._dense_dim = VOYAGE_DIM
        elif embedder == "local":
            from sentence_transformers import SentenceTransformer

            self._embedder_name = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")
            self._local = SentenceTransformer(self._embedder_name)
            self._dense_dim = self._local.get_sentence_embedding_dimension()
        else:
            raise ValueError(f"QDRANT_DENSE_EMBEDDER must be 'local' or 'voyage', got {embedder!r}")
        logger.info(f"QdrantStore dense embedder: {self._embedder_name}")

        self._sparse = SparseTextEmbedding(SPARSE_MODEL)
        self._ensure_collection()
        self._check_embedder()

    # ── Collection management ────────────────────────────────────────────────

    def _ensure_collection(self):
        existing = {c.name for c in self._client.get_collections().collections}
        if COLLECTION not in existing:
            self._client.create_collection(
                collection_name=COLLECTION,
                vectors_config={
                    "dense": VectorParams(size=self._dense_dim, distance=Distance.COSINE)
                },
                sparse_vectors_config={
                    "sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False))
                },
            )
            logger.info(f"Created Qdrant collection '{COLLECTION}'")

    def _check_embedder(self):
        """Refuse a collection embedded by another model.

        Querying it would not fail: the dimensions can match (e5-large and
        voyage-3-large are both 1024), so the results would look plausible and
        be wrong. Checking at start-up also keeps add_chunks from mixing models.
        """
        points, _ = self._client.scroll(
            collection_name=COLLECTION, limit=1, with_payload=[EMBEDDER_KEY]
        )
        if not points:
            return
        indexed_with = (points[0].payload or {}).get(EMBEDDER_KEY, LEGACY_EMBEDDER)
        if indexed_with != self._embedder_name:
            raise RuntimeError(
                f"Qdrant collection '{COLLECTION}' was embedded with {indexed_with}, but the "
                f"configured dense embedder is {self._embedder_name}. Re-index the "
                f"collection, or set QDRANT_DENSE_EMBEDDER / EMBEDDING_MODEL to match."
            )

    # ── Embeddings ───────────────────────────────────────────────────────────

    def _embed_dense(self, texts: list[str], input_type: str = "document") -> list[list[float]]:
        if self._voyage is not None:
            result = self._voyage.embed(texts, model=VOYAGE_MODEL, input_type=input_type)
            return result.embeddings
        # Encoded exactly as ChromaStore's embedding function does (no e5
        # "query:"/"passage:" prefixes), so both stores hold the same vectors.
        return self._local.encode(texts).tolist()

    def _embed_sparse(self, texts: list[str]) -> list[SparseVector]:
        vecs = []
        for sv in self._sparse.embed(texts):
            vecs.append(
                SparseVector(
                    indices=sv.indices.tolist(),
                    values=sv.values.tolist(),
                )
            )
        return vecs

    def _query_sparse(self, query: str) -> SparseVector:
        sv = next(self._sparse.query_embed(query))
        return SparseVector(indices=sv.indices.tolist(), values=sv.values.tolist())

    # ── Indexing ─────────────────────────────────────────────────────────────

    def add_chunks(self, chunks: list[dict], batch_size: int = 64):
        """Upsert chunks with dense + sparse vectors. Idempotent via UUID."""
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            texts = [c["text"] for c in batch]

            dense_vecs = self._embed_dense(texts)
            sparse_vecs = self._embed_sparse(texts)

            points = []
            for chunk, dv, sv in zip(batch, dense_vecs, sparse_vecs, strict=True):
                payload = {**chunk, EMBEDDER_KEY: self._embedder_name}
                points.append(
                    PointStruct(
                        id=_chunk_uuid(chunk["text"]),
                        vector={"dense": dv, "sparse": sv},
                        payload=payload,
                    )
                )

            self._client.upsert(collection_name=COLLECTION, points=points)
            logger.debug(f"Upserted {len(points)} chunks to Qdrant")

    # ── Retrieval ────────────────────────────────────────────────────────────

    def search(self, query: str, n_results: int = 20, where: dict | None = None) -> list[dict]:
        """
        Hybrid search: dense prefetch + sparse prefetch → native RRF fusion.
        Replaces the manual BM25 + RRF in retrieval_agent.py.
        """
        dense_q = self._embed_dense([query], input_type="query")[0]
        sparse_q = self._query_sparse(query)
        qdrant_filter = _build_filter(where) if where else None

        prefetch_limit = n_results * 3

        results = self._client.query_points(
            collection_name=COLLECTION,
            prefetch=[
                Prefetch(
                    query=dense_q,
                    using="dense",
                    limit=prefetch_limit,
                    filter=qdrant_filter,
                ),
                Prefetch(
                    query=sparse_q,
                    using="sparse",
                    limit=prefetch_limit,
                    filter=qdrant_filter,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=n_results,
            with_payload=True,
        )

        chunks = [_point_to_chunk(r) for r in results.points]
        logger.debug(f"Qdrant hybrid search → {len(chunks)} results")
        return chunks

    def count(self, where: dict | None = None) -> int:
        qdrant_filter = _build_filter(where) if where else None
        result = self._client.count(collection_name=COLLECTION, count_filter=qdrant_filter)
        return result.count
