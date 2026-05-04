import streamlit as st


def lang() -> str:
    return st.session_state.get("lang", "fr")


def t(key: str) -> str:
    return _T.get(lang(), _T["fr"]).get(key, key)


_T = {
    # ──────────────────────────────────────────────────────────────────────────
    "fr": {
        # Common
        "new_conv":      "✏️  Nouvelle conversation",
        "today":         "Aujourd'hui",
        "previous":      "Précédentes",
        "verified":      "✅ Données vérifiées",
        "verified_desc": "Toutes les réponses proviennent des rapports officiels de l'ANSD, DPEE et BCEAO.",
        "sources":       "📎 Sources utilisées",
        "spinner":       "Recherche dans les rapports officiels…",
        "error":         "⚠️ Le service est momentanément indisponible. Réessayez dans quelques instants.",

        # Home
        "home_eyebrow":    "🇸🇳 Données officielles du Sénégal",
        "home_title":      "Les chiffres officiels,<br>à portée de main.",
        "home_sub":        "Posez vos questions sur la population, l'économie, la santé ou la pauvreté au Sénégal — et obtenez une réponse tirée directement des rapports officiels, avec la source exacte.",
        "home_cta_ask":    "💬 Poser une question",
        "home_cta_themes": "📋 Parcourir les thèmes",
        "home_key_facts":  "Le Sénégal en chiffres clés",
        "home_explore":    "Explorer par thème",
        "home_how":        "Comment ça marche ?",
        "home_step1_title":"Posez votre question",
        "home_step1_desc": "En français ou en anglais, librement. Pas besoin de connaître le nom du rapport.",
        "home_step2_title":"Nous cherchons dans les sources officielles",
        "home_step2_desc": "Notre système consulte les rapports ANSD, DPEE, BCEAO — pas Internet.",
        "home_step3_title":"Vous obtenez la réponse avec sa source",
        "home_step3_desc": "Chaque chiffre est accompagné du rapport et de la page d'origine.",
        "home_step1_n":    "ÉTAPE 1",
        "home_step2_n":    "ÉTAPE 2",
        "home_step3_n":    "ÉTAPE 3",
        "home_footer":     "Données issues de l'ANSD, DPEE et BCEAO · SenStat ne remplace pas les rapports officiels",
        "explore_btn":     "Explorer",

        # Question page
        "q_banner_title":  "Posez votre question",
        "q_banner_sub":    "Réponses issues exclusivement des rapports officiels du Sénégal · ANSD · DPEE · BCEAO",
        "q_quick_label":   "Questions fréquentes — cliquez pour une réponse rapide",
        "q_chat_input":    "Ex : Quel est le taux de pauvreté au Sénégal ?",

        # Themes page
        "themes_title":    "📋 Explorez par thème",
        "themes_caption":  "Choisissez un thème pour voir les questions les plus posées et obtenir une réponse immédiate.",
        "themes_footer":   "Vous ne trouvez pas votre thème ? Posez directement votre question dans l'onglet 💬",

        # FAQ page
        "faq_title":       "❓ Questions fréquentes",
        "faq_caption":     "Tout ce que vous devez savoir sur SenStat et les données utilisées.",
        "faq_cta_title":   "Vous avez une autre question ?",
        "faq_cta_desc":    "Posez-la directement à notre assistant — il consultera les rapports officiels pour vous répondre.",
        "faq_cta_btn":     "💬 Poser ma question",
    },

    # ──────────────────────────────────────────────────────────────────────────
    "en": {
        # Common
        "new_conv":      "✏️  New conversation",
        "today":         "Today",
        "previous":      "Earlier",
        "verified":      "✅ Verified data",
        "verified_desc": "All answers come exclusively from official ANSD, DPEE and BCEAO reports.",
        "sources":       "📎 Sources used",
        "spinner":       "Searching official reports…",
        "error":         "⚠️ The service is temporarily unavailable. Please try again in a moment.",

        # Home
        "home_eyebrow":    "🇸🇳 Official data from Senegal",
        "home_title":      "Official figures,<br>at your fingertips.",
        "home_sub":        "Ask questions about Senegal's population, economy, health or poverty — and get an answer drawn directly from official reports, with the exact source.",
        "home_cta_ask":    "💬 Ask a question",
        "home_cta_themes": "📋 Browse themes",
        "home_key_facts":  "Senegal in key figures",
        "home_explore":    "Explore by theme",
        "home_how":        "How it works",
        "home_step1_title":"Ask your question",
        "home_step1_desc": "In French or English, freely. No need to know the report name.",
        "home_step2_title":"We search official sources",
        "home_step2_desc": "Our system reads ANSD, DPEE and BCEAO reports — not the internet.",
        "home_step3_title":"You get the answer with its source",
        "home_step3_desc": "Every figure comes with the report name and exact page number.",
        "home_step1_n":    "STEP 1",
        "home_step2_n":    "STEP 2",
        "home_step3_n":    "STEP 3",
        "home_footer":     "Data from ANSD, DPEE and BCEAO · SenStat does not replace official reports",
        "explore_btn":     "Explore",

        # Question page
        "q_banner_title":  "Ask your question",
        "q_banner_sub":    "Answers sourced exclusively from Senegal's official reports · ANSD · DPEE · BCEAO",
        "q_quick_label":   "Frequent questions — click for a quick answer",
        "q_chat_input":    "E.g.: What is the poverty rate in Senegal?",

        # Themes page
        "themes_title":    "📋 Explore by theme",
        "themes_caption":  "Choose a theme to see the most common questions and get an immediate answer.",
        "themes_footer":   "Can't find your theme? Ask your question directly in the 💬 tab",

        # FAQ page
        "faq_title":       "❓ Frequently Asked Questions",
        "faq_caption":     "Everything you need to know about SenStat and the data used.",
        "faq_cta_title":   "Have another question?",
        "faq_cta_desc":    "Ask it directly to our assistant — it will search the official reports for you.",
        "faq_cta_btn":     "💬 Ask my question",
    },
}

