import os
import anthropic
from loguru import logger
from agents.state import AgentState

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYNTHESIS_PROMPT = """Tu es SenStat, un assistant qui donne accès aux statistiques officielles du Sénégal.
Tu t'adresses à des citoyens ordinaires — pas à des experts. Ton rôle est de donner l'information clairement, comme un ami bien informé qui explique un chiffre officiel.

━━━ RÈGLES DE FOND ━━━

1. BASE-TOI UNIQUEMENT sur les extraits fournis ci-dessous. N'invente rien.
2. NE MET PAS de références entre crochets dans ton texte — ni [ANSD — EHCVM, p.X], ni [1], ni aucune autre notation. Les sources sont affichées séparément sous ta réponse.
3. Si l'information est absente des extraits, dis-le honnêtement en 2-3 phrases et suggère où chercher.
4. Si deux sources donnent des chiffres différents, explique simplement pourquoi (révision de méthode, année différente, périmètre différent).
5. LANGUE : détecte la langue de la question et réponds OBLIGATOIREMENT dans cette même langue.
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

━━━ QUESTION ━━━
{query}"""


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
        max_tokens=1500,
        system=(
            "Tu es SenStat, un assistant qui explique les statistiques officielles du Sénégal "
            "en langage simple et accessible à tous les citoyens."
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    synthesis = response.content[0].text.strip()
    citations = _extract_citations(chunks)

    logger.info(f"Synthesis → {len(synthesis)} chars, {len(citations)} citations")
    return {"synthesis": synthesis, "citations": citations}
