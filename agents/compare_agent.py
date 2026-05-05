import json
import os
import anthropic
from loguru import logger
from agents.state import AgentState

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

_PROMPT = """À partir des extraits suivants, extrais toutes les données permettant une comparaison entre entités.

Question : {query}

Extraits :
{chunks}

Tâche :
1. Identifie TOUTE paire d'entités comparables dans les extraits :
   - Régions ou villes (Dakar, Ziguinchor, Thiès…)
   - Catégories géographiques (milieu urbain / milieu rural, Dakar / autres régions)
   - Catégories démographiques (hommes / femmes, jeunes / adultes)
   - Secteurs ou années
   → Ne te limite pas aux entités nommées dans la question : extrais ce que les extraits contiennent réellement.

2. Pour chaque entité identifiée, extrais UNE SEULE valeur (la métrique principale, la plus récente). Limite à 6 entités maximum. Pour les tableaux régionaux, priorise les régions mentionnées dans la question + les valeurs extrêmes (min/max).

3. Calcule l'écart absolu et relatif si tu as au moins 2 entités avec la même métrique.

4. Identifie quelle entité a la valeur la plus haute.

5. Rédige un insight factuel en 1-2 phrases.

Exemples d'extractions valides :
- "Le taux de pauvreté est de 20,5% en milieu urbain et 52% en milieu rural" → entités : ["Milieu urbain", "Milieu rural"]
- "Dakar : 17%, reste du Sénégal : 44%" → entités : ["Dakar", "Reste du Sénégal"]
- "passé de 46,7% en 2011 à 37,5% en 2021" → entités : ["2011", "2021"]

Retourne UNIQUEMENT ce JSON valide (sans markdown, sans texte autour) :
{{
  "entities": [
    {{
      "name": "Milieu urbain",
      "values": [
        {{"metric": "taux de pauvreté", "value": 20.5, "unit": "%", "year": 2021}}
      ]
    }},
    {{
      "name": "Milieu rural",
      "values": [
        {{"metric": "taux de pauvreté", "value": 52.0, "unit": "%", "year": 2021}}
      ]
    }}
  ],
  "gaps": [
    {{"metric": "taux de pauvreté", "absolute": 31.5, "relative": 1.54, "winner": "Milieu rural", "unit": "%"}}
  ],
  "insight": "Le milieu rural affiche un taux de pauvreté 2,5× supérieur au milieu urbain (52% vs 20,5%)."
}}

Si vraiment aucune comparaison n'est possible :
{{"entities": [], "gaps": [], "insight": null}}"""


def _format_chunks(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] {c.get('institution','?')} — {c.get('report_name','?')}, p.{c.get('page_number','?')}\n{c['text']}"
        for i, c in enumerate(chunks, 1)
    )


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return raw.strip()


def compare_agent(state: AgentState) -> dict:
    chunks = state.get("retrieved_chunks", [])
    if not chunks:
        return {"compare_output": None}

    try:
        resp = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": _PROMPT.format(
                query=state["query"],
                chunks=_format_chunks(chunks),
            )}],
        )
        raw = resp.content[0].text
        logger.debug(f"Compare raw: {raw[:300]}")
        data = json.loads(_strip_fences(raw))
        output = data if data.get("entities") else None
    except Exception as e:
        logger.warning(f"Compare agent error: {e}")
        output = None

    entity_count = len(output["entities"]) if output else 0
    logger.info(f"Compare → {entity_count} entities")
    return {"compare_output": output}
