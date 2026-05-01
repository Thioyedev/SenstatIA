import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import httpx
from datetime import datetime
from frontend.style import inject_css, sidebar_brand, empty_state

st.set_page_config(
    page_title="Assistant — SenStat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
sidebar_brand()

API_URL = "http://localhost:8000"

INTENT_LABELS = {
    "lookup":  ("🔎", "Recherche ponctuelle"),
    "trend":   ("📈", "Analyse de tendance"),
    "compare": ("⚖️", "Comparaison"),
    "compute": ("🧮", "Calcul statistique"),
    "viz":     ("📊", "Visualisation"),
    "mixed":   ("🔀", "Requête mixte"),
}

# ── State ──────────────────────────────────────────────────────────────────────
if "messages"       not in st.session_state: st.session_state.messages       = []
if "last_citations" not in st.session_state: st.session_state.last_citations = []
if "last_intent"    not in st.session_state: st.session_state.last_intent    = ""

# ── Layout ─────────────────────────────────────────────────────────────────────
col_chat, col_side = st.columns([3, 1], gap="medium")

# ══ CHAT COLUMN ════════════════════════════════════════════════════════════════
with col_chat:
    st.markdown("<h2 style='margin-bottom:2px;'>💬 Assistant Statistique</h2>",
                unsafe_allow_html=True)
    st.caption("Posez vos questions sur les données officielles du Sénégal")
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # Message history
    if not st.session_state.messages:
        empty_state("📊",
            "Commencez par poser une question ou choisissez un exemple sur la page d'accueil.")
    else:
        for msg in st.session_state.messages:
            avatar = "🧑" if msg["role"] == "user" else "📊"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
                if msg["role"] == "assistant":
                    ts = msg.get("timestamp", "")
                    intent_key = msg.get("intent", "")
                    intent_icon, intent_label = INTENT_LABELS.get(intent_key, ("", ""))
                    meta_parts = []
                    if ts: meta_parts.append(ts)
                    if intent_label: meta_parts.append(f"{intent_icon} {intent_label}")
                    if meta_parts:
                        st.caption("  ·  ".join(meta_parts))

    # Prefill from home demo
    prefill = st.session_state.pop("prefill_query", None)
    prompt  = st.chat_input("Ex: Quel est le taux de pauvreté en 2021 ?") or prefill

    if prompt:
        now = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({"role": "user", "content": prompt})

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
            intent_icon, intent_label = INTENT_LABELS.get(intent, ("", ""))
            meta_parts = [now]
            if intent_label: meta_parts.append(f"{intent_icon} {intent_label}")
            st.caption("  ·  ".join(meta_parts))

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "intent": intent,
            "timestamp": now,
        })
        st.session_state.last_citations = citations
        st.session_state.last_intent    = intent
        st.rerun()

# ══ SIDE COLUMN ════════════════════════════════════════════════════════════════
with col_side:
    # Citations panel
    st.markdown("#### 📎 Sources citées")
    citations = st.session_state.get("last_citations", [])

    if not citations:
        st.markdown("""
<div style="background:white; border-radius:10px; padding:16px; text-align:center;
            color:#bbb; font-size:0.83rem; box-shadow:0 1px 4px rgba(0,0,0,0.05);">
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

    # Stats panel
    if st.session_state.messages:
        n_turns = sum(1 for m in st.session_state.messages if m["role"] == "user")
        n_cit   = len(citations)
        st.markdown(f"""
<div class="card" style="padding:14px; text-align:center;">
    <div style="display:flex; justify-content:space-around;">
        <div>
            <div style="font-size:1.4rem;font-weight:700;color:#00853F;">{n_turns}</div>
            <div style="font-size:0.72rem;color:#888;">questions</div>
        </div>
        <div>
            <div style="font-size:1.4rem;font-weight:700;color:#00853F;">{n_cit}</div>
            <div style="font-size:0.72rem;color:#888;">sources citées</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑 Effacer la conversation", use_container_width=True):
            st.session_state.messages       = []
            st.session_state.last_citations = []
            st.rerun()
