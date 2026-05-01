from rank_bm25 import BM25Okapi
from loguru import logger
from vectorstore.chroma_store import ChromaStore
from agents.state import AgentState

_store = None


def _get_store() -> ChromaStore:
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store


def _reciprocal_rank_fusion(rankings: list[list[dict]], k: int = 60) -> list[dict]:
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking):
            doc_id = doc.get("chunk_id") or doc["text"][:80]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
            docs[doc_id] = doc
    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [docs[i] for i in sorted_ids]


def retrieval_agent(state: AgentState) -> dict:
    query = state["query"]
    store = _get_store()

    # 1. Dense retrieval
    dense = store.search(query, n_results=20)

    # 2. BM25 sparse retrieval over dense candidates (lightweight)
    corpus = [c["text"] for c in dense]
    if corpus:
        tokenized = [doc.split() for doc in corpus]
        bm25 = BM25Okapi(tokenized)
        bm25_scores = bm25.get_scores(query.split())
        sparse = [dense[i] for i in sorted(range(len(dense)),
                                           key=lambda x: bm25_scores[x], reverse=True)]
    else:
        sparse = []

    # 3. Reciprocal Rank Fusion
    fused = _reciprocal_rank_fusion([dense, sparse])[:8]

    logger.info(f"Retrieval → {len(fused)} chunks (dense={len(dense)}, sparse={len(sparse)})")
    return {"retrieved_chunks": fused}
