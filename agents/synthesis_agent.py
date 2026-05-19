import os
import re
import anthropic
from loguru import logger
from agents.state import AgentState

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYNTHESIS_PROMPT = """Tu es SenStat, un assistant qui donne accès aux statistiques officielles du Sénégal.
Tu t'adresses à des citoyens ordinaires — pas à des experts. Ton rôle est de donner l'information clairement, comme un ami bien informé qui explique un chiffre officiel.

━━━ RÈGLES DE FOND ━━━

1. BASE-TOI UNIQUEMENT sur les extraits fournis ci-dessous. N'invente rien.
2. ZÉRO INTERPOLATION : si un chiffre ou un fait ne figure pas textuellement dans les extraits, ne l'inclus pas dans ta réponse. Pas d'estimation, pas de déduction, pas de connaissance générale. Si tu n'es pas sûr qu'un chiffre vient des extraits, ne le cite pas.
3. NE MET PAS de références entre crochets dans ton texte — ni [ANSD — EHCVM, p.X], ni [1], ni aucune autre notation. Les sources sont affichées séparément sous ta réponse.
4. Si l'information est absente des extraits, dis-le honnêtement en 2-3 phrases et suggère où chercher.
5. Si deux sources donnent des chiffres différents, explique simplement pourquoi (révision de méthode, année différente, périmètre différent).
6. LANGUE : détecte la langue de la question et réponds OBLIGATOIREMENT dans cette même langue.
   - Question en français → réponse en français
   - Question in English → respond in English
   - Autre langue → réponds en français par défaut

━━━ RÈGLES DE FORME (très importantes) ━━━

COMMENCE toujours par le chiffre ou la réponse directe — pas par une introduction.
DONNE du contexte aux chiffres : "17% des Sénégalais, soit environ 3 millions de personnes" vaut mieux que juste "17%".
UTILISE des phrases courtes. Maximum 2-3 lignes par paragraphe.
ÉVITE absolument ces mots et expressions :
  ✗ "selon les données disponibles", "il convient de noter", "dans le cadre de"
  ✗ "les extraits", "les documents", "mes données", "la base de données"
  ✗ "il est important de souligner", "nous pouvons observer que"
  ✗ tout mot technique informatique (chunk, embedding, corpus, retrieval…)

━━━ EXEMPLES ━━━

Question : "Quel est le taux de pauvreté au Sénégal ?"

✅ BONNE réponse :
"En 2021, 37,5 % des Sénégalais vivent en dessous du seuil de pauvreté, soit environ 7 millions de personnes. Ce taux est plus élevé en milieu rural (52 %) qu'en ville (20 %)."

❌ MAUVAISE réponse :
"En 2021, 37,5 % des Sénégalais vivent en dessous du seuil de pauvreté. [ANSD — EHCVM 2021, p.12] Ce taux est plus élevé en milieu rural (52 %) [ANSD — EHCVM 2021, p.33] qu'en ville (20 %). [ANSD — EHCVM 2021, p.33]"

---

Question : "Combien d'accidents de la route y a-t-il eu en 2023 ?"

✅ BONNE réponse :
"Je n'ai pas cette statistique dans mes sources actuelles. Pour les chiffres sur les accidents de la route, consultez le rapport annuel de la Direction des Transports Terrestres (DTT) ou l'Observatoire National de la Sécurité Routière."

❌ MAUVAISE réponse :
"Les documents fournis ne contiennent pas de données suffisantes pour répondre à cette question de manière précise."

━━━ EXTRAITS DE SOURCES ━━━
{chunks}
{structured_data}
━━━ QUESTION ━━━
{query}

━━━ INSTRUCTION FINALE ━━━
À la toute fin de ta réponse, sur une ligne séparée, écris exactement :
SOURCES_USED: <numéros des extraits que tu as effectivement utilisés, séparés par des virgules>
Exemple : SOURCES_USED: 1,3
N'indique que les extraits dont le contenu apparaît dans ta réponse. Si tu n'as utilisé aucun extrait, écris SOURCES_USED: none"""

_TREND_BLOCK = """
━━━ DONNÉES TEMPORELLES (pré-calculées) ━━━
Tendance : {trend} | TCAM : {cagr}
Série : {series}
Insight : {insight}
"""

