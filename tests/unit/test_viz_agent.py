import json

import pytest

from agents.viz_agent import viz_agent


class TestVizAgent:
    def test_trend_chart_from_trend_intent(self, base_state, trend_output):
        state = {**base_state, "intent": "viz", "trend_output": trend_output}
        result = viz_agent(state)

        assert result["viz_output"] is not None
        assert result["viz_output"]["chart_type"] == "trend"

    def test_fig_json_is_valid_plotly(self, base_state, trend_output):
        state = {**base_state, "intent": "viz", "trend_output": trend_output}
        result = viz_agent(state)

        fig = json.loads(result["viz_output"]["fig_json"])
        assert "data" in fig
        assert "layout" in fig
        assert fig["data"][0]["type"] == "scatter"

    def test_compare_chart_for_compare_viz_intent(self, base_state, compare_output):
        state = {**base_state, "intent": "compare_viz", "compare_output": compare_output}
        result = viz_agent(state)

        assert result["viz_output"] is not None
        assert result["viz_output"]["chart_type"] == "compare"

    def test_compare_chart_is_bar(self, base_state, compare_output):
        state = {**base_state, "intent": "compare_viz", "compare_output": compare_output}
        result = viz_agent(state)

        fig = json.loads(result["viz_output"]["fig_json"])
        assert fig["data"][0]["type"] == "bar"

    def test_compare_takes_priority_over_trend_on_compare_viz(self, base_state, trend_output, compare_output):
        state = {
            **base_state,
            "intent": "compare_viz",
            "trend_output": trend_output,
            "compare_output": compare_output,
        }
        result = viz_agent(state)
        assert result["viz_output"]["chart_type"] == "compare"

    def test_returns_none_when_no_data(self, base_state):
        result = viz_agent(base_state)
        assert result["viz_output"] is None

    def test_watermark_contains_institution(self, base_state, trend_output):
        state = {**base_state, "intent": "viz", "trend_output": trend_output}
        result = viz_agent(state)

        fig = json.loads(result["viz_output"]["fig_json"])
        annotations = fig.get("layout", {}).get("annotations", [])
        texts = [a.get("text", "") for a in annotations]
        assert any("SenStat" in t or "ANSD" in t for t in texts)

    def test_trend_direction_colours_line(self, base_state, trend_output):
        """Baisse → orange (#E65100), hausse → green (#00853F)."""
        state = {**base_state, "intent": "viz", "trend_output": trend_output}
        result = viz_agent(state)

        fig = json.loads(result["viz_output"]["fig_json"])
        line_color = fig["data"][0]["line"]["color"]
        # trend is "baisse" → should be orange
        assert line_color == "#E65100"
