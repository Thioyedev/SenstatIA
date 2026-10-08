import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from frontend_public.style_public import inject_css, sidebar_brand, section_lbl, fact_card
from frontend_public.i18n import t, THEMES

st.set_page_config(
    page_title="SenStat — Statistiques du Sénégal",
    page_icon="🇸🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
sidebar_brand()

lang = st.session_state.get("lang", "fr")

# ── Hero ──────────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-public">
    <div style="position:relative; z-index:1;">
        <div class="eyebrow">{t("home_eyebrow")}</div>
        <h1>{t("home_title")}</h1>
        <div class="sub">{t("home_sub")}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── CTA ────────────────────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([2, 2, 5])
with c1:
    if st.button(t("home_cta_ask"), use_container_width=True, type="primary"):
        st.switch_page("pages/1_💬_Poser_une_question.py")
with c2:
    if st.button(t("home_cta_themes"), use_container_width=True):
        st.switch_page("pages/2_📋_Thèmes.py")

st.markdown("<br>", unsafe_allow_html=True)

# ── Key facts ─────────────────────────────────────────────────────────────────────────────────
section_lbl(t("home_key_facts"))

FACTS = {
    "fr": [
        ("Population", "17,7 M",  "habitants au Sénégal en 2023",                  "RGPH-5, ANSD 2023"),
        ("Pauvreté",   "37,5 %",  "des Sénégalais vivent sous le seuil de pauvreté", "EHCVM 2021-2022, ANSD"),
        ("Croissance", "+8,3 %",  "de croissance du PIB prévue en 2024",             "FMI WEO 2025 · BDEF 2024, ANSD"),
        ("IDH",        "0.530",   "Indice de développement humain (rang 169/193)",   "PNUD 2024"),
    ],
    "en": [
        ("Population", "17.7 M",  "inhabitants in Senegal in 2023",                 "RGPH-5, ANSD 2023"),
        ("Poverty",    "37.5 %",  "of Senegalese live below the poverty line",      "EHCVM 2021-2022, ANSD"),
        ("Growth",     "+8.3 %",  "projected GDP growth in 2024 (oil & gas)",       "IMF WEO 2025 · BDEF 2024, ANSD"),
        ("HDI",        "0.530",   "Human Development Index (rank 169/193)",         "UNDP 2024"),
    ],
}

c1, c2, c3, c4 = st.columns(4, gap="small")
for col, (topic, stat, desc, src) in zip([c1, c2, c3, c4], FACTS[lang]):
    with col:
        fact_card(topic, stat, desc, src)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── Themes ──────────────────────────────────────────────────────────────────────────────────
section_lbl(t("home_explore"))
cols = st.columns(3, gap="small")
for i, (emoji, name, desc, src, color) in enumerate(THEMES[lang]):
    with cols[i % 3]:
        st.markdown(f"""
<div class="theme-card" style="border-top: 3px solid {color};">
    <div class="emoji">{emoji}</div>
    <div class="name">{name}</div>
    <div class="desc">{desc}</div>
    <div class="source">📄 {src}</div>
</div>
""", unsafe_allow_html=True)
        if st.button(f"{t('explore_btn')} →", key=f"theme_{i}", use_container_width=True):
            st.session_state["theme_query"] = name
            st.switch_page("pages/1_💬_Poser_une_question.py")

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── How it works ────────────────────────────────────────────────────────────────────────────────
section_lbl(t("home_how"))
c1, c2, c3 = st.columns(3, gap="small")
steps = [
    ("💬", t("home_step1_n"), t("home_step1_title"), t("home_step1_desc")),
    ("🔍", t("home_step2_n"), t("home_step2_title"), t("home_step2_desc")),
    ("📎", t("home_step3_n"), t("home_step3_title"), t("home_step3_desc")),
]
for col, (icon, n, title, desc) in zip([c1, c2, c3], steps):
    with col:
        st.markdown(f"""
<div class="fact-card" style="border-bottom:none;border-top:3px solid #00853F;
     text-align:center;padding:24px 16px;">
    <div style="font-size:2rem;margin-bottom:8px;">{icon}</div>
    <div style="font-size:0.68rem;font-weight:700;color:#00853F;letter-spacing:0.8px;margin-bottom:6px;">{n}</div>
    <div style="font-weight:700;font-size:0.97rem;color:#1A1A2E;margin-bottom:8px;">{title}</div>
    <div style="font-size:0.82rem;color:#666;line-height:1.5;">{desc}</div>
</div>
""", unsafe_allow_html=True)

# ── Footer ──────────────────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="text-align:center;color:#ccc;font-size:0.73rem;padding:8px 0 16px 0;">
    {t("home_footer")}
</div>
""", unsafe_allow_html=True)
