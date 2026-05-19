"""
SenStat MCP Server — exposes SenStat as a Model Context Protocol tool server.

Allows any MCP-compatible client (Claude Desktop, Claude Code, third-party agents)
to query official Senegalese statistics without going through the HTTP API.

Usage (stdio transport):
    python mcp_server.py

Claude Desktop config (~/.claude/claude_desktop_config.json):
    {
      "mcpServers": {
        "senstat": {
          "command": "python",
          "args": ["/path/to/senstat/mcp_server.py"],
          "env": {"ANTHROPIC_API_KEY": "sk-ant-..."}
        }
      }
    }
"""
import asyncio
import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path when run as a script
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from loguru import logger
from mcp.server.fastmcp import FastMCP

load_dotenv()

# ── Lazy-init graph (loaded once on first call) ──────────────────────────────
_graph = None

def _get_graph():
    global _graph
    if _graph is None:
        from agents.graph import build_graph
        _graph = build_graph()
        logger.info("LangGraph compiled and ready")
    return _graph


# ── MCP Server ───────────────────────────────────────────────────────────────
mcp = FastMCP(
    "SenStat",
    instructions=(
        "SenStat gives you official statistics on Senegal from ANSD, DPEE, BCEAO "
        "and other institutional sources. Every answer includes the source institution, "
        "report name, and page number. Use senstat_query for any question about "
        "Senegalese economy, demographics, poverty, employment, or sectoral data."
    ),
)


@mcp.tool()
def senstat_query(
    question: str,
    language: str = "fr",
) -> str:
    """
    Query the SenStat knowledge base for official Senegalese statistics.

    Returns a structured answer grounded in source documents, with citations
    in the format [Institution — Report, p.XX].

    Args:
        question: Question in French or English about Senegalese statistics.
        language: Response language — "fr" (default) or "en".
    """
    from agents.state import AgentState

    lang_note = "" if language == "fr" else " Answer in English."
    query = question + lang_note

    graph = _get_graph()
    state: AgentState = {
        "query": query,
        "intent": "",
        "retrieved_chunks": [],
        "trend_output": None,
        "compare_output": None,
        "compute_output": None,
        "viz_output": None,
        "synthesis": "",
        "citations": [],
        "messages": [],
        "conversation_history": [],
    }

    result = graph.invoke(state)
    answer = result.get("synthesis", "No answer generated.")
    citations = result.get("citations", [])

    # Format citations as a readable block
    if citations:
        cite_lines = [
            f"  • {c.get('institution', '?')} — {c.get('report_name', '?')}"
            + (f", p.{c['page']}" if c.get("page") else "")
            for c in citations
        ]
        sources_block = "\n\nSources:\n" + "\n".join(cite_lines)
    else:
        sources_block = ""

    return answer + sources_block


@mcp.tool()
def senstat_list_sources() -> str:
    """
    List the official statistical sources currently indexed in SenStat.

    Returns each source with its institution, description, and the number
    of text chunks available for retrieval.
    """
    import json
    from pathlib import Path

    sources_path = Path(__file__).parent / "data" / "sources.json"
    if not sources_path.exists():
        return "sources.json not found."

    with open(sources_path) as f:
        sources = json.load(f)

    lines = ["Available sources in SenStat:\n"]
    for s in sources:
        lines.append(
            f"• {s.get('institution', '?')} — {s.get('name', s.get('id', '?'))}"
            f"\n  Topics: {', '.join(s.get('topics', []))}"
            f"\n  Year: {s.get('year', 'N/A')} | Language: {s.get('language', 'N/A')}"
        )

    return "\n".join(lines)


@mcp.tool()
def senstat_get_intent(question: str) -> str:
    """
    Classify the intent of a question without running the full pipeline.

    Returns one of: lookup, trend, compare, compute, viz, mixed.
    Useful for debugging routing behaviour.

    Args:
        question: The user question to classify.
    """
    from agents.router_agent import router_agent
    from agents.state import AgentState

    state: AgentState = {
        "query": question,
        "intent": "",
        "retrieved_chunks": [],
        "trend_output": None,
        "compare_output": None,
        "compute_output": None,
        "viz_output": None,
        "synthesis": "",
        "citations": [],
        "messages": [],
        "conversation_history": [],
    }
    result = router_agent(state)
    return f"Intent: {result.get('intent', 'unknown')}"


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
