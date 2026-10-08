"""Retrieval-only evaluation on the golden dataset — no LLM calls, no API cost.

Runs agents.retrieval_agent alone on each in-corpus golden question and reports:

- keyword recall: share of the question's expected_keywords found in the text of
  the retrieved chunks, i.e. whether the fact the answer needs was retrieved;
- source precision: share of retrieved chunks whose source_id belongs to the
  question's expected source. (eval_retrieval.py matches the first word of the
  source on report_name instead, which scores every SES chunk as off-target:
  its report_name is "Situation Économique et Sociale ...".)

"Multi-sources" and "Hors corpus" questions are skipped: neither metric applies.
Scores depend on the index in CHROMA_PERSIST_DIR; compare runs on the same index.

Usage:
    python scripts/eval_retrieval_only.py
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from agents.retrieval_agent import retrieval_agent

logger.remove()

SKIP = {"Multi-sources", "Hors corpus"}

# Golden "source" label → source_ids that count as on-target. The census
# questions accept the preliminary report while the final one is not indexed.
EXPECTED_SOURCE_IDS = {
    "EHCVM 2021-2022": {"ehcvm_2021"},
    "SES 2022-2023": {"ses_2022_2023"},
    "RGPH-5 2023": {"rgph5_2023", "rgph5_preliminaire"},
    "RGPH-5 Économie 2024": {"rgph5_economie"},
}


def main() -> None:
    golden = json.loads(Path("data/golden_dataset.json").read_text())
    rows = []
    for q in golden:
        if q["source"] in SKIP:
            continue
        chunks = retrieval_agent({"query": q["question"]})["retrieved_chunks"]
        text = " ".join(c["text"] for c in chunks).lower()
        keywords = q["expected_keywords"]
        recall = sum(kw.lower() in text for kw in keywords) / len(keywords)
        expected = EXPECTED_SOURCE_IDS[q["source"]]
        on_target = sum(c.get("source_id") in expected for c in chunks)
        precision = on_target / len(chunks) if chunks else 0.0
        rows.append((q["id"], recall, precision, len(chunks)))
        print(f"{q['id']:>6}  recall={recall:.2f}  precision={precision:.2f}  n={len(chunks)}")

    n = len(rows)
    print(f"\n{n} questions")
    print(f"mean keyword recall   {sum(r[1] for r in rows) / n:.3f}")
    print(f"mean source precision {sum(r[2] for r in rows) / n:.3f}")
    print(f"full keyword recall   {sum(r[1] == 1.0 for r in rows)}/{n}")


if __name__ == "__main__":
    main()
