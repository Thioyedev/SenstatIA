import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

import httpx
import streamlit as st

from frontend.style import inject_css, metric_card, section_label, sidebar_brand

st.set_page_config(
    page_title="SenStat — Statistiques Officielles du Sénégal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
sidebar_brand()

lang = st.session_state.get("lang", "fr")

API_URL = "http://localhost:8000"

# ── Live stats ──────────────────────────────────────────────────────────────────────────
try:
    health = httpx.get(f"{API_URL}/health", timeout=3).json()
    docs = httpx.get(f"{API_URL}/documents", timeout=5).json()
    chunks_total = health.get("chunks_indexed", 0)
    sources_count = len(docs)
    is_online = True
except Exception:
    chunks_total = 7571
    sources_count = 12
    docs = []
    is_online = False

_STATUS = {
    "fr": {"online": "En ligne", "offline": "Hors ligne"},
    "en": {"online": "Online", "offline": "Offline"},
}
_HERO = {
    "fr": {
        "sub": "Interrogez les statistiques officielles du Sénégal.<br>Chaque réponse est ancrée dans les sources institutionnelles avec citation précise.",
        "demo": "Exemples de questions — cliquez pour interroger l'assistant",
        "chunks": "chunks indexés",
        "src_btn": "Query →",
        "src_query": "Quelles sont les principales statistiques de {} ?",
    },
    "en": {
        "sub": "Query Senegal's official statistics.<br>Every answer is grounded in institutional sources with precise citations.",
        "demo": "Sample questions — click to query the assistant",
        "chunks": "indexed chunks",
        "src_btn": "Query →",
        "src_query": "What are the main statistics from {} ?",
    },
}
h = _HERO[lang]
s = _STATUS[lang]
status_dot = (
    f'<span class="status-online"></span> {s["online"]}'
    if is_online
    else f'<span class="status-offline"></span> {s["offline"]}'
)

# ── Hero ──────────────────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
<div class="hero">
    <div style="position:relative;z-index:1;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <span style="background:rgba(255,222,40,0.25);border-radius:8px;padding:4px 10px;
                         font-size:0.72rem;font-weight:600;color:#FDEF42;letter-spacing:0.5px;">BETA</span>
            <span style="font-size:0.75rem;color:rgba(255,255,255,0.6);">{status_dot}</span>
        </div>
        <div class="hero-title">SenStat</div>
        <div class="hero-sub">{h["sub"]}</div>
        <span class="hero-pill">ANSD</span>
        <span class="hero-pill">FMI</span>
        <span class="hero-pill">Banque Mondiale</span>
        <span class="hero-pill">ARTP</span>
        <span class="hero-pill">DGTCP</span>
        <span class="hero-pill">Cour des Comptes</span>
        <span class="hero-pill">PNUD</span>
        <span class="hero-pill">DAPSA</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── Metrics ────────────────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4, gap="small")
with c1:
    metric_card(
        "🏗",
        sources_count,
        "Sources officielles" if lang == "fr" else "Official sources",
        "ANSD · FMI · BM · ARTP · DGTCP · PNUD · DAPSA",
    )
with c2:
    metric_card(
        "📦",
        f"{chunks_total:,}",
        "Chunks indexés" if lang == "fr" else "Indexed chunks",
        "texte + tableaux + séries" if lang == "fr" else "text + tables + series",
    )
with c3:
    metric_card(
        "🧠",
        "E5-multilingual",
        "Modèle d'embedding" if lang == "fr" else "Embedding model",
        "1 024 dim · Français natif" if lang == "fr" else "1 024 dim · Native French",
    )
