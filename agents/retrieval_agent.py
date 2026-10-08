import os
import re

from loguru import logger
from sentence_transformers import CrossEncoder

from agents.state import AgentState
from vectorstore.chroma_store import ChromaStore

# ── Feature toggles ───────────────────────────────────────────────────────────
USE_QDRANT = os.getenv("USE_QDRANT", "false").lower() == "true"
USE_COHERE_RERANK = os.getenv("USE_COHERE_RERANK", "false").lower() == "true"
USE_COLPALI = os.getenv("USE_COLPALI", "false").lower() == "true"
COLPALI_TOP_K = int(os.getenv("COLPALI_TOP_K", "3"))

# ── Source routing ─────────────────────────────────────────────────────────────
# Maps keyword patterns → source_ids. First unambiguous match wins.
# Falls back to None (full corpus) when query spans multiple domains.
_SOURCE_RULES: list[tuple[re.Pattern, list[str]]] = [
    # Poverty & living conditions
    (
        re.compile(
            r"\b(?:pauv\w*|ehcvm|esps|seuil de pauv|inégali\w*|consommation|indigent|"
            r"poor|poverty|gini|profondeur|sévérité|conditions de vie|ménage)",
            re.IGNORECASE,
        ),
        ["ehcvm_2021", "ansd_esps_2021"],
    ),
    # Population & demographics
    (
        re.compile(
            r"\b(?:population|rgph|démograph\w*|naissance|mortalité|"
            r"fécondité|densité|habitant\w*|recensement|ménage\w*)",
            re.IGNORECASE,
        ),
        ["rgph5_2023"],
    ),
    # Employment & labour market
    (
        re.compile(
            r"\b(?:emploi|chômage|chôm\w*|actif|inactif|travail|sous-emploi|"
            r"enes|ilostat|informel|activ\w* économ|employment|unemployment|labour|labor)",
            re.IGNORECASE,
        ),
        ["rgph5_economie", "ses_2022_2023", "ansd_enes", "ilo_ilostat_sen"],
    ),
    # Quarterly GDP & conjuncture
    (
        re.compile(
            r"\b(?:neer|pib trimestriel|croissance trimestrielle|conjoncture trimestrielle|"
            r"t[1-4][- ]20\d\d|trimestre)",
            re.IGNORECASE,
        ),
        ["ansd_neer", "dpee_sef"],
    ),
    # Macroeconomy & GDP (annual)
    (
        re.compile(
            r"\b(?:pib|croissance économique|secteur\w*|agriculture|industri\w*|"
            r"valeur ajoutée|économi\w*|gdp|growth|macro)",
            re.IGNORECASE,
        ),
        ["rgph5_economie", "ses_2022_2023", "dpee_sef", "imf_weo_sen", "ansd_bdef_2024"],
    ),
    # Public finances & budget
    (
        re.compile(
            r"\b(?:budget|fiscal|dépense\w*|déficit|loi de finances|"
            r"exécution budgétaire|ref |sef |dgb|finances publiques|"
            # "recette" alone is also a cooking recipe: require a fiscal qualifier
            r"recettes?\s+(?:non\s+)?(?:fiscales?|budgétaires?|publiques?|douanières?|"
            r"totales|courantes|de\s+l['’]\s*[ée]tat))",
            re.IGNORECASE,
        ),
        ["dpee_ref", "dpee_sef", "dgb_budget"],
    ),
    # Public debt
    (
        re.compile(
            r"\b(?:dette publique|dette extérieure|dette intérieure|service de la dette|"
            r"dgtcp|cour des comptes|soutenabilité|dsa|debt)",
            re.IGNORECASE,
        ),
        ["dgtcp_dette", "courdescomptes_audit_2024", "imf_country_reports", "imf_weo_sen"],
    ),
    # Agriculture & food
    (
        re.compile(
            r"\b(?:agricult\w*|récolte|culture|céréale|mil|arachide|riz|bétail|"
            r"élevage|faostat|dapsa|eaa|production agricole|alimentaire)",
            re.IGNORECASE,
        ),
        ["dapsa_eaa_2022", "fao_faostat_sen", "ses_2022_2023"],
    ),
    # Health & demography
    (
        re.compile(
            r"\b(?:santé|mortalité infantile|fertilité|nutrition|malnutrition|"
            r"eds|vaccin|paludisme|maternelle|vih|aids)",
            re.IGNORECASE,
        ),
        ["eds_2023", "ses_2022_2023"],
    ),
    # Education
    (
        re.compile(
            r"\b(?:éducation|scolarisation|alphabétis\w*|école|primaire scolaire|"
            r"secondaire scolaire|université|enseignement)",
            re.IGNORECASE,
        ),
        ["ses_2022_2023", "undp_hdi_mpi"],
    ),
    # Human development & multidimensional poverty
    (
        re.compile(
            r"\b(?:idh|ipm|développement humain|pauvreté multidimensionnelle|"
            r"hdi|mpi|indice de développement)",
            re.IGNORECASE,
        ),
        ["undp_hdi_mpi"],
    ),
    # Telecom & digital
    (
        re.compile(
            r"\b(?:télécom|mobile|internet|numérique|artp|pénétration|"
            r"opérateur|broadband|haut débit)",
            re.IGNORECASE,
        ),
        ["artp_telecom"],
    ),
    # Monetary & banking (BCEAO)
    (
        re.compile(
            r"\b(?:monnaie|inflation|franc cfa|bceao|uemoa|taux directeur|"
            r"balance des paiements|réserves)",
            re.IGNORECASE,
        ),
        ["bceao_rapport_annuel", "imf_weo_sen"],
    ),
    # Education only via SES for explicit terms
    (re.compile(r"\b(?:électrif\w*|accès à l'électricité)", re.IGNORECASE), ["ses_2022_2023"]),
]

