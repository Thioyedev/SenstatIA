import json

from agents.viz_agent import viz_agent


class TestVizAgent:
    def test_trend_chart_from_viz_intent(self, base_state, trend_output):
        result = viz_agent({**base_state, "intent": "viz", "trend_output": trend_output})
        assert result["viz_output"]["chart_type"] == "trend"

    def test_fig_json_is_valid_plotly(self, base_state, trend_output):
        result = viz_agent({**base_state, "intent": "viz", "trend_output": trend_output})
        fig = json.loads(result["viz_output"]["fig_json"])
        assert "data" in fig and "layout" in fig
        assert fig["data"][0]["type"] == "scatter"

    def test_compare_chart_for_compare_viz(self, base_state, compare_output):
        result = viz_agent(
            {**base_state, "intent": "compare_viz", "compare_output": compare_output}
        )
        assert result["viz_output"]["chart_type"] == "compare"

    def test_compare_is_bar_chart(self, base_state, compare_output):
        result = viz_agent(
            {**base_state, "intent": "compare_viz", "compare_output": compare_output}
        )
        fig = json.loads(result["viz_output"]["fig_json"])
        assert fig["data"][0]["type"] == "bar"

    def test_compare_takes_priority_over_trend(self, base_state, trend_output, compare_output):
        result = viz_agent(
            {
                **base_state,
                "intent": "compare_viz",
                "trend_output": trend_output,
                "compare_output": compare_output,
            }
        )
        assert result["viz_output"]["chart_type"] == "compare"

    def test_returns_none_when_no_data(self, base_state):
        assert viz_agent(base_state)["viz_output"] is None

    def test_watermark_present(self, base_state, trend_output):
        result = viz_agent({**base_state, "intent": "viz", "trend_output": trend_output})
        fig = json.loads(result["viz_output"]["fig_json"])
        texts = [a.get("text", "") for a in fig.get("layout", {}).get("annotations", [])]
        assert any("SenStat" in t for t in texts)

    def test_baisse_uses_orange_color(self, base_state, trend_output):
        result = viz_agent({**base_state, "intent": "viz", "trend_output": trend_output})
        fig = json.loads(result["viz_output"]["fig_json"])
        assert fig["data"][0]["line"]["color"] == "#E65100"
