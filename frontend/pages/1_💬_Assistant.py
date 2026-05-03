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
from frontend.style import inject_css, sidebar_brand, section_label, empty_state

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
    "compare": ("⚖️",  "Comparaison"),
    "compute": ("🧮", "Calcul statistique"),
    "viz":     ("📊", "Visualisation"),
    "mixed":   ("🔀", "Requête mixte"),
}

QUICK = [
    ("🏙️", "Population totale du Sénégal en 2023 ?"),
    ("📉", "Taux de pauvreté au Sénégal en 2021 ?"),
    ("💼", "Taux de chômage au Sénégal ?"),
    ("📈", "Taux de croissance du PIB ?"),
    ("💧", "Accès à l'eau potable en milieu rural ?"),
    ("📚", "Taux d'alphabétisation au Sénégal ?"),
]

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

# ── Sidebar ─────────────────────────────────────────────────────────────────────
sidebar_brand()

if st.sidebar.button("✏️  Nouvelle conversation", use_container_width=True):
    new_conversation()
    st.rerun()

st.sidebar.markdown(
    "<hr style='border-color:rgba(255,255,255,0.08);margin:8px 12px;'>",
    unsafe_allow_html=True,
)

today      = datetime.now().date()
today_convs, older_convs = [], []
for c_id, c in reversed(list(st.session_state.conversations.items())):
    # Skip placeholder conversations with no messages
    if c["title"] == "Nouvelle conversation" and not c["messages"]:
        continue
    if c["timestamp"].date() == today:
        today_convs.append((c_id, c))
    else:
        older_convs.append((c_id, c))

def render_conv_list(items):
    for c_id, c in items:
        label  = c["title"][:38] + "…" if len(c["title"]) > 38 else c["title"]
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
    st.sidebar.markdown(
        "<div class='conv-group-label'>Aujourd'hui</div>",
        unsafe_allow_html=True,
    )
    render_conv_list(today_convs)

if older_convs:
    st.sidebar.markdown(
        "<div class='conv-group-label'>Précédentes</div>",
        unsafe_allow_html=True,
    )
    render_conv_list(older_convs)

# ── Page banner ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-banner">
    <div class="page-banner-icon">📊</div>
    <div>
        <div class="page-banner-title">Assistant Statistique</div>
        <div class="page-banner-sub">
            Données officielles du Sénégal &nbsp;·&nbsp; ANSD &nbsp;·&nbsp; DPEE &nbsp;·&nbsp; BCEAO
            &nbsp;·&nbsp; Réponses sourcées et vérifiées
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Layout: right column only when there are citations ───────────────────────────
citations = conv.get("citations", [])
has_conv  = bool(conv["messages"])

if citations:
    col_chat, col_side = st.columns([3, 1], gap="medium")
else:
    col_chat = st.container()
    col_side = None

# ══ CHAT COLUMN ══════════════════════════════════════════════════════════════════
with col_chat:
    # Quick questions — only shown before any conversation starts
    if not has_conv:
        section_label("Questions fréquentes — cliquez pour une réponse rapide")
        scols = st.columns(3, gap="small")
        for i, (icon, q) in enumerate(QUICK):
            with scols[i % 3]:
                if st.button(f"{icon}  {q}", key=f"quick_{i}", use_container_width=True):
                    st.session_state["prefill_query"] = q
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Chat history
    for msg in conv["messages"]:
        avatar = "🧑" if msg["role"] == "user" else "📊"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                ts         = msg.get("timestamp", "")
                intent_key = msg.get("intent", "")
                icon, label = INTENT_LABELS.get(intent_key, ("", ""))
                parts = [p for p in [ts, f"{icon} {label}" if label else ""] if p]
                if parts:
                    st.caption("  ·  ".join(parts))
                # Inline source pills
                if msg.get("citations"):
                    pills = "".join(
                        f'<span class="citation-pill">📎 {c.get("institution","?")} — '
                        f'{c.get("report_name","?")} (p.{c.get("page","?")})</span>'
                        for c in msg["citations"][:4]
                    )
                    st.markdown(
                        f'<div style="margin-top:6px">{pills}</div>',
                        unsafe_allow_html=True,
                    )

    # Chat input
    prefill = st.session_state.pop("prefill_query", None)
    prompt  = st.chat_input("Ex: Quel est le taux de pauvreté en 2021 ?") or prefill

    if prompt:
        now = datetime.now().strftime("%H:%M")

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
                    new_cites = data.get("citations", [])
                    intent    = data.get("intent", "")
                except httpx.ConnectError:
                    answer    = "⚠️ Impossible de contacter l'API. Vérifiez que le serveur tourne sur le port 8000."
                    new_cites = []
                    intent    = ""
                except Exception as e:
                    answer    = f"⚠️ Erreur : {e}"
                    new_cites = []
                    intent    = ""

            st.markdown(answer)
            icon, label = INTENT_LABELS.get(intent, ("", ""))
            parts = [now] + ([f"{icon} {label}"] if label else [])
            st.caption("  ·  ".join(parts))

            if new_cites:
                pills = "".join(
                    f'<span class="citation-pill">📎 {c.get("institution","?")} — '
                    f'{c.get("report_name","?")} (p.{c.get("page","?")})</span>'
                    for c in new_cites[:4]
                )
                st.markdown(
                    f'<div style="margin-top:6px">{pills}</div>',
                    unsafe_allow_html=True,
                )

        conv["messages"].append({
            "role":      "assistant",
            "content":   answer,
            "intent":    intent,
            "timestamp": now,
            "citations": new_cites,
        })
        conv["citations"] = new_cites
        st.rerun()

# ══ SIDE COLUMN — only rendered when citations exist ════════════════════════════
if col_side and citations:
    with col_side:
        st.markdown("#### 📎 Sources citées")

        for c in citations:
            url_html = (
                f'<a href="{c["url"]}" target="_blank" '
                f'style="color:#00853F;text-decoration:none;">↗</a>'
                if c.get("url") else ""
            )
            st.markdown(f"""
<div class="citation-card">
    <div class="source">{c.get("institution","?")} {url_html}</div>
    <div style="font-size:0.82rem;color:#333;margin:2px 0;">{c.get("report_name","?")}</div>
    <div class="details">{c.get("year","?")} · page {c.get("page","?")}</div>
</div>
""", unsafe_allow_html=True)

        n_turns = sum(1 for m in conv["messages"] if m["role"] == "user")
        st.markdown(f"""
<div class="card" style="padding:14px;text-align:center;margin-top:12px;">
    <div style="display:flex;justify-content:space-around;">
        <div>
            <div style="font-size:1.3rem;font-weight:700;color:#00853F;">{n_turns}</div>
            <div style="font-size:0.72rem;color:#888;">questions</div>
        </div>
        <div>
            <div style="font-size:1.3rem;font-weight:700;color:#00853F;">{len(citations)}</div>
            <div style="font-size:0.72rem;color:#888;">sources</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div style="background:#F0FFF4;border-radius:10px;padding:12px;font-size:0.77rem;
            color:#2D6A4F;margin-top:10px;">
    <strong>✅ Données vérifiées</strong><br><br>
    Réponses issues des rapports officiels ANSD, DPEE et BCEAO uniquement.
</div>
""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑 Effacer cette conversation", use_container_width=True):
            conv["messages"]  = []
            conv["citations"] = []
            conv["title"]     = "Nouvelle conversation"
            st.rerun()