TOP_K = 8
CE_THRESHOLD = 0.0  # ms-marco logit score — chunks below this are off-topic


def _detect_source_filter(query: str) -> dict | None:
    """Return a where-filter if query maps unambiguously to one domain."""
    matched: list[list[str]] = []
    for pattern, source_ids in _SOURCE_RULES:
        if pattern.search(query):
            matched.append(source_ids)
            if len(matched) > 1:
                return None  # spans multiple domains — no filter
    if not matched:
        return None
    source_ids = matched[0]
    if len(source_ids) == 1:
        return {"source_id": source_ids[0]}
    return {"source_id": {"$in": source_ids}}


# ── Lazy singletons ───────────────────────────────────────────────────────────
_store = None
_colpali_indexer = None
_cross_encoder = None
_cohere_client = None


def _get_store():
    global _store
    if _store is None:
        if USE_QDRANT:
            from vectorstore.qdrant_store import QdrantStore

            _store = QdrantStore()
            logger.info("Retrieval backend: Qdrant (dense+sparse hybrid)")
        else:
            _store = ChromaStore()
            logger.info("Retrieval backend: ChromaDB")
    return _store


def _get_colpali():
    global _colpali_indexer
    if _colpali_indexer is None:
        from ingestion.colpali_indexer import ColPaliIndexer

        _colpali_indexer = ColPaliIndexer()
    return _colpali_indexer


def _rerank(query: str, docs: list[dict]) -> list[dict]:
    global _cross_encoder, _cohere_client
    if USE_COHERE_RERANK:
        if _cohere_client is None:
            import cohere

            _cohere_client = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))
        response = _cohere_client.rerank(
            model="rerank-v3.5",
            query=query,
            documents=[d["text"] for d in docs],
            top_n=TOP_K,
        )
        return [docs[r.index] for r in response.results]

    # CrossEncoder path — apply CE_THRESHOLD to drop off-topic chunks
    if _cross_encoder is None:
        _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    pairs = [(query, d["text"]) for d in docs]
    scores = _cross_encoder.predict(pairs)
    scored = sorted(zip(scores, docs, strict=True), key=lambda x: x[0], reverse=True)

    # Keep only chunks above CE_THRESHOLD; always keep at least 1
    above = [(s, d) for s, d in scored if s >= CE_THRESHOLD]
    reranked = [d for _, d in (above if above else scored[:1])][:TOP_K]

    dropped = len(scored) - len(above)
    if dropped:
        logger.debug(
            f"CE threshold dropped {dropped}/{len(scored)} off-topic chunks "
            f"(threshold={CE_THRESHOLD})"
        )
    return reranked


