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
from frontend_public.i18n import t, QUICK

st.set_page_config(
    page_title="Question — SenStat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ── Conversation state ──────────────────────────────────────────────────────────
def new_conversation():
    cid = str(uuid.uuid4())
    st.session_state.pub_conversations[cid] = {
        "title":     t("new_conv").replace("✏️  ", ""),
        "messages":  [],
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

# ── Sidebar (toggle is inside sidebar_brand) ────────────────────────────────────
sidebar_brand()

if st.sidebar.button(t("new_conv"), use_container_width=True):
    new_conversation()
    st.rerun()

st.sidebar.markdown(
    "<hr style='border-color:rgba(255,255,255,0.08);margin:8px 12px;'>",
    unsafe_allow_html=True,
)

today      = datetime.now().date()
today_convs, older_convs = [], []
for c_id, c in reversed(list(st.session_state.pub_conversations.items())):
    if not c["messages"]:
        continue
    if c["timestamp"].date() == today:
        today_convs.append((c_id, c))
    else:
        older_convs.append((c_id, c))

def render_conv_list(items):
    for c_id, c in items:
        label  = c["title"][:38] + "…" if len(c["title"]) > 38 else c["title"]
        active = c_id == st.session_state.pub_current_id
        if st.sidebar.button(label, key=f"pub_conv_{c_id}",
                             use_container_width=True,
                             type="primary" if active else "secondary"):
            st.session_state.pub_current_id = c_id
            st.rerun()

if today_convs:
    st.sidebar.markdown(
        f"<div class='conv-group-label'>{t('today')}</div>",
        unsafe_allow_html=True,
    )
    render_conv_list(today_convs)

if older_convs:
    st.sidebar.markdown(
        f"<div class='conv-group-label'>{t('previous')}</div>",
        unsafe_allow_html=True,
    )
    render_conv_list(older_convs)

# ── Page banner ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-banner">
    <div class="page-banner-icon">💬</div>
    <div>
        <div class="page-banner-title">{t("q_banner_title")}</div>
        <div class="page-banner-sub">{t("q_banner_sub")}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Layout ───────────────────────────────────────────────────────────────────────
lang     = st.session_state.get("lang", "fr")
has_conv = bool(conv["messages"])

theme_query = st.session_state.pop("theme_query", None)
if theme_query:
    st.session_state["pub_prefill"] = theme_query

if not has_conv:
    section_lbl(t("q_quick_label"))
    scols = st.columns(3, gap="small")
    for i, (icon, q) in enumerate(QUICK[lang]):
        with scols[i % 3]:
            if st.button(f"{icon}  {q}", key=f"quick_{i}", use_container_width=True):
                st.session_state["pub_prefill"] = q
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

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
        f'<span class="source-pill">📎 {c.get("institution","?")} — '
        f'{c.get("report_name","?")}</span>'
        for c in _dedup_citations(cites)
    )
    if pills:
        st.markdown(f'<div style="margin-top:10px">{pills}</div>',
                    unsafe_allow_html=True)

for msg in conv["messages"]:
    avatar = "🧑" if msg["role"] == "user" else "🇸🇳"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("citations"):
            _render_pills(msg["citations"])

prefill = st.session_state.pop("pub_prefill", None)
prompt  = st.chat_input(t("q_chat_input")) or prefill

if prompt:
    if not conv["messages"]:
        conv["title"] = prompt[:50]

    conv["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🇸🇳"):
        with st.spinner(t("spinner")):
            try:
                resp = httpx.post(f"{API_URL}/query",
                                  json={"query": prompt}, timeout=90.0)
                resp.raise_for_status()
                data      = resp.json()
                answer    = data["answer"]
                new_cites = data.get("citations", [])
            except Exception:
                answer    = t("error")
                new_cites = []

        st.markdown(answer)
        _render_pills(new_cites)

    conv["messages"].append({
        "role":      "assistant",
        "content":   answer,
        "citations": new_cites,
    })
    st.rerun()
