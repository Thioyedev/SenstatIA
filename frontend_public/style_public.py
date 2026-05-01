import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

/* ── Background ───────────────────────────────────────────── */
[data-testid="stAppViewContainer"] { background-color: #F5F7FA; }
[data-testid="block-container"] {
    padding-top: 2rem;
    padding-left: 3rem;
    padding-right: 3rem;
    max-width: 980px;
}

/* ── Global text ──────────────────────────────────────────── */
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] .stMarkdown { color: #1A1A1A; }
[data-testid="stCaptionContainer"] p { color: #777 !important; }

/* ── Sidebar ──────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #1A1A2E;
    border-right: none;
}
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
[data-testid="stSidebarNav"] a {
    border-radius: 8px;
    margin: 2px 8px;
    padding: 8px 12px;
    font-size: 0.92rem;
    font-weight: 500;
    transition: background 0.15s;
}
[data-testid="stSidebarNav"] a:hover { background: rgba(255,255,255,0.08) !important; }
[data-testid="stSidebarNav"] a[aria-selected="true"] {
    background: rgba(0,133,63,0.3) !important;
    color: white !important;
    font-weight: 600;
    border-left: 3px solid #00853F;
    padding-left: 9px;
}

/* ── Hero ─────────────────────────────────────────────────── */
.hero-public {
    background: linear-gradient(135deg, #1A1A2E 0%, #16213E 60%, #0F3460 100%);
    border-radius: 20px;
    padding: 44px 40px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero-public::before {
    content: "";
    position: absolute;
    top: -30px; right: -30px;
    width: 180px; height: 180px;
    background: rgba(0,133,63,0.15);
    border-radius: 50%;
}
.hero-public::after {
    content: "";
    position: absolute;
    bottom: -50px; right: 80px;
    width: 120px; height: 120px;
    background: rgba(255,222,40,0.08);
    border-radius: 50%;
}
.hero-public .eyebrow {
    font-size: 0.72rem; font-weight: 600;
    letter-spacing: 1.2px; text-transform: uppercase;
    color: #00853F; margin-bottom: 10px;
}
.hero-public h1 {
    font-size: 2.4rem; font-weight: 800;
    color: white !important; margin: 0 0 10px 0;
    line-height: 1.15; letter-spacing: -0.5px;
}
.hero-public .sub {
    color: rgba(255,255,255,0.72);
    font-size: 1rem; line-height: 1.6;
    max-width: 520px; margin-bottom: 20px;
}
.hero-cta {
    display: inline-block;
    background: #00853F;
    color: white !important;
    border-radius: 10px;
    padding: 10px 22px;
    font-weight: 600; font-size: 0.92rem;
    text-decoration: none;
    margin-right: 10px;
}
.hero-cta-ghost {
    display: inline-block;
    border: 1.5px solid rgba(255,255,255,0.3);
    color: rgba(255,255,255,0.85) !important;
    border-radius: 10px;
    padding: 10px 22px;
    font-weight: 500; font-size: 0.92rem;
    text-decoration: none;
}

/* ── Fact cards ───────────────────────────────────────────── */
.fact-card {
    background: white;
    border-radius: 14px;
    padding: 20px 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    height: 100%;
    border-bottom: 3px solid #00853F;
    color: #1A1A1A;
    transition: transform 0.15s, box-shadow 0.15s;
}
.fact-card:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,0.10); }
.fact-card .topic { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.6px; text-transform: uppercase; color: #00853F; margin-bottom: 6px; }
.fact-card .stat  { font-size: 2rem; font-weight: 800; color: #1A1A2E; line-height: 1.1; }
.fact-card .desc  { font-size: 0.82rem; color: #555; margin-top: 4px; line-height: 1.4; }
.fact-card .src   { font-size: 0.68rem; color: #aaa; margin-top: 10px; font-style: italic; }

/* ── Theme cards ──────────────────────────────────────────── */
.theme-card {
    background: white;
    border-radius: 14px;
    padding: 22px 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    cursor: pointer;
    transition: all 0.15s;
    text-align: center;
    height: 100%;
    color: #1A1A1A;
}
.theme-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
.theme-card .emoji { font-size: 2.2rem; margin-bottom: 10px; }
.theme-card .name  { font-weight: 700; font-size: 1rem; color: #1A1A2E; }
.theme-card .desc  { font-size: 0.78rem; color: #777; margin-top: 4px; line-height: 1.4; }
.theme-card .count { font-size: 0.7rem; color: #00853F; font-weight: 600; margin-top: 10px; }

/* ── Answer box ───────────────────────────────────────────── */
.answer-box {
    background: white;
    border-radius: 16px;
    padding: 24px 28px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    color: #1A1A1A;
    line-height: 1.7;
    font-size: 0.97rem;
    border-left: 4px solid #00853F;
}

/* ── Source pill ──────────────────────────────────────────── */
.source-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #F0FFF4;
    border: 1px solid #C6F6D5;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    color: #2D6A4F;
    font-weight: 500;
    margin: 3px 3px 0 0;
}

/* ── Chat ─────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: white !important;
    border-radius: 14px !important;
    padding: 16px 20px !important;
    margin: 8px 0 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
[data-testid="stChatMessage"] p { color: #1A1A1A !important; font-size: 0.97rem !important; }
[data-testid="stChatInput"] > div {
    border: 2px solid #e0e0e0 !important;
    border-radius: 14px !important;
    background: white !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
[data-testid="stChatInput"] > div:focus-within { border-color: #00853F !important; }
[data-testid="stChatInput"] textarea { color: #1A1A1A !important; font-size: 0.97rem !important; }

/* ── Buttons ──────────────────────────────────────────────── */
.stButton > button {
    border-radius: 10px;
    font-weight: 500;
    font-size: 0.88rem;
    padding: 8px 16px;
    transition: all 0.15s;
    border: 1.5px solid #e0e0e0;
    background: white;
    color: #1A1A1A;
}
.stButton > button:hover {
    border-color: #00853F;
    color: #00853F;
    transform: translateY(-1px);
    box-shadow: 0 3px 10px rgba(0,133,63,0.15);
}

/* ── Section label ────────────────────────────────────────── */
.section-lbl {
    font-size: 0.7rem; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase;
    color: #999; margin: 24px 0 12px 0;
}
.divider { border: none; border-top: 1px solid #E8E8E8; margin: 20px 0; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def sidebar_brand():
    st.sidebar.markdown("""
<div style="padding:20px 16px 12px 16px; text-align:center;">
    <div style="font-size:1.8rem;">🇸🇳</div>
    <div style="font-size:1.2rem; font-weight:700; color:white; margin-top:6px;">SenStat</div>
    <div style="font-size:0.68rem; color:rgba(255,255,255,0.4); margin-top:3px;">
        Statistiques officielles du Sénégal
    </div>
</div>
<hr style="border-color:rgba(255,255,255,0.08); margin:0 16px 8px 16px;">
""", unsafe_allow_html=True)


def section_lbl(text: str):
    st.markdown(f'<div class="section-lbl">{text}</div>', unsafe_allow_html=True)


def fact_card(topic: str, stat: str, desc: str, source: str):
    st.markdown(f"""
<div class="fact-card">
    <div class="topic">{topic}</div>
    <div class="stat">{stat}</div>
    <div class="desc">{desc}</div>
    <div class="src">Source : {source}</div>
</div>
""", unsafe_allow_html=True)
