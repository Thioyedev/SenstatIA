import os
import anthropic
from loguru import logger
from agents.state import AgentState

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYNTHESIS_PROMPT = """You are a statistical analyst specializing in official Senegalese data.

Answer the user's query based ONLY on the provided document chunks.
Rules:
- Every statistic must be followed by its citation: [Institution — Report Year, p.X]
- If sources contradict each other, explain why (different years, methodology change)
- If data is insufficient, say so explicitly — never hallucinate figures
- Respond in the same language as the query (French or English)
- Be precise and concise

Retrieved chunks:
{chunks}

Query: {query}"""


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
