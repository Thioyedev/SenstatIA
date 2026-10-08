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

lang = st.session_state.get("lang", "fr")

T = {
    "fr": {
        "title": "ℹ️ À propos de SenStat",
        "what_h": "Qu'est-ce que SenStat ?",
        "what_body": (
            "**SenStat** est un système multi-agent RAG (*Retrieval-Augmented Generation*) "
            "qui permet d'interroger les statistiques officielles du Sénégal publiées par "
            "les institutions nationales et internationales."
        ),
        "value_h": "Proposition de valeur",
        "value_quote": (
            "> ChatGPT vous donne un chiffre.\n"
            "> **SenStat vous donne le chiffre officiel, avec la source, le rapport et la page.**"
        ),
        "sources_h": "Sources de données",
        "pipeline_h": "Pipeline RAG",
        "pipeline": (
            "1. **Extraction** : PyMuPDF + pdfplumber + Camelot (tableaux)\n"
            "2. **Chunking** : RecursiveCharacterTextSplitter (512 tokens, 64 overlap)\n"
            "3. **Embedding** : `intfloat/multilingual-e5-large` (supporte le français)\n"
            "4. **Stockage** : ChromaDB (vectorstore local)\n"
            "5. **Retrieval** : Dense + BM25 + Reciprocal Rank Fusion\n"
            "6. **Génération** : Claude Sonnet 4.6 avec citations obligatoires"
        ),
        "stack_h": "Stack technique",
        "phases_h": "Phases de développement",
        "phases": (
            "- ✅ **Phase 1** — Ingestion + Agents de base + API + UI\n"
            "- 🔄 **Phase 2** — Trend agent, Compare agent, CrossEncoder\n"
            "- ⏳ **Phase 3** — Compute agent, Viz agent, Qdrant\n"
            "- ⏳ **Phase 4** — CI/CD, Docker, RAGAS eval"
        ),
        "footer": "SenStat v0.1 · Projet portfolio · Données ANSD, DPEE, BCEAO",
        "src_institution": "Institution",
        "src_type": "Type",
        "src_coverage": "Couverture",
        "src_rows": [
            ("**ANSD**", "Recensement, Enquêtes", "Population, Pauvreté, Emploi"),
            ("**DPEE**", "Bulletins mensuels", "PIB, Conjoncture"),
            ("**BCEAO**", "Rapports annuels", "Monnaie, Finance"),
            ("**Banque Mondiale**", "API Open Data", "Indicateurs macro"),
        ],
    },
    "en": {
        "title": "ℹ️ About SenStat",
        "what_h": "What is SenStat?",
        "what_body": (
            "**SenStat** is a RAG (*Retrieval-Augmented Generation*) multi-agent system "
            "that enables querying official Senegalese statistics published by national "
            "and international institutions."
        ),
        "value_h": "Value proposition",
        "value_quote": (
            "> ChatGPT gives you a number.\n"
            "> **SenStat gives you the official number, with the source, the report, and the page.**"
        ),
        "sources_h": "Data sources",
        "pipeline_h": "RAG Pipeline",
        "pipeline": (
            "1. **Extraction**: PyMuPDF + pdfplumber + Camelot (tables)\n"
            "2. **Chunking**: RecursiveCharacterTextSplitter (512 tokens, 64 overlap)\n"
            "3. **Embedding**: `intfloat/multilingual-e5-large` (French support)\n"
            "4. **Storage**: ChromaDB (local vectorstore)\n"
            "5. **Retrieval**: Dense + BM25 + Reciprocal Rank Fusion\n"
            "6. **Generation**: Claude Sonnet 4.6 with mandatory citations"
        ),
        "stack_h": "Tech stack",
        "phases_h": "Development phases",
        "phases": (
            "- ✅ **Phase 1** — Ingestion + Base agents + API + UI\n"
            "- 🔄 **Phase 2** — Trend agent, Compare agent, CrossEncoder\n"
            "- ⏳ **Phase 3** — Compute agent, Viz agent, Qdrant\n"
            "- ⏳ **Phase 4** — CI/CD, Docker, RAGAS eval"
        ),
        "footer": "SenStat v0.1 · Portfolio project · Data from ANSD, DPEE, BCEAO",
        "src_institution": "Institution",
        "src_type": "Type",
        "src_coverage": "Coverage",
        "src_rows": [
            ("**ANSD**", "Census, Surveys", "Population, Poverty, Employment"),
            ("**DPEE**", "Monthly bulletins", "GDP, Economic outlook"),
            ("**BCEAO**", "Annual reports", "Money, Finance"),
            ("**World Bank**", "Open Data API", "Macro indicators"),
        ],
    },
}

t = T[lang]

st.title(t["title"])

col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown(f"## {t['what_h']}")
    st.markdown(t["what_body"])
    st.markdown(f"### {t['value_h']}")
    st.markdown(t["value_quote"])
    st.markdown(f"### {t['sources_h']}")
    header = f"| {t['src_institution']} | {t['src_type']} | {t['src_coverage']} |\n|---|---|---|"
    rows = "\n".join(f"| {a} | {b} | {c} |" for a, b, c in t["src_rows"])
    st.markdown(header + "\n" + rows)
    st.markdown(f"### {t['pipeline_h']}")
    st.markdown(t["pipeline"])

with col_right:
    st.markdown(f"### {t['stack_h']}")

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
        st.markdown(
            f"""
<div style="display:flex;align-items:center;background:white;border-radius:8px;
            padding:10px 14px;margin:6px 0;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
    <span style="font-size:1.3rem;margin-right:10px;">{icon}</span>
    <div>
        <div style="font-size:0.72rem;color:#888;">{layer}</div>
        <div style="font-size:0.88rem;font-weight:600;color:#222;">{tech}</div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"### {t['phases_h']}")
    st.markdown(t["phases"])

st.markdown("---")
st.markdown(
    f"<div style='text-align:center;color:#aaa;font-size:0.78rem;'>{t['footer']}</div>",
    unsafe_allow_html=True,
)
