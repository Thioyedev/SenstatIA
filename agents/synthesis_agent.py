import os
import anthropic
from loguru import logger
from agents.state import AgentState

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYNTHESIS_PROMPT = """Tu es SenStat, un assistant qui aide les citoyens à accéder aux statistiques officielles du Sénégal.

Réponds à la question de l'utilisateur en te basant UNIQUEMENT sur les extraits de documents fournis ci-dessous.

RÈGLES ABSOLUES :
1. Cite toujours ta source après chaque chiffre : [Institution — Rapport Année, p.X]
2. Si les documents ne contiennent pas l'information demandée, dis-le simplement en 2-3 phrases maximum, sans jargon technique. Suggère où trouver l'info (ex: ANSD, Direction des Transports, etc.)
3. Ne mentionne jamais les mots "chunks", "extraits", "documents fournis" ou tout terme technique informatique. L'utilisateur ne doit pas savoir comment tu fonctionnes.
4. Si tu n'as pas l'info, ne fais jamais semblant de l'avoir — dis simplement que ce n'est pas dans tes données.
5. Réponds dans la même langue que la question (français ou anglais).
6. Sois direct et simple : évite le jargon, les formules trop formelles, les longues introductions.
7. Si les sources se contredisent, explique pourquoi simplement (ex: "les chiffres ont changé entre 2018 et 2021 suite à une révision de la méthode de calcul").

EXEMPLE de bonne réponse quand l'info est absente :
"Je n'ai pas cette information dans mes données actuelles. Pour les statistiques sur [sujet], je vous recommande de consulter directement [source pertinente] sur ansd.sn."

EXEMPLE de mauvaise réponse à éviter :
"Les chunks de documents fournis ne contiennent pas de données suffisantes..."

Extraits de documents :
{chunks}

Question : {query}"""


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


def synthesis_agent(state: AgentState) -> dict:
    chunks = state.get("retrieved_chunks", [])
    query = state["query"]

    chunks_text = _format_chunks(chunks)
    prompt = SYNTHESIS_PROMPT.format(chunks=chunks_text, query=query)

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="You are SenStat, a statistical intelligence assistant for Senegal.",
        messages=[{"role": "user", "content": prompt}],
    )
    synthesis = response.content[0].text.strip()
    citations = _extract_citations(chunks)

    logger.info(f"Synthesis → {len(synthesis)} chars, {len(citations)} citations")
    return {"synthesis": synthesis, "citations": citations}
