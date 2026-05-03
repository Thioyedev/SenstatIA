import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

#MainMenu                        { visibility: hidden; }
footer                           { visibility: hidden; }
[data-testid="stToolbar"]        { visibility: hidden; }
[data-testid="stDecoration"]     { display: none; }

/* Transparent header */
[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
}

/* ── Sidebar collapse button (inside open sidebar) ─────────── */
[data-testid="stSidebarCollapseButton"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
}
[data-testid="stSidebarCollapseButton"] button {
    background: transparent !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 6px !important;
    cursor: pointer !important;
    transition: background 0.15s !important;
}
[data-testid="stSidebarCollapseButton"] button:hover {
    background: rgba(255,255,255,0.1) !important;
}
[data-testid="stSidebarCollapseButton"] svg {
    stroke: rgba(255,255,255,0.5) !important;
    fill: none !important;
    width: 18px !important;
    height: 18px !important;
}
[data-testid="stSidebarCollapseButton"] button:hover svg {
    stroke: white !important;
}

/* Hide Streamlit's expand control — custom JS tab handles it */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] { display: none !important; }

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

/* ── Sidebar — Claude style ───────────────────────────────── */
[data-testid="stSidebar"] {
    background: #171717 !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] * { color: #ececec !important; }
[data-testid="stSidebarNav"] a {
    border-radius: 8px;
    margin: 1px 8px;
    padding: 7px 12px;
    font-size: 0.88rem;
    font-weight: 500;
    transition: background 0.15s;
    color: rgba(255,255,255,0.72) !important;
}
[data-testid="stSidebarNav"] a:hover { background: rgba(255,255,255,0.08) !important; color: white !important; }
[data-testid="stSidebarNav"] a[aria-selected="true"] {
    background: rgba(255,255,255,0.12) !important;
    color: white !important;
    font-weight: 600;
}

/* Chat history */
.conv-item {
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 0.82rem;
    color: rgba(255,255,255,0.65);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin: 1px 0;
}
.conv-group-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.35) !important;
    padding: 12px 12px 4px 12px;
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


SIDEBAR_JS = """
<script>
(function() {
    var ID = 'senstat-sidebar-tab';
    function make() {
        var btn = document.createElement('button');
        btn.id = ID;
        btn.title = 'Ouvrir la sidebar';
        btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>';
        btn.style.cssText = 'position:fixed;left:0;top:50%;transform:translateY(-50%);z-index:2147483647;background:#1A1A2E;border:none;border-radius:0 8px 8px 0;width:28px;height:52px;cursor:pointer;align-items:center;justify-content:center;box-shadow:3px 0 14px rgba(0,0,0,0.55);padding:0;outline:none;display:none;';
        btn.onmouseenter = function() { btn.style.background = '#252545'; };
        btn.onmouseleave = function() { btn.style.background = '#1A1A2E'; };
        btn.onclick = function(e) {
            e.stopPropagation();
            var expandBtn = document.querySelector('[data-testid="stSidebarCollapsedControl"] button');
            if (expandBtn) { expandBtn.click(); return; }
            var cb = document.querySelector('[data-testid="stSidebarCollapseButton"] button');
            if (cb) cb.click();
        };
        document.body.appendChild(btn);
        return btn;
    }
    function update() {
        var btn = document.getElementById(ID) || make();
        var sidebar = document.querySelector('[data-testid="stSidebar"]');
        var open = sidebar && sidebar.getBoundingClientRect().width > 60;
        btn.style.display = open ? 'none' : 'flex';
    }
    function ensure() { if (!document.getElementById(ID)) make(); update(); }
    setTimeout(ensure, 500);
    setInterval(update, 600);
    new MutationObserver(ensure).observe(document.body, { childList: true });
})();
</script>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(SIDEBAR_JS, unsafe_allow_html=True)


def sidebar_brand():
    st.sidebar.markdown("""
<div style="padding:16px 12px 10px 12px; display:flex; align-items:center; gap:10px;">
    <span style="font-size:1.3rem;">🇸🇳</span>
    <span style="font-size:1rem; font-weight:700; color:white;">SenStat</span>
</div>
<hr style="border-color:rgba(255,255,255,0.08); margin:0 12px 6px 12px;">
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
