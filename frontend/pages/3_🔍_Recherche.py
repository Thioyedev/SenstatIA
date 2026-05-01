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

st.title("🔍 Recherche dans les sources")
st.caption("Recherche sémantique directe dans les chunks indexés")

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
            placeholder="Ex: taux de chômage par région",
            label_visibility="collapsed",
        )
    with col_n:
        n = st.number_input("Résultats", min_value=1, max_value=20, value=8)

    col_src, col_submit = st.columns([3, 1])
    with col_src:
        source_filter = st.selectbox(
            "Filtrer par source",
            ["Toutes les sources", "rgph5_preliminaire", "rgph5_economie",
             "ehcvm_2021", "ses_2022_2023"],
        )
    with col_submit:
        submitted = st.form_submit_button("🔍 Rechercher", use_container_width=True)

# ── Results ───────────────────────────────────────────────────────────────────
if submitted and query.strip():
    where = None if source_filter == "Toutes les sources" else {"source_id": source_filter}

    with st.spinner("Recherche en cours..."):
        results = store.search(query, n_results=n, where=where)

    st.markdown(f"**{len(results)} chunks trouvés** pour *\"{query}\"*")
    st.markdown("---")

    for i, chunk in enumerate(results, 1):
        score_pct = int(chunk["score"] * 100)
        score_color = "#00853F" if score_pct >= 80 else "#F57F17" if score_pct >= 60 else "#888"
        institution = chunk.get("institution", "?")
        report = chunk.get("report_name", "?")
        year = chunk.get("year", "?")
        page = chunk.get("page_number", "?")
        is_table = chunk.get("is_table", False)

        tag = '<span style="background:#E3F2FD;color:#1565C0;border-radius:3px;padding:1px 6px;font-size:0.72rem;">TABLE</span>' if is_table else ""

        st.markdown(f"""
<div class="chunk-card">
    <div class="meta">
        #{i} &nbsp;·&nbsp; {institution} — {report} ({year}), p.{page}
        &nbsp; {tag}
        <span class="score" style="color:{score_color};">
            similarité {score_pct}%
        </span>
    </div>
    <div style="font-size:0.88rem; color:#333; line-height:1.5;">
        {chunk['text'][:400]}{'...' if len(chunk['text']) > 400 else ''}
    </div>
</div>
""", unsafe_allow_html=True)
elif submitted:
    st.warning("Veuillez saisir une requête.")
