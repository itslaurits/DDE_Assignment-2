import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from components.filters import render_page_filter_banner
from components.charts import (
    CLUSTER_COLORS, CLUSTER_LABELS, PLOTLY_TEMPLATE, PLOTLY_LAYOUT,
    apply_design, data_coverage_note, DESIGN, format_kpi,
)

df = st.session_state["filtered_df"]
render_page_filter_banner(df)

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div class="page-title">🏢 Essen – Company Intelligence</div>
    <div class="page-subtitle">879 companies · Essen, Germany · Source: Bureau van Dijk</div>
</div>""", unsafe_allow_html=True)

# ── KPI Row ───────────────────────────────────────────────────────────────────
REV_COL = "Revenue th EUR last avail. year"
EMP_COL = "Number of employees 2024"

rev_series = df[REV_COL].dropna()
active_n   = int((df["Status"] == "Active").sum())
emp_total  = int(df[EMP_COL].sum()) if df[EMP_COL].notna().any() else 0
scaleup_24 = int(df["Scaleup 2024"].sum()) if "Scaleup 2024" in df.columns else 0
scaleup_20 = int(df["Scaleup 2020"].sum()) if "Scaleup 2020" in df.columns else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Active Companies", f"{active_n:,}",          delta=f"of {len(df)} total")
c2.metric("Employment 2024",  format_kpi(emp_total))
c3.metric("Total Revenue",    format_kpi(rev_series.sum() * 1e3, prefix="€"),
          delta=f"{len(rev_series)} with data")
c4.metric("Scaleups 2024",    f"{scaleup_24}",
          delta=f"↑ from {scaleup_20} in 2020")

# ── Insight Cards ─────────────────────────────────────────────────────────────
st.markdown("<hr style='border-color:#E5E5E5;margin:32px 0'>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    st.markdown("""
    <div class="insight-card-accent" style="min-height:72px">
        <strong>📊 Revenue Concentration</strong><br>
        Top 10 firms generate 87.5% of total revenue (€200B)
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="insight-card" style="min-height:72px">
        <strong>🚀 Growth Momentum</strong><br>
        High-Growth firms: 7 (2020) → 36 (2024) · +414% in 4 years
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="insight-card" style="min-height:72px">
        <strong>🏗️ Young Business Landscape</strong><br>
        53% of firms founded after 2000 · Strongest decade: 2010s (247 firms)
    </div>""", unsafe_allow_html=True)
with col4:
    st.markdown("""
    <div class="insight-card" style="min-height:72px">
        <strong>👥 Gender Gap in Leadership</strong><br>
        Only 22.4% female decision makers · Large variation by sector
    </div>""", unsafe_allow_html=True)

# ── 3 Mini Charts ─────────────────────────────────────────────────────────────
st.markdown("<hr style='border-color:#E5E5E5;margin:32px 0'>", unsafe_allow_html=True)
mc1, mc2, mc3 = st.columns(3)

with mc1:
    cdata = (
        df[df["primary_cluster"] != "unknown"]["primary_cluster"]
        .value_counts()
        .reset_index()
    )
    cdata.columns = ["cluster", "count"]
    cdata["label"] = cdata["cluster"].map(CLUSTER_LABELS).fillna(cdata["cluster"])
    cdata["color"] = cdata["cluster"].map(CLUSTER_COLORS)
    if len(cdata) > 0:
        fig = go.Figure(go.Pie(
            labels=cdata["label"],
            values=cdata["count"],
            hole=0.45,
            marker_colors=cdata["color"].fillna("#A0A0A0").tolist(),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} companies (%{percent})<extra></extra>",
        ))
        apply_design(fig, "Cluster Distribution")
        fig.update_layout(
            height=320,
            legend=dict(orientation="v", font=dict(size=10)),
            margin=dict(l=0, r=0, t=40, b=0),
        )
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No cluster data available.")

with mc2:
    ndata = (
        df["NACE Rev. 2 main section"]
        .value_counts()
        .head(8)
        .reset_index()
    )
    ndata.columns = ["nace", "count"]
    ndata["label"] = ndata["nace"].str[:35]
    if len(ndata) > 0:
        fig = px.bar(
            ndata.sort_values("count"),
            y="label", x="count",
            orientation="h",
            color_discrete_sequence=[DESIGN["color_brand"]],
        )
        apply_design(fig, "Top 8 NACE Sectors")
        fig.update_layout(
            yaxis_title="", xaxis_title="No. of companies",
            height=320, showlegend=False,
        )
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No NACE data available.")

with mc3:
    years = list(range(2017, 2025))
    emp_totals = [
        df[f"Number of employees {y}"].sum()
        for y in years
        if f"Number of employees {y}" in df.columns
    ]
    valid_years = [y for y in years if f"Number of employees {y}" in df.columns]
    emp_df = pd.DataFrame({"Year": valid_years, "Employees": emp_totals})
    emp_df = emp_df[emp_df["Employees"] > 0]
    if len(emp_df) > 1:
        fig = go.Figure(go.Scatter(
            x=emp_df["Year"],
            y=emp_df["Employees"],
            mode="lines+markers",
            line=dict(color=DESIGN["color_brand"], width=2),
            marker=dict(size=6),
            hovertemplate="<b>%{x}</b><br>%{y:,.0f} employees<extra></extra>",
        ))
        apply_design(fig, "Total Employment 2017–2024")
        fig.update_layout(
            xaxis_title="", yaxis_title="Employees",
            height=320, showlegend=False,
        )
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(data_coverage_note(df, EMP_COL))
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No employment data available.")

# ── Top-20 Table ──────────────────────────────────────────────────────────────
st.markdown("<hr style='border-color:#E5E5E5;margin:32px 0'>", unsafe_allow_html=True)
st.markdown(
    "<div style='font-size:16px;font-weight:600;color:#1A1A1A;margin-bottom:12px;'>"
    "Top 20 Companies by Revenue</div>",
    unsafe_allow_html=True,
)

top20_raw = df.nlargest(20, REV_COL, keep="all") if df[REV_COL].notna().any() else df.head(20)
top20 = top20_raw[[
    "Company name (Latin alphabet)", "primary_cluster", REV_COL, EMP_COL, "Status"
]].copy()
top20["Revenue (M €)"]   = (top20[REV_COL] / 1000).round(1)
top20["Employees 2024"]  = top20[EMP_COL].astype("Int64")
top20["Cluster"]         = top20["primary_cluster"].map(CLUSTER_LABELS).fillna(top20["primary_cluster"])
top20["Status"] = top20["Status"].apply(
    lambda v: "✅ Active" if v == "Active" else f"⚪ {v}"
)
top20 = top20.rename(columns={
    "Company name (Latin alphabet)": "Company",
})[["Company", "Cluster", "Revenue (M €)", "Employees 2024", "Status"]]

st.dataframe(
    top20,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Revenue (M €)": st.column_config.NumberColumn("Revenue (M €)", format="%.1f"),
    },
)
