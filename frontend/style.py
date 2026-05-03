import streamlit as st

SENEGAL_GREEN  = "#00853F"
SENEGAL_YELLOW = "#FDEF42"
SENEGAL_RED    = "#E31B23"

CSS = """
<style>
/* ── Google Font ──────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Hide ugly Streamlit defaults ─────────────────────────── */
#MainMenu                        { visibility: hidden; }
footer                           { visibility: hidden; }
[data-testid="stToolbar"]        { visibility: hidden; }
[data-testid="stDecoration"]     { display: none; }

/* Transparent header — keeps sidebar toggle functional */
[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
}

/* Sidebar toggle always visible */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    visibility: visible !important;
    opacity: 1 !important;
}

/* ── Sidebar ──────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #004d24 0%, #003018 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] * { color: #d4edda !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.10) !important; }

/* Nav items */
[data-testid="stSidebarNav"] {
    padding-top: 0;
}
[data-testid="stSidebarNav"] a {
    border-radius: 8px;
    margin: 1px 8px;
    padding: 7px 12px;
    font-size: 0.9rem;
    font-weight: 500;
    transition: background 0.15s;
    color: rgba(255,255,255,0.82) !important;
}
[data-testid="stSidebarNav"] a:hover {
    background: rgba(255,255,255,0.10) !important;
    color: white !important;
}
[data-testid="stSidebarNav"] a[aria-selected="true"] {
    background: rgba(255,255,255,0.16) !important;
    color: white !important;
    font-weight: 600;
    border-left: 3px solid #FDEF42;
    padding-left: 9px;
}

/* ── App background ───────────────────────────────────────── */
[data-testid="stAppViewContainer"] { background-color: #EDEEF2; }
[data-testid="block-container"] {
    padding-top: 1.8rem;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
    max-width: 1100px;
}

/* ── Global text ──────────────────────────────────────────── */
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4,
[data-testid="stAppViewContainer"] .stMarkdown { color: #1A1A1A; }

[data-testid="stAppViewContainer"] h1 { font-size: 1.9rem; font-weight: 700; letter-spacing: -0.4px; }
[data-testid="stAppViewContainer"] h2 { font-size: 1.35rem; font-weight: 600; }
[data-testid="stAppViewContainer"] h3 { font-size: 1.1rem; font-weight: 600; }
[data-testid="stCaptionContainer"] p  { color: #666 !important; font-size: 0.82rem !important; }

/* ── Buttons ──────────────────────────────────────────────── */
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    font-size: 0.85rem;
    padding: 7px 14px;
    transition: all 0.15s ease;
    border: 1.5px solid #ddd;
    background: white;
    color: #1A1A1A;
}
.stButton > button:hover {
    border-color: #00853F;
    color: #00853F;
    transform: translateY(-1px);
    box-shadow: 0 3px 10px rgba(0,133,63,0.15);
}
.stButton > button[kind="primary"] {
    background: #00853F;
    color: white !important;
    border-color: #00853F;
}

/* ── Inputs ───────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: white !important;
    color: #1A1A1A !important;
    border: 1.5px solid #e0e0e0 !important;
    border-radius: 8px !important;
    transition: border-color 0.15s;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus { border-color: #00853F !important; box-shadow: 0 0 0 2px rgba(0,133,63,0.1) !important; }

.stSelectbox > div > div {
    background: white !important;
    color: #1A1A1A !important;
    border: 1.5px solid #e0e0e0 !important;
    border-radius: 8px !important;
}

/* Chat input */
[data-testid="stChatInput"] > div {
    border: 1.5px solid #ddd !important;
    border-radius: 12px !important;
    background: white !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
[data-testid="stChatInput"] textarea { color: #1A1A1A !important; }

/* ── Chat messages ────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: white !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    margin: 6px 0 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
[data-testid="stChatMessage"] p { color: #1A1A1A !important; }

/* ── Hero ─────────────────────────────────────────────────── */
.hero {
    background: linear-gradient(135deg, #00853F 0%, #004d24 100%);
    border-radius: 14px;
    padding: 32px 36px;
    color: white;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "";
    position: absolute;
    top: -40px; right: -40px;
    width: 200px; height: 200px;
    background: rgba(255,222,40,0.08);
    border-radius: 50%;
}
.hero::after {
    content: "";
    position: absolute;
    bottom: -60px; right: 60px;
    width: 160px; height: 160px;
    background: rgba(255,255,255,0.05);
    border-radius: 50%;
}
.hero-title { font-size: 2rem; font-weight: 700; color: white !important; margin: 0 0 6px 0; }
.hero-sub   { color: rgba(255,255,255,0.82); font-size: 0.95rem; line-height: 1.55; margin-bottom: 16px; }
.hero-pill  {
    display: inline-block;
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 20px;
    padding: 3px 11px;
    font-size: 0.75rem;
    font-weight: 500;
    margin: 0 4px 4px 0;
    color: white;
}

/* ── Metric cards ─────────────────────────────────────────── */
.metric-card {
    background: white;
    border-radius: 12px;
    padding: 18px 16px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    border-top: 3px solid #00853F;
    height: 100%;
}
.metric-card .icon  { font-size: 1.4rem; margin-bottom: 6px; }
.metric-card .value { font-size: 1.5rem; font-weight: 700; color: #00853F; line-height: 1.2; }
.metric-card .label { font-size: 0.76rem; color: #666; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.4px; }
.metric-card .sub   { font-size: 0.72rem; color: #aaa; margin-top: 2px; }

/* Status dot */
.status-online  { display:inline-block; width:8px; height:8px; border-radius:50%; background:#00853F; margin-right:5px; vertical-align:middle; }
.status-offline { display:inline-block; width:8px; height:8px; border-radius:50%; background:#E31B23; margin-right:5px; vertical-align:middle; }

/* ── Demo query chips ─────────────────────────────────────── */
.demo-grid { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 16px 0; }
.demo-chip {
    background: white;
    border: 1.5px solid #e0e0e0;
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 0.82rem;
    color: #333;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
}
.demo-chip:hover { border-color: #00853F; color: #00853F; background: #f0faf4; }

/* ── General cards ────────────────────────────────────────── */
.card {
    background: white;
    border-radius: 12px;
    padding: 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    margin-bottom: 10px;
    color: #1A1A1A;
    transition: box-shadow 0.15s, transform 0.15s;
}
.card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.10); transform: translateY(-1px); }

/* Citation card */
.citation-card {
    background: #F8FFF8;
    border-left: 3px solid #00853F;
    border-radius: 0 8px 8px 0;
    padding: 9px 13px;
    margin: 5px 0;
    font-size: 0.82rem;
    color: #1A1A1A;
}
.citation-card .source  { font-weight: 600; color: #00853F; font-size: 0.83rem; }
.citation-card .report  { color: #333; font-size: 0.8rem; margin: 2px 0; }
.citation-card .details { color: #777; font-size: 0.73rem; }

/* Chunk card */
.chunk-card {
    background: white;
    border-radius: 10px;
    padding: 14px 16px;
    margin: 8px 0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    border-left: 3px solid #00853F;
    color: #1A1A1A;
}
.chunk-card .meta  { font-size: 0.74rem; color: #00853F; font-weight: 600; margin-bottom: 6px; display: flex; justify-content: space-between; }
.chunk-card .body  { font-size: 0.87rem; line-height: 1.55; color: #2A2A2A; }

/* ── Badges ───────────────────────────────────────────────── */
.badge {
    display: inline-block;
    border-radius: 5px;
    padding: 2px 8px;
    font-size: 0.70rem;
    font-weight: 600;
    margin-right: 3px;
    letter-spacing: 0.2px;
}
.badge-green  { background: #E8F5E9; color: #2E7D32; }
.badge-blue   { background: #E3F2FD; color: #1565C0; }
.badge-yellow { background: #FFF8E1; color: #E65100; }
.badge-gray   { background: #F5F5F5; color: #555; }

/* ── Section label ────────────────────────────────────────── */
.section-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: #888;
    margin: 20px 0 10px 0;
}

/* ── Divider ──────────────────────────────────────────────── */
.section-divider { border: none; border-top: 1px solid #E5E7EB; margin: 16px 0; }

/* ── Empty state ──────────────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 40px 24px;
    color: #bbb;
}
.empty-state .icon { font-size: 2.5rem; margin-bottom: 10px; }
.empty-state .msg  { font-size: 0.88rem; line-height: 1.5; color: #aaa; }

/* ── Expander ─────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: white !important;
    border-radius: 10px !important;
    border: 1px solid #E8E8E8 !important;
    margin-bottom: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
[data-testid="stExpander"] summary { font-weight: 600; color: #1A1A1A !important; padding: 12px 16px; }
[data-testid="stExpander"] summary:hover { background: #f8f8f8 !important; border-radius: 10px; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def sidebar_brand():
    st.sidebar.markdown("""
