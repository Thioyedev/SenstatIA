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
    """Full pipeline: query → router → retrieval → specialist → synthesis."""

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
        state = {**empty_state, "query": "Quel est le taux de pauvreté au Sénégal en 2021 ?"}
        result = graph.invoke(state)

        assert result["synthesis"]
        assert result["intent"] in ("lookup", "trend", "compare")
        assert isinstance(result["citations"], list)

    def test_out_of_corpus_query_is_refused(self, graph, empty_state):
        state = {**empty_state, "query": "Quel est le taux de criminalité au Sénégal ?"}
        result = graph.invoke(state)

        # The system should say it doesn't have this data
        synthesis_lower = result["synthesis"].lower()
        has_refusal = any(word in synthesis_lower for word in (
            "pas", "absent", "disponible", "corpus", "don't", "not available"
        ))
        assert has_refusal, f"Expected refusal but got: {result['synthesis'][:200]}"

    def test_trend_query_produces_trend_output(self, graph, empty_state):
        state = {**empty_state, "query": "Évolution du taux de pauvreté au Sénégal depuis 2018"}
        result = graph.invoke(state)

        assert result["intent"] in ("trend", "viz", "lookup")
        assert result["synthesis"]

    def test_compare_query_produces_compare_output(self, graph, empty_state):
        state = {**empty_state, "query": "Comparez le taux de pauvreté entre milieu urbain et rural"}
        result = graph.invoke(state)

        assert result["intent"] in ("compare", "compare_viz")
        assert result["synthesis"]
