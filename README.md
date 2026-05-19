# SenStat — Intelligence Statistique Multi-Agents sur le Sénégal

> **ChatGPT vous donne un chiffre. SenStat vous donne le chiffre officiel, avec la source, le rapport et la page.**

SenStat est un système RAG multi-agents permettant d'interroger en langage naturel les statistiques officielles du Sénégal publiées par l'ANSD, la DPEE, la BCEAO et d'autres institutions. Chaque réponse est ancrée dans les documents sources avec des citations précises : `[ANSD — EHCVM 2021-2022, p.32]`.

---

## Résultats d'évaluation

Évaluation sur 20 questions issues du golden dataset :

| Métrique | Score |
|---|---|
| Keyword Hit Rate | **100%** (20/20) |
| Citations présentes | **95%** (19/20) |
| Anti-hallucination (hors corpus) | **100%** (2/2) |
| Latence moyenne bout en bout | **10.3 s** |
| Faithfulness (RAGAS) | **0.753 / 1.0** |
| Answer Relevancy (RAGAS) | **0.679 / 1.0** |
| Context Precision (RAGAS) | **0.513 / 1.0** |
| **Score global RAGAS** | **0.648 / 1.0 — 🟡 Bon** |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE D'INGESTION                        │
│                                                                 │
│   PDFs ANSD ──► Extraction ──► Chunking ──► ChromaDB           │
│   (4 rapports)  (pdfplumber   (512 tokens,  (1 887 chunks)     │
│                  + OCR)        64 overlap)                      │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LANGGRAPH MULTI-AGENTS                        │
│                                                                 │
│   Question utilisateur                                          │
│          │                                                      │
│          ▼                                                      │
│   ┌──────────────┐   intent    ┌─────────────────┐             │
│   │ Router Agent │ ──────────► │ Retrieval Agent │             │
│   │ (intent      │             │ Dense + BM25    │             │
│   │  classifier) │             │ + RRF fusion    │             │
│   └──────────────┘             └────────┬────────┘             │
│   claude-sonnet-4-6                     │ top-8 chunks          │
│                                         ▼                       │
│                                ┌─────────────────┐             │
│                                │ Synthesis Agent │             │
│                                │ + Citations     │             │
│                                └─────────────────┘             │
│                                claude-sonnet-4-6               │
└─────────────────────────────────────────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
   ┌──────────────┐   ┌─────────────┐   ┌──────────────────┐
   │  FastAPI     │   │ Frontend    │   │ Frontend         │
   │  REST API    │   │ Pro         │   │ Grand Public     │
   │  :8000       │   │ :8501       │   │ :8502            │
   └──────────────┘   └─────────────┘   └──────────────────┘
```

---

## Sources indexées (1 887 chunks)

| Source | Institution | Année | Thèmes couverts |
|---|---|---|---|
| RGPH-5 Rapport Préliminaire | ANSD | 2023 | Population, démographie, régions, ménages |
| RGPH-5 Économie | ANSD | 2024 | Emploi, chômage, secteurs d'activité |
| EHCVM 2021-2022 | ANSD | 2022 | Pauvreté monétaire, conditions de vie, inégalités |
| SES 2022-2023 | ANSD / DPEE | 2023 | PIB, éducation, santé, agriculture, eau, électricité |

---

## Stack technique

| Couche | Technologie | Détails |
|---|---|---|
| Extraction PDF | `pdfplumber` + `PyMuPDF` | pdfplumber pour les tableaux, PyMuPDF pour le texte |
| OCR | `pytesseract` + `pdf2image` | Fallback automatique si texte < 200 car/page |
| Extraction tableaux | `camelot-py` | Mode lattice pour tableaux avec bordures |
| Chunking | `langchain-text-splitters` | RecursiveCharacterTextSplitter, 512 tokens, 64 overlap |
| Embeddings | `intfloat/multilingual-e5-large` | HuggingFace, 768 dimensions, support français natif |
| Vector store | `chromadb` | PersistentClient SQLite (dev) → Qdrant Cloud (prod) |
| Sparse search | `rank-bm25` | BM25 sur les candidats denses |
| Fusion retrieval | Reciprocal Rank Fusion | Combine dense + sparse sans reranker externe |
| LLM | `claude-sonnet-4-6` | Router + synthèse avec citations |
| Agents | `langgraph` | StateGraph, orchestration multi-agents |
| Calcul statistique | `pandas` + `statsmodels` | Trend agent, compute agent |
| Visualisation | `plotly` | Graphiques interactifs |
| API | `fastapi` + `uvicorn` | Async, CORS, OpenAPI auto-généré |
| Frontend Pro | `streamlit` | Interface technique, port 8501 |
| Frontend Public | `streamlit` | Interface citoyenne, port 8502 |
| Évaluation | `ragas` | Faithfulness, Answer Relevancy, Context Precision |
| Logs | `loguru` | Structured logging |

---

## Installation

### Prérequis

- Python 3.11+
- [poppler](https://poppler.freedesktop.org/) : `brew install poppler` (macOS) — requis par pdf2image
- [tesseract](https://github.com/tesseract-ocr/tesseract) : `brew install tesseract` (macOS) — requis pour l'OCR
- Une clé API Anthropic (`ANTHROPIC_API_KEY`)

### 1. Cloner le dépôt

```bash
git clone https://github.com/YOUR_ORG/senstat.git
cd senstat
```

### 2. Créer l'environnement virtuel

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. Installer les dépendances

```bash
pip install -e .
```

### 4. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Éditez `.env` :

```env
ANTHROPIC_API_KEY=sk-ant-...

