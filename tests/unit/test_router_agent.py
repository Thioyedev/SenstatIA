import json
from unittest.mock import MagicMock, patch

import pytest

from agents.router_agent import _resolve_intent, router_agent


class TestResolveIntent:
    def test_single_lookup(self):
        assert _resolve_intent(["lookup"]) == "lookup"

    def test_single_trend(self):
        assert _resolve_intent(["trend"]) == "trend"

    def test_single_compare(self):
        assert _resolve_intent(["compare"]) == "compare"

    def test_single_compute(self):
        assert _resolve_intent(["compute"]) == "compute"

    def test_trend_and_viz_collapses_to_viz(self):
        assert _resolve_intent(["trend", "viz"]) == "viz"

    def test_compare_and_viz_collapses_to_compare_viz(self):
        assert _resolve_intent(["compare", "viz"]) == "compare_viz"

    def test_trend_and_compare_collapses_to_mixed(self):
        assert _resolve_intent(["trend", "compare"]) == "mixed"

    def test_viz_alone_returns_viz(self):
        assert _resolve_intent(["viz"]) == "viz"

    def test_empty_defaults_to_lookup(self):
        assert _resolve_intent([]) == "lookup"


class TestRouterAgent:
    def _mock_response(self, intents, reasoning="test"):
        payload = json.dumps({"intents": intents, "reasoning": reasoning})
        resp = MagicMock()
        resp.content = [MagicMock(text=payload)]
        return resp

    def test_lookup_intent(self, base_state):
        with patch("agents.router_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(["lookup"])
            result = router_agent(base_state)
        assert result["intent"] == "lookup"

    def test_trend_intent(self, base_state):
        with patch("agents.router_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(["trend"])
            result = router_agent({**base_state, "query": "évolution du PIB"})
        assert result["intent"] == "trend"

    def test_trend_viz_intent(self, base_state):
        with patch("agents.router_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(["trend", "viz"])
            result = router_agent(base_state)
        assert result["intent"] == "viz"

    def test_invalid_json_falls_back_to_lookup(self, base_state):
        resp = MagicMock()
        resp.content = [MagicMock(text="not json")]
        with patch("agents.router_agent._client") as mock_client:
            mock_client.messages.create.return_value = resp
            result = router_agent(base_state)
        assert result["intent"] == "lookup"

    def test_markdown_fenced_json_is_parsed(self, base_state):
        payload = '```json\n{"intents": ["compute"], "reasoning": "test"}\n```'
        resp = MagicMock()
        resp.content = [MagicMock(text=payload)]
        with patch("agents.router_agent._client") as mock_client:
            mock_client.messages.create.return_value = resp
            result = router_agent(base_state)
        assert result["intent"] == "compute"

    def test_uses_haiku_model(self, base_state):
        with patch("agents.router_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(["lookup"])
            router_agent(base_state)
            call_kwargs = mock_client.messages.create.call_args
        assert "haiku" in call_kwargs.kwargs["model"]

    def test_max_tokens_is_low(self, base_state):
        with patch("agents.router_agent._client") as mock_client:
            mock_client.messages.create.return_value = self._mock_response(["lookup"])
            router_agent(base_state)
            call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["max_tokens"] <= 256
