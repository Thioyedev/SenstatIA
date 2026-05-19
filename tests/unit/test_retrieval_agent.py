from unittest.mock import MagicMock, patch

import pytest

from agents.retrieval_agent import _detect_source_filter, retrieval_agent


# ── Pure logic: _detect_source_filter ────────────────────────────────────────

class TestDetectSourceFilter:
    def test_poverty_query_maps_to_ehcvm(self):
        f = _detect_source_filter("taux de pauvreté au Sénégal")
        assert f is not None
        sources = f.get("source_id") or f.get("source_id", {}).get("$in", [])
        # ehcvm_2021 must be in the resolved filter
        if isinstance(sources, str):
            assert "ehcvm" in sources
        else:
            assert any("ehcvm" in s for s in sources)

    def test_population_query_maps_to_rgph5(self):
        f = _detect_source_filter("population totale du Sénégal recensement")
        assert f is not None

    def test_multi_domain_returns_none(self):
        # poverty + employment → spans two domains → no filter
        f = _detect_source_filter("taux de pauvreté et taux de chômage")
        assert f is None

    def test_unrecognised_query_returns_none(self):
        f = _detect_source_filter("recette de thiéboudienne")
        assert f is None


# ── retrieval_agent with mocked store and reranker ────────────────────────────

RAW_CHUNKS = [
    {"text": f"chunk {i}", "source_id": "ehcvm_2021", "chunk_id": f"c{i}"}
    for i in range(5)
]


class TestRetrievalAgent:
    def test_returns_retrieved_chunks(self, base_state):
        mock_store = MagicMock()
        mock_store.search.return_value = RAW_CHUNKS

        with (
            patch("agents.retrieval_agent._get_store", return_value=mock_store),
            patch("agents.retrieval_agent._rerank", side_effect=lambda q, docs: docs),
        ):
            result = retrieval_agent(base_state)

        assert "retrieved_chunks" in result
        assert len(result["retrieved_chunks"]) == len(RAW_CHUNKS)

    def test_fallback_to_full_corpus_when_filtered_empty(self, base_state):
        mock_store = MagicMock()
        # First call (filtered) returns empty; second call (unfiltered) returns chunks
        mock_store.search.side_effect = [[], RAW_CHUNKS]

        with (
            patch("agents.retrieval_agent._get_store", return_value=mock_store),
            patch("agents.retrieval_agent._rerank", side_effect=lambda q, docs: docs),
        ):
            result = retrieval_agent({
                **base_state,
                "query": "taux de pauvreté au Sénégal",  # triggers a filter
            })

        assert len(result["retrieved_chunks"]) > 0
        assert mock_store.search.call_count == 2  # filtered then full-corpus

    def test_empty_store_returns_empty_chunks(self, base_state):
        mock_store = MagicMock()
        mock_store.search.return_value = []

        with (
            patch("agents.retrieval_agent._get_store", return_value=mock_store),
            patch("agents.retrieval_agent._rerank", side_effect=lambda q, docs: docs),
        ):
            result = retrieval_agent(base_state)

        assert result["retrieved_chunks"] == []
