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
        "verified_desc": "Toutes les réponses proviennent des rapports officiels de l'ANSD, FMI, Banque Mondiale, ARTP, DGTCP et PNUD.",
        "sources":       "📎 Sources utilisées",
        "spinner":       "Recherche dans les rapports officiels…",
        "error":         "⚠️ Le service est momentanément indisponible. Réessayez dans quelques instants.",

        # Home
        "home_eyebrow":    "🇸🇳 Données officielles du Sénégal",
        "home_title":      "Les chiffres officiels,<br>à portée de main.",
        "home_sub":        "Posez vos questions sur la population, l'économie, la dette publique, les télécoms ou l'agriculture au Sénégal — et obtenez une réponse tirée directement des rapports officiels, avec la source exacte.",
        "home_cta_ask":    "💬 Poser une question",
        "home_cta_themes": "📋 Parcourir les thèmes",
        "home_key_facts":  "Le Sénégal en chiffres clés",
        "home_explore":    "Explorer par thème",
        "home_how":        "Comment ça marche ?",
        "home_step1_title":"Posez votre question",
        "home_step1_desc": "En français ou en anglais, librement. Pas besoin de connaître le nom du rapport.",
        "home_step2_title":"Nous cherchons dans les sources officielles",
        "home_step2_desc": "Notre système consulte les rapports ANSD, FMI, Banque Mondiale, ARTP, DGTCP et PNUD — pas Internet.",
        "home_step3_title":"Vous obtenez la réponse avec sa source",
        "home_step3_desc": "Chaque chiffre est accompagné du rapport, de l'institution et de la page d'origine.",
        "home_step1_n":    "ÉTAPE 1",
        "home_step2_n":    "ÉTAPE 2",
        "home_step3_n":    "ÉTAPE 3",
        "home_footer":     "Données issues de l'ANSD, FMI, Banque Mondiale, ARTP, DGTCP, Cour des Comptes et PNUD · SenStat ne remplace pas les rapports officiels",
        "explore_btn":     "Explorer",

        # Question page
        "q_banner_title":  "Posez votre question",
        "q_banner_sub":    "Réponses issues exclusivement des rapports officiels · ANSD · FMI · Banque Mondiale · ARTP · DGTCP · Cour des Comptes · PNUD · DAPSA",
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
        "verified_desc": "All answers come exclusively from official ANSD, IMF, World Bank, ARTP, DGTCP and UNDP reports.",
        "sources":       "📎 Sources used",
        "spinner":       "Searching official reports…",
        "error":         "⚠️ The service is temporarily unavailable. Please try again in a moment.",

        # Home
        "home_eyebrow":    "🇸🇳 Official data from Senegal",
        "home_title":      "Official figures,<br>at your fingertips.",
        "home_sub":        "Ask questions about Senegal's population, economy, public debt, telecoms or agriculture — and get an answer drawn directly from official reports, with the exact source.",
        "home_cta_ask":    "💬 Ask a question",
        "home_cta_themes": "📋 Browse themes",
        "home_key_facts":  "Senegal in key figures",
        "home_explore":    "Explore by theme",
        "home_how":        "How it works",
        "home_step1_title":"Ask your question",
        "home_step1_desc": "In French or English, freely. No need to know the report name.",
        "home_step2_title":"We search official sources",
        "home_step2_desc": "Our system reads ANSD, IMF, World Bank, ARTP, DGTCP and UNDP reports — not the internet.",
        "home_step3_title":"You get the answer with its source",
        "home_step3_desc": "Every figure comes with the report name, institution, and exact page number.",
        "home_step1_n":    "STEP 1",
        "home_step2_n":    "STEP 2",
        "home_step3_n":    "STEP 3",
        "home_footer":     "Data from ANSD, IMF, World Bank, ARTP, DGTCP, Cour des Comptes and UNDP · SenStat does not replace official reports",
        "explore_btn":     "Explore",

        # Question page
        "q_banner_title":  "Ask your question",
        "q_banner_sub":    "Answers sourced exclusively from official reports · ANSD · IMF · World Bank · ARTP · DGTCP · Cour des Comptes · UNDP · DAPSA",
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
        ("📡", "Pénétration mobile et internet au Sénégal ?"),
        ("🏦", "Quel est le niveau de la dette publique ?"),
        ("🌍", "Quel est l'IDH du Sénégal ?"),
        ("💼", "Taux de chômage des jeunes au Sénégal ?"),
    ],
    "en": [
        ("🏙️", "Total population of Senegal in 2023?"),
        ("📉", "Poverty rate in Senegal in 2021?"),
        ("📡", "Mobile and internet penetration in Senegal?"),
        ("🏦", "What is the public debt level of Senegal?"),
        ("🌍", "What is Senegal's HDI?"),
        ("💼", "Youth unemployment rate in Senegal?"),
    ],
}

