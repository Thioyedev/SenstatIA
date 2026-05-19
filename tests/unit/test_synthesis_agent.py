from unittest.mock import MagicMock, patch

import pytest

from agents.synthesis_agent import _extract_citations, _format_chunks, synthesis_agent


# ── Pure helpers ──────────────────────────────────────────────────────────────

class TestFormatChunks:
    def test_includes_index_institution_report_page(self, sample_chunks):
        result = _format_chunks(sample_chunks)
        assert "[1]" in result
        assert "ANSD" in result
        assert "EHCVM 2021-2022" in result
        assert "p.32" in result

    def test_includes_chunk_text(self, sample_chunks):
        result = _format_chunks(sample_chunks)
        assert "37,5%" in result

    def test_empty_chunks_returns_empty_string(self):
        assert _format_chunks([]) == ""

    def test_multiple_chunks_are_separated(self, sample_chunks):
        result = _format_chunks(sample_chunks)
        assert "[1]" in result and "[2]" in result


class TestExtractCitations:
    def test_deduplicates_by_source_id_and_page(self, sample_chunks):
        # Our two sample chunks differ by page_number (32 vs 33) → 2 citations
        citations = _extract_citations(sample_chunks)
        assert len(citations) == 2

    def test_deduplicates_identical_source_page(self, sample_chunks):
        doubled = sample_chunks + [sample_chunks[0]]  # exact duplicate
        citations = _extract_citations(doubled)
        assert len(citations) == 2  # still 2, not 3

    def test_citation_fields_are_present(self, sample_chunks):
        citations = _extract_citations(sample_chunks)
        for c in citations:
            assert "institution" in c
            assert "report_name" in c
            assert "year" in c
            assert "page" in c


# ── synthesis_agent with mocked Anthropic client ──────────────────────────────

class TestSynthesisAgent:
    def _mock_response(self, text: str) -> MagicMock:
        resp = MagicMock()
        resp.content = [MagicMock(text=text)]
        return resp

    def test_returns_synthesis_and_citations(self, base_state):
        with patch("agents.synthesis_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(
                "Le taux de pauvreté est de 37,5%.\nSOURCES_USED: 1"
            )
            result = synthesis_agent(base_state)

        assert result["synthesis"] == "Le taux de pauvreté est de 37,5%."
        assert len(result["citations"]) == 1

    def test_strips_sources_used_tag_from_synthesis(self, base_state):
        with patch("agents.synthesis_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(
                "Réponse.\nSOURCES_USED: 1"
            )
            result = synthesis_agent(base_state)
        assert "SOURCES_USED" not in result["synthesis"]

    def test_no_citations_when_sources_used_is_none(self, base_state):
        with patch("agents.synthesis_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(
                "Je n'ai pas cette information.\nSOURCES_USED: none"
            )
            result = synthesis_agent(base_state)
        assert result["citations"] == []

    def test_filters_to_only_used_chunks(self, base_state):
        """SOURCES_USED: 1 → only first chunk cited, not the second."""
        with patch("agents.synthesis_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(
                "Réponse avec chunk 1 seulement.\nSOURCES_USED: 1"
            )
            result = synthesis_agent(base_state)
        assert len(result["citations"]) == 1

    def test_fallback_cites_all_when_tag_missing(self, base_state):
        with patch("agents.synthesis_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(
                "Réponse sans tag sources."
            )
            result = synthesis_agent(base_state)
        # Falls back to citing all retrieved chunks
        assert len(result["citations"]) == len(base_state["retrieved_chunks"])

    def test_uses_sonnet_model(self, base_state):
        with patch("agents.synthesis_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(
                "Réponse.\nSOURCES_USED: 1"
            )
            synthesis_agent(base_state)
            call_kwargs = mock_client.messages.create.call_args
        assert "sonnet" in call_kwargs.kwargs["model"]

    def test_temperature_is_zero(self, base_state):
        with patch("agents.synthesis_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(
                "Réponse.\nSOURCES_USED: 1"
            )
            synthesis_agent(base_state)
            call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs.get("temperature") == 0

    def test_conversation_history_is_injected(self, base_state):
        history = [{"role": "user", "content": "question précédente"}]
        state = {**base_state, "conversation_history": history}

        with patch("agents.synthesis_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(
                "Réponse.\nSOURCES_USED: 1"
            )
            synthesis_agent(state)
            call_kwargs = mock_client.messages.create.call_args

        messages = call_kwargs.kwargs["messages"]
        # History should be injected before the current prompt
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "question précédente"
