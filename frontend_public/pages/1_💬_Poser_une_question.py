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
from frontend_public.style_public import inject_css, sidebar_brand, section_lbl

st.set_page_config(
    page_title="Question — SenStat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

API_URL = os.getenv("API_URL", "http://localhost:8000")

SUGGESTIONS = {
    "Population":  "Quelle est la population totale du Sénégal en 2023 ?",
    "Pauvreté":    "Quel est le taux de pauvreté au Sénégal en 2021 ?",
    "Économie":    "Quel est le taux de croissance du PIB du Sénégal ?",
    "Santé":       "Quel est le taux de mortalité infantile au Sénégal ?",
    "Éducation":   "Quel est le taux d'alphabétisation au Sénégal ?",
    "Agriculture": "Quelle est la part de l'agriculture dans le PIB sénégalais ?",
}

# ── Conversation state ─────────────────────────────────────────────────────────
def new_conversation():
    cid = str(uuid.uuid4())
    st.session_state.pub_conversations[cid] = {
        "title": "Nouvelle conversation",
        "messages": [],
        "citations": [],
        "timestamp": datetime.now(),
    }
    st.session_state.pub_current_id = cid

if "pub_conversations" not in st.session_state:
    st.session_state.pub_conversations = {}
    new_conversation()

if "pub_current_id" not in st.session_state or \
        st.session_state.pub_current_id not in st.session_state.pub_conversations:
    new_conversation()

cid  = st.session_state.pub_current_id
conv = st.session_state.pub_conversations[cid]

# ── Sidebar ────────────────────────────────────────────────────────────────────
sidebar_brand()

if st.sidebar.button("✏️  Nouvelle conversation", use_container_width=True):
    new_conversation()
    st.rerun()

st.sidebar.markdown("<hr style='border-color:rgba(255,255,255,0.08);margin:8px 12px;'>",
                    unsafe_allow_html=True)

today = datetime.now().date()
today_convs = []
older_convs = []
for c_id, c in reversed(list(st.session_state.pub_conversations.items())):
    if c["timestamp"].date() == today:
        today_convs.append((c_id, c))
    else:
        older_convs.append((c_id, c))

def render_conv_list(items):
    for c_id, c in items:
        label = c["title"][:38] + "…" if len(c["title"]) > 38 else c["title"]
        active = c_id == st.session_state.pub_current_id
        if st.sidebar.button(
            label,
            key=f"pub_conv_{c_id}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            st.session_state.pub_current_id = c_id
            st.rerun()

if today_convs:
    st.sidebar.markdown("<div class='conv-group-label'>Aujourd'hui</div>",
                        unsafe_allow_html=True)
    render_conv_list(today_convs)

if older_convs:
    st.sidebar.markdown("<div class='conv-group-label'>Précédentes</div>",
                        unsafe_allow_html=True)
    render_conv_list(older_convs)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("<h2 style='margin-bottom:4px;'>💬 Posez votre question</h2>",
            unsafe_allow_html=True)
st.caption("Nos réponses sont tirées exclusivement des rapports officiels du Sénégal.")
st.markdown("<hr class='divider'>", unsafe_allow_html=True)

col_main, col_side = st.columns([3, 1], gap="large")

# ══ MAIN COLUMN ════════════════════════════════════════════════════════════════
with col_main:
    theme_query = st.session_state.pop("theme_query", None)
    if theme_query and theme_query in SUGGESTIONS:
        st.session_state["pub_prefill"] = SUGGESTIONS[theme_query]

    section_lbl("Questions fréquentes — cliquez pour obtenir une réponse")
    scols = st.columns(3, gap="small")
    quick = [
        "Population totale du Sénégal 2023 ?",
        "Taux de pauvreté en 2021 ?",
        "Taux de chômage au Sénégal ?",
        "Régions les plus pauvres ?",
        "Accès à l'eau potable ?",
        "Taux de scolarisation ?",
    ]
    for i, q in enumerate(quick):
        with scols[i % 3]:
            if st.button(q, key=f"quick_{i}", use_container_width=True):
                st.session_state["pub_prefill"] = q

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    if not conv["messages"]:
        st.markdown("""
<div style="text-align:center;padding:32px;color:#bbb;">
    <div style="font-size:2.5rem;margin-bottom:10px;">🇸🇳</div>
    <div style="font-size:0.95rem;color:#aaa;">
        Posez votre question ci-dessous ou choisissez un exemple.
    </div>
</div>
""", unsafe_allow_html=True)
    else:
        for msg in conv["messages"]:
            avatar = "🧑" if msg["role"] == "user" else "🇸🇳"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    prefill = st.session_state.pop("pub_prefill", None)
    prompt  = st.chat_input("Ex : Quel est le taux de pauvreté au Sénégal ?") or prefill

    if prompt:
        if conv["title"] == "Nouvelle conversation":
            conv["title"] = prompt[:50]

        conv["messages"].append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🇸🇳"):
            with st.spinner("Recherche dans les rapports officiels…"):
                try:
                    resp = httpx.post(f"{API_URL}/query",
                                      json={"query": prompt}, timeout=90.0)
                    resp.raise_for_status()
                    data      = resp.json()
                    answer    = data["answer"]
                    citations = data.get("citations", [])
                except Exception:
                    answer    = "⚠️ Le service est momentanément indisponible. Réessayez dans quelques instants."
                    citations = []

            st.markdown(answer)

            if citations:
                st.markdown("<br>", unsafe_allow_html=True)
                pills = ""
                for c in citations[:4]:
                    pills += f'<span class="source-pill">📎 {c.get("institution","?")} — {c.get("report_name","?")} (p.{c.get("page","?")})</span>'
                st.markdown(f'<div>{pills}</div>', unsafe_allow_html=True)

        conv["messages"].append({"role": "assistant", "content": answer})
        conv["citations"] = citations
        st.rerun()

# ══ SIDE COLUMN ════════════════════════════════════════════════════════════════
with col_side:
    st.markdown("#### 📎 Sources utilisées")
    citations = conv.get("citations", [])

    if not citations:
        st.markdown("""
<div style="background:white;border-radius:12px;padding:16px;text-align:center;
            color:#ccc;font-size:0.82rem;box-shadow:0 1px 4px rgba(0,0,0,0.05);">
    Les sources officielles apparaîtront ici.
</div>
""", unsafe_allow_html=True)
    else:
        seen = set()
        for c in citations:
            key = c.get("source_id")
            if key in seen:
                continue
            seen.add(key)
            st.markdown(f"""
<div style="background:white;border-radius:10px;padding:12px 14px;margin:6px 0;
            box-shadow:0 1px 4px rgba(0,0,0,0.06);border-left:3px solid #00853F;">
    <div style="font-weight:600;font-size:0.83rem;color:#00853F;">{c.get('institution','?')}</div>
    <div style="font-size:0.8rem;color:#333;margin:3px 0;">{c.get('report_name','?')}</div>
    <div style="font-size:0.7rem;color:#888;">{c.get('year','?')}</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
<div style="background:#F0FFF4;border-radius:10px;padding:14px;font-size:0.78rem;color:#2D6A4F;">
    <strong>✅ Données vérifiées</strong><br><br>
    Toutes les réponses proviennent uniquement des rapports officiels de l'ANSD, DPEE et BCEAO.
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if conv["messages"]:
        if st.button("🔄 Nouvelle conversation", use_container_width=True):
            new_conversation()
            st.rerun()
