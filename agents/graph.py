from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.router_agent import router_agent
from agents.retrieval_agent import retrieval_agent
from agents.synthesis_agent import synthesis_agent


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("router", router_agent)
    graph.add_node("retrieval", retrieval_agent)
    graph.add_node("synthesis", synthesis_agent)

    graph.set_entry_point("router")
    graph.add_edge("router", "retrieval")
    graph.add_edge("retrieval", "synthesis")
    graph.add_edge("synthesis", END)

    return graph.compile()


# Singleton compiled graph
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
