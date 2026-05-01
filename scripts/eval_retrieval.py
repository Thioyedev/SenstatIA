"""
Evaluation pipeline for SenStat RAG system.

Usage:
    python scripts/eval_retrieval.py                    # Full eval (all 20 questions)
    python scripts/eval_retrieval.py --n 5              # Quick eval (first 5 questions)
    python scripts/eval_retrieval.py --theme pauvreté   # Filter by theme
    python scripts/eval_retrieval.py --no-ragas         # Custom metrics only (faster)
"""

import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from loguru import logger
import pandas as pd
from vectorstore.chroma_store import ChromaStore
from agents.graph import get_graph

# ── CLI ────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Evaluate SenStat RAG pipeline")
parser.add_argument("--n",        type=int,   default=None, help="Limit number of questions")
parser.add_argument("--theme",    type=str,   default=None, help="Filter by theme")
parser.add_argument("--no-ragas", action="store_true",      help="Skip RAGAS (faster)")
parser.add_argument("--output",   type=str,   default=None, help="Output CSV path")
args = parser.parse_args()


# ── Load golden dataset ────────────────────────────────────────────────────────
GOLDEN_PATH = Path("data/golden_dataset.json")
with open(GOLDEN_PATH) as f:
    golden = json.load(f)

if args.theme:
    golden = [q for q in golden if args.theme.lower() in q["theme"].lower()]
if args.n:
    golden = golden[:args.n]

logger.info(f"Loaded {len(golden)} questions from golden dataset")


# ── Custom metrics ─────────────────────────────────────────────────────────────

def keyword_hit_rate(answer: str, keywords: list[str]) -> float:
    """Fraction of expected keywords found in the answer."""
    if not keywords:
        return 1.0
    answer_lower = answer.lower()
    hits = sum(1 for kw in keywords if kw.lower() in answer_lower)
    return hits / len(keywords)


def citation_present(answer: str) -> bool:
    """Check if answer contains at least one citation pattern [X — Y, p.Z]."""
    import re
    return bool(re.search(r'\[.+?—.+?p\.\d+\]', answer))


def refusal_rate(answer: str, is_out_of_corpus: bool) -> bool:
    """For out-of-corpus questions, did the system correctly refuse to hallucinate?"""
    if not is_out_of_corpus:
        return True
    refusal_signals = [
        "pas disponible", "pas dans", "ne contient pas",
        "indisponible", "ne figure pas", "pas de données",
        "insufficient", "not available", "cannot", "données insuffisantes",
        "je ne peux pas", "il n'est pas possible"
    ]
    answer_lower = answer.lower()
    return any(s in answer_lower for s in refusal_signals)


def retrieval_quality(chunks: list[dict], source_hint: str) -> float:
    """Check if retrieved chunks come from the expected source."""
    if source_hint == "Multi-sources" or source_hint == "Hors corpus":
        return 1.0
    if not chunks:
        return 0.0
    on_target = sum(1 for c in chunks if source_hint.split()[0].lower()
                    in c.get("report_name", "").lower())
    return on_target / len(chunks)


# ── Run evaluation ─────────────────────────────────────────────────────────────
graph   = get_graph()
store   = ChromaStore()
results = []

