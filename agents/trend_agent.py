import json
import os

import anthropic
from loguru import logger

from agents.state import AgentState

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

_PROMPT = """À partir des extraits suivants, extrais TOUTES les données temporelles disponibles.

Question : {query}

Extraits :
{chunks}

Tâche :
1. Cherche TOUTE valeur numérique associée à une année, même implicitement
   (ex: "passé de 46,7% en 2011 à 37,5% en 2021", "en 2018/2019 : 37,8%", tableaux…)
2. Calcule le TCAM si au moins 2 points disponibles :
   TCAM = (valeur_finale / valeur_initiale)^(1 / nb_années) - 1
3. Détermine la tendance globale : "hausse" | "baisse" | "stable" | "volatile"
4. Rédige un insight factuel en 1 phrase

Retourne UNIQUEMENT ce JSON valide (sans markdown, sans texte autour) :
{{
  "series": [
    {{"year": 2015, "value": 6.5, "unit": "%", "label": "Croissance du PIB"}},
    {{"year": 2019, "value": 5.3, "unit": "%", "label": "Croissance du PIB"}}
  ],
  "cagr": -0.041,
  "trend": "baisse",
  "insight": "La croissance du PIB est passée de 6,5% en 2015 à 5,3% en 2019."
}}

Si les données temporelles sont absentes ou insuffisantes :
{{"series": [], "cagr": null, "trend": null, "insight": null}}"""


def _format_chunks(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] {c.get('institution', '?')} — {c.get('report_name', '?')}, p.{c.get('page_number', '?')}\n{c['text']}"
        for i, c in enumerate(chunks, 1)
    )


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return raw.strip()


def trend_agent(state: AgentState) -> dict:
    chunks = state.get("retrieved_chunks", [])
    if not chunks:
        return {"trend_output": None}

    try:
        resp = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[
                {
                    "role": "user",
                    "content": _PROMPT.format(
                        query=state["query"],
                        chunks=_format_chunks(chunks),
                    ),
                }
            ],
        )
        data = json.loads(_strip_fences(resp.content[0].text))
        output = data if data.get("series") else None
    except Exception as e:
        logger.warning(f"Trend agent error: {e}")
        output = None

    logger.info(f"Trend → {len(output['series']) if output else 0} data points")
    return {"trend_output": output}
