import ast
import json
import os
import re
import subprocess
import sys

import anthropic
from loguru import logger

from agents.state import AgentState

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

_ALLOWED_IMPORTS = frozenset({"math", "statistics"})

# Reflection/eval builtins. The real defense against a CPython object-graph
# escape — ().__class__.__base__.__subclasses__()[...].__init__.__globals__ —
# is _no_dunder below; these names are the getattr/type routes to the same place.
_FORBIDDEN_BUILTINS = frozenset(
    {
        "__import__",
        "eval",
        "exec",
        "open",
        "compile",
        "globals",
        "locals",
        "vars",
        "dir",
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
        "type",
        "__builtins__",
        "breakpoint",
        "input",
    }
)

# Builtins the generated statistical code is allowed to call. Everything else —
# including anything not listed — is absent from the sandbox namespace at
# runtime, so the AST check and the runtime namespace must both be defeated to
# reach a dangerous call. No print: the runner emits the result.
_SAFE_BUILTINS = frozenset(
    {
        "abs",
        "all",
        "any",
        "bool",
        "dict",
        "divmod",
        "enumerate",
        "filter",
        "float",
        "int",
        "len",
        "list",
        "map",
        "max",
        "min",
        "pow",
        "range",
        "reversed",
        "round",
        "set",
        "sorted",
        "str",
        "sum",
        "tuple",
        "zip",
    }
)


# str.format / format_map resolve "{0.attr}" fields at runtime, so a format
# string assembled from pieces reaches dunders without any dunder in the source.
# f-strings stay allowed: their attribute accesses are ordinary AST nodes.
_FORBIDDEN_ATTRS = frozenset({"format", "format_map"})
_DUNDER_RE = re.compile(r"__\w+__")


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _validate_ast(code: str) -> tuple[bool, str]:
    """Reject dangerous constructs before the code is run.

    Blocklisting builtin names alone is not enough: generated code can walk the
    object graph through dunder attributes to reach os/subprocess without naming
    any forbidden builtin. So this also forbids every dunder attribute access,
    any string literal containing a dunder, and str.format, which together close
    the ways into that graph. Statistical code needs none of them.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom):
                # The module is what gets imported; the names come from it.
                # Checking the names refused "from math import sqrt".
                names = [(node.module or "").split(".")[0] if node.level == 0 else "."]
            else:
                names = [alias.name.split(".")[0] for alias in node.names]
            blocked = [n for n in names if n not in _ALLOWED_IMPORTS]
            if blocked:
                return False, f"forbidden import: {blocked[0]}"
        if isinstance(node, ast.Name) and node.id in _FORBIDDEN_BUILTINS:
            return False, f"forbidden builtin: {node.id}"
        if isinstance(node, ast.Attribute) and _is_dunder(node.attr):
            return False, f"forbidden dunder attribute: {node.attr}"
        if isinstance(node, ast.Attribute) and node.attr in _FORBIDDEN_ATTRS:
            return False, f"forbidden attribute: {node.attr}"
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and _DUNDER_RE.search(node.value)
        ):
            return False, f"forbidden dunder in literal: {node.value!r}"
    return True, ""


_CODE_PROMPT = """Tu es un assistant de calcul statistique. À partir des extraits suivants et de la question, génère du code Python pour effectuer le calcul demandé.

Question : {query}

Extraits :
{chunks}

Génère UNIQUEMENT du code Python valide qui :
1. Effectue le calcul demandé à partir des données trouvées dans les extraits
2. Stocke le résultat final dans une variable `result` (nombre, dict, ou liste)
3. N'utilise QUE les modules stdlib autorisés : math, statistics
4. Est court (< 20 lignes), sans print(), sans import supplémentaire

Retourne UNIQUEMENT le code Python brut, sans markdown, sans explication."""

_INTERPRET_PROMPT = """Voici le résultat d'un calcul statistique :

Question : {query}
Code exécuté :
{code}
Résultat : {result}

Explique ce résultat en 1-2 phrases simples, dans la même langue que la question."""


# Fixed runner: the generated code arrives on stdin, never spliced into source,
# and runs in a namespace whose __builtins__ holds only _SAFE_BUILTINS plus an
# __import__ that returns math or statistics and refuses the rest. Memory
# and CPU are capped inside the child (RLIMIT_AS is not enforced on macOS; the
# subprocess timeout still applies there). Using a limit in the runner rather
# than preexec_fn, which is unsafe in a threaded server like this one.
_RUNNER = """
import builtins, json, math, statistics, sys
try:
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
except (ImportError, ValueError, OSError):
    pass
allowed_modules = {"math": math, "statistics": statistics}
def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level or name not in allowed_modules:
        raise ImportError(f"import of {name!r} is not allowed")
    return allowed_modules[name]
safe = {name: getattr(builtins, name) for name in json.loads(sys.argv[1])}
safe["__import__"] = guarded_import  # "import math" works; nothing else does
ns = {"__builtins__": safe, "math": math, "statistics": statistics, "result": None}
exec(compile(sys.stdin.read(), "<sandbox>", "exec"), ns)
print(json.dumps({"result": ns["result"]}))
"""


def _run_sandbox(code: str, timeout: int = 8) -> dict:
    """AST-validate, then run generated code in a restricted subprocess."""
    ok, reason = _validate_ast(code)
    if not ok:
        logger.warning(f"Compute sandbox rejected code: {reason}")
        return {"error": reason}
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", _RUNNER, json.dumps(sorted(_SAFE_BUILTINS))],
            input=code,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp"},
            cwd="/tmp",
        )
        if proc.returncode != 0:
            return {"error": proc.stderr.strip()[:300]}
        return json.loads(proc.stdout.strip())
    except subprocess.TimeoutExpired:
        return {"error": f"timeout after {timeout}s"}
    except Exception as e:
        return {"error": str(e)[:200]}


def _format_chunks(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] {c.get('institution', '?')} — {c.get('report_name', '?')}, p.{c.get('page_number', '?')}\n{c['text']}"
        for i, c in enumerate(chunks, 1)
    )


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return raw.strip()


def compute_agent(state: AgentState) -> dict:
    chunks = state.get("retrieved_chunks", [])
    query = state["query"]
    if not chunks:
        return {"compute_output": None}
    try:
        code_resp = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": _CODE_PROMPT.format(
                        query=query,
                        chunks=_format_chunks(chunks),
                    ),
                }
            ],
        )
        code = _strip_fences(code_resp.content[0].text)
        sandbox = _run_sandbox(code)
        if "error" in sandbox:
            logger.warning(f"Compute sandbox error: {sandbox['error']}")
            return {"compute_output": None}
        result = sandbox["result"]
        interp_resp = _client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": _INTERPRET_PROMPT.format(
                        query=query,
                        code=code,
                        result=json.dumps(result, ensure_ascii=False),
                    ),
                }
            ],
        )
        output = {
            "code": code,
            "result": result,
            "interpretation": interp_resp.content[0].text.strip(),
        }
    except Exception as e:
        logger.warning(f"Compute agent error: {e}")
        output = None
    logger.info(f"Compute → result: {output['result'] if output else None}")
    return {"compute_output": output}
