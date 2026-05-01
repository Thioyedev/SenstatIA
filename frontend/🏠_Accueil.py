import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import httpx
from frontend.style import inject_css, sidebar_brand, section_label, metric_card

st.set_page_config(
    page_title="SenStat — Statistiques Officielles du Sénégal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
sidebar_brand()

API_URL = "http://localhost:8000"

# ── Live stats ──────────────────────────────────────────────────────────────────
try:
    health        = httpx.get(f"{API_URL}/health", timeout=3).json()
    docs          = httpx.get(f"{API_URL}/documents", timeout=5).json()
    chunks_total  = health.get("chunks_indexed", 0)
    sources_count = len(docs)
    is_online     = True
except Exception:
    chunks_total  = 1887
    sources_count = 4
    docs          = []
    is_online     = False

# ── Hero ────────────────────────────────────────────────────────────────────────
status_dot = '<span class="status-online"></span> En ligne' if is_online else '<span class="status-offline"></span> Hors ligne'
st.markdown(f"""
<div class="hero">
    <div style="position:relative; z-index:1;">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
            <span style="background:rgba(255,222,40,0.25); border-radius:8px; padding:4px 10px;
                         font-size:0.72rem; font-weight:600; color:#FDEF42; letter-spacing:0.5px;">
                BETA
            </span>
            <span style="font-size:0.75rem; color:rgba(255,255,255,0.6);">{status_dot}</span>
        </div>
        <div class="hero-title">SenStat</div>
        <div class="hero-sub">
            Interrogez les statistiques officielles du Sénégal.<br>
            Chaque réponse est ancrée dans les sources institutionnelles avec citation précise.
        </div>
        <span class="hero-pill">ANSD</span>
        <span class="hero-pill">DPEE</span>
        <span class="hero-pill">BCEAO</span>
        <span class="hero-pill">Banque Mondiale</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Metrics ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4, gap="small")
with c1: metric_card("🏛", sources_count, "Sources officielles", "ANSD · DPEE · BCEAO")
with c2: metric_card("📦", f"{chunks_total:,}", "Chunks indexés", "texte + tableaux")
with c3: metric_card("🧠", "E5-multilingual", "Modèle d'embedding", "Français natif")
with c4: metric_card("⚡", "Claude Sonnet 4.6", "LLM", "Anthropic")

st.markdown("<br>", unsafe_allow_html=True)

# ── Demo queries ─────────────────────────────────────────────────────────────────
section_label("Exemples de questions — cliquez pour interroger l'assistant")

demo_queries = [
    ("👥", "Population totale selon le RGPH-5 2023"),
    ("💰", "Taux de pauvreté au Sénégal en 2021 ?"),
    ("📈", "Évolution du PIB entre 2015 et 2023"),
    ("⚖️", "Accès à l'eau potable : Dakar vs Ziguinchor"),
    ("💼", "Taux de chômage par région — RGPH-5"),
    ("🌾", "Principaux secteurs économiques du Sénégal"),
]

cols = st.columns(3, gap="small")
for i, (icon, q) in enumerate(demo_queries):
    with cols[i % 3]:
        if st.button(f"{icon}  {q}", key=f"demo_{i}", use_container_width=True):
            st.session_state["prefill_query"] = q
            st.switch_page("pages/1_💬_Assistant.py")

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Sources cards ────────────────────────────────────────────────────────────────
if docs:
    section_label("Sources indexées")
    cols = st.columns(len(docs), gap="small")
    ICONS = {"ANSD": "🏛", "DPEE": "📈", "BCEAO": "🏦", "Banque Mondiale": "🌍"}

    for col, doc in zip(cols, docs):
        icon = ICONS.get(doc["institution"], "📄")
        topics_html = "".join(
            f'<span class="badge badge-gray">{t}</span>'
            for t in doc["topics"][:3]
        )
        with col:
            st.markdown(f"""
<div class="card" style="border-top: 3px solid #00853F; padding:16px; cursor:default;">
    <div style="font-size:1.5rem; margin-bottom:8px;">{icon}</div>
    <div style="margin-bottom:6px;">
        <span class="badge badge-green">{doc['institution']}</span>
        <span class="badge badge-blue">{doc['year']}</span>
    </div>
    <div style="font-weight:600; font-size:0.88rem; color:#1A1A1A; margin:8px 0; min-height:36px; line-height:1.35;">
        {doc['report_name']}
    </div>
    <div style="font-size:1.4rem; font-weight:700; color:#00853F; margin-bottom:2px;">
        {doc['chunk_count']:,}
    </div>
    <div style="font-size:0.7rem; color:#888; text-transform:uppercase; letter-spacing:0.4px; margin-bottom:10px;">
        chunks indexés
    </div>
    <div style="margin-top:4px;">{topics_html}</div>
</div>
""", unsafe_allow_html=True)
            if st.button("Interroger →", key=f"src_{doc['source_id']}", use_container_width=True):
                st.session_state["prefill_query"] = (
                    f"Quelles sont les principales statistiques de {doc['report_name']} ?"
                )
                st.switch_page("pages/1_💬_Assistant.py")

# ── Footer ───────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; color:#bbb; font-size:0.73rem; padding:4px 0 12px 0;">
    SenStat v0.1 · Données ANSD, DPEE, BCEAO · Claude Sonnet 4.6 + ChromaDB + LangGraph
</div>
""", unsafe_allow_html=True)
