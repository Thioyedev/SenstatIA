"""Run RAGAS metrics on previously saved eval CSV."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

import json

import pandas as pd
from langchain_anthropic import ChatAnthropic
from langchain_huggingface import HuggingFaceEmbeddings
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_relevancy, context_precision, faithfulness

from vectorstore.chroma_store import ChromaStore

with open("data/golden_dataset.json") as f:
    golden = json.load(f)

df = pd.read_csv(sorted(Path("data").glob("eval_*.csv"))[-1])
store = ChromaStore()

llm = LangchainLLMWrapper(ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=1024))
emb = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large"))

print("Building RAGAS samples…")
samples = []
for item in golden:
    row = df[df["id"] == item["id"]]
    if row.empty:
        continue
    answer = row["answer"].values[0]
    chunks = store.search(item["question"], n_results=8)
    contexts = [c["text"] for c in chunks]
    samples.append(
        SingleTurnSample(
            user_input=item["question"],
            response=answer,
            retrieved_contexts=contexts,
            reference=item["ground_truth"],
        )
    )

print(f"Evaluating {len(samples)} samples…\n")
dataset = EvaluationDataset(samples=samples)
result = evaluate(
    dataset=dataset,
    metrics=[faithfulness, answer_relevancy, context_precision],
    llm=llm,
    embeddings=emb,
)

import numpy as np


def safe_score(val) -> float:
    if isinstance(val, (int, float)):
        return float(val)
    arr = [v for v in val if v is not None and not (isinstance(v, float) and np.isnan(v))]
    return float(np.mean(arr)) if arr else float("nan")


faith = safe_score(result["faithfulness"])
relev = safe_score(result["answer_relevancy"])
prec = safe_score(result["context_precision"])
scores = [s for s in [faith, relev, prec] if not np.isnan(s)]
overall = float(np.mean(scores)) if scores else float("nan")

print("\n══════════════════════════════════════════════")
print("  RAGAS EVALUATION — SenStat RAG Pipeline")
print("══════════════════════════════════════════════")
print(f"  Faithfulness        : {faith:.3f} / 1.0")
print("    → Les réponses restent dans les chunks récupérés")
print(f"  Answer Relevancy    : {relev:.3f} / 1.0")
print("    → Les réponses adressent bien les questions posées")
print(f"  Context Precision   : {prec:.3f} / 1.0")
print("    → Les chunks récupérés sont pertinents")
print("  ──────────────────────────────────────────")
print(
    f"  Score global RAGAS  : {overall:.3f} / 1.0  "
    f"({'🟢 Excellent' if overall >= 0.8 else '🟡 Bon' if overall >= 0.6 else '🔴 À améliorer'})"
)
print("══════════════════════════════════════════════\n")
