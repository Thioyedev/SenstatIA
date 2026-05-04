import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from frontend.style import inject_css, sidebar_brand
from vectorstore.chroma_store import ChromaStore

st.set_page_config(
    page_title="Recherche — SenStat",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
sidebar_brand()

lang = st.session_state.get("lang", "fr")

T = {
    "fr": {
        "title":       "🔍 Recherche dans les sources",
        "caption":     "Recherche sémantique directe dans les chunks indexés",
        "placeholder": "Ex: taux de chômage par région",
        "n_label":     "Résultats",
        "src_label":   "Filtrer par source",
        "all_sources": "Toutes les sources",
        "search_btn":  "🔍 Rechercher",
        "spinner":     "Recherche en cours...",
        "results_found": "{n} chunks trouvés pour *\"{q}\"*",
        "similarity":  "similarité",
        "no_query":    "Veuillez saisir une requête.",
    },
    "en": {
        "title":       "🔍 Search within sources",
        "caption":     "Direct semantic search across indexed chunks",
        "placeholder": "E.g.: unemployment rate by region",
        "n_label":     "Results",
        "src_label":   "Filter by source",
        "all_sources": "All sources",
        "search_btn":  "🔍 Search",
        "spinner":     "Searching...",
        "results_found": "{n} chunks found for *\"{q}\"*",
        "similarity":  "similarity",
        "no_query":    "Please enter a search query.",
    },
}

t = T[lang]

st.title(t["title"])
st.caption(t["caption"])

@st.cache_resource
def get_store():
    return ChromaStore()

store = get_store()

# ── Filters ───────────────────────────────────────────────────────────────────
with st.form("search_form"):
    col_q, col_n = st.columns([4, 1])
    with col_q:
        query = st.text_input(
            "Requête",
            placeholder=t["placeholder"],
            label_visibility="collapsed",
        )
    with col_n:
        n = st.number_input(t["n_label"], min_value=1, max_value=20, value=8)

    col_src, col_submit = st.columns([3, 1])
    with col_src:
        source_options = [
            t["all_sources"],
            "rgph5_preliminaire",
            "rgph5_economie",
            "ehcvm_2021",
            "ses_2022_2023",
        ]
        source_filter = st.selectbox(t["src_label"], source_options)
    with col_submit:
        submitted = st.form_submit_button(t["search_btn"], use_container_width=True)

# ── Results ───────────────────────────────────────────────────────────────────
if submitted and query.strip():
    where = None if source_filter == t["all_sources"] else {"source_id": source_filter}

    with st.spinner(t["spinner"]):
        results = store.search(query, n_results=n, where=where)

    st.markdown(t["results_found"].format(n=len(results), q=query))
    st.markdown("---")

    for i, chunk in enumerate(results, 1):
        score_pct = int(chunk["score"] * 100)
        score_color = "#00853F" if score_pct >= 80 else "#F57F17" if score_pct >= 60 else "#888"
        institution = chunk.get("institution", "?")
        report = chunk.get("report_name", "?")
        year = chunk.get("year", "?")
        page = chunk.get("page_number", "?")
        is_table = chunk.get("is_table", False)

        tag = (
            '<span style="background:#E3F2FD;color:#1565C0;border-radius:3px;'
            'padding:1px 6px;font-size:0.72rem;">TABLE</span>'
            if is_table else ""
        )

        st.markdown(f"""
<div class="chunk-card">
    <div class="meta">
        #{i} &nbsp;·&nbsp; {institution} — {report} ({year}), p.{page}
        &nbsp; {tag}
        <span class="score" style="color:{score_color};">
            {t['similarity']} {score_pct}%
        </span>
    </div>
    <div style="font-size:0.88rem; color:#333; line-height:1.5;">
        {chunk['text'][:400]}{'...' if len(chunk['text']) > 400 else ''}
    </div>
</div>
""", unsafe_allow_html=True)
elif submitted:
    st.warning(t["no_query"])
