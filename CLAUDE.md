# CLAUDE.md — SenStat: Multi-Agent Statistical Intelligence on Senegal Official Data

## Project Overview

SenStat is a RAG-powered multi-agent system that allows users to query official Senegalese
statistics published by institutional sources (ANSD, DPEE, BCEAO, ministries, etc.).
Every answer is grounded in source documents with precise citations (institution + report + page).

**Core value proposition:** ChatGPT gives you a number. SenStat gives you the official number,
with the source, the report, and the page — updated in real time.

---

## Repository Structure

```
senstat/
├── CLAUDE.md                    # This file
├── README.md
├── .env.example
├── docker-compose.yml
├── pyproject.toml
│
├── ingestion/                   # Data pipeline
│   ├── __init__.py
│   ├── scrapers/                # EMPTY (.gitkeep only) — Phase 4
│   ├── api_fetchers/            # Structured-API ingestion (no scraping)
│   │   ├── worldbank.py
│   │   ├── faostat.py
│   │   ├── ilostat.py
│   │   └── imf_weo.py
│   ├── extractors/
│   │   ├── pdf_extractor.py     # pdfplumber + Tesseract OCR fallback
│   │   └── table_extractor.py   # Tables → markdown/JSON
│   ├── chunkers/
│   │   └── text_chunker.py      # RecursiveCharacterTextSplitter
│   ├── colpali_indexer.py       # Page images → ColQwen2 → Qdrant multivector
│   └── pipeline.py              # Orchestrates full ingestion
│
├── vectorstore/
│   ├── __init__.py
│   ├── chroma_store.py          # Local ChromaDB (default)
│   └── qdrant_store.py          # Qdrant, dense + sparse (USE_QDRANT=true)
│
├── mcp_server.py                # MCP tools — a client of the HTTP API (API_URL)
│
├── agents/                      # LangGraph multi-agent system
│   ├── __init__.py
│   ├── graph.py                 # LangGraph StateGraph definition
│   ├── state.py                 # AgentState TypedDict
│   ├── router_agent.py          # Intent classification → route to agents
│   ├── retrieval_agent.py       # Hybrid search (dense + BM25) + reranking
│   ├── trend_agent.py           # Time series extraction + TCAM + statsmodels
│   ├── compare_agent.py         # Geographic/sectoral comparisons
│   ├── compute_agent.py         # Python sandbox for statistical calculations
│   ├── viz_agent.py             # Plotly charts with source watermark
│   └── synthesis_agent.py       # Assembles final response with citations
│
├── api/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app
│   ├── routes/
│   │   ├── query.py             # POST /query
│   │   ├── documents.py         # GET /documents (list indexed sources)
│   │   └── health.py            # GET /health
│   └── schemas.py               # Pydantic models
│
├── frontend/
│   ├── app.py                   # Streamlit app
│   ├── components/
│   │   ├── chat.py              # Chat interface
│   │   ├── sources.py           # Source citations panel
│   │   └── charts.py            # Chart rendering
│   └── static/
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_{router,retrieval,trend,compare,compute,viz,synthesis}_agent.py
│   │   ├── test_api.py          # Routes + CORS, graph and store faked
│   │   └── test_extractors.py   # OCR fallback decision table (Tesseract mocked)
│   └── integration/
│       ├── test_query_e2e.py    # Full graph; needs a real API key + indexed Chroma
│       └── test_ocr_pipeline.py # OCR against a real Tesseract
│
├── data/
│   ├── raw/                     # Downloaded PDFs (gitignored)
│   ├── processed/               # Extracted text/tables
│   └── sources.json             # Registry of official sources + URLs
│
├── scripts/
│   ├── ingest_all.py            # Full ingestion run
│   ├── ingest_source.py         # Ingest single source
│   └── eval_retrieval.py        # Retrieval quality evaluation
│
└── notebooks/
    ├── 01_pdf_extraction_poc.ipynb
    ├── 02_chunking_strategy.ipynb
    ├── 03_retrieval_eval.ipynb
    └── 04_agent_traces.ipynb
```

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| PDF extraction | `PyMuPDF` + `pdfplumber` | pdfplumber for tables, PyMuPDF for text |
| OCR | `pytesseract` + `pdf2image` | Fallback in `pdf_extractor.py`; needs `tesseract`, `fra` langdata, `poppler` |
| Table extraction | `camelot-py` | Lattice mode for bordered tables |
| Chunking | `langchain-text-splitters` | RecursiveCharacterTextSplitter, 512 tokens, 64 overlap |
| Embeddings | `intfloat/multilingual-e5-large` | Both stores by default; Qdrant can opt into `voyage-3-large` (`QDRANT_DENSE_EMBEDDER=voyage`) |
| Vector store | `chromadb` (dev) → `qdrant-client` (prod) | Filter by metadata |
| Sparse search | `rank_bm25` | Hybrid retrieval |
| Reranking | Cohere `rerank-v3.5` or `cross-encoder/ms-marco-MiniLM-L-6-v2` | Cohere when `USE_COHERE_RERANK=true`, else CrossEncoder |
| Visual retrieval | `colpali` / ColQwen2 → Qdrant multivector | Optional, `USE_COLPALI=true` |
| LLM | `anthropic` SDK | Synthesis: `claude-sonnet-4-6`. Router + all specialists: `claude-haiku-4-5-20251001` |
| Agent framework | `langgraph` | StateGraph, Send API for parallel agents |
| Statistical compute | `pandas` + `statsmodels` + `scipy` | Trend agent, compute agent |
| Visualization | `plotly` | Interactive charts, source watermark |
| API | `fastapi` + `uvicorn` | Async |
| Frontend | `streamlit` | Rapid proto, v2 → React |
| Containerization | `docker` + `docker-compose` | |
| CI/CD | `github-actions` | `ci.yml`: lint → unit tests (70% coverage gate) → Docker build. No deploy job |