# ── Themes ─────────────────────────────────────────────────────────────────────
THEMES = {
    "fr": [
        ("👥", "Population",           "Démographie, régions, ménages, migrations",               "RGPH-5 2023 — ANSD",                  "#1565C0"),
        ("💰", "Pauvreté",             "Inégalités, conditions de vie, seuil de pauvreté",        "PNUD HDI/MPI · Banque Mondiale",      "#E65100"),
        ("📊", "Économie",             "PIB, croissance, conjoncture trimestrielle, secteurs",    "BDEF 2024 · WEO FMI · Banque Mondiale", "#00853F"),
        ("💼", "Emploi",               "Chômage, activité, marché du travail, secteur informel", "ENES · RGPH-5 Économie — ANSD",        "#1976D2"),
        ("🏥", "Santé",                "Mortalité, nutrition, espérance de vie, vaccination",    "Banque Mondiale · PNUD",              "#C62828"),
        ("🎓", "Éducation",            "Scolarisation, alphabétisation, parité, université",     "Banque Mondiale · PNUD",              "#6A1B9A"),
        ("🌾", "Agriculture",          "Céréales, arachide, riz, élevage, sécurité alimentaire", "EAA 2022-2023 — DAPSA",               "#558B2F"),
        ("📡", "Télécoms & Numérique", "Mobile, internet, opérateurs, pénétration, données",     "ARTP 2024",                           "#00838F"),
        ("🏦", "Finances & Dette",     "Dette publique, budget, audit, exécution budgétaire",    "DGTCP · Cour des Comptes",            "#5D4037"),
    ],
    "en": [
        ("👥", "Population",           "Demographics, regions, households, migration",            "RGPH-5 2023 — ANSD",                  "#1565C0"),
        ("💰", "Poverty",              "Inequality, living conditions, poverty threshold",        "UNDP HDI/MPI · World Bank",           "#E65100"),
        ("📊", "Economy",              "GDP, growth, quarterly outlook, sectors",                 "BDEF 2024 · IMF WEO · World Bank",    "#00853F"),
        ("💼", "Employment",           "Unemployment, activity, labour market, informal sector", "ENES · RGPH-5 Economy — ANSD",        "#1976D2"),
        ("🏥", "Health",               "Mortality, nutrition, life expectancy, vaccination",      "World Bank · UNDP",                   "#C62828"),
        ("🎓", "Education",            "Enrollment, literacy, gender parity, university",         "World Bank · UNDP",                   "#6A1B9A"),
        ("🌾", "Agriculture",          "Cereals, groundnut, rice, livestock, food security",     "EAA 2022-2023 — DAPSA",               "#558B2F"),
        ("📡", "Telecoms & Digital",   "Mobile, internet, operators, penetration, data usage",   "ARTP 2024",                           "#00838F"),
        ("🏦", "Public Finance & Debt","Public debt, budget, audit, budget execution",            "DGTCP · Cour des Comptes",            "#5D4037"),
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
            "Quelle est la croissance prévue avec le pétrole et le gaz ?",
            "Quels sont les principaux secteurs économiques ?",
            "Quel est le taux d'inflation au Sénégal ?",
            "Comment évolue la balance courante du Sénégal ?",
        ],
        "Emploi": [
            "Quel est le taux de chômage au Sénégal ?",
            "Quel est le taux de chômage des jeunes au Sénégal ?",
            "Quelle est la part de l'emploi informel au Sénégal ?",
            "Comment a évolué le taux d'activité depuis 2020 ?",
            "Quelles régions ont le chômage le plus élevé ?",
        ],
        "Santé": [
            "Quel est le taux de mortalité infantile au Sénégal ?",
            "Quelle est l'espérance de vie au Sénégal ?",
            "Quel est le taux de malnutrition chez les enfants ?",
            "Quelle est la couverture vaccinale au Sénégal ?",
            "Comment évolue la mortalité maternelle au Sénégal ?",
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
            "Quel est le niveau de sécurité alimentaire au Sénégal ?",
        ],
        "Télécoms & Numérique": [
            "Quel est le taux de pénétration mobile au Sénégal ?",
            "Combien d'abonnés internet au Sénégal en 2024 ?",
            "Quels sont les principaux opérateurs télécoms au Sénégal ?",
            "Quel est le débit mobile moyen au Sénégal ?",
            "Quelle est la couverture 4G au Sénégal ?",
        ],
        "Finances & Dette": [
            "Quel est le niveau de la dette publique du Sénégal ?",
            "Quelle est la dette extérieure du Sénégal ?",
            "Quel est le déficit budgétaire du Sénégal ?",
            "Quelles sont les conclusions de la Cour des Comptes sur les finances publiques ?",
            "Quel est le service de la dette du Sénégal en 2024 ?",
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
            "What growth is expected with oil and gas?",
            "What are the main economic sectors in Senegal?",
            "What is the inflation rate in Senegal?",
            "How is Senegal's current account balance evolving?",
        ],
        "Employment": [
            "What is the unemployment rate in Senegal?",
            "What is the youth unemployment rate in Senegal?",
            "What share of employment is in the informal sector?",
            "How has the activity rate evolved since 2020?",
            "Which regions have the highest unemployment in Senegal?",
        ],
        "Health": [
            "What is the infant mortality rate in Senegal?",
            "What is the life expectancy in Senegal?",
            "What is the malnutrition rate among children?",
            "What is the vaccination coverage rate in Senegal?",
            "How is maternal mortality evolving in Senegal?",
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
        "Telecoms & Digital": [
            "What is the mobile penetration rate in Senegal?",
            "How many internet subscribers in Senegal in 2024?",
            "What are the main telecom operators in Senegal?",
            "What is the average mobile speed in Senegal?",
            "What is the 4G coverage in Senegal?",
        ],
        "Public Finance & Debt": [
            "What is the public debt level of Senegal?",
            "What is Senegal's external debt?",
            "What is the fiscal deficit of Senegal?",
            "What are the Cour des Comptes findings on public finances?",
            "What is Senegal's debt service level in 2024?",
        ],
    },
}

