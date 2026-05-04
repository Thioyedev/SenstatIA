import streamlit as st
import streamlit.components.v1 as components

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
.fact-card .src   { font-size: 0.68rem; color: #666; margin-top: 10px; font-style: italic; }

/* ── Theme cards ──────────────────────────────────────────── */
.theme-card {
    background: white;
    border-radius: 14px;
    padding: 24px 18px 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    cursor: pointer;
    transition: transform 0.18s, box-shadow 0.18s;
    text-align: center;
    color: #1A1A1A;
    /* accent border-top set inline per theme */
}
.theme-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 28px rgba(0,0,0,0.13);
}
.theme-card .emoji  { font-size: 2.2rem; margin-bottom: 12px; line-height: 1; }
.theme-card .name   { font-weight: 700; font-size: 1rem; color: #1A1A2E; margin-bottom: 6px; }
.theme-card .desc   { font-size: 0.78rem; color: #666; line-height: 1.4; margin-bottom: 10px; }
.theme-card .source { font-size: 0.69rem; color: #00853F; font-weight: 600; }
.theme-card .explore-cta {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    margin-top: 14px;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.79rem;
    font-weight: 600;
    background: #F0FFF4;
    color: #00853F;
    transition: background 0.18s, color 0.18s;
}
.theme-card:hover .explore-cta {
    background: #00853F;
    color: white;
}

/* Hide external explore buttons — card click triggers them via JS */
[data-testid="column"]:has(.theme-card) .stButton {
    height: 0 !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}

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

/* ── Sticky chat input ────────────────────────────────────── */
[data-testid="stBottom"] {
    position: sticky !important;
    bottom: 0 !important;
    z-index: 99 !important;
    background: #F5F7FA !important;
    padding: 8px 0 12px 0 !important;
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
    border-radius: 20px;
    font-weight: 500;
    font-size: 0.84rem;
    padding: 7px 16px;
    transition: all 0.15s;
    border: 1.5px solid #e0e0e0;
    background: white;
    color: #333;
    text-align: left;
}
.stButton > button:hover {
    border-color: #00853F;
    color: #00853F;
    background: #F0FFF4;
    box-shadow: 0 2px 8px rgba(0,133,63,0.12);
}

/* Sidebar buttons — dark theme override */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.08) !important;
    border-color: rgba(255,255,255,0.14) !important;
    color: rgba(255,255,255,0.85) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.16) !important;
    border-color: rgba(255,255,255,0.25) !important;
    color: white !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #00853F !important;
    border-color: #00853F !important;
    color: white !important;
}

