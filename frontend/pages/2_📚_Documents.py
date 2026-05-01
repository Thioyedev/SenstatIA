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

API_URL = "http://localhost:8000"

st.title("📚 Sources Indexées")
st.caption("Documents officiels ingérés dans la base vectorielle")

try:
    docs = httpx.get(f"{API_URL}/documents", timeout=10).json()
except Exception as e:
    st.error(f"Impossible de contacter l'API : {e}")
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
    c1.metric("Documents indexés", len(docs))
    c2.metric("Total chunks", f"{total_chunks:,}")
    c3.metric("Institutions", len({d["institution"] for d in docs}))

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
                    f'<span style="background:{TOPIC_COLORS.get(t, TOPIC_COLORS["default"])};'
                    f'border-radius:4px;padding:2px 8px;font-size:0.78rem;margin:2px;'
                    f'display:inline-block;">{t}</span>'
                    for t in doc["topics"]
                )
                st.markdown(f"**Thématiques :** {topic_html}", unsafe_allow_html=True)
                st.markdown(f"**URL :** [{doc['url']}]({doc['url']})")

            with col_stats:
                st.markdown(f"""
<div class="metric-card" style="padding:12px;">
    <div class="value" style="font-size:1.6rem;">{doc['chunk_count']}</div>
    <div class="label">chunks indexés</div>
</div>
""", unsafe_allow_html=True)

            if st.button(
                f"💬 Interroger cette source",
                key=f"query_{doc['source_id']}",
            ):
                st.session_state["prefill_query"] = (
                    f"Quelles sont les principales données de {doc['report_name']} ?"
                )
                st.switch_page("pages/1_💬_Assistant.py")
else:
    st.info("Aucun document indexé. Lancez le pipeline d'ingestion : `python -m ingestion.pipeline`")