# Vector store
CHROMA_PERSIST_DIR=./data/chroma

# Embeddings
EMBEDDING_MODEL=intfloat/multilingual-e5-large
EMBEDDING_DEVICE=cpu

# Données
DATA_RAW_DIR=./data/raw
DATA_PROCESSED_DIR=./data/processed

# API
API_HOST=0.0.0.0
API_PORT=8000

LOG_LEVEL=INFO
```

### 5. Télécharger les PDFs sources

Téléchargez les rapports officiels ANSD depuis [ansd.sn](https://www.ansd.sn) et placez-les dans `data/raw/` :

```
data/raw/
├── rgph5_preliminaire.pdf      # RGPH-5 Rapport Préliminaire 2023
├── rgph5_economie.pdf          # RGPH-5 Économie 2024
├── ehcvm_2021.pdf              # EHCVM 2021-2022
└── ses_2022_2023.pdf           # SES 2022-2023
```

### 6. Lancer l'ingestion

```bash
python -m ingestion.pipeline
```

Sortie attendue :
```
✓ rgph5_preliminaire  → XXX chunks ingested
✓ rgph5_economie      → XXX chunks ingested
✓ ehcvm_2021          → XXX chunks ingested
✓ ses_2022_2023       → XXX chunks ingested
Total : 1 887 chunks indexés dans ChromaDB
```

---

## Lancer l'application

### API FastAPI

```bash
uvicorn api.main:app --reload --port 8000
```

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Statut du système + nombre de chunks |
| `GET` | `/documents` | Liste des sources avec chunks par source |
| `POST` | `/query` | Interroger le pipeline RAG |

**Exemple :**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Quel est le taux de pauvreté au Sénégal en 2021 ?"}'
```

**Réponse :**
```json
{
  "answer": "Le taux de pauvreté monétaire au Sénégal est de 37,5% en 2021-2022... [ANSD — EHCVM 2021-2022, p.32]",
  "intent": "lookup",
  "citations": [{"institution": "ANSD", "report": "EHCVM 2021-2022", "page": "32"}],
  "n_chunks": 8,
  "latency_s": 9.75
}
```

### Frontend Pro (interface technique)

```bash
streamlit run "frontend/🏠_Accueil.py" --server.port 8501
```

| Page | Description |
|---|---|
| 🏠 Accueil | Vue d'ensemble, métriques clés, 6 requêtes démo |
| 💬 Assistant | Chat RAG avec panel de citations et statistiques de session |
| 📚 Documents | Sources indexées, topics par source, chunk counts |
| 🔍 Recherche | Recherche vectorielle directe avec score de similarité |
| ℹ️ À propos | Architecture, stack technique, phases de développement |

### Frontend Grand Public (interface citoyenne)

```bash
streamlit run "frontend_public/🏠_Accueil.py" --server.port 8502
```

| Page | Description |
|---|---|
| 🏠 Accueil | Faits clés (17,7M hab., 37,5% pauvreté...), thèmes, explications simples |
| 💬 Poser une question | Chat simplifié avec questions rapides par thème |
| 📋 Thèmes | 6 thèmes × 5 questions d'exemple cliquables |
| ❓ FAQ | Fiabilité, sources, usage, citation des données |

---

## Système d'agents

### État LangGraph

