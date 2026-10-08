import plotly.graph_objects as go
from loguru import logger

from agents.state import AgentState


def _source_label(chunks: list[dict]) -> str:
    if not chunks:
        return "ANSD"
    institutions = list(
        dict.fromkeys(c.get("institution", "ANSD") for c in chunks if c.get("institution"))
    )
    return " · ".join(institutions[:2])


def _watermark(fig: go.Figure, label: str):
    fig.add_annotation(
        text=f"SenStat · {label}",
        xref="paper",
        yref="paper",
        x=1.0,
        y=-0.16,
        showarrow=False,
        font=dict(size=10, color="#bbb", family="Inter"),
        xanchor="right",
    )


def _trend_chart(trend_output: dict, query: str, source: str) -> dict:
    series = trend_output["series"]
    years = [p["year"] for p in series]
    values = [p["value"] for p in series]
    unit = series[0].get("unit", "") if series else ""
    label = series[0].get("label", "") if series else query[:50]
    trend = trend_output.get("trend", "")
    cagr = trend_output.get("cagr")

    color = "#E65100" if trend == "baisse" else "#00853F"
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=years,
            y=values,
            mode="lines+markers",
            line=dict(color=color, width=3),
            marker=dict(size=9, color=color, line=dict(color="white", width=2)),
            fill="tozeroy",
            fillcolor=f"rgba({r},{g},{b},0.08)",
            name=label,
            hovertemplate=f"%{{x}} : %{{y}}{unit}<extra></extra>",
        )
    )

    if cagr is not None:
        sign = "+" if cagr >= 0 else ""
        fig.add_annotation(
            text=f"TCAM {sign}{cagr:.1%}",
            xref="paper",
            yref="paper",
            x=0.01,
            y=0.97,
            showarrow=False,
            font=dict(size=12, color=color, family="Inter"),
            bgcolor="rgba(255,255,255,0.85)",
            borderpad=4,
        )

    _watermark(fig, source)

    fig.update_layout(
        title=dict(text=label, font=dict(size=14, family="Inter", color="#1A1A2E")),
        xaxis=dict(title="Année", tickmode="linear", dtick=1, tickfont=dict(size=11)),
        yaxis=dict(title=unit or "Valeur"),
        template="plotly_white",
        height=320,
        margin=dict(l=50, r=20, t=55, b=75),
        showlegend=False,
    )
    return {"fig_json": fig.to_json(), "chart_type": "trend"}


def _compare_chart(compare_output: dict, source: str) -> dict:
    entities = compare_output["entities"]

    # Pick the first common metric across all entities
    all_metrics = []
    for e in entities:
        for v in e.get("values", []):
            if v["metric"] not in all_metrics:
                all_metrics.append(v["metric"])
    metric = all_metrics[0] if all_metrics else "valeur"

    names, values, unit = [], [], ""
    for e in entities:
        names.append(e["name"])
        match = next((v for v in e.get("values", []) if v["metric"] == metric), None)
        values.append(match["value"] if match else 0)
        if not unit and match:
            unit = match.get("unit", "")

    palette = ["#00853F", "#1565C0", "#E65100", "#FFDE28", "#6A1B9A", "#558B2F"]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=names,
            y=values,
            marker_color=palette[: len(names)],
            text=[f"{v}{unit}" for v in values],
            textposition="outside",
            hovertemplate="%{x} : %{y}" + unit + "<extra></extra>",
        )
    )

    _watermark(fig, source)

    fig.update_layout(
        title=dict(text=metric.capitalize(), font=dict(size=14, family="Inter", color="#1A1A2E")),
        yaxis=dict(title=unit or "Valeur"),
        template="plotly_white",
        height=320,
        margin=dict(l=50, r=20, t=55, b=75),
        showlegend=False,
    )
    return {"fig_json": fig.to_json(), "chart_type": "compare"}


def viz_agent(state: AgentState) -> dict:
    intent = state.get("intent", "")
    trend = state.get("trend_output")
    compare = state.get("compare_output")
    chunks = state.get("retrieved_chunks", [])
    query = state["query"]
    source = _source_label(chunks)

    output = None
    try:
        # compare_viz intent: bar chart takes priority
        if intent == "compare_viz" and compare and compare.get("entities"):
            output = _compare_chart(compare, source)
        elif trend and trend.get("series"):
            output = _trend_chart(trend, query, source)
        elif compare and compare.get("entities"):
            output = _compare_chart(compare, source)
    except Exception as e:
        logger.warning(f"Viz agent error: {e}")
        output = None

    logger.info(f"Viz → {output['chart_type'] if output else 'no chart'}")
    return {"viz_output": output}
