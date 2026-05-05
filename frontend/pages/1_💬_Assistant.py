import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

import os
import uuid
import httpx
import streamlit as st
from datetime import datetime
from frontend.style import inject_css, sidebar_brand, section_label

st.set_page_config(
    page_title="Assistant — SenStat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

API_URL = os.getenv("API_URL", "http://localhost:8000")

INTENT_LABELS = {
    "fr": {
        "lookup":  ("🔎", "Recherche ponctuelle"),
        "trend":   ("📈", "Tendance"),
        "compare": ("⚖️",  "Comparaison"),
        "compute": ("🧮", "Calcul"),
        "viz":     ("📊", "Visualisation"),
        "mixed":   ("🔀", "Requête mixte"),
    },
    "en": {
        "lookup":  ("🔎", "Quick lookup"),
        "trend":   ("📈", "Trend analysis"),
        "compare": ("⚖️",  "Comparison"),
        "compute": ("🧮", "Calculation"),
        "viz":     ("📊", "Visualization"),
        "mixed":   ("🔀", "Mixed query"),
    },
}

T = {
    "fr": {
        "banner_title": "Assistant Statistique",
        "banner_sub":   "Données officielles du Sénégal · ANSD · DPEE · BCEAO · Réponses sourcées et vérifiées",
        "new_conv":     "✏️  Nouvelle conversation",
        "today":        "Aujourd'hui",
        "previous":     "Précédentes",
        "quick_label":  "Questions fréquentes — cliquez pour une réponse rapide",
        "chat_input":   "Ex: Quel est le taux de pauvreté en 2021 ?",
        "spinner":      "Recherche dans les sources officielles…",
        "sources":      "📎 Sources citées",
        "questions":    "questions",
        "sources_count":"sources",
        "verified":     "✅ Données vérifiées",
        "verified_desc":"Réponses issues des rapports officiels ANSD, DPEE et BCEAO uniquement.",
        "clear":        "🗑 Effacer cette conversation",
        "error_conn":   "⚠️ Impossible de contacter l'API. Vérifiez que le serveur tourne sur le port 8000.",
        "error_gen":    "⚠️ Erreur : ",
    },
    "en": {
        "banner_title": "Statistical Assistant",
        "banner_sub":   "Official data from Senegal · ANSD · DPEE · BCEAO · Sourced and verified answers",
        "new_conv":     "✏️  New conversation",
        "today":        "Today",
        "previous":     "Earlier",
        "quick_label":  "Frequent questions — click for a quick answer",
        "chat_input":   "E.g.: What is the poverty rate in 2021?",
        "spinner":      "Searching official sources…",
        "sources":      "📎 Sources cited",
        "questions":    "questions",
        "sources_count":"sources",
        "verified":     "✅ Verified data",
        "verified_desc":"Answers sourced exclusively from official ANSD, DPEE and BCEAO reports.",
        "clear":        "🗑 Clear this conversation",
        "error_conn":   "⚠️ Cannot reach the API. Make sure the server is running on port 8000.",
        "error_gen":    "⚠️ Error: ",
    },
}

QUICK = {
    "fr": [
        ("🏙️", "Population totale du Sénégal en 2023 ?"),
        ("📉", "Taux de pauvreté au Sénégal en 2021 ?"),
        ("💼", "Taux de chômage au Sénégal ?"),
        ("📈", "Taux de croissance du PIB ?"),
        ("💧", "Accès à l'eau potable en milieu rural ?"),
        ("📚", "Taux d'alphabétisation au Sénégal ?"),
    ],
    "en": [
        ("🏙️", "Total population of Senegal in 2023?"),
        ("📉", "Poverty rate in Senegal in 2021?"),
        ("💼", "Unemployment rate in Senegal?"),
        ("📈", "GDP growth rate in Senegal?"),
        ("💧", "Access to clean water in rural areas?"),
        ("📚", "Literacy rate in Senegal?"),
    ],
}

# ── Language ────────────────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "fr"

lang = st.session_state.lang
t    = T[lang]

# ── Conversation state ──────────────────────────────────────────────────────────
def new_conversation():
    cid = str(uuid.uuid4())
    st.session_state.conversations[cid] = {
        "title":     "Nouvelle conversation",
        "messages":  [],
        "citations": [],
        "timestamp": datetime.now(),
    }
    st.session_state.current_conv_id = cid

if "conversations" not in st.session_state:
    st.session_state.conversations = {}
    new_conversation()

if "current_conv_id" not in st.session_state or \
        st.session_state.current_conv_id not in st.session_state.conversations:
    new_conversation()

cid  = st.session_state.current_conv_id
conv = st.session_state.conversations[cid]

# ── Sidebar (toggle is inside sidebar_brand) ────────────────────────────────────
sidebar_brand()

if st.sidebar.button(t["new_conv"], use_container_width=True):
    new_conversation()
    st.rerun()

st.sidebar.markdown(
    "<hr style='border-color:rgba(255,255,255,0.08);margin:8px 12px;'>",
    unsafe_allow_html=True,
)

today      = datetime.now().date()
today_convs, older_convs = [], []
for c_id, c in reversed(list(st.session_state.conversations.items())):
    if not c["messages"]:
        continue
    if c["timestamp"].date() == today:
        today_convs.append((c_id, c))
    else:
        older_convs.append((c_id, c))

def render_conv_list(items):
    for c_id, c in items:
        label  = c["title"][:38] + "…" if len(c["title"]) > 38 else c["title"]
        active = c_id == st.session_state.current_conv_id
        if st.sidebar.button(label, key=f"conv_{c_id}",
                             use_container_width=True,
                             type="primary" if active else "secondary"):
            st.session_state.current_conv_id = c_id
            st.rerun()

if today_convs:
    st.sidebar.markdown(
        f"<div class='conv-group-label'>{t['today']}</div>",
        unsafe_allow_html=True,
    )
    render_conv_list(today_convs)

if older_convs:
    st.sidebar.markdown(
        f"<div class='conv-group-label'>{t['previous']}</div>",
        unsafe_allow_html=True,
    )
    render_conv_list(older_convs)

# ── Page banner ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-banner">
    <div class="page-banner-icon">📊</div>
    <div>
        <div class="page-banner-title">{t['banner_title']}</div>
        <div class="page-banner-sub">{t['banner_sub']}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────────
def _dedup_citations(cites: list) -> list:
    seen, out = set(), []
    for c in cites:
        key = (c.get("institution"), c.get("report_name"))
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out

def _render_pills(cites: list):
    pills = "".join(
        f'<span class="citation-pill">📎 {c.get("institution","?")} — '
        f'{c.get("report_name","?")}</span>'
        for c in _dedup_citations(cites)
    )
    if pills:
        st.markdown(f'<div style="margin-top:8px">{pills}</div>',
                    unsafe_allow_html=True)

# ── Layout ───────────────────────────────────────────────────────────────────────
has_conv   = bool(conv["messages"])
intent_map = INTENT_LABELS[lang]

if not has_conv:
    section_label(t["quick_label"])
    scols = st.columns(3, gap="small")
    for i, (icon, q) in enumerate(QUICK[lang]):
        with scols[i % 3]:
            if st.button(f"{icon}  {q}", key=f"quick_{i}", use_container_width=True):
                st.session_state["prefill_query"] = q
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

def _render_viz(viz: dict | None):
    if not viz or not viz.get("fig_json"):
        return
    import plotly.io as pio
    fig = pio.from_json(viz["fig_json"])
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

for msg in conv["messages"]:
    avatar = "🧑" if msg["role"] == "user" else "📊"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            _render_viz(msg.get("viz"))
            ts         = msg.get("timestamp", "")
            intent_key = msg.get("intent", "")
            icon, lbl  = intent_map.get(intent_key, ("", ""))
            parts = [p for p in [ts, f"{icon} {lbl}" if lbl else ""] if p]
            if parts:
                st.caption("  ·  ".join(parts))
            if msg.get("citations"):
                _render_pills(msg["citations"])

prefill = st.session_state.pop("prefill_query", None)
prompt  = st.chat_input(t["chat_input"]) or prefill

if prompt:
    now = datetime.now().strftime("%H:%M")

    if not conv["messages"]:
        conv["title"] = prompt[:50]

    conv["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="📊"):
        with st.spinner(t["spinner"]):
            try:
                resp = httpx.post(f"{API_URL}/query",
                                  json={"query": prompt}, timeout=90.0)
                resp.raise_for_status()
                data      = resp.json()
                answer    = data["answer"]
                new_cites = data.get("citations", [])
                intent    = data.get("intent", "")
                new_viz   = data.get("viz")
            except httpx.ConnectError:
                answer    = t["error_conn"]
                new_cites = []
                intent    = ""
                new_viz   = None
            except Exception as e:
                answer    = t["error_gen"] + str(e)
                new_cites = []
                intent    = ""
                new_viz   = None

        _render_viz(new_viz)
        st.markdown(answer)
        icon, lbl = intent_map.get(intent, ("", ""))
        parts = [now] + ([f"{icon} {lbl}"] if lbl else [])
        st.caption("  ·  ".join(parts))
        _render_pills(new_cites)

    conv["messages"].append({
        "role":      "assistant",
        "content":   answer,
        "intent":    intent,
        "timestamp": now,
        "citations": new_cites,
        "viz":       new_viz,
    })
    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
if conv["messages"] and st.button(t["clear"], use_container_width=False):
    conv["messages"] = []
    conv["title"]    = "Nouvelle conversation"
    st.rerun()
