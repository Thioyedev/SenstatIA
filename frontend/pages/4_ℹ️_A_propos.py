import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from frontend.style import inject_css, sidebar_brand

st.set_page_config(
    page_title="À propos — SenStat",
    page_icon="ℹ️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
sidebar_brand()

st.title("ℹ️ À propos de SenStat")

col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("""
## Qu'est-ce que SenStat ?

**SenStat** est un système multi-agent RAG (*Retrieval-Augmented Generation*)
qui permet d'interroger les statistiques officielles du Sénégal publiées par
les institutions nationales et internationales.

### Proposition de valeur

> ChatGPT vous donne un chiffre.
> **SenStat vous donne le chiffre officiel, avec la source, le rapport et la page.**

### Sources de données

| Institution | Type | Couverture |
|---|---|---|
| **ANSD** | Recensement, Enquêtes | Population, Pauvreté, Emploi |
| **DPEE** | Bulletins mensuels | PIB, Conjoncture |
| **BCEAO** | Rapports annuels | Monnaie, Finance |
| **Banque Mondiale** | API Open Data | Indicateurs macro |

### Pipeline RAG

1. **Extraction** : PyMuPDF + pdfplumber + Camelot (tableaux)
2. **Chunking** : RecursiveCharacterTextSplitter (512 tokens, 64 overlap)
3. **Embedding** : `intfloat/multilingual-e5-large` (supporte le français)
4. **Stockage** : ChromaDB (vectorstore local)
5. **Retrieval** : Dense + BM25 + Reciprocal Rank Fusion
6. **Génération** : Claude Sonnet 4.6 avec citations obligatoires
""")

with col_right:
    st.markdown("### Stack technique")

    stack = [
        ("🤖", "LLM", "Claude Sonnet 4.6 (Anthropic)"),
        ("🔗", "Agents", "LangGraph StateGraph"),
        ("🗄", "Vectorstore", "ChromaDB (dev) / Qdrant (prod)"),
        ("🔤", "Embeddings", "E5-multilingual-large"),
        ("📄", "PDF", "PyMuPDF + pdfplumber"),
        ("📊", "Tables", "Camelot-py (Lattice)"),
        ("🔍", "Search", "Dense + BM25 + RRF"),
        ("⚡", "API", "FastAPI + Uvicorn"),
        ("🎨", "Frontend", "Streamlit"),
    ]

    for icon, layer, tech in stack:
        st.markdown(f"""
<div style="display:flex;align-items:center;background:white;border-radius:8px;
            padding:10px 14px;margin:6px 0;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
    <span style="font-size:1.3rem;margin-right:10px;">{icon}</span>
    <div>
        <div style="font-size:0.72rem;color:#888;">{layer}</div>
        <div style="font-size:0.88rem;font-weight:600;color:#222;">{tech}</div>
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
### Phases de développement

- ✅ **Phase 1** — Ingestion + Agents de base + API + UI
- 🔄 **Phase 2** — Trend agent, Compare agent, CrossEncoder
- ⏳ **Phase 3** — Compute agent, Viz agent, Qdrant
- ⏳ **Phase 4** — CI/CD, Docker, RAGAS eval
""")

st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#aaa;font-size:0.78rem;'>"
    "SenStat v0.1 · Projet portfolio · Données ANSD, DPEE, BCEAO"
    "</div>",
    unsafe_allow_html=True,
)
