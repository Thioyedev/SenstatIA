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
    "insight": "Légère baisse.",
})
EMPTY_TREND_JSON = json.dumps({"series": [], "cagr": None, "trend": None, "insight": None})


class TestTrendAgent:
    def _mock(self, text):
        resp = MagicMock()
        resp.content = [MagicMock(text=text)]
        return resp

    def test_extracts_series_and_cagr(self, base_state):
        with patch("agents.trend_agent._client") as c:
            c.messages.create.return_value = self._mock(VALID_TREND_JSON)
            result = trend_agent(base_state)
        assert result["trend_output"] is not None
        assert len(result["trend_output"]["series"]) == 2

    def test_returns_none_when_no_chunks(self, base_state):
        assert trend_agent({**base_state, "retrieved_chunks": []})["trend_output"] is None

    def test_returns_none_when_series_empty(self, base_state):
        with patch("agents.trend_agent._client") as c:
            c.messages.create.return_value = self._mock(EMPTY_TREND_JSON)
            result = trend_agent(base_state)
        assert result["trend_output"] is None

    def test_handles_api_error(self, base_state):
        with patch("agents.trend_agent._client") as c:
            c.messages.create.side_effect = Exception("timeout")
            result = trend_agent(base_state)
        assert result["trend_output"] is None

    def test_strips_markdown_fences(self, base_state):
        fenced = f"```json\n{VALID_TREND_JSON}\n```"
        with patch("agents.trend_agent._client") as c:
            c.messages.create.return_value = self._mock(fenced)
            result = trend_agent(base_state)
        assert result["trend_output"] is not None

    def test_uses_haiku_model(self, base_state):
        with patch("agents.trend_agent._client") as c:
            c.messages.create.return_value = self._mock(VALID_TREND_JSON)
            trend_agent(base_state)
        assert "haiku" in c.messages.create.call_args.kwargs["model"]