---

## Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...
CHROMA_PERSIST_DIR=./data/chroma
QDRANT_URL=https://...qdrant.io
QDRANT_API_KEY=...
QDRANT_COLLECTION=senstat
EMBEDDING_MODEL=intfloat/multilingual-e5-large
EMBEDDING_DEVICE=cpu

# Backend toggles — all default to false (ChromaDB + CrossEncoder path)
USE_QDRANT=false
USE_COLPALI=false
USE_COHERE_RERANK=false
QDRANT_PATH=
QDRANT_COLPALI_COLLECTION=senstat_visual
COLPALI_TOP_K=3
COHERE_API_KEY=
QDRANT_DENSE_EMBEDDER=local    # local = EMBEDDING_MODEL; voyage = voyage-3-large (paid)
VOYAGE_API_KEY=
API_URL=http://localhost:8000
DATA_RAW_DIR=./data/raw
DATA_PROCESSED_DIR=./data/processed
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

---

## Agent System — LangGraph Design

### State
```python
class AgentState(TypedDict):
    query: str
    intent: str                          # lookup | trend | compare | compute | viz | compare_viz | mixed
    retrieved_chunks: List[dict]
    trend_output: Optional[dict]
    compare_output: Optional[dict]
    compute_output: Optional[dict]
    viz_output: Optional[dict]
    synthesis: str
    citations: List[dict]
    messages: Annotated[List[BaseMessage], operator.add]
    conversation_history: List[dict]     # [{"role": "user"|"assistant", "content": str}]
```

### Graph topology
```
query_rewriter → router → [prep_viz] → retrieval → fan-out by intent
                                                    ├── trend   → [viz] → synthesis
                                                    ├── compare → [viz] → synthesis
                                                    ├── compute →         synthesis
                                                    └── (lookup)          synthesis
```
`mixed` fans out to trend + compare in parallel via the Send API. The router
returns a *list* of intents; `viz` is a modifier collapsed onto the data path,
which is what produces `compare_viz`. `prep_viz` strips visualization keywords
from the query so retrieval fetches data chunks rather than matching on the word
"graphique".

### Retrieval Strategy
1. Dense retrieval (semantic) via ChromaDB
2. Sparse retrieval (BM25 keyword) over the whole corpus, not just the dense
   hits — Chroma path only; Qdrant fuses dense + BM42 sparse natively.
   A Qdrant collection records the model that embedded it and the store refuses
   to start against a mismatch, since e5-large and voyage-3-large are both
   1024-d and a mismatch would return wrong results silently.
3. Reciprocal Rank Fusion
4. Optional ColPali visual page refs merged into the candidate pool
5. Reranking — Cohere `rerank-v3.5`, or CrossEncoder with `CE_THRESHOLD` to drop
   off-topic chunks
6. Top-k with metadata filter

### Citation Format
Every statistic cited as: `[ANSD — EHCVM 2021, p.47]`

---

## Key Implementation Notes