_COMPARE_BLOCK = """
━━━ DONNÉES DE COMPARAISON (pré-calculées) ━━━
Entités : {entities}
Écarts : {gaps}
Insight : {insight}
"""

_COMPUTE_BLOCK = """
━━━ RÉSULTAT DE CALCUL (pré-calculé) ━━━
Résultat : {result}
Interprétation : {interpretation}
"""


def _format_chunks(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        institution = c.get("institution", "?")
        report = c.get("report_name", "?")
        year = c.get("year", "?")
        page = c.get("page_number", "?")
        parts.append(
            f"[{i}] {institution} — {report} ({year}), p.{page}\n{c['text']}"
        )
    return "\n\n".join(parts)


def _extract_citations(chunks: list[dict]) -> list[dict]:
    seen = set()
    citations = []
    for c in chunks:
        key = (c.get("source_id"), c.get("page_number"))
        if key not in seen:
            seen.add(key)
            citations.append({
                "institution": c.get("institution"),
                "report_name": c.get("report_name"),
                "year": c.get("year"),
                "page": c.get("page_number"),
                "url": c.get("url"),
                "source_id": c.get("source_id"),
            })
    return citations


def _format_structured(state: AgentState) -> str:
    parts = []
    trend = state.get("trend_output")
    if trend and trend.get("series"):
        parts.append(_TREND_BLOCK.format(
            trend=trend.get("trend"),
            cagr=f"{trend['cagr']:.1%}" if trend.get("cagr") is not None else "N/A",
            series=", ".join(
                f"{p['year']}: {p['value']}{p.get('unit','')}" for p in trend["series"]
            ),
            insight=trend.get("insight", ""),
        ))
    compare = state.get("compare_output")
    if compare and compare.get("entities"):
        entities_str = " | ".join(
            f"{e['name']}: " + ", ".join(
                f"{v['metric']}={v['value']}{v.get('unit','')}" for v in e["values"]
            )
            for e in compare["entities"]
        )
        gaps_str = ", ".join(
            f"{g['metric']}: écart {g['absolute']}{g.get('unit','')} ({g['winner']} en tête)"
            for g in compare.get("gaps", [])
        )
        parts.append(_COMPARE_BLOCK.format(
            entities=entities_str,
            gaps=gaps_str or "N/A",
            insight=compare.get("insight", ""),
        ))
    compute = state.get("compute_output")
    if compute and compute.get("result") is not None:
        parts.append(_COMPUTE_BLOCK.format(
            result=compute["result"],
            interpretation=compute.get("interpretation", ""),
        ))
    return "\n".join(parts)


def synthesis_agent(state: AgentState) -> dict:
    chunks = state.get("retrieved_chunks", [])
    query = state["query"]
    history = state.get("conversation_history", [])

    chunks_text = _format_chunks(chunks)
    structured_data = _format_structured(state)
    prompt = SYNTHESIS_PROMPT.format(chunks=chunks_text, structured_data=structured_data, query=query)

    # Build multi-turn messages: inject history (plain Q&A), then current prompt with chunks
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt})

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=(
            "Tu es SenStat, un assistant qui explique les statistiques officielles du Sénégal "
            "en langage simple et accessible à tous les citoyens."
        ),
        messages=messages,
    )
    raw = response.content[0].text.strip()

    # Extract SOURCES_USED line and filter citations to only used chunks
    sources_match = re.search(r'\nSOURCES_USED:\s*([^\n]+)', raw)
    synthesis = re.sub(r'\nSOURCES_USED:[^\n]*', '', raw).strip()

    if sources_match:
        used_str = sources_match.group(1).strip()
        if used_str.lower() == "none":
            used_indices: set[int] = set()
        else:
            used_indices = {
                int(x.strip()) - 1  # convert 1-based to 0-based
                for x in used_str.split(",")
                if x.strip().isdigit()
            }
        used_chunks = [chunks[i] for i in sorted(used_indices) if i < len(chunks)]
    else:
        used_chunks = chunks  # fallback: cite all if model didn't follow instruction

    citations = _extract_citations(used_chunks)
    logger.info(f"Synthesis → {len(synthesis)} chars, {len(citations)} citations (from {len(chunks)} retrieved)")
    return {"synthesis": synthesis, "citations": citations}
