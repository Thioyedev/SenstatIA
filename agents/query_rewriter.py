import os
import anthropic
from loguru import logger
from agents.state import AgentState

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

_FOLLOWUP_TRIGGERS = (
    "et ", "et pour", "et à", "et en", "et le", "et la", "et les",
    "qu'en est-il", "ça", "cela", "idem", "pareil", "même chose",
    "et chez", "et dans", "et au", "et aux", "mais ", "mais pour",
    "c'est quoi", "c'est combien", "combien pour",
)

_PROMPT = """Voici une conversation sur les statistiques du Sénégal.

Historique récent :
{history}

Nouvelle question : {query}

Si cette question est une question de suivi qui dépend du contexte précédent (ellipse, pronom, "et pour X ?", etc.), \
reformule-la en une question complète et autonome qu'un moteur de recherche peut comprendre sans l'historique.

Règles :
- Conserve la même langue que la question
- Reste fidèle à l'intention : ne change pas le sujet, ne rajoute pas d'informations
- Si la question est déjà autonome et claire, retourne-la EXACTEMENT telle quelle

Retourne UNIQUEMENT la question reformulée, sans explication, sans guillemets."""


def query_rewriter(state: AgentState) -> dict:
    query = state["query"]
    history = state.get("conversation_history", [])

    if not history:
        return {}

    words = query.split()
    is_short = len(words) <= 5
    starts_with_trigger = query.lower().startswith(_FOLLOWUP_TRIGGERS)

    if not (is_short or starts_with_trigger):
        return {}

    # Last 2 user/assistant exchanges (4 messages max)
    recent = history[-4:] if len(history) >= 4 else history
    history_text = "\n".join(
        f"{'Utilisateur' if m['role'] == 'user' else 'Assistant'}: {m['content'][:400]}"
        for m in recent
    )

    try:
        resp = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            messages=[{"role": "user", "content": _PROMPT.format(
                history=history_text,
                query=query,
            )}],
        )
        rewritten = resp.content[0].text.strip().strip('"').strip("'")
        if rewritten and rewritten != query:
            logger.info(f"Query rewritten: '{query}' → '{rewritten}'")
            return {"query": rewritten}
    except Exception as e:
        logger.warning(f"Query rewriter error: {e}")

    return {}