### PDF Quality Issues (ANSD-specific)
Text extraction first, OCR as fallback — but **OCR output is kept only when it
recovers more characters than pdfplumber did.** On partially-extracted pages
(charts, tables) Tesseract typically returns *less* than pdfplumber, and an
earlier unconditional overwrite was destroying valid text on 6 of 8 sampled
pages in `SES_2022_2023.pdf`.

Measured 2026-09-17: the corpus currently in `data/raw/` is **not scanned**.
All 5 PDFs yield extractable text; the 55 blank pages in `Rapport-def-RGPH-5.pdf`
contain no images at all. Re-measure before assuming OCR is worth tuning — check
`page.images` on empty pages, not just character counts.

Pages recovered by OCR carry `ocr: true` in their chunk metadata.

### Methodology Change Detection
```python
METHODOLOGY_BREAKS = {
    "pauvreté": {"year": 2018, "note": "Révision seuil pauvreté ANSD (EHCVM). ESPS non comparable."},
    "PIB": {"year": 2014, "note": "Rebasing PIB 2014 par DPEE. Base 2014 = 100."}
}
```

### Compute Agent Sandbox
LLM-generated code runs in two layers, and both must be defeated to reach the OS:

1. **AST validation** (`_validate_ast`): imports limited to `math`/`statistics`;
   reflection builtins refused (`getattr`, `type`, `dir`, …); **every dunder
   attribute, any string literal containing a dunder, and `str.format`/
   `format_map` refused**. A builtin-name blocklist alone was bypassed
   (2026-10-08): code walked the object graph through dunder attributes to `os`
   without naming any forbidden builtin.
2. **Restricted runtime**: a fixed runner reads the code on stdin (never spliced
   into source) and `exec`s it with `__builtins__` = an allowlist plus an
   `__import__` that only returns `math`/`statistics`; RLIMIT_AS 512 MB and
   RLIMIT_CPU 5 s in the child (RLIMIT_AS is not enforced on macOS).

Not isolated: the child still runs as the API user, with its filesystem and
network. A separate user / nsjail / no-network container is the next step if the
corpus ever ingests untrusted documents — chunk text reaches the code prompt.

---

## Development Phases

### Phase 1 — Foundation ✓ (Complete)
- [x] Repo setup, pyproject.toml, Dockerfile, docker-compose
- [x] PDF extraction pipeline (`pdf_extractor.py`, `table_extractor.py`)
- [x] ChromaDB setup (`chroma_store.py`)
- [x] Ingestion pipeline (`pipeline.py`) — 26 sources registered in
      `data/sources.json` across 16 institutions; 12 indexed, 13 pending,
      1 excluded (as of 2026-09-17)
- [x] Basic retrieval agent + FastAPI `/query` endpoint
- [x] Streamlit MVP — two frontends: public (`frontend_public/`) + pro (`frontend/`)
- [x] Bilingual public frontend (FR/EN) with theme cards, FAQ, search
- [x] OCR fallback — implemented inline in `pdf_extractor.py::_ocr_page`, not a
      separate `ocr_extractor.py`. Tesseract + `fra` + poppler required.
- [ ] Table chunker (`table_chunker.py` — not yet implemented)
- [ ] Scrapers (`ingestion/scrapers/` — empty, only `.gitkeep`). API fetchers
      exist instead under `ingestion/api_fetchers/` (World Bank, FAOSTAT,
      ILOSTAT, IMF WEO).

### Phase 2 — Multi-Agent ✓ (Complete)
- [x] LangGraph `StateGraph`: router → retrieval → [trend|compare] → synthesis
- [x] Hybrid search: dense (ChromaDB) + BM25 + Reciprocal Rank Fusion
- [x] CrossEncoder reranking (`ms-marco-MiniLM-L-6-v2`, top 20 → top 8)
- [x] Trend agent: time-series extraction, CAGR, trend direction (Haiku)
- [x] Compare agent: entity extraction, gap calculation, insight (Haiku)
- [x] Conditional graph routing: intent → correct specialist agent
- [x] Citation formatter: deduped by (institution, report_name), rendered as pills
- [x] Inline citation stripping (prompt rule + regex safety net in API)
- [x] RAGAS evaluation pipeline + golden dataset (20 questions, 6 themes)

