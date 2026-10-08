from unittest.mock import MagicMock, patch

from agents.retrieval_agent import _detect_source_filter, retrieval_agent

RAW_CHUNKS = [
    {"text": f"chunk {i}", "source_id": "ehcvm_2021", "chunk_id": f"c{i}"} for i in range(5)
]


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
        mock_store.search.side_effect = [[], RAW_CHUNKS]
        with (
            patch("agents.retrieval_agent._get_store", return_value=mock_store),
            patch("agents.retrieval_agent._rerank", side_effect=lambda q, docs: docs),
        ):
            result = retrieval_agent({**base_state, "query": "taux de pauvreté"})
        assert len(result["retrieved_chunks"]) > 0
        assert mock_store.search.call_count == 2

    def test_empty_store_returns_empty_chunks(self, base_state):
        mock_store = MagicMock()
        mock_store.search.return_value = []
        with (
            patch("agents.retrieval_agent._get_store", return_value=mock_store),
            patch("agents.retrieval_agent._rerank", side_effect=lambda q, docs: docs),
        ):
            result = retrieval_agent(base_state)
        assert result["retrieved_chunks"] == []