/* ── Section label ────────────────────────────────────────── */
.section-lbl {
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase;
    color: #666; margin: 0 0 10px 0;
}
.divider { border: none; border-top: 1px solid #E8E8E8; margin: 16px 0; }

/* ── Page banner ──────────────────────────────────────────── */
.page-banner {
    display: flex;
    align-items: center;
    gap: 16px;
    background: white;
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 16px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.07);
    border-left: 4px solid #00853F;
}
.page-banner-icon { font-size: 1.9rem; line-height: 1; }
.page-banner-title { font-size: 1.15rem; font-weight: 700; color: #1A1A2E; margin-bottom: 2px; }
.page-banner-sub { font-size: 0.79rem; color: #777; line-height: 1.4; }

/* ── Hide Streamlit header anchor icons ───────────────────── */
h1 a, h2 a, h3 a { display: none !important; }

/* ── Inline source pill ───────────────────────────────────── */
.source-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #F0FFF4;
    border: 1px solid #C6F6D5;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.72rem;
    color: #2D6A4F;
    font-weight: 500;
    margin: 2px 3px 0 0;
}
</style>
"""


_SIDEBAR_JS = """
<script>
(function() {
    var doc = window.parent.document;

    // ── Sidebar tab ──────────────────────────────────────────────────────────
    var ID = 'senstat-sidebar-tab';

    function makeSidebarTab() {
        if (doc.getElementById(ID)) return doc.getElementById(ID);
        var btn = doc.createElement('button');
        btn.id    = ID;
        btn.title = 'Ouvrir la sidebar';
        btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" '
            + 'viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" '
            + 'stroke-linecap="round" stroke-linejoin="round">'
            + '<rect x="3" y="3" width="18" height="18" rx="2"/>'
            + '<line x1="9" y1="3" x2="9" y2="21"/></svg>';
        btn.style.cssText = [
            'position:fixed', 'left:0', 'top:50%', 'transform:translateY(-50%)',
            'z-index:2147483647', 'background:#1A1A2E', 'border:none',
            'border-radius:0 8px 8px 0', 'width:28px', 'height:52px',
            'cursor:pointer', 'display:none', 'align-items:center',
            'justify-content:center', 'box-shadow:3px 0 14px rgba(0,0,0,0.6)',
            'padding:0', 'outline:none'
        ].join(';');
        btn.onmouseenter = function() { btn.style.background = '#252545'; };
        btn.onmouseleave = function() { btn.style.background = '#1A1A2E'; };
        btn.onclick = function(e) {
            e.stopPropagation();
            var exp = doc.querySelector('[data-testid="stSidebarCollapsedControl"] button');
            if (exp) { exp.click(); return; }
            var col = doc.querySelector('[data-testid="stSidebarCollapseButton"] button');
            if (col) col.click();
        };
        doc.body.appendChild(btn);
        return btn;
    }

    function updateSidebar() {
        var tab     = makeSidebarTab();
        var sidebar = doc.querySelector('[data-testid="stSidebar"]');
        var open    = sidebar && sidebar.getBoundingClientRect().width > 60;
        tab.style.display = open ? 'none' : 'flex';
    }

    // ── Theme card click delegation ──────────────────────────────────────────
    function setupThemeCards() {
        doc.querySelectorAll('.theme-card').forEach(function(card) {
            if (card.dataset.clickReady) return;
            card.dataset.clickReady = '1';
            card.addEventListener('click', function() {
                // Walk up until we are a direct child of stVerticalBlock
                var el = card;
                while (el && el.parentElement &&
                       !el.parentElement.matches('[data-testid="stVerticalBlock"]')) {
                    el = el.parentElement;
                }
                if (!el) return;
                // Find the immediately following sibling that contains a button
                var next = el.nextElementSibling;
                while (next) {
                    var btn = next.querySelector('.stButton > button');
                    if (btn) { btn.click(); return; }
                    next = next.nextElementSibling;
                }
            });
        });
    }

    // ── Shared observer + init ───────────────────────────────────────────────
    setTimeout(function() { updateSidebar(); setupThemeCards(); }, 300);
    setInterval(updateSidebar, 500);

    var observer = new MutationObserver(function() {
        updateSidebar();
        setupThemeCards();
    });
    observer.observe(doc.body, { childList: true, subtree: true });
})();
</script>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)
    components.html(_SIDEBAR_JS, height=0)


def sidebar_brand():
    if "lang" not in st.session_state:
        st.session_state.lang = "fr"

    st.sidebar.markdown("""
<div style="padding:16px 12px 8px 12px; display:flex; align-items:center; gap:10px;">
    <span style="font-size:1.3rem;">🇸🇳</span>
    <span style="font-size:1rem; font-weight:700; color:white;">SenStat</span>
</div>
<hr style="border-color:rgba(255,255,255,0.08); margin:0 12px 6px 12px;">
""", unsafe_allow_html=True)

    lc1, lc2 = st.sidebar.columns(2)
    if lc1.button("🇫🇷 FR", use_container_width=True, key="sb_lang_fr",
                  type="primary" if st.session_state.lang == "fr" else "secondary"):
        st.session_state.lang = "fr"
        st.rerun()
    if lc2.button("🇬🇧 EN", use_container_width=True, key="sb_lang_en",
                  type="primary" if st.session_state.lang == "en" else "secondary"):
        st.session_state.lang = "en"
        st.rerun()
    st.sidebar.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


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
