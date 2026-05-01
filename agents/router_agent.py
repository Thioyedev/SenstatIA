import json
import os
import anthropic
from loguru import logger
from agents.state import AgentState

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

INTENT_PROMPT = """Classify the user query into one or more intents:
- lookup: single statistic, punctual fact
- trend: time series, evolution, CAGR, historical comparison
- compare: geographic or sectoral comparison (regions, countries, sectors)
- compute: calculation, projection, ratio, formula
- viz: chart, map, visualization requested

Query: {query}

Return JSON only: {{"intents": ["intent1"], "reasoning": "..."}}"""


def router_agent(state: AgentState) -> dict:
    query = state["query"]
    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": INTENT_PROMPT.format(query=query)}],
    )
    raw = response.content[0].text.strip()
    try:
        parsed = json.loads(raw)
        intents = parsed.get("intents", ["lookup"])
        intent = intents[0] if len(intents) == 1 else "mixed"
    except json.JSONDecodeError:
        intent = "lookup"

    logger.info(f"Router → intent: {intent}")
    return {"intent": intent}