with c4:
    metric_card(
        "⚡",
        "Haiku + Sonnet",
        "Anthropic Claude",
        "routing + synthèse" if lang == "fr" else "routing + synthesis",
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Demo queries ──────────────────────────────────────────────────────────────────────────────
section_label(h["demo"])

DEMOS = {
    "fr": [
        ("👥", "Population totale selon le RGPH-5 2023"),
        ("📡", "Taux de pénétration mobile et internet au Sénégal en 2024"),
        ("📈", "Évolution du PIB du Sénégal entre 2015 et 2023"),
        ("🏦", "Quel est le niveau de la dette publique du Sénégal en 2024 ?"),
        ("💼", "Taux de chômage des jeunes au Sénégal"),
        ("🌍", "Quel est l'IDH du Sénégal et son classement mondial ?"),
    ],
    "en": [
        ("👥", "Total population according to RGPH-5 2023"),
        ("📡", "Mobile and internet penetration rate in Senegal in 2024"),
        ("📈", "GDP evolution in Senegal between 2015 and 2023"),
        ("🏦", "What is the public debt level of Senegal in 2024?"),
        ("💼", "Youth unemployment rate in Senegal"),
        ("🌍", "What is Senegal's HDI and its global ranking?"),
    ],
}

cols = st.columns(3, gap="small")
for i, (icon, q) in enumerate(DEMOS[lang]):
    with cols[i % 3]:
        if st.button(f"{icon}  {q}", key=f"demo_{i}", use_container_width=True):
            st.session_state["prefill_query"] = q
            st.switch_page("pages/1_💬_Assistant.py")

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Sources ───────────────────────────────────────────────────────────────────────────────────
if docs:
    section_label("Sources indexées" if lang == "fr" else "Indexed sources")
    cols = st.columns(len(docs), gap="small")
    ICONS = {
        "ANSD": "🏗",
        "DPEE": "📈",
        "BCEAO": "🏦",
        "Banque Mondiale": "🌍",
        "FMI": "📊",
        "ARTP": "📡",
        "DGTCP": "🏦",
        "Cour des Comptes": "⚖️",
        "PNUD": "🌍",
        "DAPSA": "🌾",
        "OIT": "💼",
    }

    for col, doc in zip(cols, docs, strict=False):
        icon = ICONS.get(doc["institution"], "📄")
        topics_html = "".join(
            f'<span class="badge badge-gray">{tp}</span>' for tp in doc["topics"][:3]
        )
        with col:
            st.markdown(
                f"""
<div class="card" style="border-top:3px solid #00853F;padding:16px;cursor:default;">
    <div style="font-size:1.5rem;margin-bottom:8px;">{icon}</div>
    <div style="margin-bottom:6px;">
        <span class="badge badge-green">{doc["institution"]}</span>
        <span class="badge badge-blue">{doc["year"]}</span>
    </div>
    <div style="font-weight:600;font-size:0.88rem;color:#1A1A1A;margin:8px 0;min-height:36px;line-height:1.35;">
        {doc["report_name"]}
    </div>
    <div style="font-size:1.4rem;font-weight:700;color:#00853F;margin-bottom:2px;">{doc["chunk_count"]:,}</div>
    <div style="font-size:0.7rem;color:#888;text-transform:uppercase;letter-spacing:0.4px;margin-bottom:10px;">
        {h["chunks"]}
    </div>
    <div style="margin-top:4px;">{topics_html}</div>
</div>
""",
                unsafe_allow_html=True,
            )
            if st.button(h["src_btn"], key=f"src_{doc['source_id']}", use_container_width=True):
                st.session_state["prefill_query"] = h["src_query"].format(doc["report_name"])
                st.switch_page("pages/1_💬_Assistant.py")

# ── Footer ──────────────────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
footer = (
    "SenStat v0.3 · 12 sources officielles · "
    "ANSD · FMI · Banque Mondiale · ARTP · DGTCP · Cour des Comptes · PNUD · DAPSA · "
    "Claude Haiku (routing) + Sonnet (synthèse) · ChromaDB + LangGraph"
)
st.markdown(
    f'<div style="text-align:center;color:#bbb;font-size:0.73rem;padding:4px 0 12px 0;">{footer}</div>',
    unsafe_allow_html=True,
)