logger.info("Starting evaluation…")
print("\n" + "═" * 70)
print(f"  SenStat RAG Evaluation — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"  {len(golden)} questions · {'RAGAS ON' if not args.no_ragas else 'RAGAS OFF'}")
print("═" * 70 + "\n")

ragas_samples = []  # collect for RAGAS batch evaluation

for i, item in enumerate(golden, 1):
    q           = item["question"]
    expected    = item["ground_truth"]
    keywords    = item.get("expected_keywords", [])
    source      = item["source"]
    is_oos      = source == "Hors corpus"

    print(f"[{i:02d}/{len(golden)}] {q[:65]}…")

    t0 = time.time()
    try:
        state = graph.invoke({
            "query": q,
            "intent": "",
            "retrieved_chunks": [],
            "trend_output": None,
            "compare_output": None,
            "compute_output": None,
            "viz_output": None,
            "synthesis": "",
            "citations": [],
            "messages": [],
        })
        answer  = state["synthesis"]
        chunks  = state["retrieved_chunks"]
        intent  = state["intent"]
        latency = time.time() - t0
        error   = None
    except Exception as e:
        answer  = ""
        chunks  = []
        intent  = "error"
        latency = time.time() - t0
        error   = str(e)
        logger.error(f"  Error on question {i}: {e}")

    # ── Custom metrics
    kw_score    = keyword_hit_rate(answer, keywords)
    has_cite    = citation_present(answer)
    refused_ok  = refusal_rate(answer, is_oos)
    ret_quality = retrieval_quality(chunks, source)
    n_chunks    = len(chunks)

    row = {
        "id":              item["id"],
        "theme":           item["theme"],
        "source":          source,
        "question":        q,
        "answer":          answer[:300] + "…" if len(answer) > 300 else answer,
        "intent":          intent,
        "latency_s":       round(latency, 2),
        "keyword_score":   round(kw_score, 3),
        "has_citation":    has_cite,
        "refusal_correct": refused_ok,
        "retrieval_quality": round(ret_quality, 3),
        "n_chunks":        n_chunks,
        "error":           error,
    }
    results.append(row)

    # Status indicator
    ok = "✅" if kw_score >= 0.5 and (not is_oos or refused_ok) else "⚠️ "
    print(f"  {ok} keywords={kw_score:.0%}  cite={'✓' if has_cite else '✗'}  "
          f"refusal={'✓' if refused_ok else '✗'}  latency={latency:.1f}s\n")

    # Collect for RAGAS
    if not args.no_ragas and not error:
        ragas_samples.append({
            "question":   q,
            "answer":     answer,
            "contexts":   [c["text"] for c in chunks],
            "ground_truth": expected,
        })

# ── RAGAS evaluation ───────────────────────────────────────────────────────────
ragas_scores = {}
if not args.no_ragas and ragas_samples:
    logger.info("Running RAGAS evaluation…")
    print("Running RAGAS metrics (this may take a few minutes)…\n")
    try:
        from ragas import evaluate, EvaluationDataset, SingleTurnSample
        from ragas.metrics.collections import Faithfulness, ResponseRelevancy, ContextPrecision
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from langchain_anthropic import ChatAnthropic
        from langchain_huggingface import HuggingFaceEmbeddings

        llm = LangchainLLMWrapper(
            ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=1024)
        )
        embeddings = LangchainEmbeddingsWrapper(
            HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
        )

        samples = [
            SingleTurnSample(
                user_input=s["question"],
                response=s["answer"],
                retrieved_contexts=s["contexts"],
                reference=s["ground_truth"],
            )
            for s in ragas_samples
        ]
        dataset = EvaluationDataset(samples=samples)

        ragas_result = evaluate(
            dataset=dataset,
            metrics=[Faithfulness(), ResponseRelevancy(), ContextPrecision()],
            llm=llm,
            embeddings=embeddings,
        )
        ragas_scores = {
            "faithfulness":        round(float(ragas_result["faithfulness"]), 3),
            "response_relevancy":  round(float(ragas_result["response_relevancy"]), 3),
            "context_precision":   round(float(ragas_result["context_precision"]), 3),
        }
    except Exception as e:
        logger.warning(f"RAGAS failed: {e}")
        ragas_scores = {"ragas_error": str(e)}

# ── Summary report ─────────────────────────────────────────────────────────────
df = pd.DataFrame(results)

print("\n" + "═" * 70)
print("  EVALUATION SUMMARY")
print("═" * 70)

# Custom metrics summary
n       = len(df)
n_ok    = int((df["keyword_score"] >= 0.5).sum())
n_cite  = int(df["has_citation"].sum())
n_ref   = int(df["refusal_correct"].sum())
oos_df  = df[df["source"] == "Hors corpus"]
n_oos   = len(oos_df)

print(f"\n  Questions évaluées : {n}")
print(f"  Latence moyenne    : {df['latency_s'].mean():.1f}s  (max: {df['latency_s'].max():.1f}s)")
print()
print("  ── Métriques personnalisées ──────────────────────")
print(f"  Keyword hit rate    : {n_ok}/{n}  ({n_ok/n:.0%})")
print(f"  Citations présentes : {n_cite}/{n}  ({n_cite/n:.0%})")
print(f"  Refus corrects      : {n_ref}/{n}  ({n_ref/n:.0%})")
print(f"  Retrieval quality   : {df['retrieval_quality'].mean():.0%} (moyenne)")
if n_oos > 0:
    oos_ok = int(oos_df["refusal_correct"].sum())
    print(f"  Anti-hallucination  : {oos_ok}/{n_oos} questions hors-corpus refusées")

if ragas_scores and "ragas_error" not in ragas_scores:
    print()
    print("  ── RAGAS metrics ─────────────────────────────────")
    print(f"  Faithfulness        : {ragas_scores.get('faithfulness', 'N/A'):.3f}")
    print(f"  Response Relevancy  : {ragas_scores.get('response_relevancy', 'N/A'):.3f}")
    print(f"  Context Precision   : {ragas_scores.get('context_precision', 'N/A'):.3f}")
    overall = sum(ragas_scores.values()) / len(ragas_scores)
    print(f"  Score global RAGAS  : {overall:.3f}/1.0")

# Per-theme breakdown
print()
print("  ── Par thème ────────────────────────────────────")
for theme, group in df.groupby("theme"):
    kw_avg = group["keyword_score"].mean()
    bar = "█" * int(kw_avg * 10) + "░" * (10 - int(kw_avg * 10))
    print(f"  {theme:<25} {bar} {kw_avg:.0%}")

# Problematic questions
failures = df[(df["keyword_score"] < 0.4) | (df["error"].notna())]
if not failures.empty:
    print()
    print("  ── Questions problématiques ──────────────────────")
    for _, row in failures.iterrows():
        print(f"  ⚠️  [{row['id']}] {row['question'][:60]}…")
        print(f"      keyword_score={row['keyword_score']:.0%}  error={row['error']}")

print("\n" + "═" * 70 + "\n")

# ── Save results ───────────────────────────────────────────────────────────────
out_path = args.output or f"data/eval_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
df_full = pd.DataFrame(results)
if ragas_scores and "ragas_error" not in ragas_scores:
    for k, v in ragas_scores.items():
        df_full[f"ragas_{k}"] = v
df_full.to_csv(out_path, index=False)
print(f"  Results saved → {out_path}\n")
