import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from frontend_public.style_public import inject_css, sidebar_brand
from frontend_public.i18n import t, FAQ_ITEMS

st.set_page_config(
    page_title="FAQ — SenStat",
    page_icon="❓",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
sidebar_brand()

lang = st.session_state.get("lang", "fr")

st.markdown(f"<h2>{t('faq_title')}</h2>", unsafe_allow_html=True)
st.caption(t("faq_caption"))
st.markdown("<hr class='divider'>", unsafe_allow_html=True)

for question, answer in FAQ_ITEMS[lang]:
    with st.expander(f"**{question}**", expanded=False):
        st.markdown(answer)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)
st.markdown(f"""
<div style="background:white;border-radius:14px;padding:24px 28px;
            box-shadow:0 2px 8px rgba(0,0,0,0.07);text-align:center;">
    <div style="font-size:1.5rem;margin-bottom:8px;">💬</div>
    <div style="font-weight:600;font-size:1rem;color:#1A1A2E;margin-bottom:6px;">
        {t("faq_cta_title")}
    </div>
    <div style="font-size:0.85rem;color:#666;margin-bottom:16px;">
        {t("faq_cta_desc")}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
if st.button(t("faq_cta_btn"), type="primary"):
    st.switch_page("pages/1_💬_Poser_une_question.py")
