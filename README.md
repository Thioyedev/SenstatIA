# SenstatIA — Intelligence Statistique Multi-Agents sur le Sénégal

> **ChatGPT vous donne un chiffre. SenStat vous donne le chiffre officiel, avec la source, le rapport et la page.**

Système RAG multi-agents permettant d'interroger en langage naturel les statistiques officielles du Sénégal (ANSD, DPEE, BCEAO, IMF, World Bank…). Chaque réponse est ancrée dans les documents sources avec des citations précises : `[ANSD — EHCVM 2021-2022, p.32]`.

**Branche :** `dev` — environnement de développement local

---

## État actuel

| Métrique | Valeur |
|---|---|
| Chunks indexés | **7 571** |
| Sources actives | **10 / 25** |
| Phase complétée | **Phase 2 — Multi-Agents** |
| Keyword Hit Rate | 100 % (20/20) |
| Score global RAGAS | 0.648 / 1.0 |
| Latence moyenne | 10.3 s |

---

## Architecture

```
Utilisateur
    │
    ▼
FastAPI :8000  ──────────────────────────────────────
    │  asyncio.to_thread
    ▼
LangGraph StateGraph
    │
    ├─► Router Agent (Haiku)        → classifie l'intent
    ├─► Retrieval Agent             → dense + BM25 + RRF + CrossEncoder
    ├─► Trend Agent (Haiku)         → séries temporelles, TCAM
    ├─► Compare Agent (Haiku)       → comparaisons entités / géo
    ├─► Compute Agent               → calculs Python sandboxé
    ├─► Viz Agent                   → graphiques Plotly
    └─► Synthesis Agent (Sonnet)    → réponse finale + citations

ChromaDB (local)     ←── embeddings multilingual-e5-large (1024 dim)
Qdrant (optionnel)   ←── USE_QDRANT=true
Anthropic Claude API ←── Haiku (routing) + Sonnet (synthesis)
```

Flux complet : `router → retrieval → [trend|compare|compute|viz] → synthesis`

**Intents supportés :** `lookup` · `trend` · `compare` · `compute` · `viz` · `compare_viz` · `mixed`

---

## Stack technique

| Couche | Technologie |
|---|---|
| LLM | `claude-haiku-4-5` (routing) · `claude-sonnet-4-20250514` (synthesis) |
| Agents | `langgraph` StateGraph + Send API |
| Embeddings | `intfloat/multilingual-e5-large` (HuggingFace) |
| Vector store | `chromadb` (dev) · `qdrant-client` (prod, `USE_QDRANT=true`) |
| Retrieval | Dense + BM25 + RRF + CrossEncoder `ms-marco-MiniLM-L-6-v2` |
| Reranking optionnel | Cohere `rerank-v3.5` (`USE_COHERE_RERANK=true`) |
| Visual retrieval | ColQwen2 / ColPali (`USE_COLPALI=true`) |
| API | `fastapi` + `uvicorn` |
| Frontend Pro | `streamlit` :8502 |
| Frontend Public | `streamlit` :8501 |
| MCP Server | `fastmcp` (stdio) |
| Visualisation | `plotly` |
| Proxy | `nginx:alpine` |
| Containerisation | `docker` + `docker-compose` |

---

## Installation locale

### Prérequis

- Python 3.11+
- `brew install poppler tesseract` (macOS) — requis par pdf2image et OCR
- Clé API Anthropic

### Setup

```bash
git clone https://github.com/SenStat/SenstatIA.git
cd SenstatIA
git checkout dev

python -m venv venv && source venv/bin/activate
pip install -e .

cp .env.example .env
# Renseigner ANTHROPIC_API_KEY au minimum
```

### Variables d'environnement clés

```env
ANTHROPIC_API_KEY=sk-ant-...
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_MODEL=intfloat/multilingual-e5-large
EMBEDDING_DEVICE=cpu

# Feature flags
USE_QDRANT=false
USE_COHERE_RERANK=false
USE_COLPALI=false
```

### Lancer en local

```bash
# API
uvicorn api.main:app --reload --port 8000

# Frontend Public (autre terminal)
streamlit run "frontend_public/🏠_Accueil.py" --server.port 8501

# Frontend Pro (autre terminal)
streamlit run "frontend/🏠_Accueil.py" --server.port 8502
```

Ou via Docker :

```bash
docker compose up --build
```

| URL | Interface |
|---|---|
| http://localhost:8501 | Grand Public |
| http://localhost:8502 | Interface Pro |
| http://localhost:8000/health | Santé API |
| http://localhost:8000/docs | OpenAPI |

---

## Ingestion des données

```bash
# Ingérer toutes les sources en attente
python ingestion/pipeline.py

# Ingérer une source précise
python ingestion/pipeline.py --id rgph5_2023

# Forcer la ré-ingestion
python ingestion/pipeline.py --force

# Dry run (affiche le plan sans écrire)
python ingestion/pipeline.py --dry-run
```

Les sources sont déclarées dans `data/sources.json` (25 sources, 10 indexées).

---

## Évaluation

```bash
# Pipeline complet (custom metrics + RAGAS)
python scripts/eval_retrieval.py

# Sans RAGAS (plus rapide)
python scripts/eval_retrieval.py --no-ragas

# Filtrer par thème
python scripts/eval_retrieval.py --theme pauvreté

# Limiter à N questions
python scripts/eval_retrieval.py --n 5
```

**Golden dataset :** 20 questions, 6 thèmes, incluant 2 questions anti-hallucination.

---

## MCP Server

Expose SenstatIA comme outil natif pour Claude Desktop / Claude Code :

```bash
python mcp_server.py
```

**Outils exposés :** `senstat_query` · `senstat_list_sources` · `senstat_get_intent`

Config Claude Desktop : voir `ARCHITECTURE.md §9`.

---

## Git Branching

```
feature/* ──┐
fix/*       ├──► dev ──► stg ──► main
docs/*      │
chore/*   ──┘

hotfix/* ──► main ──► (backport) ──► dev
```

Voir `CLAUDE.md` pour les règles complètes de merge et de nommage.

---

## Questions de test

```
"Quel est le taux de pauvreté au Sénégal en 2021 ?"
"Comment a évolué le PIB depuis 2015 ?"
"Compare le taux de chômage entre Dakar et Ziguinchor."
"Prévois le PIB à 5 ans avec un TCAM de 6 %."
"Montre l'évolution de la population par région."
"Quel est le taux de criminalité ?"   ← doit refuser (hors corpus)
```

---

## Documentation

| Fichier | Contenu |
|---|---|
| `ARCHITECTURE.md` | Architecture complète, agents, retrieval, API, infra |
| `CLAUDE.md` | Guide développeur, git branching, phases |
| `DEPLOY.md` | Déploiement Hetzner pas à pas |
| `SETUP.md` | Setup détaillé |

---

## Licence

MIT — Données issues de sources officielles publiques (ANSD, DPEE, BCEAO, IMF, World Bank).

*Phase 2 complétée · Phase 3 en cours · Mai 2026*
