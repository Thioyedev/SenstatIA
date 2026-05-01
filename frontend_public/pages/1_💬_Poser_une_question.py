import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import httpx
from frontend_public.style_public import inject_css, sidebar_brand, section_lbl

st.set_page_config(
    page_title="Question — SenStat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
sidebar_brand()

API_URL = "http://localhost:8000"

SUGGESTIONS = {
    "Population":  "Quelle est la population totale du Sénégal en 2023 ?",
    "Pauvreté":    "Quel est le taux de pauvreté au Sénégal en 2021 ?",
    "Économie":    "Quel est le taux de croissance du PIB du Sénégal ?",
    "Santé":       "Quel est le taux de mortalité infantile au Sénégal ?",
    "Éducation":   "Quel est le taux d'alphabétisation au Sénégal ?",
    "Agriculture": "Quelle est la part de l'agriculture dans le PIB sénégalais ?",
}

if "pub_messages"       not in st.session_state: st.session_state.pub_messages       = []
if "pub_last_citations" not in st.session_state: st.session_state.pub_last_citations = []

# ── Header ──────────────────────────────────────────────────────────────────────
st.markdown("<h2 style='margin-bottom:4px;'>💬 Posez votre question</h2>",
            unsafe_allow_html=True)
st.caption("Nos réponses sont tirées exclusivement des rapports officiels du Sénégal.")
st.markdown("<hr class='divider'>", unsafe_allow_html=True)

col_main, col_side = st.columns([3, 1], gap="large")

# ══ MAIN COLUMN ════════════════════════════════════════════════════════════════
with col_main:
    # Suggestions rapides
    theme_query = st.session_state.pop("theme_query", None)
    if theme_query and theme_query in SUGGESTIONS:
        st.session_state.pub_messages = []
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

    # Message history
    if not st.session_state.pub_messages:
        st.markdown("""
<div style="text-align:center; padding:32px; color:#bbb;">
    <div style="font-size:2.5rem; margin-bottom:10px;">🇸🇳</div>
    <div style="font-size:0.95rem; color:#aaa;">
        Posez votre question ci-dessous ou choisissez un exemple.
    </div>
</div>
""", unsafe_allow_html=True)
    else:
        for msg in st.session_state.pub_messages:
            avatar = "🧑" if msg["role"] == "user" else "🇸🇳"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # Input
    prefill = st.session_state.pop("pub_prefill", None)
    prompt  = st.chat_input("Ex : Quel est le taux de pauvreté au Sénégal ?") or prefill

    if prompt:
        st.session_state.pub_messages.append({"role": "user", "content": prompt})

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
                except Exception as e:
                    answer    = "⚠️ Le service est momentanément indisponible. Réessayez dans quelques instants."
                    citations = []

            st.markdown(answer)

            # Sources en bas de réponse — format grand public
            if citations:
                st.markdown("<br>", unsafe_allow_html=True)
                pills = ""
                for c in citations[:4]:
                    pills += f'<span class="source-pill">📎 {c.get("institution","?")} — {c.get("report_name","?")} (p.{c.get("page","?")})</span>'
                st.markdown(f'<div>{pills}</div>', unsafe_allow_html=True)

        st.session_state.pub_messages.append({"role": "assistant", "content": answer})
        st.session_state.pub_last_citations = citations
        st.rerun()

# ══ SIDE COLUMN ════════════════════════════════════════════════════════════════
with col_side:
    st.markdown("#### 📎 Sources utilisées")

    citations = st.session_state.get("pub_last_citations", [])
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
            if key in seen: continue
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
    Aucune information n'est inventée.
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.pub_messages:
        if st.button("🔄 Nouvelle conversation", use_container_width=True):
            st.session_state.pub_messages       = []
            st.session_state.pub_last_citations = []
            st.rerun()
