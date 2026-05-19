import json
from unittest.mock import MagicMock, patch

import pytest

from agents.compare_agent import compare_agent

VALID_COMPARE_JSON = json.dumps({
    "entities": [
        {
            "name": "Milieu urbain",
            "values": [{"metric": "taux de pauvreté", "value": 20.5, "unit": "%", "year": 2021}],
        },
        {
            "name": "Milieu rural",
            "values": [{"metric": "taux de pauvreté", "value": 52.0, "unit": "%", "year": 2021}],
        },
    ],
    "gaps": [
        {"metric": "taux de pauvreté", "absolute": 31.5, "relative": 1.54, "winner": "Milieu rural", "unit": "%"}
    ],
    "insight": "Le milieu rural affiche un taux 2,5× supérieur au milieu urbain.",
})

EMPTY_COMPARE_JSON = json.dumps({"entities": [], "gaps": [], "insight": None})


class TestCompareAgent:
    def _mock_response(self, text: str) -> MagicMock:
        resp = MagicMock()
        resp.content = [MagicMock(text=text)]
        return resp

    def test_extracts_entities_and_gaps(self, base_state):
        state = {**base_state, "intent": "compare"}
        with patch("agents.compare_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(VALID_COMPARE_JSON)
            result = compare_agent(state)

        assert result["compare_output"] is not None
        assert len(result["compare_output"]["entities"]) == 2
        assert len(result["compare_output"]["gaps"]) == 1
        assert result["compare_output"]["gaps"][0]["winner"] == "Milieu rural"

    def test_returns_none_when_no_chunks(self, base_state):
        result = compare_agent({**base_state, "retrieved_chunks": []})
        assert result["compare_output"] is None

    def test_returns_none_when_entities_empty(self, base_state):
        with patch("agents.compare_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(EMPTY_COMPARE_JSON)
            result = compare_agent(base_state)
        assert result["compare_output"] is None

    def test_handles_api_error_gracefully(self, base_state):
        with patch("agents.compare_agent._client") as mock_client:
            mock_client.messages.create.side_effect = Exception("Network error")
            result = compare_agent(base_state)
        assert result["compare_output"] is None

    def test_strips_markdown_fences(self, base_state):
        fenced = f"```json\n{VALID_COMPARE_JSON}\n```"
        with patch("agents.compare_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(fenced)
            result = compare_agent(base_state)
        assert result["compare_output"] is not None

    def test_uses_haiku_model(self, base_state):
        with patch("agents.compare_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(VALID_COMPARE_JSON)
            compare_agent(base_state)
            call_kwargs = mock_client.messages.create.call_args
        assert "haiku" in call_kwargs.kwargs["model"]
