import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from frontend_public.style_public import inject_css, sidebar_brand

st.set_page_config(
    page_title="FAQ — SenStat",
    page_icon="❓",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
sidebar_brand()

st.markdown("<h2>❓ Questions fréquentes</h2>", unsafe_allow_html=True)
st.caption("Tout ce que vous devez savoir sur SenStat et les données utilisées.")
st.markdown("<hr class='divider'>", unsafe_allow_html=True)

FAQ = [
    ("D'où viennent les données ?",
     """Les données proviennent exclusivement des institutions officielles sénégalaises et internationales :
- **ANSD** (Agence Nationale de la Statistique et de la Démographie) — RGPH-5, EHCVM, SES
- **DPEE** (Direction de la Prévision et des Études Économiques)
- **BCEAO** (Banque Centrale des États de l'Afrique de l'Ouest)
- **Banque Mondiale** — Open Data Sénégal

SenStat ne collecte pas de données propres et ne navigue pas sur Internet."""),

    ("Les réponses sont-elles fiables ?",
     """Chaque réponse est tirée mot pour mot des rapports officiels. Le système cite toujours :
- Le nom du rapport
- L'institution qui l'a publié
- L'année de publication
- La page exacte

Si une information n'est pas dans les documents indexés, le système vous le dit clairement plutôt que d'inventer une réponse."""),

    ("Les données sont-elles à jour ?",
     """Les sources actuellement indexées sont :
- RGPH-5 (2023) — données les plus récentes sur la population
- EHCVM 2021-2022 — enquête sur les conditions de vie
- SES 2022-2023 — situation économique et sociale
- RGPH-5 Économie (2024)

Nous mettons à jour régulièrement avec les nouvelles publications de l'ANSD et du DPEE."""),

    ("Puis-je poser ma question en wolof ou en anglais ?",
     """Pour l'instant, SenStat répond principalement en **français**, qui est la langue des rapports officiels.
Vous pouvez poser votre question en anglais — le système comprendra et répondra en anglais,
mais les données resteront celles des rapports français de l'ANSD."""),

    ("Comment citer une réponse de SenStat ?",
     """Ne citez pas SenStat directement — citez la source officielle indiquée dans la réponse.

Exemple : *"Selon l'ANSD, Enquête EHCVM 2021-2022, p.27, le taux de pauvreté est de 37,5%."*

SenStat est un outil d'accès aux données, pas une source en lui-même."""),

    ("Quelle est la différence avec une recherche Google ?",
     """Google vous renvoie vers des pages web qui peuvent contenir des erreurs, des données obsolètes
ou des interprétations erronées.

SenStat lit directement dans les rapports PDF officiels et cite la page exacte.
Vous avez la garantie que le chiffre vient du document officiel, pas d'un article de blog."""),
]

for question, answer in FAQ:
    with st.expander(f"**{question}**", expanded=False):
        st.markdown(answer)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

st.markdown("""
<div style="background:white; border-radius:14px; padding:24px 28px;
            box-shadow:0 2px 8px rgba(0,0,0,0.07); text-align:center;">
    <div style="font-size:1.5rem; margin-bottom:8px;">💬</div>
    <div style="font-weight:600; font-size:1rem; color:#1A1A2E; margin-bottom:6px;">
        Vous avez une autre question ?
    </div>
    <div style="font-size:0.85rem; color:#666; margin-bottom:16px;">
        Posez-la directement à notre assistant — il consultera les rapports officiels pour vous répondre.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
if st.button("💬 Poser ma question", use_container_width=False, type="primary"):
    st.switch_page("pages/1_💬_Poser_une_question.py")
