import json
from unittest.mock import MagicMock, patch

from agents.compare_agent import compare_agent

VALID_JSON = json.dumps({
    "entities": [
        {"name": "Urbain", "values": [{"metric": "pauvreté", "value": 20.5, "unit": "%", "year": 2021}]},
        {"name": "Rural", "values": [{"metric": "pauvreté", "value": 52.0, "unit": "%", "year": 2021}]},
    ],
    "gaps": [{"metric": "pauvreté", "absolute": 31.5, "relative": 1.54, "winner": "Rural", "unit": "%"}],
    "insight": "Rural 2,5× plus pauvre.",
})
EMPTY_JSON = json.dumps({"entities": [], "gaps": [], "insight": None})


class TestCompareAgent:
    def _mock(self, text):
        resp = MagicMock()
        resp.content = [MagicMock(text=text)]
        return resp

    def test_extracts_entities_and_gaps(self, base_state):
        with patch("agents.compare_agent._client") as c:
            c.messages.create.return_value = self._mock(VALID_JSON)
            result = compare_agent({**base_state, "intent": "compare"})
        assert result["compare_output"] is not None
        assert len(result["compare_output"]["entities"]) == 2

    def test_returns_none_when_no_chunks(self, base_state):
        assert compare_agent({**base_state, "retrieved_chunks": []})["compare_output"] is None

    def test_returns_none_when_entities_empty(self, base_state):
        with patch("agents.compare_agent._client") as c:
            c.messages.create.return_value = self._mock(EMPTY_JSON)
            result = compare_agent(base_state)
        assert result["compare_output"] is None

    def test_handles_api_error(self, base_state):
        with patch("agents.compare_agent._client") as c:
            c.messages.create.side_effect = Exception("error")
            result = compare_agent(base_state)
        assert result["compare_output"] is None

    def test_uses_haiku_model(self, base_state):
        with patch("agents.compare_agent._client") as c:
            c.messages.create.return_value = self._mock(VALID_JSON)
            compare_agent(base_state)
        assert "haiku" in c.messages.create.call_args.kwargs["model"]
