from unittest.mock import MagicMock, patch

from agents.retrieval_agent import _bm25_index, _detect_source_filter, retrieval_agent

RAW_CHUNKS = [
    {"text": f"chunk {i}", "source_id": "ehcvm_2021", "chunk_id": f"c{i}"} for i in range(5)
]


def _store(dense, corpus=()):
    """Mock Chroma store: `dense` is what search() returns, `corpus` what BM25 indexes."""
    store = MagicMock()
    if isinstance(dense, list):
        store.search.return_value = dense
    else:
        store.search.side_effect = dense
    corpus = list(corpus)
    store.collection.count.return_value = len(corpus)
    store.collection.get.return_value = {
        "documents": [c["text"] for c in corpus],
        "metadatas": [{k: v for k, v in c.items() if k != "text"} for c in corpus],
    }
    return store


class TestDetectSourceFilter:
    def test_poverty_query_maps_to_ehcvm(self):
        f = _detect_source_filter("taux de pauvreté au Sénégal")
        assert f is not None

    def test_population_query_maps_to_rgph5(self):
        f = _detect_source_filter("population totale recensement")
        assert f is not None

    def test_multi_domain_returns_none(self):
        f = _detect_source_filter("taux de pauvreté et taux de chômage")
        assert f is None

    def test_unrecognised_query_returns_none(self):
        f = _detect_source_filter("recette de thiéboudienne")
        assert f is None

    def test_fiscal_revenue_maps_to_budget_sources(self):
        budget = {"source_id": {"$in": ["dpee_ref", "dpee_sef", "dgb_budget"]}}
        assert _detect_source_filter("recettes budgétaires 2023") == budget
        assert _detect_source_filter("recettes de l'État en 2022") == budget

    def test_recipe_plural_returns_none(self):
        assert _detect_source_filter("recettes de cuisine sénégalaise") is None


class TestRetrievalAgent:
    def test_returns_retrieved_chunks(self, base_state):
        mock_store = _store(RAW_CHUNKS)
        with (
            patch("agents.retrieval_agent._get_store", return_value=mock_store),
            patch("agents.retrieval_agent._rerank", side_effect=lambda q, docs: docs),
        ):
            result = retrieval_agent(base_state)
        assert "retrieved_chunks" in result
        assert len(result["retrieved_chunks"]) == len(RAW_CHUNKS)

    def test_fallback_to_full_corpus_when_filtered_empty(self, base_state):
        mock_store = _store(iter([[], RAW_CHUNKS]))
        with (
            patch("agents.retrieval_agent._get_store", return_value=mock_store),
            patch("agents.retrieval_agent._rerank", side_effect=lambda q, docs: docs),
        ):
            result = retrieval_agent({**base_state, "query": "taux de pauvreté"})
        assert len(result["retrieved_chunks"]) > 0
        assert mock_store.search.call_count == 2

    def test_empty_store_returns_empty_chunks(self, base_state):
        mock_store = _store([])
        with (
            patch("agents.retrieval_agent._get_store", return_value=mock_store),
            patch("agents.retrieval_agent._rerank", side_effect=lambda q, docs: docs),
        ):
            result = retrieval_agent(base_state)
        assert result["retrieved_chunks"] == []


class TestBM25:
    def _run(self, store, query):
        with (
            patch("agents.retrieval_agent._get_store", return_value=store),
            patch("agents.retrieval_agent._rerank", side_effect=lambda q, docs: docs),
        ):
            return retrieval_agent({"query": query})["retrieved_chunks"]

    def test_surfaces_exact_term_the_dense_search_missed(self):
        # Regression: BM25 used to reorder the dense hits only, so a chunk that
        # matches on an exact term but not semantically could never come back.
        dense = [{"text": "Le taux de chômage des jeunes", "source_id": "ansd_enes"}]
        exact = {"text": "Classification NAEMA rév. 1 des activités", "source_id": "ansd_enes"}
        # Okapi IDF is 0 for a term in half the documents: pad to a realistic ratio.
        filler = [{"text": f"population région {i}", "source_id": "rgph5_2023"} for i in range(8)]
        store = _store(dense, corpus=[*dense, exact, *filler])

        texts = [c["text"] for c in self._run(store, "nomenclature NAEMA")]

        assert exact["text"] in texts

    def test_respects_the_source_filter(self):
        # "taux de pauvreté" maps to the EHCVM/ESPS sources; with 8 dense hits the
        # filter holds, and BM25 must not bring a chunk from another source.
        dense = [{"text": f"pauvreté EHCVM {i}", "source_id": "ehcvm_2021"} for i in range(8)]
        other = {"text": "taux de pauvreté pauvreté pauvreté", "source_id": "ses_2022_2023"}
        store = _store(dense, corpus=[*dense, other])

        chunks = self._run(store, "taux de pauvreté")

        assert all(c["source_id"] == "ehcvm_2021" for c in chunks)

    def test_index_is_rebuilt_only_when_the_corpus_changes(self):
        store = _store([], corpus=[{"text": "a b", "source_id": "x"}])
        _bm25_index(store)
        _bm25_index(store)
        assert store.collection.get.call_count == 1

        store.collection.count.return_value = 2
        store.collection.get.return_value = {
            "documents": ["a b", "c d"],
            "metadatas": [{"source_id": "x"}, {"source_id": "x"}],
        }
        _bm25_index(store)
        assert store.collection.get.call_count == 2
