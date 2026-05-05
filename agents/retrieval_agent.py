import re
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
from loguru import logger
from vectorstore.chroma_store import ChromaStore
from agents.state import AgentState

# ── Source routing ─────────────────────────────────────────────────────────────
# Maps keyword patterns to source_ids. Order matters: first match wins.
# Falls back to None (no filter) when the query spans multiple domains.
_SOURCE_RULES: list[tuple[re.Pattern, list[str]]] = [
    # Note: no trailing \b so French suffixed forms match (pauvreté, inégalité…)
    (re.compile(
        r"\b(?:pauv\w*|ehcvm|seuil de pauv|inégali\w*|consommation|indigent|"
        r"poor|poverty|gini|profondeur|sévérité)",
        re.IGNORECASE),
     ["ehcvm_2021"]),

    (re.compile(
        r"\b(?:population|rgph|démograph\w*|ménage|naissance|mortalité|"
        r"fécondité|densité|habitant\w*|recensement)",
        re.IGNORECASE),
     ["rgph5_preliminaire"]),

    (re.compile(
        r"\b(?:pib|croissance économique|secteur\w*|agriculture|industri\w*|"
        r"valeur ajoutée|économi\w*|gdp|growth)",
        re.IGNORECASE),
     ["rgph5_economie", "ses_2022_2023"]),

    (re.compile(
        r"\b(?:emploi|chômage|chôm\w*|actif|inactif|travail|sous-emploi|"
        r"employment|unemployment)",
        re.IGNORECASE),
     ["rgph5_economie", "ses_2022_2023"]),

    # Only route to SES for explicit education/electrification terms
    # "social" and "accès" are too generic — they appear across all sources
    (re.compile(
        r"\b(?:éducation|scolarisation|alphabétis\w*|école|primaire scolaire|"
        r"secondaire scolaire|électrif\w*)",
        re.IGNORECASE),
     ["ses_2022_2023"]),
]

TOP_K = 8  # reverted: top-k 5 hurt recall on multi-aspect questions


def _detect_source_filter(query: str) -> dict | None:
    """Return a ChromaDB where-filter if the query maps unambiguously to one domain."""
    matched: list[list[str]] = []
    for pattern, source_ids in _SOURCE_RULES:
        if pattern.search(query):
            matched.append(source_ids)
            if len(matched) > 1:
                # Query spans multiple domains — don't filter, use full corpus
                return None
    if not matched:
        return None
    source_ids = matched[0]
    if len(source_ids) == 1:
        return {"source_id": source_ids[0]}
    return {"source_id": {"$in": source_ids}}

_store = None
_cross_encoder = None


def _get_store() -> ChromaStore:
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store


def _get_cross_encoder() -> CrossEncoder:
    global _cross_encoder
    if _cross_encoder is None:
        _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _cross_encoder


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

    # 0. Source filter — restrict dense search to the relevant report(s)
    src_filter = _detect_source_filter(query)

    # 1. Dense retrieval (with optional source filter)
    dense = store.search(query, n_results=20, where=src_filter)
    # Fall back to unfiltered if filter returns too few results
    if len(dense) < TOP_K and src_filter is not None:
        logger.debug(f"Source filter returned only {len(dense)} chunks — falling back to full corpus")
        dense = store.search(query, n_results=20)
        src_filter = None

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
    fused = _reciprocal_rank_fusion([dense, sparse])[:20]

    # 4. CrossEncoder reranking — keep top TOP_K (reduced from 8 → 5 for precision)
    if fused:
        ce = _get_cross_encoder()
        pairs = [(query, doc["text"]) for doc in fused]
        ce_scores = ce.predict(pairs)
        reranked = [doc for _, doc in sorted(
            zip(ce_scores, fused), key=lambda x: x[0], reverse=True
        )][:TOP_K]
    else:
        reranked = []

    filter_label = list(src_filter.values())[0] if src_filter else "full"
    logger.info(f"Retrieval → {len(reranked)} chunks (filter={filter_label}, dense={len(dense)}, fused={len(fused)})")
    return {"retrieved_chunks": reranked}
