import json
import os
import subprocess
import textwrap
import anthropic
from loguru import logger
from agents.state import AgentState

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

_CODE_PROMPT = """Tu es un assistant de calcul statistique. À partir des extraits suivants et de la question, génère du code Python pour effectuer le calcul demandé.

Question : {query}

Extraits :
{chunks}

Génère UNIQUEMENT du code Python valide qui :
1. Effectue le calcul demandé à partir des données trouvées dans les extraits
2. Stocke le résultat final dans une variable `result` (nombre, dict, ou liste)
3. N'utilise QUE les modules stdlib : math, statistics (déjà importés)
4. Est court (< 20 lignes), sans print(), sans import supplémentaire

Retourne UNIQUEMENT le code Python brut, sans markdown, sans explication."""

_INTERPRET_PROMPT = """Voici le résultat d'un calcul statistique :

Question : {query}
Code exécuté :
{code}
Résultat : {result}

Explique ce résultat en 1-2 phrases simples, dans la même langue que la question."""


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


def _run_sandbox(code: str, timeout: int = 8) -> dict:
    """Run generated code in an isolated subprocess with stdlib only."""
    wrapped = textwrap.dedent(f"""
import json, math, statistics
result = None
{code}
print(json.dumps({{"result": result}}))
""")
    try:
        proc = subprocess.run(
            ["python3", "-c", wrapped],
            capture_output=True, text=True, timeout=timeout,
        )
        if proc.returncode != 0:
            return {"error": proc.stderr.strip()[:300]}
        return json.loads(proc.stdout.strip())
    except subprocess.TimeoutExpired:
        return {"error": f"timeout after {timeout}s"}
    except Exception as e:
        return {"error": str(e)[:200]}


def compute_agent(state: AgentState) -> dict:
    chunks = state.get("retrieved_chunks", [])
    query  = state["query"]

    if not chunks:
        return {"compute_output": None}

    try:
        # Step 1 — generate Python code from chunks
        code_resp = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": _CODE_PROMPT.format(
                query=query,
                chunks=_format_chunks(chunks),
            )}],
        )
        code = _strip_fences(code_resp.content[0].text)

        # Step 2 — execute in sandbox
        sandbox = _run_sandbox(code)
        if "error" in sandbox:
            logger.warning(f"Compute sandbox error: {sandbox['error']}")
            return {"compute_output": None}

        result = sandbox["result"]

        # Step 3 — plain-language interpretation
        interp_resp = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": _INTERPRET_PROMPT.format(
                query=query,
                code=code,
                result=json.dumps(result, ensure_ascii=False),
            )}],
        )
        output = {
            "code":           code,
            "result":         result,
            "interpretation": interp_resp.content[0].text.strip(),
        }

    except Exception as e:
        logger.warning(f"Compute agent error: {e}")
        output = None

    logger.info(f"Compute → result: {output['result'] if output else None}")
    return {"compute_output": output}
