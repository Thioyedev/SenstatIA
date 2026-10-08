"""End-to-end integration tests — require a live ANTHROPIC_API_KEY and indexed ChromaDB.

Run with:
    pytest tests/integration/ -v -m integration

Skipped automatically in CI (no API key).
"""

import os

import pytest


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ANTHROPIC_API_KEY", "").startswith("sk-ant-api03-test"),
    reason="Skipped: dummy API key — set a real ANTHROPIC_API_KEY to run integration tests",
)
class TestQueryEndToEnd:
    @pytest.fixture(scope="class")
    def graph(self):
        from agents.graph import get_graph

        return get_graph()

    @pytest.fixture
    def empty_state(self):
        from agents.state import AgentState

        return AgentState(
            query="",
            intent="",
            retrieved_chunks=[],
            trend_output=None,
            compare_output=None,
            compute_output=None,
            viz_output=None,
            synthesis="",
            citations=[],
            messages=[],
            conversation_history=[],
        )

    def test_lookup_returns_answer_with_citations(self, graph, empty_state):
        result = graph.invoke({**empty_state, "query": "Quel est le taux de pauvreté en 2021 ?"})
        assert result["synthesis"]
        assert isinstance(result["citations"], list)

    def test_out_of_corpus_query_is_refused(self, graph, empty_state):
        result = graph.invoke({**empty_state, "query": "Quel est le taux de criminalité ?"})
        synthesis_lower = result["synthesis"].lower()
        assert any(w in synthesis_lower for w in ("pas", "absent", "disponible", "don't", "not"))

    def test_trend_query_produces_trend_output(self, graph, empty_state):
        result = graph.invoke({**empty_state, "query": "Évolution du taux de pauvreté depuis 2018"})
        assert result["intent"] in ("trend", "viz", "lookup")
        assert result["synthesis"]