# ── Quick-question chips ───────────────────────────────────────────────────────
QUICK = {
    "fr": [
        ("🏙️", "Population totale du Sénégal 2023 ?"),
        ("📉", "Taux de pauvreté en 2021 ?"),
        ("💼", "Taux de chômage au Sénégal ?"),
        ("🗺️", "Régions les plus pauvres ?"),
        ("💧", "Accès à l'eau potable ?"),
        ("📚", "Taux de scolarisation ?"),
    ],
    "en": [
        ("🏙️", "Total population of Senegal in 2023?"),
        ("📉", "Poverty rate in Senegal in 2021?"),
        ("💼", "Unemployment rate in Senegal?"),
        ("🗺️", "Poorest regions in Senegal?"),
        ("💧", "Access to clean water in Senegal?"),
        ("📚", "School enrollment rate in Senegal?"),
    ],
}

# ── Themes ─────────────────────────────────────────────────────────────────────
THEMES = {
    "fr": [
        ("👥", "Population", "Démographie, régions, ménages, migrations", "RGPH-5 2023"),
        ("💰", "Pauvreté",   "Inégalités, conditions de vie, accès aux services", "EHCVM 2021-2022"),
        ("📈", "Économie",   "PIB, emploi, secteurs, croissance", "SES 2022-2023"),
        ("🏥", "Santé",      "Mortalité, nutrition, accès aux soins", "EDS + SES 2023"),
        ("🎓", "Éducation",  "Scolarisation, alphabétisation, formation", "SES 2022-2023"),
        ("🌾", "Agriculture","Productions, filières, sécurité alimentaire", "SES 2022-2023"),
    ],
    "en": [
        ("👥", "Population", "Demographics, regions, households, migration", "RGPH-5 2023"),
        ("💰", "Poverty",    "Inequality, living conditions, access to services", "EHCVM 2021-2022"),
        ("📈", "Economy",    "GDP, employment, sectors, growth", "SES 2022-2023"),
        ("🏥", "Health",     "Mortality, nutrition, access to care", "EDS + SES 2023"),
        ("🎓", "Education",  "Enrollment, literacy, training", "SES 2022-2023"),
        ("🌾", "Agriculture","Production, supply chains, food security", "SES 2022-2023"),
    ],
}

