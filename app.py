import streamlit as st
from utils.data_loader import load_data
from components.filters import render_global_filters
from components.charts import inject_global_css

st.set_page_config(
    layout="wide",
    page_title="DDE Essen | Company Intelligence",
    page_icon="🏢",
    initial_sidebar_state="expanded",
)

inject_global_css()

# ── Load data ──────────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    with st.spinner("Loading data…"):
        st.session_state["df"] = load_data()


# ── Navigation (no "app" entry) ────────────────────────────────────────────────
pages = [
    st.Page("pages/01_home.py",       title="Home",        icon="🏢", default=True),
    st.Page("pages/02_financials.py", title="Financials",  icon="💰"),
    st.Page("pages/03_analytics.py",  title="Analytics",   icon="📊"),
    st.Page("pages/04_clusters.py",   title="Clusters",    icon="🗂️"),
    st.Page("pages/05_people.py",     title="People",      icon="👥"),
    st.Page("pages/06_chat.py",       title="Chat",        icon="🤖"),
]
pg = st.navigation(pages)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div id="essen-logo">
        <div style="font-family:Inter,sans-serif;font-size:22px;font-weight:800;
                    color:#1A1A1A;letter-spacing:-1.5px;line-height:1.1;">
            Essen<span style="display:inline-block;width:7px;height:7px;
                background:#2563EB;border-radius:50%;margin-left:3px;
                vertical-align:middle;margin-bottom:5px;"></span>
        </div>
        <div style="font-size:10px;color:#999999;letter-spacing:0.08em;
                    text-transform:uppercase;margin-top:3px;">Company Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🤖 AI Agent", expanded=False):
        st.text_input(
            "Groq API Key",
            type="password",
            placeholder="gsk_...",
            help="Get your free key at console.groq.com/keys",
            key="groq_api_key",
            label_visibility="collapsed",
        )
        if st.session_state.get("groq_api_key"):
            st.caption("🟢 Groq active · go to Chat tab")
        else:
            st.caption("⚪ Enter key to enable Chat")

    st.divider()

# ── Global filters (also writes to sidebar) ───────────────────────────────────
filtered_df = render_global_filters(st.session_state["df"])
st.session_state["filtered_df"] = filtered_df

# ── Run the selected page ──────────────────────────────────────────────────────
pg.run()