```python
class AgentState(TypedDict):
    query: str
    intent: str                    # lookup | trend | compare | compute | viz | mixed
    retrieved_chunks: List[dict]
    trend_output: Optional[dict]
    compare_output: Optional[dict]
    compute_output: Optional[dict]
    viz_output: Optional[dict]
    synthesis: str
    citations: List[dict]
    messages: Annotated[List[BaseMessage], operator.add]
```

### Graphe d'exécution

```
router_agent
     │
     │ intent classifié
     ▼
retrieval_agent ──► synthesis_agent ──► END
```

### Stratégie de retrieval hybride

1. **Dense retrieval** — ChromaDB cosine similarity sur 20 candidats
2. **BM25 sparse** — sur les 20 candidats denses
3. **Reciprocal Rank Fusion** — fusion des deux classements
4. **Top-8** — les meilleurs chunks avec métadonnées complètes

### Format des citations

Toute statistique est citée sous la forme :

```
[ANSD — EHCVM 2021-2022, p.32]
[ANSD — RGPH-5 Rapport Préliminaire 2023, p.15]
[ANSD — SES 2022-2023, p.78]
```

### Anti-hallucination

Pour les questions hors corpus, le système refuse d'inventer une réponse :

```
Q : Quel est le taux de criminalité au Sénégal en 2023 ?
R : Les documents indexés (RGPH-5, EHCVM, SES) ne contiennent pas
    de données sur le taux de criminalité. [...]
```

---

## Évaluation

### Golden dataset (20 questions)

Le dataset couvre 6 thèmes et 3 types de difficulté :

| Thème | Questions | Source |
|---|---|---|
| Pauvreté | 5 | EHCVM 2021-2022 |
| Population | 3 | RGPH-5 2023 |
| Emploi | 3 | RGPH-5 Économie 2024 |
| Économie / Social | 5 | SES 2022-2023 |
| Multi-sources | 2 | EHCVM + SES |
| Test anti-hallucination | 2 | Hors corpus |

### Lancer l'évaluation

```bash
# Évaluation complète (custom metrics + RAGAS)
python scripts/eval_retrieval.py

# Sans RAGAS (plus rapide)
python scripts/eval_retrieval.py --no-ragas

# Filtrer par thème
python scripts/eval_retrieval.py --theme pauvreté

# Limiter à N questions
python scripts/eval_retrieval.py --n 5

# RAGAS sur un CSV déjà généré
python scripts/_ragas_only.py
```

### Métriques personnalisées

| Métrique | Définition |
|---|---|
| `keyword_hit_rate` | Fraction des mots-clés attendus présents dans la réponse |
| `citation_present` | Au moins une citation `[X — Y, p.Z]` dans la réponse |
| `refusal_rate` | Refus correct pour les questions hors corpus |
| `retrieval_quality` | Chunks provenant de la bonne source documentaire |

---

## Structure du projet

```
senstat/
├── agents/                      # Système multi-agents LangGraph
│   ├── graph.py                 # StateGraph + singleton get_graph()
│   ├── state.py                 # AgentState TypedDict
│   ├── router_agent.py          # Classification d'intention
│   ├── retrieval_agent.py       # Dense + BM25 + RRF
│   └── synthesis_agent.py       # Réponse finale + citations
│
├── api/                         # REST API FastAPI
│   ├── main.py                  # App + CORS
│   ├── schemas.py               # Modèles Pydantic
│   └── routes/
│       ├── query.py             # POST /query
│       ├── documents.py         # GET /documents
│       └── health.py            # GET /health
│
├── frontend/                    # Interface Pro (port 8501)
│   ├── 🏠_Accueil.py
│   ├── style.py
│   └── pages/
│       ├── 1_💬_Assistant.py
│       ├── 2_📚_Documents.py
│       ├── 3_🔍_Recherche.py
│       └── 4_ℹ️_A_propos.py
│
├── frontend_public/             # Interface Grand Public (port 8502)
│   ├── 🏠_Accueil.py
│   ├── style_public.py
│   └── pages/
│       ├── 1_💬_Poser_une_question.py
│       ├── 2_📋_Thèmes.py
│       └── 3_❓_FAQ.py
│
├── ingestion/                   # Pipeline d'ingestion
│   ├── pipeline.py              # Orchestration + registre SOURCES
│   ├── extractors/
│   │   ├── pdf_extractor.py     # pdfplumber + OCR fallback
│   │   └── table_extractor.py   # camelot lattice mode → markdown
│   └── chunkers/
│       └── text_chunker.py      # RecursiveCharacterTextSplitter
│
├── vectorstore/
│   └── chroma_store.py          # ChromaDB wrapper avec embeddings e5
│
├── scripts/
│   ├── eval_retrieval.py        # Pipeline d'évaluation complet
│   ├── _ragas_only.py           # RAGAS sur CSV existant
│   ├── ingest_all.py            # Ingestion complète
│   └── ingest_source.py         # Ingestion d'une source unique
│
├── data/
│   ├── golden_dataset.json      # 20 paires Q&A pour l'évaluation
│   ├── sources.json             # Registre des sources officielles
│   ├── raw/                     # PDFs sources (gitignored)
│   ├── processed/               # Texte extrait (gitignored)
│   └── chroma/                  # Vector store (gitignored)
│
├── pyproject.toml
├── .env.example
├── .gitignore
└── CLAUDE.md                    # Documentation technique (pour Claude Code)
```

