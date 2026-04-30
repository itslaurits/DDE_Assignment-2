import streamlit as st

from components.filters import render_page_filter_banner
from components.charts import DESIGN
from components.agent import build_system_prompt, get_groq_response

df_raw = st.session_state["df"]
filtered_df = st.session_state["filtered_df"]

# ── Init session state ────────────────────────────────────────────────────────
if "system_prompt" not in st.session_state:
    st.session_state["system_prompt"] = build_system_prompt(df_raw)
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

render_page_filter_banner(filtered_df)

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div class="page-title">🤖 AI Company Intelligence Agent</div>
    <div class="page-subtitle">Powered by Groq · Llama 3.3 70B · Knows all 879 Essen companies</div>
</div>""", unsafe_allow_html=True)

# ── Filter info ───────────────────────────────────────────────────────────────
if len(filtered_df) < len(df_raw):
    st.markdown("""
    <div style="background:#EFF6FF;border-left:3px solid #2563EB;
        border-radius:0 6px 6px 0;padding:8px 16px;
        font-family:Inter,sans-serif;font-size:13px;color:#1D4ED8;
        margin-bottom:16px;">
    💡 Filters active – the agent always knows all 879 companies</div>
    """, unsafe_allow_html=True)

# ── Quick questions ───────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:Inter,sans-serif;font-size:12px;font-weight:600;
color:#666666;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:8px;">
Quick Questions</div>""", unsafe_allow_html=True)

suggestions = [
    "Which firm has the highest revenue?",
    "How many scaleups exist in 2024?",
    "Which cluster grows the fastest?",
    "What is the gender split among executives?",
    "Who are the top 5 employers?",
    "How concentrated is revenue in Essen?",
    "Which firms were scaleups multiple times?",
    "Which sectors are structurally loss-making?",
]

cols = st.columns(4)
for i, s in enumerate(suggestions):
    with cols[i % 4]:
        if st.button(s, key=f"sug_{i}", use_container_width=True):
            st.session_state["pending_question"] = s

st.markdown("<hr style='border-color:#E5E5E5;margin:16px 0'>", unsafe_allow_html=True)

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state["chat_history"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ── Pending question (from quick-question button) ─────────────────────────────
if "pending_question" in st.session_state:
    q = st.session_state.pop("pending_question")
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        with st.spinner("Groq is analysing…"):
            answer = get_groq_response(
                q,
                st.session_state["system_prompt"],
                st.session_state["chat_history"],
            )
        st.write(answer)
    st.session_state["chat_history"] += [
        {"role": "user",      "content": q},
        {"role": "assistant", "content": answer},
    ]
    st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask me anything about Essen companies…"):
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Groq is analysing…"):
            answer = get_groq_response(
                prompt,
                st.session_state["system_prompt"],
                st.session_state["chat_history"],
            )
        st.write(answer)
    st.session_state["chat_history"] += [
        {"role": "user",      "content": prompt},
        {"role": "assistant", "content": answer},
    ]

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<hr style='border-color:#E5E5E5;margin:24px 0'>", unsafe_allow_html=True)
fc1, fc2 = st.columns([3, 1])
with fc1:
    n_msg = len(st.session_state["chat_history"]) // 2
    st.caption(f"💬 {n_msg} questions this session · Context: last 10 messages")
with fc2:
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state["chat_history"] = []
        st.rerun()
