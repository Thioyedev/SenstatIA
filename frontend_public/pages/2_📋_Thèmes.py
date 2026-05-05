import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from frontend_public.style_public import inject_css, sidebar_brand, section_lbl
from frontend_public.i18n import t, THEMES, THEME_QUESTIONS

st.set_page_config(
    page_title="Thèmes — SenStat",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
sidebar_brand()

lang = st.session_state.get("lang", "fr")

st.markdown(f"<h2>{t('themes_title')}</h2>", unsafe_allow_html=True)
st.caption(t("themes_caption"))
st.markdown("<hr class='divider'>", unsafe_allow_html=True)

questions = THEME_QUESTIONS[lang]

for emoji, name, desc, src, color in THEMES[lang]:
    theme_qs = questions.get(name, [])
    with st.expander(f"**{emoji} {name}**", expanded=False):
        st.caption(f"{desc} · {src}")
        cols = st.columns(2, gap="small")
        for i, q in enumerate(theme_qs):
            with cols[i % 2]:
                if st.button(q, key=f"{name}_{i}", use_container_width=True):
                    st.session_state["pub_prefill"] = q
                    st.switch_page("pages/1_💬_Poser_une_question.py")

st.markdown("<hr class='divider'>", unsafe_allow_html=True)
st.markdown(f"""
<div style="text-align:center;color:#bbb;font-size:0.75rem;padding:8px 0 16px 0;">
    {t("themes_footer")}
</div>
""", unsafe_allow_html=True)