---

## Variables d'environnement

| Variable | Défaut | Requis | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | — | ✅ | Clé API Anthropic |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | | Répertoire de persistance ChromaDB |
| `EMBEDDING_MODEL` | `intfloat/multilingual-e5-large` | | Modèle d'embeddings HuggingFace |
| `EMBEDDING_DEVICE` | `cpu` | | `cpu` ou `cuda` |
| `DATA_RAW_DIR` | `./data/raw` | | Répertoire des PDFs sources |
| `DATA_PROCESSED_DIR` | `./data/processed` | | Texte extrait |
| `API_HOST` | `0.0.0.0` | | Hôte FastAPI |
| `API_PORT` | `8000` | | Port FastAPI |
| `LOG_LEVEL` | `INFO` | | Niveau de logs loguru |

---

## Exemples de questions

```
# Pauvreté
"Quel est le taux de pauvreté monétaire au Sénégal en 2021 ?"
"Quelles sont les régions les plus pauvres du Sénégal ?"
"Quel est le lien entre niveau d'instruction et pauvreté ?"
"Comment a évolué la pauvreté entre 2018 et 2021 ?"

# Population
"Quelle est la population totale du Sénégal selon le RGPH-5 2023 ?"
"Quel est le taux de croissance démographique annuel ?"
"Quand a eu lieu le RGPH-5 au Sénégal ?"

# Emploi
"Quel est le taux d'activité économique des femmes au Sénégal ?"
"Quelle est la structure de l'emploi par secteur selon le RGPH-5 ?"
"Quel est le taux de chômage au Sénégal ?"

# Économie
"Quel est le taux de croissance du PIB du Sénégal en 2023 ?"
"Quelle est la part de l'agriculture dans le PIB ?"

# Social
"Quel est le taux d'électrification au Sénégal ?"
"Quelle est la situation de l'accès à l'eau potable ?"
"Quel est le taux de scolarisation au primaire ?"

# Multi-sources
"Quelles sont les régions les plus pauvres du Sénégal ?"
"Comparez l'accès à l'eau potable entre Dakar et le reste du Sénégal"
```

---

## Notes techniques

### Qualité des PDFs ANSD

Certains rapports ANSD sont scannés (images). Le pipeline tente d'abord l'extraction texte via pdfplumber. Si le texte extrait est insuffisant (< 200 caractères par page), il bascule automatiquement sur l'OCR via pytesseract + pdf2image.

### Ruptures méthodologiques

Les comparaisons temporelles doivent tenir compte des ruptures de méthodologie :

- **Pauvreté** : révision du seuil de pauvreté ANSD en 2018 — les données ESPS antérieures ne sont pas comparables avec l'EHCVM.
- **PIB** : rebasing de la base PIB à 2014 par la DPEE — base 2014 = 100.

### Sécurité

Le fichier `.env` est exclu du dépôt via `.gitignore`. Ne commitez jamais de clés API. Utilisez `.env.example` comme template pour les nouveaux développeurs.

---

## Licence

Ce projet est sous licence MIT. Les données utilisées proviennent de sources officielles publiques (ANSD, DPEE, BCEAO) et sont la propriété de leurs institutions respectives.

---

*Construit avec [LangGraph](https://github.com/langchain-ai/langgraph), [Claude Sonnet 4.6](https://www.anthropic.com), [ChromaDB](https://www.trychroma.com) et [Streamlit](https://streamlit.io).*

**Version** : 0.1.0 — **Dernière mise à jour** : Mai 2026