THEME_QUESTIONS = {
    "fr": {
        "Population": [
            "Quelle est la population totale du Sénégal en 2023 ?",
            "Quelle est la population de Dakar ?",
            "Quel est le taux de croissance démographique ?",
            "Quelle région est la plus peuplée du Sénégal ?",
            "Combien de ménages au Sénégal selon le RGPH-5 ?",
        ],
        "Pauvreté": [
            "Quel est le taux de pauvreté au Sénégal en 2021 ?",
            "Quelles régions sont les plus pauvres ?",
            "Comment a évolué la pauvreté depuis 2018 ?",
            "Quel est le taux de pauvreté en milieu rural vs urbain ?",
            "Quel est l'indice de Gini au Sénégal ?",
        ],
        "Économie": [
            "Quel est le PIB du Sénégal en 2023 ?",
            "Quel est le taux de chômage au Sénégal ?",
            "Quels sont les principaux secteurs économiques ?",
            "Quelle est la croissance prévue avec le pétrole et le gaz ?",
            "Quel est le taux d'inflation au Sénégal ?",
        ],
        "Santé": [
            "Quel est le taux de mortalité infantile au Sénégal ?",
            "Quelle est l'espérance de vie au Sénégal ?",
            "Quel est le taux de malnutrition chez les enfants ?",
            "Combien d'établissements de santé au Sénégal ?",
            "Quel est le taux de couverture vaccinale ?",
        ],
        "Éducation": [
            "Quel est le taux d'alphabétisation au Sénégal ?",
            "Quel est le taux de scolarisation au primaire ?",
            "Quelle est la parité filles/garçons à l'école ?",
            "Quel est le taux de réussite au BFEM ?",
            "Combien d'universités au Sénégal ?",
        ],
        "Agriculture": [
            "Quelle est la part de l'agriculture dans le PIB ?",
            "Quelles sont les principales cultures au Sénégal ?",
            "Quelle est la production d'arachide au Sénégal ?",
            "Combien de personnes travaillent dans l'agriculture ?",
            "Quel est le niveau de sécurité alimentaire ?",
        ],
    },
    "en": {
        "Population": [
            "What is the total population of Senegal in 2023?",
            "What is the population of Dakar?",
            "What is the population growth rate in Senegal?",
            "Which region is the most populated in Senegal?",
            "How many households in Senegal according to RGPH-5?",
        ],
        "Poverty": [
            "What is the poverty rate in Senegal in 2021?",
            "Which regions are the poorest in Senegal?",
            "How has poverty evolved since 2018?",
            "What is the poverty rate in rural vs urban areas?",
            "What is the Gini index in Senegal?",
        ],
        "Economy": [
            "What is Senegal's GDP in 2023?",
            "What is the unemployment rate in Senegal?",
            "What are the main economic sectors in Senegal?",
            "What growth is expected with oil and gas?",
            "What is the inflation rate in Senegal?",
        ],
        "Health": [
            "What is the infant mortality rate in Senegal?",
            "What is the life expectancy in Senegal?",
            "What is the malnutrition rate among children?",
            "How many healthcare facilities are in Senegal?",
            "What is the vaccination coverage rate?",
        ],
        "Education": [
            "What is the literacy rate in Senegal?",
            "What is the primary school enrollment rate?",
            "What is the gender parity in schools?",
            "What is the BFEM pass rate?",
            "How many universities are in Senegal?",
        ],
        "Agriculture": [
            "What share of GDP comes from agriculture?",
            "What are the main crops in Senegal?",
            "What is the groundnut production in Senegal?",
            "How many people work in agriculture?",
            "What is the food security level in Senegal?",
        ],
    },
}

FAQ_ITEMS = {
    "fr": [
        ("D'où viennent les données ?",
         """Les données proviennent exclusivement des institutions officielles sénégalaises :
- **ANSD** — RGPH-5, EHCVM, SES
- **DPEE** — Bulletins économiques
- **BCEAO** — Rapports financiers
- **Banque Mondiale** — Open Data Sénégal

SenStat ne collecte pas de données propres et ne navigue pas sur Internet."""),

        ("Les réponses sont-elles fiables ?",
         """Chaque réponse cite toujours : le rapport, l'institution, l'année et la page exacte.
Si une information n'est pas disponible, le système vous le dit clairement plutôt que d'inventer une réponse."""),

        ("Les données sont-elles à jour ?",
         """Sources actuelles : RGPH-5 (2023), EHCVM 2021-2022, SES 2022-2023.
Nous mettons à jour régulièrement avec les nouvelles publications de l'ANSD et du DPEE."""),

        ("Puis-je poser ma question en anglais ?",
         """Oui — le système répond dans la même langue que votre question.
Les données restent celles des rapports officiels sénégalais."""),

        ("Comment citer une réponse de SenStat ?",
         """Citez la source officielle indiquée dans la réponse, pas SenStat lui-même.

*Exemple : « Selon l'ANSD, EHCVM 2021-2022, p.27, le taux de pauvreté est de 37,5%. »*"""),

        ("Quelle est la différence avec Google ?",
         """Google vous renvoie vers des pages web pouvant contenir des erreurs ou des données obsolètes.
SenStat lit directement dans les rapports PDF officiels et cite la page exacte."""),
    ],
    "en": [
        ("Where does the data come from?",
         """Data comes exclusively from official Senegalese institutions:
- **ANSD** — RGPH-5, EHCVM, SES
- **DPEE** — Economic bulletins
- **BCEAO** — Financial reports
- **World Bank** — Senegal Open Data

SenStat does not collect its own data and does not browse the internet."""),

        ("Are the answers reliable?",
         """Every answer always cites: the report, the institution, the year and the exact page.
If information is not available, the system tells you clearly rather than making up an answer."""),

        ("Is the data up to date?",
         """Current sources: RGPH-5 (2023), EHCVM 2021-2022, SES 2022-2023.
We update regularly with new publications from ANSD and DPEE."""),

        ("Can I ask my question in English?",
         """Yes — the system responds in the same language as your question.
The underlying data remains from official Senegalese reports."""),

        ("How do I cite a SenStat answer?",
         """Cite the official source shown in the answer, not SenStat itself.

*Example: "According to ANSD, EHCVM 2021-2022, p.27, the poverty rate is 37.5%."*"""),

        ("What is the difference with Google?",
         """Google points to web pages that may contain errors or outdated figures.
SenStat reads directly from official PDF reports and cites the exact page."""),
    ],
}
