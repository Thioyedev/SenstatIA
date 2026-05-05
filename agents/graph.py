import re
from langgraph.graph import StateGraph, END
from langgraph.types import Send
from agents.state import AgentState
from agents.query_rewriter import query_rewriter
from agents.router_agent import router_agent
from agents.retrieval_agent import retrieval_agent
from agents.trend_agent import trend_agent
from agents.compare_agent import compare_agent
from agents.compute_agent import compute_agent
from agents.viz_agent import viz_agent
from agents.synthesis_agent import synthesis_agent


_VIZ_KEYWORDS = re.compile(
    r"\b(graphique|graph|chart|visualis[ae]|montre|affiche|courbe|histogramme|plot|visualize|show me a)\b",
    re.IGNORECASE,
)


def _strip_viz_keywords(query: str) -> str:
    """Remove visualization request words so retrieval focuses on the data."""
    cleaned = _VIZ_KEYWORDS.sub("", query)
    return " ".join(cleaned.split()).strip() or query


def _route_after_retrieval(state: AgentState):
    intent = state.get("intent", "lookup")
    if intent == "trend":
        return "trend"
    if intent in ("compare", "compare_viz"):
        return "compare"
    if intent == "mixed":
        # Parallel: trend and compare run simultaneously via Send API
        return [Send("trend", state), Send("compare", state)]
    if intent == "compute":
        return "compute"
    if intent == "viz":
        return "trend"   # trend extracts series first, then viz renders it
    return "synthesis"


def _prep_viz_query(state: AgentState) -> dict:
    """For viz intent: strip visualization keywords so retrieval fetches data chunks."""
    return {"query": _strip_viz_keywords(state["query"])}


def _route_after_router(state: AgentState) -> str:
    if state.get("intent") in ("viz", "compare_viz"):
        return "prep_viz"
    return "retrieval"


def _route_after_trend(state: AgentState) -> str:
    if state.get("intent") == "viz":
        return "viz"
    return "synthesis"


def _route_after_compare(state: AgentState) -> str:
    if state.get("intent") == "compare_viz":
        return "viz"
    return "synthesis"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("query_rewriter", query_rewriter)
    graph.add_node("router",    router_agent)
    graph.add_node("prep_viz",  _prep_viz_query)
    graph.add_node("retrieval", retrieval_agent)
    graph.add_node("trend",     trend_agent)
    graph.add_node("compare",   compare_agent)
    graph.add_node("compute",   compute_agent)
    graph.add_node("viz",       viz_agent)
    graph.add_node("synthesis", synthesis_agent)

    graph.set_entry_point("query_rewriter")
    graph.add_edge("query_rewriter", "router")
    graph.add_conditional_edges("router", _route_after_router,
                                {"prep_viz": "prep_viz", "retrieval": "retrieval"})
    graph.add_edge("prep_viz", "retrieval")

    # After retrieval: fan-out by intent (Send API handles parallel for "mixed")
    graph.add_conditional_edges("retrieval", _route_after_retrieval)

    # After trend: go to viz (trend+viz) or synthesis
    graph.add_conditional_edges(
        "trend",
        _route_after_trend,
        {"viz": "viz", "synthesis": "synthesis"},
    )

    # After compare: go to viz (compare+viz) or synthesis
    graph.add_conditional_edges(
        "compare",
        _route_after_compare,
        {"viz": "viz", "synthesis": "synthesis"},
    )
    graph.add_edge("compute",  "synthesis")
    graph.add_edge("viz",      "synthesis")
    graph.add_edge("synthesis", END)

    return graph.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
