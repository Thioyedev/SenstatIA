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
from frontend.style import inject_css, sidebar_brand, empty_state

st.set_page_config(
    page_title="Assistant — SenStat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

API_URL = os.getenv("API_URL", "http://localhost:8000")

INTENT_LABELS = {
    "lookup":  ("🔎", "Recherche ponctuelle"),
    "trend":   ("📈", "Analyse de tendance"),
    "compare": ("⚖️", "Comparaison"),
    "compute": ("🧮", "Calcul statistique"),
    "viz":     ("📊", "Visualisation"),
    "mixed":   ("🔀", "Requête mixte"),
}

# ── Conversation state ─────────────────────────────────────────────────────────
def new_conversation():
    cid = str(uuid.uuid4())
    st.session_state.conversations[cid] = {
        "title": "Nouvelle conversation",
        "messages": [],
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

# ── Sidebar ────────────────────────────────────────────────────────────────────
sidebar_brand()

if st.sidebar.button("✏️  Nouvelle conversation", use_container_width=True):
    new_conversation()
    st.rerun()

st.sidebar.markdown("<hr style='border-color:rgba(255,255,255,0.08);margin:8px 12px;'>",
                    unsafe_allow_html=True)

# Group conversations by date
today     = datetime.now().date()
today_convs  = []
older_convs  = []
for c_id, c in reversed(list(st.session_state.conversations.items())):
    if c["timestamp"].date() == today:
        today_convs.append((c_id, c))
    else:
        older_convs.append((c_id, c))

def render_conv_list(items):
    for c_id, c in items:
        label = c["title"][:38] + "…" if len(c["title"]) > 38 else c["title"]
        active = c_id == st.session_state.current_conv_id
        if st.sidebar.button(
            label,
            key=f"conv_{c_id}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            st.session_state.current_conv_id = c_id
            st.rerun()

if today_convs:
    st.sidebar.markdown("<div class='conv-group-label'>Aujourd'hui</div>",
                        unsafe_allow_html=True)
    render_conv_list(today_convs)

if older_convs:
    st.sidebar.markdown("<div class='conv-group-label'>Précédentes</div>",
                        unsafe_allow_html=True)
    render_conv_list(older_convs)

# ── Main layout ────────────────────────────────────────────────────────────────
col_chat, col_side = st.columns([3, 1], gap="medium")

# ══ CHAT COLUMN ════════════════════════════════════════════════════════════════
with col_chat:
    st.markdown("<h2 style='margin-bottom:2px;'>💬 Assistant Statistique</h2>",
                unsafe_allow_html=True)
    st.caption("Posez vos questions sur les données officielles du Sénégal")
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    if not conv["messages"]:
        empty_state("📊",
            "Commencez par poser une question ou choisissez un exemple sur la page d'accueil.")
    else:
        for msg in conv["messages"]:
            avatar = "🧑" if msg["role"] == "user" else "📊"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
                if msg["role"] == "assistant":
                    ts = msg.get("timestamp", "")
                    intent_key = msg.get("intent", "")
                    icon, label = INTENT_LABELS.get(intent_key, ("", ""))
                    parts = [p for p in [ts, f"{icon} {label}" if label else ""] if p]
                    if parts:
                        st.caption("  ·  ".join(parts))

    prefill = st.session_state.pop("prefill_query", None)
    prompt  = st.chat_input("Ex: Quel est le taux de pauvreté en 2021 ?") or prefill

    if prompt:
        now = datetime.now().strftime("%H:%M")

        # Auto-title from first question
        if conv["title"] == "Nouvelle conversation":
            conv["title"] = prompt[:50]

        conv["messages"].append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="📊"):
            with st.spinner("Recherche dans les sources officielles…"):
                try:
                    resp = httpx.post(
                        f"{API_URL}/query",
                        json={"query": prompt},
                        timeout=90.0,
                    )
                    resp.raise_for_status()
                    data      = resp.json()
                    answer    = data["answer"]
                    citations = data.get("citations", [])
                    intent    = data.get("intent", "")
                except httpx.ConnectError:
                    answer    = "⚠️ Impossible de contacter l'API. Vérifiez que le serveur tourne sur le port 8000."
                    citations = []
                    intent    = ""
                except Exception as e:
                    answer    = f"⚠️ Erreur : {e}"
                    citations = []
                    intent    = ""

            st.markdown(answer)
            icon, label = INTENT_LABELS.get(intent, ("", ""))
            parts = [now] + ([f"{icon} {label}"] if label else [])
            st.caption("  ·  ".join(parts))

        conv["messages"].append({
            "role": "assistant",
            "content": answer,
            "intent": intent,
            "timestamp": now,
        })
        conv["citations"] = citations
        st.rerun()

# ══ SIDE COLUMN ════════════════════════════════════════════════════════════════
with col_side:
    st.markdown("#### 📎 Sources citées")
    citations = conv.get("citations", [])

    if not citations:
        st.markdown("""
<div style="background:white;border-radius:10px;padding:16px;text-align:center;
            color:#bbb;font-size:0.83rem;box-shadow:0 1px 4px rgba(0,0,0,0.05);">
    Les sources apparaîtront<br>après votre première question.
</div>
""", unsafe_allow_html=True)
    else:
        for c in citations:
            url_html = (f'<a href="{c["url"]}" target="_blank" '
                        f'style="color:#00853F;text-decoration:none;">↗</a>'
                        if c.get("url") else "")
            st.markdown(f"""
<div class="citation-card">
    <div class="source">{c.get("institution","?")} {url_html}</div>
    <div style="font-size:0.82rem;color:#333;margin:2px 0;">{c.get("report_name","?")}</div>
    <div class="details">{c.get("year","?")} · page {c.get("page","?")}</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if conv["messages"]:
        n_turns = sum(1 for m in conv["messages"] if m["role"] == "user")
        st.markdown(f"""
<div class="card" style="padding:14px;text-align:center;">
    <div style="display:flex;justify-content:space-around;">
        <div>
            <div style="font-size:1.4rem;font-weight:700;color:#00853F;">{n_turns}</div>
            <div style="font-size:0.72rem;color:#888;">questions</div>
        </div>
        <div>
            <div style="font-size:1.4rem;font-weight:700;color:#00853F;">{len(citations)}</div>
            <div style="font-size:0.72rem;color:#888;">sources</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑 Effacer cette conversation", use_container_width=True):
            conv["messages"] = []
            conv["citations"] = []
            conv["title"] = "Nouvelle conversation"
            st.rerun()