# ── BM25 over the whole corpus (Chroma path) ──────────────────────────────────
# Built lazily from every chunk in the collection and rebuilt when the chunk count
# changes. Scoring the corpus rather than the dense hits is the point: a chunk that
# only matches on an exact term (an acronym, a code, a figure) can still surface.
_bm25 = None  # (BM25Okapi, chunks, cache key)
_TOKEN_RE = re.compile(r"\w+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _bm25_index(store):
    global _bm25
    from rank_bm25 import BM25Okapi

    count = store.collection.count()
    # Keyed on the collection name, not id(collection): a GC'd collection object
    # can hand its id() to a new one and silently serve a stale index. count still
    # misses an edit that keeps the chunk total unchanged; the corpus is
    # append-mostly, so a re-ingest that changes content also changes count.
    key = (store.collection.name, count)
    if _bm25 is None or _bm25[2] != key:
        if count == 0:
            _bm25 = (None, [], key)
        else:
            data = store.collection.get(include=["documents", "metadatas"])
            chunks = [
                {"text": doc, **(meta or {})}
                for doc, meta in zip(data["documents"], data["metadatas"], strict=True)
            ]
            _bm25 = (BM25Okapi([_tokenize(c["text"]) for c in chunks]), chunks, key)
            logger.info(f"BM25 index built over {count} chunks")
    return _bm25[0], _bm25[1]


def _bm25_search(store, query: str, n_results: int, src_filter: dict | None) -> list[dict]:
    bm25, chunks = _bm25_index(store)
    if bm25 is None:
        return []
    allowed = None
    if src_filter:
        wanted = src_filter["source_id"]
        allowed = set(wanted["$in"]) if isinstance(wanted, dict) else {wanted}
    scores = bm25.get_scores(_tokenize(query))
    hits = [
        i
        for i in range(len(chunks))
        if scores[i] > 0 and (allowed is None or chunks[i].get("source_id") in allowed)
    ]
    hits.sort(key=lambda i: scores[i], reverse=True)
    return [chunks[i] for i in hits[:n_results]]


def _chunk_key(doc: dict):
    """Stable identity for fusion/dedup.

    (source_id, page_number, chunk_index) is unique across the corpus. No chunk
    carries a ``chunk_id`` field, so the previous ``doc.get("chunk_id") or
    doc["text"][:80]`` always fell back to an 80-char prefix — and distinct
    chunks that share boilerplate (table headers, cover text) collapsed into one,
    dropping a real BM25-only hit. Fall back to the full text, never a prefix,
    for docs that lack the metadata (e.g. ColPali page refs)."""
    sid, page, idx = doc.get("source_id"), doc.get("page_number"), doc.get("chunk_index")
    if sid is not None and page is not None and idx is not None:
        return (sid, page, idx)
    return doc["text"]


def _reciprocal_rank_fusion(rankings: list[list[dict]], k: int = 60) -> list[dict]:
    scores: dict = {}
    docs: dict = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking):
            doc_id = _chunk_key(doc)
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
            docs[doc_id] = doc
    return [docs[i] for i in sorted(scores, key=lambda x: scores[x], reverse=True)]


# ── ColPali retrieval ─────────────────────────────────────────────────────────


def _colpali_retrieval(query: str) -> list[dict]:
    """Query the ColPali visual index and return page-level chunks."""
    try:
        indexer = _get_colpali()
        return indexer.search(query, n_results=COLPALI_TOP_K)
    except Exception as e:
        logger.warning(f"ColPali retrieval failed (non-fatal): {e}")
        return []


# ── Main retrieval agent ──────────────────────────────────────────────────────


def retrieval_agent(state: AgentState) -> dict:
    query = state["query"]
    store = _get_store()
    src_filter = _detect_source_filter(query)

    # ── Text / hybrid retrieval ───────────────────────────────────────────────
    if USE_QDRANT:
        # Qdrant fuses dense+sparse natively — no BM25 sidecar needed
        text_candidates = store.search(query, n_results=20, where=src_filter)
        if len(text_candidates) < TOP_K and src_filter is not None:
            logger.debug(f"Source filter → {len(text_candidates)} results, retrying unfiltered")
            text_candidates = store.search(query, n_results=20)
        fused = text_candidates
    else:
        dense = store.search(query, n_results=20, where=src_filter)
        if len(dense) < TOP_K and src_filter is not None:
            logger.debug(f"Source filter → {len(dense)} results, falling back to full corpus")
            dense = store.search(query, n_results=20)
            src_filter = None
        sparse = _bm25_search(store, query, 20, src_filter)
        fused = _reciprocal_rank_fusion([dense, sparse])[:20]

    # ── ColPali visual retrieval (fan-out) ────────────────────────────────────
    if USE_COLPALI:
        colpali_chunks = _colpali_retrieval(query)
        if colpali_chunks:
            # Merge visual page refs into the candidate pool before reranking
            fused = _reciprocal_rank_fusion([fused, colpali_chunks])[:20]
            logger.debug(f"ColPali contributed {len(colpali_chunks)} visual chunks")

    # ── Reranking ─────────────────────────────────────────────────────────────
    reranked = _rerank(query, fused) if fused else []

    backend = "qdrant" if USE_QDRANT else "chroma"
    reranker = "cohere" if USE_COHERE_RERANK else "cross-encoder"
    colpali_tag = "+colpali" if USE_COLPALI else ""
    filter_label = list(src_filter.values())[0] if src_filter else "full"
    logger.info(
        f"Retrieval [{backend}{colpali_tag}+{reranker}] → {len(reranked)} chunks "
        f"(filter={filter_label}, candidates={len(fused)})"
    )
    return {"retrieved_chunks": reranked}