<div style="padding: 20px 16px 12px 16px; text-align: center;">
    <div style="font-size: 2rem; line-height: 1;">📊</div>
    <div style="font-size: 1.25rem; font-weight: 700; color: white; margin-top: 6px; letter-spacing: 0.3px;">
        SenStat
    </div>
    <div style="font-size: 0.7rem; color: rgba(255,255,255,0.5); margin-top: 3px;">
        Intelligence Statistique · Sénégal
    </div>
</div>
<hr style="border-color: rgba(255,255,255,0.10); margin: 0 16px 8px 16px;">
""", unsafe_allow_html=True)


def page_header(icon: str, title: str, subtitle: str = ""):
    st.markdown(f"<h2>{icon} {title}</h2>", unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)


def section_label(text: str):
    st.markdown(f"<div class='section-label'>{text}</div>", unsafe_allow_html=True)


def empty_state(icon: str, message: str):
    st.markdown(f"""
<div class="empty-state">
    <div class="icon">{icon}</div>
    <div class="msg">{message}</div>
</div>
""", unsafe_allow_html=True)


def metric_card(icon: str, value, label: str, sub: str = ""):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    st.markdown(f"""
<div class="metric-card">
    <div class="icon">{icon}</div>
    <div class="value">{value}</div>
    <div class="label">{label}</div>
    {sub_html}
</div>
""", unsafe_allow_html=True)