FAQ_ITEMS = {
    "fr": [
        ("D'où viennent les données ?",
         """Les données proviennent exclusivement des institutions officielles sénégalaises et internationales :
- **ANSD** — RGPH-5 (population), BDEF (macroéconomie), ENES (emploi), NEER (conjoncture trimestrielle)
- **DGTCP** — Bulletins statistiques de la dette publique (T1-T2 2024)
- **Cour des Comptes** — Rapport d'audit des finances publiques 2019-2024
- **FMI** — World Economic Outlook (projections macroéconomiques)
- **Banque Mondiale** — Open Data (multi-sectoriel : pauvreté, éducation, santé)
- **DAPSA** — Enquête Agricole Annuelle 2022-2023
- **PNUD** — IDH 2024 et IPM 2023
- **ARTP** — Rapport sur les marchés des communications électroniques 2024

SenStat ne collecte pas de données propres et ne navigue pas sur Internet."""),

        ("Les réponses sont-elles fiables ?",
         """Chaque réponse cite toujours : le rapport, l'institution, l'année et la page exacte.
Si une information n'est pas disponible dans les sources indexées, le système vous le dit clairement plutôt que d'inventer une réponse."""),

        ("Les données sont-elles à jour ?",
         """Sources actuellement indexées :
- RGPH-5 2023, BDEF 2024, ENES T3-2023, NEER T4-2024 (ANSD)
- DGTCP dette T2-2024
- Cour des Comptes audit 2024
- FMI WEO 2025, Banque Mondiale 2024
- DAPSA EAA 2022-2023
- PNUD HDI/MPI 2024
- ARTP S1-2024

Nous mettons à jour régulièrement avec les nouvelles publications."""),

        ("Puis-je poser ma question en anglais ?",
         """Oui — le système répond dans la même langue que votre question.
Les données restent celles des rapports officiels sénégalais."""),

        ("Comment citer une réponse de SenStat ?",
         """Citez la source officielle indiquée dans la réponse, pas SenStat lui-même.

*Exemple : « Selon l'ANSD, EHCVM 2021-2022, p.27, le taux de pauvreté est de 37,5 %. »*"""),

        ("Quelle est la différence avec Google ?",
         """Google vous renvoie vers des pages web pouvant contenir des erreurs ou des données obsolètes.
SenStat lit directement dans les rapports PDF officiels et cite la page exacte."""),
    ],
    "en": [
        ("Where does the data come from?",
         """Data comes exclusively from official Senegalese and international institutions:
- **ANSD** — RGPH-5 (population), BDEF (macroeconomy), ENES (employment), NEER (quarterly outlook)
- **DGTCP** — Public debt statistical bulletins (Q1-Q2 2024)
- **Cour des Comptes** — Public finance audit report 2019-2024
- **IMF** — World Economic Outlook (macroeconomic projections)
- **World Bank** — Open Data (multi-sector: poverty, education, health)
- **DAPSA** — Annual Agricultural Survey 2022-2023
- **UNDP** — HDI 2024 and MPI 2023
- **ARTP** — Electronic communications market report 2024

SenStat does not collect its own data and does not browse the internet."""),

        ("Are the answers reliable?",
         """Every answer always cites: the report, the institution, the year and the exact page.
If information is not available in the indexed sources, the system tells you clearly rather than making up an answer."""),

        ("Is the data up to date?",
         """Currently indexed sources:
- RGPH-5 2023, BDEF 2024, ENES Q3-2023, NEER Q4-2024 (ANSD)
- DGTCP debt Q2-2024
- Cour des Comptes audit 2024
- IMF WEO 2025, World Bank 2024
- DAPSA EAA 2022-2023
- UNDP HDI/MPI 2024
- ARTP H1-2024

We update regularly with new publications."""),

        ("Can I ask my question in English?",
         """Yes — the system responds in the same language as your question.
The underlying data remains from official Senegalese reports."""),

        ("How do I cite a SenStat answer?",
         """Cite the official source shown in the answer, not SenStat itself.

*Example: \"According to ANSD, EHCVM 2021-2022, p.27, the poverty rate is 37.5%.\"*"""),

        ("What is the difference with Google?",
         """Google points to web pages that may contain errors or outdated figures.
SenStat reads directly from official PDF reports and cites the exact page."""),
    ],
}
