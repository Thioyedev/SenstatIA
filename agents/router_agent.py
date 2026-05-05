import json
import os
import anthropic
from loguru import logger
from agents.state import AgentState

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

INTENT_PROMPT = """Classify this statistical query into one or more intents.

Intents:
- lookup   : single fact or statistic at a specific point in time
- trend    : time series, evolution over years, CAGR, historical progression
- compare  : comparison between regions, countries, sectors, or demographic groups
- compute  : numerical calculation, projection, ratio, formula application
- viz      : user explicitly asks for a chart, graph, plot, map, or visualization

Rules:
- A query can have multiple intents (e.g. trend + viz if they ask for a chart of evolution)
- "compare" only if two or more distinct entities are contrasted
- "viz" only if the user explicitly requests a visual output (graphique, chart, visualise, montre, affiche, courbe, histogramme…)
- Default to ["lookup"] if uncertain

Examples:
- "taux de pauvreté en 2021" → ["lookup"]
- "évolution du PIB depuis 2015" → ["trend"]
- "Dakar vs Ziguinchor pauvreté" → ["compare"]
- "montre l'évolution de la pauvreté" → ["trend", "viz"]
- "graphique de la croissance" → ["trend", "viz"]
- "calcule le ratio dette/PIB" → ["compute"]

Query: {query}

Return JSON only: {{"intents": ["intent1", "intent2"], "reasoning": "one line"}}"""


def _resolve_intent(intents: list[str]) -> str:
    """Collapse intents list into a single routing key."""
    s = set(intents)
    has_viz = "viz" in s
    # viz is a modifier — the data path determines the chart type
    if "trend" in s and "compare" in s:
        return "mixed"            # parallel trend+compare (no viz for now)
    if "compare" in s:
        return "compare_viz" if has_viz else "compare"
    if "trend" in s:
        return "viz" if has_viz else "trend"
    if "compute" in s:
        return "compute"
    if has_viz:
        return "viz"              # fallback: trend path
    return "lookup"


def router_agent(state: AgentState) -> dict:
    query = state["query"]
    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        messages=[{"role": "user", "content": INTENT_PROMPT.format(query=query)}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        parsed  = json.loads(raw)
        intents = parsed.get("intents", ["lookup"])
        intent  = _resolve_intent(intents)
    except (json.JSONDecodeError, Exception):
        intent = "lookup"

    logger.info(f"Router → intent: {intent}")
    return {"intent": intent}
