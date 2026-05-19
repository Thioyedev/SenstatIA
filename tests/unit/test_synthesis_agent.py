from unittest.mock import MagicMock, patch

from agents.synthesis_agent import _extract_citations, _format_chunks, synthesis_agent


class TestFormatChunks:
    def test_includes_index_institution_report_page(self, sample_chunks):
        result = _format_chunks(sample_chunks)
        assert "[1]" in result and "ANSD" in result and "p.32" in result

    def test_includes_chunk_text(self, sample_chunks):
        assert "37,5%" in _format_chunks(sample_chunks)

    def test_empty_chunks_returns_empty_string(self):
        assert _format_chunks([]) == ""


class TestExtractCitations:
    def test_two_different_pages_give_two_citations(self, sample_chunks):
        assert len(_extract_citations(sample_chunks)) == 2

    def test_deduplicates_exact_duplicates(self, sample_chunks):
        assert len(_extract_citations(sample_chunks + [sample_chunks[0]])) == 2

    def test_citation_fields_are_present(self, sample_chunks):
        for c in _extract_citations(sample_chunks):
            assert "institution" in c and "report_name" in c and "year" in c


class TestSynthesisAgent:
    def _mock(self, text):
        resp = MagicMock()
        resp.content = [MagicMock(text=text)]
        return resp

    def test_returns_synthesis_and_citations(self, base_state):
        with patch("agents.synthesis_agent._client") as c:
            c.messages.create.return_value = self._mock("Le taux est 37,5%.\nSOURCES_USED: 1")
            result = synthesis_agent(base_state)
        assert result["synthesis"] == "Le taux est 37,5%."
        assert len(result["citations"]) == 1

    def test_strips_sources_used_tag(self, base_state):
        with patch("agents.synthesis_agent._client") as c:
            c.messages.create.return_value = self._mock("Réponse.\nSOURCES_USED: 1")
            result = synthesis_agent(base_state)
        assert "SOURCES_USED" not in result["synthesis"]

    def test_no_citations_when_sources_none(self, base_state):
        with patch("agents.synthesis_agent._client") as c:
            c.messages.create.return_value = self._mock("Info absente.\nSOURCES_USED: none")
            result = synthesis_agent(base_state)
        assert result["citations"] == []

    def test_filters_to_used_chunks_only(self, base_state):
        with patch("agents.synthesis_agent._client") as c:
            c.messages.create.return_value = self._mock("Chunk 1 seulement.\nSOURCES_USED: 1")
            result = synthesis_agent(base_state)
        assert len(result["citations"]) == 1

    def test_fallback_cites_all_when_tag_missing(self, base_state):
        with patch("agents.synthesis_agent._client") as c:
            c.messages.create.return_value = self._mock("Sans tag.")
            result = synthesis_agent(base_state)
        assert len(result["citations"]) == len(base_state["retrieved_chunks"])

    def test_uses_sonnet_model(self, base_state):
        with patch("agents.synthesis_agent._client") as c:
            c.messages.create.return_value = self._mock("Rép.\nSOURCES_USED: 1")
            synthesis_agent(base_state)
        assert "sonnet" in c.messages.create.call_args.kwargs["model"]

    def test_temperature_is_zero(self, base_state):
        with patch("agents.synthesis_agent._client") as c:
            c.messages.create.return_value = self._mock("Rép.\nSOURCES_USED: 1")
            synthesis_agent(base_state)
        assert c.messages.create.call_args.kwargs.get("temperature") == 0

    def test_history_is_injected(self, base_state):
        history = [{"role": "user", "content": "question précédente"}]
        with patch("agents.synthesis_agent._client") as c:
            c.messages.create.return_value = self._mock("Rép.\nSOURCES_USED: 1")
            synthesis_agent({**base_state, "conversation_history": history})
        messages = c.messages.create.call_args.kwargs["messages"]
        assert messages[0]["content"] == "question précédente"
