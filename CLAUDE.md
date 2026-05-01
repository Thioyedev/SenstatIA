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
│   ├── scrapers/
│   │   ├── ansd_scraper.py      # Scrape ansd.sn publications
│   │   ├── dpee_scraper.py      # Bulletins mensuel DPEE
│   │   ├── bceao_scraper.py     # Rapports BCEAO
│   │   └── worldbank_scraper.py # World Bank API (country=SN)
│   ├── extractors/
│   │   ├── pdf_extractor.py     # PyMuPDF + pdfplumber
│   │   ├── table_extractor.py   # Tables → markdown/JSON
│   │   └── ocr_extractor.py     # Tesseract for scanned PDFs
│   ├── chunkers/
│   │   ├── text_chunker.py      # RecursiveCharacterTextSplitter
│   │   └── table_chunker.py     # Preserve table structure in chunks
│   ├── embedder.py              # multilingual-e5-large embeddings
│   └── pipeline.py              # Orchestrates full ingestion
│
├── vectorstore/
│   ├── __init__.py
│   ├── chroma_store.py          # Local ChromaDB
│   ├── qdrant_store.py          # Qdrant Cloud (prod)
│   └── schemas.py               # Document metadata schemas
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
│   ├── unit/
│   │   ├── test_extractors.py
│   │   ├── test_chunkers.py
│   │   └── test_agents.py
│   └── integration/
│       ├── test_pipeline.py
│       └── test_query_e2e.py
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
| OCR | `pytesseract` + `pdf2image` | For scanned ANSD reports |
| Table extraction | `camelot-py` | Lattice mode for bordered tables |
| Chunking | `langchain-text-splitters` | RecursiveCharacterTextSplitter, 512 tokens, 64 overlap |
| Embeddings | `intfloat/multilingual-e5-large` | HuggingFace, French support |
| Vector store | `chromadb` (dev) → `qdrant-client` (prod) | Filter by metadata |
| Sparse search | `rank_bm25` | Hybrid retrieval |
| Reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` | After hybrid fusion |
| LLM | `anthropic` SDK — `claude-sonnet-4-20250514` | Citations + statistical reasoning |
| Agent framework | `langgraph` | StateGraph, Send API for parallel agents |
| Statistical compute | `pandas` + `statsmodels` + `scipy` | Trend agent, compute agent |
| Visualization | `plotly` | Interactive charts, source watermark |
| API | `fastapi` + `uvicorn` | Async |
| Frontend | `streamlit` | Rapid proto, v2 → React |
| Containerization | `docker` + `docker-compose` | |
| CI/CD | `github-actions` | Lint → test → build → deploy |

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
    intent: str                          # lookup | trend | compare | compute | viz | mixed
    retrieved_chunks: List[dict]
    trend_output: Optional[dict]
    compare_output: Optional[dict]
    compute_output: Optional[dict]
    viz_output: Optional[dict]
    synthesis: str
    citations: List[dict]
    messages: Annotated[List[BaseMessage], operator.add]
```

### Retrieval Strategy
1. Dense retrieval (semantic) via ChromaDB
2. Sparse retrieval (BM25 keyword)
3. Reciprocal Rank Fusion
4. CrossEncoder reranking
5. Top-k with metadata filter

### Citation Format
Every statistic cited as: `[ANSD — EHCVM 2021, p.47]`

---

## Key Implementation Notes

### PDF Quality Issues (ANSD-specific)
Many ANSD PDFs are scanned — always try text extraction first, OCR as fallback.

### Methodology Change Detection
```python
METHODOLOGY_BREAKS = {
    "pauvreté": {"year": 2018, "note": "Révision seuil pauvreté ANSD (EHCVM). ESPS non comparable."},
    "PIB": {"year": 2014, "note": "Rebasing PIB 2014 par DPEE. Base 2014 = 100."}
}
```

### Compute Agent Sandbox
Use `subprocess` with timeout, never raw `exec()`.

---

## Development Phases

### Phase 1 — Foundation ✓ (Week 1-2)
- [x] Repo setup, pyproject.toml
- [x] PDF extraction pipeline
- [x] ChromaDB setup
- [x] Ingestion pipeline
- [ ] Basic retrieval agent
- [ ] FastAPI endpoint `/query`
- [ ] Streamlit MVP

### Phase 2 — Multi-Agent (Week 3-4)
- [ ] LangGraph graph: router + retrieval + synthesis
- [ ] Hybrid search (BM25 + dense) + CrossEncoder reranking
- [ ] Trend agent, Compare agent
- [ ] Citation formatter

### Phase 3 — Advanced Agents (Week 5-6)
- [ ] Compute agent (Python sandbox)
- [ ] Viz agent (Plotly + source watermark)
- [ ] Parallel agent execution via Send API
- [ ] Qdrant migration

### Phase 4 — Production (Week 7-8)
- [ ] GitHub Actions CI/CD
- [ ] Docker deployment
- [ ] RAGAS evaluation
- [ ] Frontend v2 (React)
