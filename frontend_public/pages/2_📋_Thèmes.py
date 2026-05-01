import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from frontend_public.style_public import inject_css, sidebar_brand, section_lbl

st.set_page_config(
    page_title="Thèmes — SenStat",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
sidebar_brand()

st.markdown("<h2>📋 Explorez par thème</h2>", unsafe_allow_html=True)
st.caption("Choisissez un thème pour voir les questions les plus posées et obtenir une réponse immédiate.")
st.markdown("<hr class='divider'>", unsafe_allow_html=True)

THEMES = {
    "👥 Population": {
        "desc": "Recensement général (RGPH-5 2023) — démographie, régions, ménages",
        "questions": [
            "Quelle est la population totale du Sénégal en 2023 ?",
            "Quelle est la population de Dakar ?",
            "Quel est le taux de croissance démographique ?",
            "Quelle région est la plus peuplée du Sénégal ?",
            "Combien de ménages au Sénégal selon le RGPH-5 ?",
        ],
        "color": "#E8F5E9", "border": "#00853F",
    },
    "💰 Pauvreté & Conditions de vie": {
        "desc": "EHCVM 2021-2022 — inégalités, pauvreté, accès aux services",
        "questions": [
            "Quel est le taux de pauvreté au Sénégal en 2021 ?",
            "Quelles régions sont les plus pauvres ?",
            "Comment a évolué la pauvreté depuis 2018 ?",
            "Quel est le taux de pauvreté en milieu rural vs urbain ?",
            "Quel est l'indice de Gini au Sénégal ?",
        ],
        "color": "#FFF8E1", "border": "#F57F17",
    },
    "📈 Économie & Emploi": {
        "desc": "SES 2022-2023, DPEE — PIB, secteurs, chômage, croissance",
        "questions": [
            "Quel est le PIB du Sénégal en 2023 ?",
            "Quel est le taux de chômage au Sénégal ?",
            "Quels sont les principaux secteurs économiques ?",
            "Quelle est la croissance prévue avec le pétrole et le gaz ?",
            "Quel est le taux d'inflation au Sénégal ?",
        ],
        "color": "#E3F2FD", "border": "#1565C0",
    },
    "🏥 Santé": {
        "desc": "SES 2022-2023, EDS — mortalité, nutrition, accès aux soins",
        "questions": [
            "Quel est le taux de mortalité infantile au Sénégal ?",
            "Quelle est l'espérance de vie au Sénégal ?",
            "Quel est le taux de malnutrition chez les enfants ?",
            "Combien d'établissements de santé au Sénégal ?",
            "Quel est le taux de couverture vaccinale ?",
        ],
        "color": "#FCE4EC", "border": "#C62828",
    },
    "🎓 Éducation": {
        "desc": "SES 2022-2023 — scolarisation, alphabétisation, formation",
        "questions": [
            "Quel est le taux d'alphabétisation au Sénégal ?",
            "Quel est le taux de scolarisation au primaire ?",
            "Quelle est la parité filles/garçons à l'école ?",
            "Quel est le taux de réussite au BFEM ?",
            "Combien d'universités au Sénégal ?",
        ],
        "color": "#F3E5F5", "border": "#6A1B9A",
    },
    "🌾 Agriculture": {
        "desc": "SES 2022-2023 — productions, filières, sécurité alimentaire",
        "questions": [
            "Quelle est la part de l'agriculture dans le PIB ?",
            "Quelles sont les principales cultures au Sénégal ?",
            "Quelle est la production d'arachide au Sénégal ?",
            "Combien de personnes travaillent dans l'agriculture ?",
            "Quel est le niveau de sécurité alimentaire ?",
        ],
        "color": "#E8F5E9", "border": "#2E7D32",
    },
}

for theme_name, theme in THEMES.items():
    with st.expander(f"**{theme_name}**", expanded=False):
        st.caption(theme["desc"])
        cols = st.columns(2, gap="small")
        for i, q in enumerate(theme["questions"]):
            with cols[i % 2]:
                if st.button(q, key=f"{theme_name}_{i}", use_container_width=True):
                    st.session_state["pub_prefill"] = q
                    st.switch_page("pages/1_💬_Poser_une_question.py")

st.markdown("<hr class='divider'>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; color:#bbb; font-size:0.75rem; padding:8px 0 16px 0;">
    Vous ne trouvez pas votre thème ? Posez directement votre question dans l'onglet 💬
</div>
""", unsafe_allow_html=True)
