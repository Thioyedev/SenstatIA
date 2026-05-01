import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from frontend_public.style_public import inject_css, sidebar_brand, section_lbl, fact_card

st.set_page_config(
    page_title="SenStat — Statistiques du Sénégal",
    page_icon="🇸🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
sidebar_brand()

# ── Hero ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-public">
    <div style="position:relative; z-index:1;">
        <div class="eyebrow">🇸🇳 Données officielles du Sénégal</div>
        <h1>Les chiffres officiels,<br>à portée de main.</h1>
        <div class="sub">
            Posez vos questions sur la population, l'économie, la santé ou
            la pauvreté au Sénégal — et obtenez une réponse tirée directement
            des rapports officiels, avec la source exacte.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── CTA buttons ─────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([2, 2, 5])
with c1:
    if st.button("💬 Poser une question", use_container_width=True, type="primary"):
        st.switch_page("pages/1_💬_Poser_une_question.py")
with c2:
    if st.button("📋 Parcourir les thèmes", use_container_width=True):
        st.switch_page("pages/2_📋_Thèmes.py")

st.markdown("<br>", unsafe_allow_html=True)

# ── Key facts ────────────────────────────────────────────────────────────────────
section_lbl("Le Sénégal en chiffres clés")
c1, c2, c3, c4 = st.columns(4, gap="small")
with c1:
    fact_card("Population", "17,7 M", "habitants au Sénégal en 2023", "RGPH-5, ANSD 2023")
with c2:
    fact_card("Pauvreté", "37,5 %", "des Sénégalais vivent sous le seuil de pauvreté", "EHCVM 2021-2022, ANSD")
with c3:
    fact_card("Croissance", "+8,3 %", "de croissance du PIB prévue en 2024 (pétrole/gaz)", "SES 2022-2023, ANSD")
with c4:
    fact_card("Chômage", "23,2 %", "taux de chômage au sens du BIT (2023)", "RGPH-5, ANSD 2023")

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── Themes ───────────────────────────────────────────────────────────────────────
section_lbl("Explorer par thème")

THEMES = [
    ("👥", "Population",  "Démographie, régions, ménages, migrations",     "RGPH-5 2023"),
    ("💰", "Pauvreté",    "Inégalités, conditions de vie, accès aux services", "EHCVM 2021-2022"),
    ("📈", "Économie",    "PIB, emploi, secteurs, croissance",              "SES 2022-2023"),
    ("🏥", "Santé",       "Mortalité, nutrition, accès aux soins",          "EDS + SES 2023"),
    ("🎓", "Éducation",   "Scolarisation, alphabétisation, formation",      "SES 2022-2023"),
    ("🌾", "Agriculture", "Productions, filières, sécurité alimentaire",    "SES 2022-2023"),
]

cols = st.columns(3, gap="small")
for i, (emoji, name, desc, src) in enumerate(THEMES):
    with cols[i % 3]:
        st.markdown(f"""
<div class="theme-card">
    <div class="emoji">{emoji}</div>
    <div class="name">{name}</div>
    <div class="desc">{desc}</div>
    <div class="count">📄 {src}</div>
</div>
""", unsafe_allow_html=True)
        if st.button(f"Explorer {name}", key=f"theme_{i}", use_container_width=True):
            st.session_state["theme_query"] = name
            st.switch_page("pages/1_💬_Poser_une_question.py")

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── How it works ─────────────────────────────────────────────────────────────────
section_lbl("Comment ça marche ?")
c1, c2, c3 = st.columns(3, gap="small")

for col, (n, icon, title, desc) in zip([c1, c2, c3], [
    ("1", "💬", "Posez votre question",
     "En français, librement. Pas besoin de connaître le nom du rapport."),
    ("2", "🔍", "Nous cherchons dans les sources officielles",
     "Notre système consulte les rapports ANSD, DPEE, BCEAO — pas Internet."),
    ("3", "📎", "Vous obtenez la réponse avec sa source",
     "Chaque chiffre est accompagné du rapport et de la page d'origine."),
]):
    with col:
        st.markdown(f"""
<div class="fact-card" style="border-bottom:none; border-top:3px solid #00853F; text-align:center; padding:24px 16px;">
    <div style="font-size:2rem; margin-bottom:8px;">{icon}</div>
    <div style="font-size:0.68rem; font-weight:700; color:#00853F; letter-spacing:0.8px; margin-bottom:6px;">ÉTAPE {n}</div>
    <div style="font-weight:700; font-size:0.97rem; color:#1A1A2E; margin-bottom:8px;">{title}</div>
    <div style="font-size:0.82rem; color:#666; line-height:1.5;">{desc}</div>
</div>
""", unsafe_allow_html=True)

# ── Footer ───────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; color:#ccc; font-size:0.73rem; padding:8px 0 16px 0;">
    Données issues de l'ANSD, DPEE et BCEAO · SenStat ne remplace pas les rapports officiels
</div>
""", unsafe_allow_html=True)