### Phase 3 — Advanced Agents ✓ (Complete)
- [x] Compute agent — `subprocess` sandbox, Haiku, timeout 8s
- [x] Viz agent — Plotly trend/compare charts with source watermark
- [x] Parallel agent execution — Send API fan-out on `mixed` intent
- [x] Router cost optimisation — router and every specialist now run Haiku 4.5;
      only synthesis uses Sonnet
- [x] Qdrant store (`qdrant_store.py`) — dense + sparse native fusion, gated by
      `USE_QDRANT` (defaults to ChromaDB)
- [x] Query rewriter node — resolves follow-up questions against history
- [x] ColPali visual indexing (`colpali_indexer.py`) — gated by `USE_COLPALI`
- [x] Cohere `rerank-v3.5` — gated by `USE_COHERE_RERANK`, CrossEncoder fallback
- [x] Unit + integration tests — every agent has a unit test file, plus
      FastAPI routes, ingestion/OCR and a full-graph e2e test. Unit coverage
      of `agents` + `api`: 78% (2026-10-08)

### Phase 4 — Production
- [ ] GitHub Actions CI/CD — `ci.yml` exists (lint, unit tests, Docker build)
      and all three jobs passed on GitHub for the first time on 2026-10-08
      (run 37794741477, commit 113bc04). A `deploy-staging` job exists but is
      skipped until `STAGING_DEPLOY_ENABLED=true` (setup in `DEPLOY.md`)
- [ ] Docker hardening: health checks on frontend services. Non-root user
      added 2026-10-09 (UID 10001, model cache moved to the `hf_cache`
      volume); not yet run on staging, which needs `data/chroma` chowned to
      10001 — `deploy_ci.sh` does it, a manual deploy must too
- [ ] Re-run RAGAS eval after Phase 3 agents to get updated baseline scores
- [ ] Frontend v2 (React) — replaces Streamlit, Phase 4 target per roadmap
- [ ] Scrapers: automate PDF fetching from ANSD, DPEE, BCEAO (World Bank,
      FAOSTAT, ILOSTAT and IMF WEO already covered by `api_fetchers/`)

---

## Known Gaps (verified against code 2026-09-17)

| Gap | Impact | Fix in |
|---|---|---|
| Local `data/chroma` disagrees with `sources.json` (measured 2026-10-08: 1,887 chunks in 4 sources). 11 sources marked `indexed` have 0 chunks; `ehcvm_2021` and `ses_2022_2023` are marked `pending` but indexed; `rgph5_preliminaire` is `excluded` yet still has 109 chunks | Registry status is not evidence of what is searchable; superseded census figures can be cited. Staging's index (7,571 chunks per README) is a different copy | Re-index |
| No scrapers → manual PDF ingestion only | Stale data risk | Phase 4 |
| `table_chunker.py` missing → tables chunked as one blob | Large tables may exceed useful chunk size | Phase 4 |
| RAGAS eval last run 2026-05-05, pre-dates compute/viz/ColPali | Eval scores don't reflect current pipeline | Re-run |
| Qdrant + ColPali + Cohere rerank off by default | Prod path is exercised less than the Chroma path | Phase 4 |
| e5-large is used without its `query:` / `passage:` prefixes, in both stores | Below the model's documented retrieval quality; fixing it means re-embedding the whole index | Re-index |
| `scripts/eval_retrieval.py` scores source precision on the first word of `report_name` | Every SES chunk counts as off-target; use `eval_retrieval_only.py`, which scores on `source_id` | Fix |

### Corrected claims

Entries previously listed here that no longer hold, kept so they are not
re-added from memory:

- **"Zero tests" / "`tests/` holds only `__init__.py`"** — false. Agent unit
  tests and `ci.yml` landed on remote `stg` on 2026-05-19; the local `stg`
  had diverged and never pulled them, which is how this claim survived (and
  was briefly re-asserted on 2026-10-08). Check `git status -sb` against the
  remote before declaring something missing.
- **"OCR fallback missing"** — false. OCR has always been wired into
  `extract_text_from_pdf`. Separately, measured 2026-09-17: the current corpus
  (5 PDFs, 962 pages) contains **no scanned content** — every document yields
  extractable text, and the 55 blank pages in `Rapport-def-RGPH-5.pdf` hold no
  images. OCR gains here are marginal; do not prioritise OCR quality work on
  recall grounds until genuinely scanned sources are ingested.
- **"Router uses Sonnet"** — false. Router and all specialists run Haiku 4.5.
- **"`compute`/`viz` fall through to synthesis"** — false. Both are wired in
  `graph.py` with dedicated nodes.
