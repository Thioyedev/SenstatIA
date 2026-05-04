import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import httpx
from frontend.style import inject_css, sidebar_brand

st.set_page_config(
    page_title="Documents — SenStat",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
sidebar_brand()

lang = st.session_state.get("lang", "fr")
API_URL = "http://localhost:8000"

T = {
    "fr": {
        "title":   "📚 Sources Indexées",
        "caption": "Documents officiels ingérés dans la base vectorielle",
        "api_err": "Impossible de contacter l'API",
        "docs_indexed": "Documents indexés",
        "total_chunks": "Total chunks",
        "institutions": "Institutions",
        "topics_label": "Thématiques",
        "url_label":    "URL",
        "chunks_label": "chunks indexés",
        "query_btn":    "💬 Interroger cette source",
        "query_prefill": "Quelles sont les principales données de {} ?",
        "no_docs": "Aucun document indexé. Lancez le pipeline d'ingestion : `python -m ingestion.pipeline`",
    },
    "en": {
        "title":   "📚 Indexed Sources",
        "caption": "Official documents ingested into the vector database",
        "api_err": "Cannot reach the API",
        "docs_indexed": "Indexed documents",
        "total_chunks": "Total chunks",
        "institutions": "Institutions",
        "topics_label": "Topics",
        "url_label":    "URL",
        "chunks_label": "indexed chunks",
        "query_btn":    "💬 Query this source",
        "query_prefill": "What are the main statistics from {} ?",
        "no_docs": "No documents indexed. Run the ingestion pipeline: `python -m ingestion.pipeline`",
    },
}

t = T[lang]

st.title(t["title"])
st.caption(t["caption"])

try:
    docs = httpx.get(f"{API_URL}/documents", timeout=10).json()
except Exception as e:
    st.error(f"{t['api_err']} : {e}")
    docs = []

TOPIC_COLORS = {
    "population": "#E8F5E9",
    "pauvreté": "#FFF3E0",
    "économie": "#E3F2FD",
    "santé": "#FCE4EC",
    "éducation": "#F3E5F5",
    "emploi": "#E0F7FA",
    "default": "#F5F5F5",
}

INSTITUTION_ICONS = {
    "ANSD": "🏛",
    "DPEE": "📈",
    "BCEAO": "🏦",
    "Banque Mondiale": "🌍",
    "Ministère de la Santé": "🏥",
}

if docs:
    total_chunks = sum(d["chunk_count"] for d in docs)
    c1, c2, c3 = st.columns(3)
    c1.metric(t["docs_indexed"], len(docs))
    c2.metric(t["total_chunks"], f"{total_chunks:,}")
    c3.metric(t["institutions"], len({d["institution"] for d in docs}))

    st.markdown("<br>", unsafe_allow_html=True)

    for doc in docs:
        icon = INSTITUTION_ICONS.get(doc["institution"], "📄")
        with st.expander(
            f"{icon} **{doc['report_name']}**  —  {doc['institution']} ({doc['year']})",
            expanded=True,
        ):
            col_info, col_stats = st.columns([3, 1])

            with col_info:
                st.markdown(f"""
<div style="margin-bottom:10px;">
    <span class="badge">{doc['institution']}</span>
    <span class="badge" style="background:#E3F2FD;color:#1565C0;">{doc['year']}</span>
</div>
""", unsafe_allow_html=True)

                topic_html = " ".join(
                    f'<span style="background:{TOPIC_COLORS.get(tp, TOPIC_COLORS["default"])};'
                    f'border-radius:4px;padding:2px 8px;font-size:0.78rem;margin:2px;'
                    f'display:inline-block;">{tp}</span>'
                    for tp in doc["topics"]
                )
                st.markdown(f"**{t['topics_label']} :** {topic_html}", unsafe_allow_html=True)
                st.markdown(f"**{t['url_label']} :** [{doc['url']}]({doc['url']})")

            with col_stats:
                st.markdown(f"""
<div class="metric-card" style="padding:12px;">
    <div class="value" style="font-size:1.6rem;">{doc['chunk_count']}</div>
    <div class="label">{t['chunks_label']}</div>
</div>
""", unsafe_allow_html=True)

            if st.button(t["query_btn"], key=f"query_{doc['source_id']}"):
                st.session_state["prefill_query"] = t["query_prefill"].format(doc["report_name"])
                st.switch_page("pages/1_💬_Assistant.py")
else:
    st.info(t["no_docs"])
