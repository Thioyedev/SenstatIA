"""
Unit tests for Phase 2 agents.
Requires ANTHROPIC_API_KEY in environment (or .env file).

Usage:
    python scripts/test_agents.py              # all tests
    python scripts/test_agents.py --no-llm     # skip LLM calls (routing logic only)
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("--no-llm", action="store_true", help="Skip tests that call the API")
args = parser.parse_args()

from agents.state import AgentState
from agents.graph import _route_after_retrieval, _route_after_trend

PASS = "✅"
FAIL = "❌"
SKIP = "⏭ "

results = []


def check(name: str, condition: bool):
    icon = PASS if condition else FAIL
    print(f"  {icon}  {name}")
    results.append(condition)


def section(title: str):
    print(f"\n── {title} {'─' * (50 - len(title))}")


# ── 1. Graph routing (no LLM) ─────────────────────────────────────────────────
section("Graph routing logic")

check("trend intent → trend node",    _route_after_retrieval({"intent": "trend"})   == "trend")
check("compare intent → compare node", _route_after_retrieval({"intent": "compare"}) == "compare")
check("lookup intent → synthesis",     _route_after_retrieval({"intent": "lookup"})  == "synthesis")
check("compute intent → synthesis",    _route_after_retrieval({"intent": "compute"}) == "synthesis")
check("mixed intent → trend first",    _route_after_retrieval({"intent": "mixed"})   == "trend")
check("mixed after trend → compare",  _route_after_trend({"intent": "mixed"})       == "compare")
check("trend after trend → synthesis", _route_after_trend({"intent": "trend"})      == "synthesis")


# ── 2. CrossEncoder reranking (local model, no LLM) ──────────────────────────
section("CrossEncoder reranking")

try:
    from agents.retrieval_agent import _get_cross_encoder
    ce = _get_cross_encoder()
    pairs = [
        ("taux de pauvreté Sénégal", "Le taux de pauvreté est de 37.5% en 2021"),
        ("taux de pauvreté Sénégal", "La pluviométrie annuelle est de 600mm au nord"),
    ]
    scores = ce.predict(pairs)
    check("CrossEncoder loads successfully",        ce is not None)
    check("Relevant passage scores higher",         float(scores[0]) > float(scores[1]))
    check("Irrelevant passage scores below 0",      float(scores[1]) < 0)
except Exception as e:
    check(f"CrossEncoder available (error: {e})", False)


# ── 3. Trend agent (requires ANTHROPIC_API_KEY) ───────────────────────────────
section("Trend agent")

_TREND_STATE: AgentState = {
    "query": "Évolution du taux de pauvreté au Sénégal entre 2011 et 2021",
    "intent": "trend",
    "retrieved_chunks": [
        {
            "text": (
                "Selon l'EHCVM, le taux de pauvreté monétaire était de 46,7% en 2011, "
                "de 37,8% en 2018-2019 et de 37,5% en 2021."
            ),
            "institution": "ANSD",
            "report_name": "EHCVM 2021-2022",
            "page_number": 12,
        }
    ],
    "trend_output": None,
    "compare_output": None,
    "compute_output": None,
    "viz_output": None,
    "synthesis": "",
    "citations": [],
    "messages": [],
}

if args.no_llm:
    print(f"  {SKIP} Skipped (--no-llm)")
else:
    try:
        from agents.trend_agent import trend_agent
        out = trend_agent(_TREND_STATE)
        td = out.get("trend_output")
        check("trend_output is not None",          td is not None)
        check("series has at least 2 data points", td is not None and len(td.get("series", [])) >= 2)
        check("trend field is present",            td is not None and td.get("trend") is not None)
        check("cagr is a float",                   td is not None and isinstance(td.get("cagr"), float))
        check("insight is a non-empty string",     td is not None and bool(td.get("insight")))
    except Exception as e:
        check(f"trend_agent runs without exception (error: {e})", False)


# ── 4. Compare agent (requires ANTHROPIC_API_KEY) ────────────────────────────
section("Compare agent")

_COMPARE_STATE: AgentState = {
    "query": "Comparer le taux de pauvreté entre Dakar et Ziguinchor",
    "intent": "compare",
    "retrieved_chunks": [
        {
            "text": (
                "À Dakar, le taux de pauvreté est de 20,5% en 2021. "
                "À Ziguinchor, ce taux atteint 67,3% (EHCVM 2021-2022, p.33)."
            ),
            "institution": "ANSD",
            "report_name": "EHCVM 2021-2022",
            "page_number": 33,
        }
    ],
    "trend_output": None,
    "compare_output": None,
    "compute_output": None,
    "viz_output": None,
    "synthesis": "",
    "citations": [],
    "messages": [],
}

if args.no_llm:
    print(f"  {SKIP} Skipped (--no-llm)")
else:
    try:
        from agents.compare_agent import compare_agent
        out = compare_agent(_COMPARE_STATE)
        cd = out.get("compare_output")
        check("compare_output is not None",          cd is not None)
        check("entities has at least 2 entries",     cd is not None and len(cd.get("entities", [])) >= 2)
        check("gaps field is present",               cd is not None and "gaps" in cd)
        check("insight is a non-empty string",       cd is not None and bool(cd.get("insight")))
        names = [e["name"] for e in cd.get("entities", [])] if cd else []
        check("Dakar found in entities",             any("Dakar" in n for n in names))
        check("Ziguinchor found in entities",        any("Ziguinchor" in n for n in names))
    except Exception as e:
        check(f"compare_agent runs without exception (error: {e})", False)


# ── 5. Synthesis uses structured data ─────────────────────────────────────────
section("Synthesis — structured data injection")

if args.no_llm:
    print(f"  {SKIP} Skipped (--no-llm)")
else:
    try:
        from agents.synthesis_agent import _format_structured

        state_with_trend: AgentState = {
            **_TREND_STATE,
            "trend_output": {
                "series": [
                    {"year": 2011, "value": 46.7, "unit": "%", "label": "Taux de pauvreté"},
                    {"year": 2021, "value": 37.5, "unit": "%", "label": "Taux de pauvreté"},
                ],
                "cagr": -0.021,
                "trend": "baisse",
                "insight": "La pauvreté a reculé de 9 points entre 2011 et 2021.",
            },
        }
        block = _format_structured(state_with_trend)
        check("Trend block included when trend_output present", "DONNÉES TEMPORELLES" in block)
        check("CAGR formatted as percentage",                   "-2.1%" in block)
        check("Trend direction present",                        "baisse" in block)

        state_no_trend: AgentState = {**_TREND_STATE, "trend_output": None}
        empty_block = _format_structured(state_no_trend)
        check("No block when trend_output is None",             empty_block == "")
    except Exception as e:
        check(f"_format_structured works (error: {e})", False)


# ── Summary ───────────────────────────────────────────────────────────────────
total  = len(results)
passed = sum(results)
failed = total - passed

print(f"\n{'═' * 55}")
print(f"  {passed}/{total} passed  |  {failed} failed")
if failed:
    print(f"  Run with --no-llm to isolate API-dependent failures.")
print(f"{'═' * 55}\n")

sys.exit(0 if failed == 0 else 1)
