"""
SenStat MCP Server — exposes SenStat as a Model Context Protocol tool server.

Allows any MCP-compatible client (Claude Desktop, Claude Code, third-party agents)
to query official Senegalese statistics.

Answers come from the SenStat HTTP API at API_URL (default http://localhost:8000),
the same backend the frontends use, so an MCP client sees the same index and
pipeline as the web app. Point API_URL at staging to query staging.

Usage (stdio transport):
    python mcp_server.py

Claude Desktop config (~/.claude/claude_desktop_config.json):
    {
      "mcpServers": {
        "senstat": {
          "command": "python",
          "args": ["/path/to/senstat/mcp_server.py"],
          "env": {"API_URL": "http://localhost:8000", "ANTHROPIC_API_KEY": "sk-ant-..."}
        }
      }
    }
"""

import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
QUERY_TIMEOUT = 180  # seconds; a chart or a multi-agent question can take a while


def _client() -> httpx.Client:
    return httpx.Client(base_url=API_URL, timeout=QUERY_TIMEOUT)


def _api(method: str, path: str, **kwargs):
    try:
        with _client() as client:
            response = client.request(method, path, **kwargs)
    except httpx.HTTPError as e:
        raise RuntimeError(f"SenStat API unreachable at {API_URL}: {e}") from e
    if response.status_code >= 400:
        raise RuntimeError(f"SenStat API {method} {path} → {response.status_code}: {response.text}")
    return response.json()


# ── MCP Server ────────────────────────────────────────────────────────────────────────────
mcp = FastMCP(
    "SenStat",
    instructions=(
        "SenStat gives you official statistics on Senegal from 12 indexed institutional sources:\n"
        "• ANSD — RGPH-5 2023 (population, demographics), BDEF 2024 (macroeconomy), "
        "ENES quarterly (employment), NEER quarterly (GDP outlook)\n"
        "• DGTCP — Public debt statistical bulletins Q1-Q2 2024\n"
        "• Cour des Comptes — Public finance audit report 2019-2024\n"
        "• IMF — World Economic Outlook (GDP, inflation, debt projections, 2025)\n"
        "• World Bank — Open Data Senegal (poverty, education, health, multi-sector)\n"
        "• DAPSA — Annual Agricultural Survey 2022-2023 (cereals, groundnut, food security)\n"
        "• UNDP — HDI 2024 (0.530, rank 169/193) + MPI 2023 (45.1% multidimensional poverty)\n"
        "• ARTP — Telecoms market report 2024 (mobile, internet, operators, penetration)\n\n"
        "Every answer includes the source institution, report name, and page number. "
        "Use senstat_query for any question about: population, poverty, employment, GDP/growth, "
        "public debt, budget/fiscal, telecoms/digital, agriculture, human development (HDI/MPI), "
        "quarterly economic outlook, or any official Senegalese statistical indicator. "
        "The list above is the intended coverage; call senstat_list_sources for what the "
        "connected index can actually search."
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

    Covered domains (12 indexed sources):
    - Population & demographics: ANSD RGPH-5 2023 (17.7M inhabitants, all regions)
    - Employment & labour market: ANSD ENES quarterly, RGPH-5 economic characteristics
    - Macroeconomy & GDP: ANSD BDEF 2024, ANSD NEER quarterly, IMF WEO 2025, World Bank
    - Quarterly economic outlook: ANSD NEER T3-T4 2024
    - Poverty & living conditions: UNDP HDI/MPI 2024, World Bank Open Data
    - Agriculture & food security: DAPSA Annual Agricultural Survey 2022-2023
    - Public debt: DGTCP debt bulletins Q1-Q2 2024
    - Public finances & audit: Cour des Comptes audit 2019-2024
    - Telecoms & digital: ARTP 2024 (mobile penetration, internet, operators)
    - Human development: UNDP HDI 0.530 (rank 169/193), MPI 2023

    Args:
        question: Question in French or English about Senegalese statistics.
        language: Response language — "fr" (default) or "en".
    """
    lang_note = "" if language == "fr" else " Answer in English."
    result = _api("POST", "/query", json={"query": question + lang_note})
    answer = result.get("answer") or "No answer generated."
    citations = result.get("citations", [])

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

    Returns each source with its institution, topics and year. A source is
    searchable when the API's index holds chunks for it — the registry status
    in sources.json is not used, as it can disagree with the index.
    """
    sources = _api("GET", "/documents")
    searchable = [s for s in sources if s.get("chunk_count", 0) > 0]
    absent = [s for s in sources if s.get("chunk_count", 0) == 0]

    lines = [
        f"SenStat sources at {API_URL} ({len(searchable)} searchable, "
        f"{len(absent)} registered but not indexed):\n",
        "─ SEARCHABLE ─",
    ]
    for s in searchable:
        lines.append(
            f"• {s.get('institution') or '?'} — {s.get('report_name') or s['source_id']}"
            f"\n  Topics: {', '.join(s.get('topics', []))}"
            f"\n  Year: {s.get('year') or 'n/a'} · {s['chunk_count']} chunks"
        )

    lines.append("\n─ NOT INDEXED (not searchable) ─")
    for s in absent:
        lines.append(f"• {s.get('institution') or '?'} — {s.get('report_name') or s['source_id']}")

    return "\n".join(lines)


@mcp.tool()
def senstat_get_intent(question: str) -> str:
    """
    Classify the intent of a question without running the full pipeline.

    Returns one of: lookup, trend, compare, compute, viz, compare_viz, mixed.
    Useful for debugging routing behaviour. Runs the router locally (one Haiku
    call, needs ANTHROPIC_API_KEY): it reads no index, so it cannot drift from
    the API.

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


# ── Entry point ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
