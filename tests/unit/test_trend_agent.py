import json
from unittest.mock import MagicMock, patch

import pytest

from agents.trend_agent import trend_agent

VALID_TREND_JSON = json.dumps({
    "series": [
        {"year": 2018, "value": 38.0, "unit": "%", "label": "Taux de pauvreté"},
        {"year": 2021, "value": 37.5, "unit": "%", "label": "Taux de pauvreté"},
    ],
    "cagr": -0.004,
    "trend": "baisse",
    "insight": "Le taux de pauvreté a légèrement baissé de 2018 à 2021.",
})

EMPTY_TREND_JSON = json.dumps({"series": [], "cagr": None, "trend": None, "insight": None})


class TestTrendAgent:
    def _mock_response(self, text: str) -> MagicMock:
        resp = MagicMock()
        resp.content = [MagicMock(text=text)]
        return resp

    def test_extracts_series_and_cagr(self, base_state):
        with patch("agents.trend_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(VALID_TREND_JSON)
            result = trend_agent(base_state)

        assert result["trend_output"] is not None
        assert len(result["trend_output"]["series"]) == 2
        assert result["trend_output"]["trend"] == "baisse"
        assert result["trend_output"]["cagr"] == pytest.approx(-0.004)

    def test_returns_none_when_no_chunks(self, base_state):
        result = trend_agent({**base_state, "retrieved_chunks": []})
        assert result["trend_output"] is None

    def test_returns_none_when_series_is_empty(self, base_state):
        with patch("agents.trend_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(EMPTY_TREND_JSON)
            result = trend_agent(base_state)
        assert result["trend_output"] is None

    def test_handles_api_error_gracefully(self, base_state):
        with patch("agents.trend_agent._client") as mock_client:
            mock_client.messages.create.side_effect = Exception("API timeout")
            result = trend_agent(base_state)
        assert result["trend_output"] is None

    def test_handles_invalid_json_gracefully(self, base_state):
        with patch("agents.trend_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response("not json")
            result = trend_agent(base_state)
        assert result["trend_output"] is None

    def test_strips_markdown_fences(self, base_state):
        fenced = f"```json\n{VALID_TREND_JSON}\n```"
        with patch("agents.trend_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(fenced)
            result = trend_agent(base_state)
        assert result["trend_output"] is not None

    def test_uses_haiku_model(self, base_state):
        with patch("agents.trend_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(VALID_TREND_JSON)
            trend_agent(base_state)
            call_kwargs = mock_client.messages.create.call_args
        assert "haiku" in call_kwargs.kwargs["model"]
