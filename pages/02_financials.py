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
    <div class="page-title">💰 Financials</div>
    <div class="page-subtitle">Revenue, Profit &amp; Growth Analysis</div>
</div>""", unsafe_allow_html=True)

REV_COL    = "Revenue th EUR last avail. year"
PROFIT_COL = "Profit/loss before tax th EUR last avail. year"
NI_COL     = "Net income th USD last avail. year"
EQ_COL     = "Equity ratio last avail. year"
EMP_COL    = "Number of employees 2024"

# ── Local Filters ─────────────────────────────────────────────────────────────
with st.expander("⚙️ Advanced Filters", expanded=True):
    flt_col1, flt_col2, flt_col3 = st.columns([2, 1, 2])

    rev_data = df[REV_COL].dropna() / 1000  # M EUR
    with flt_col1:
        if len(rev_data) > 0:
            rev_min, rev_max = float(rev_data.min()), float(rev_data.max())
            rev_range = st.slider(
                "Revenue (M EUR)",
                min_value=rev_min, max_value=rev_max,
                value=(rev_min, min(rev_max, rev_min + (rev_max - rev_min))),
                key="fin_rev_range",
            )
        else:
            rev_range = None

    with flt_col2:
        only_profitable = st.toggle("Profitable only", key="fin_profitable")

    with flt_col3:
        growth_map_local = {
            "Scaleup": "Scaleup 2024",
            "Gazelle": "Gazelle 2024",
            "High Growth": "HighGrowthFirm 2024",
            "Very High Growth": "VeryHighGrowthFirm 2024",
            "Superstar": "Superstar 2024",
        }
        sel_growth = st.multiselect(
            "Growth Type 2024", list(growth_map_local.keys()),
            placeholder="All", key="fin_growth",
        )

    year_range = st.slider("Founded Year", 1850, 2024, (1950, 2024), key="fin_year")

# Apply local filters
ldf = df.copy()
if rev_range is not None:
    ldf = ldf[
        (ldf[REV_COL] / 1000 >= rev_range[0]) &
        (ldf[REV_COL] / 1000 <= rev_range[1])
    ]
if only_profitable:
    ldf = ldf[ldf["profit_margin"] > 0]
if sel_growth:
    mask = pd.Series(False, index=ldf.index)
    for g in sel_growth:
        col = growth_map_local[g]
        if col in ldf.columns:
            mask |= (ldf[col] == 1)
    ldf = ldf[mask]
ldf = ldf[
    (ldf["Founded year"] >= year_range[0]) &
    (ldf["Founded year"] <= year_range[1])
]

# ── KPI Row ───────────────────────────────────────────────────────────────────
rev_series  = ldf[REV_COL].dropna()
prof_series = ldf[PROFIT_COL].dropna()
ni_series   = ldf[NI_COL].dropna()
profitable_n   = int((ldf["profit_margin"] > 0).sum())
profitable_pct = f"{profitable_n / len(ldf) * 100:.1f}%" if len(ldf) > 0 else "–"

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue",    format_kpi(rev_series.sum() * 1e3, prefix="€"))
k2.metric("Median Revenue",   format_kpi(rev_series.median() * 1e3, prefix="€") if len(rev_series) > 0 else "–")
k3.metric("Profitable Cos.",  f"{profitable_n:,} ({profitable_pct})")
k4.metric("Net Income",       format_kpi(ni_series.sum() * 1e3, prefix="$") if len(ni_series) > 0 else "–")

st.caption(
    f"Revenue: {len(rev_series)} companies · Net Income: {len(ni_series)} companies with data"
)

st.markdown("<hr style='border-color:#E5E5E5;margin:32px 0'>", unsafe_allow_html=True)

# ── Top 20 Horizontal Bar ─────────────────────────────────────────────────────
st.markdown(
    "<div style='font-size:15px;font-weight:600;color:#1A1A1A;margin-bottom:8px;'>"
    "Top 20 Companies by Revenue</div>",
    unsafe_allow_html=True,
)

top20 = ldf.nlargest(20, REV_COL) if ldf[REV_COL].notna().any() else ldf.head(0)

if len(top20) >= 2:
    top20 = top20.copy()
    top20["Revenue (M EUR)"]     = top20[REV_COL] / 1000
    top20["profit_margin_pct"]   = (top20["profit_margin"] * 100).round(2)

    fig = go.Figure(go.Bar(
        y=top20["Company name (Latin alphabet)"],
        x=top20["Revenue (M EUR)"],
        orientation="h",
        marker_color=[CLUSTER_COLORS.get(c, "#A0A0A0") for c in top20["primary_cluster"]],
        customdata=np.stack([
            top20["primary_cluster"],
            top20["Revenue (M EUR)"].round(1),
            top20[EMP_COL].fillna(0).astype(int),
            top20["profit_margin_pct"].fillna(0),
        ], axis=-1),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Cluster: %{customdata[0]}<br>"
            "Revenue: %{customdata[1]:.1f} M EUR<br>"
            "Employees: %{customdata[2]:,}<br>"
            "Profit Margin: %{customdata[3]:.1f}%<extra></extra>"
        ),
    ))
    apply_design(fig, "Top 20 by Revenue")
    fig.update_layout(
        height=520,
        yaxis=dict(autorange="reversed"),
        xaxis_title="Revenue (M EUR)",
        yaxis_title="",
        showlegend=False,
    )
    with st.container():
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(data_coverage_note(ldf, REV_COL))
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("Not enough data for Top 20 chart.")

st.markdown("<hr style='border-color:#E5E5E5;margin:32px 0'>", unsafe_allow_html=True)

# ── Distribution & Profitability ──────────────────────────────────────────────
st.markdown(
    "<div style='font-size:15px;font-weight:600;color:#1A1A1A;margin-bottom:16px;'>"
    "Distribution &amp; Profitability</div>",
    unsafe_allow_html=True,
)
va, vb = st.columns(2)

with va:
    hist_data = ldf[REV_COL].dropna() / 1000
    if len(hist_data) >= 5:
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=np.log10(hist_data.clip(lower=0.001)),
            nbinsx=30,
            marker_color=DESIGN["color_brand"],
            opacity=0.8,
            name="Revenue",
            hovertemplate="log₁₀(Rev)=%{x:.1f}<br>Companies=%{y}<extra></extra>",
        ))
        median_log = np.log10(hist_data.median())
        mean_log   = np.log10(hist_data.mean())
        fig.add_vline(x=median_log, line_color=DESIGN["color_brand"],
                      line_width=2, annotation_text="Median",
                      annotation_position="top right")
        fig.add_vline(x=mean_log, line_color=DESIGN["color_warning"],
                      line_dash="dash", line_width=2,
                      annotation_text="Mean",
                      annotation_position="top left")
        apply_design(fig, "Revenue Distribution (log₁₀ M EUR)")
        fig.update_layout(
            xaxis_title="log₁₀(Revenue M EUR)",
            yaxis_title="No. of companies",
            height=380, showlegend=False,
        )
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(data_coverage_note(ldf, REV_COL))
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Not enough revenue data for histogram.")

with vb:
    scatter_df = ldf[[
        "Company name (Latin alphabet)", "primary_cluster",
        REV_COL, PROFIT_COL, EMP_COL
    ]].dropna(subset=[REV_COL, PROFIT_COL])
    scatter_df = scatter_df[scatter_df[REV_COL] > 0].copy()

    if len(scatter_df) >= 5:
        scatter_df["Revenue (M EUR)"] = scatter_df[REV_COL] / 1000
        scatter_df["Profit (M EUR)"]  = scatter_df[PROFIT_COL] / 1000
        emp_vals = scatter_df[EMP_COL].fillna(scatter_df[EMP_COL].median())
        emp_min, emp_max = emp_vals.min(), emp_vals.max()
        if emp_max > emp_min:
            scatter_df["emp_size"] = 6 + (emp_vals - emp_min) / (emp_max - emp_min) * 24
        else:
            scatter_df["emp_size"] = 12

        fig = px.scatter(
            scatter_df,
            x="Revenue (M EUR)",
            y="Profit (M EUR)",
            color="primary_cluster",
            color_discrete_map=CLUSTER_COLORS,
            size="emp_size",
            size_max=24,
            hover_name="Company name (Latin alphabet)",
            hover_data={
                "Revenue (M EUR)": ":.1f",
                "Profit (M EUR)":  ":.1f",
                "primary_cluster":   True,
                "emp_size": False,
            },
            log_x=True,
        )
        fig.add_hline(y=0, line_color=DESIGN["color_error"],
                      line_dash="dash", line_width=1.5)
        apply_design(fig, "Profit vs Revenue")
        fig.update_layout(height=380, legend_title_text="Cluster")
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(data_coverage_note(ldf, PROFIT_COL))
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Not enough data for scatter plot.")

st.markdown("<hr style='border-color:#E5E5E5;margin:32px 0'>", unsafe_allow_html=True)

# ── Cluster Comparison ────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-size:15px;font-weight:600;color:#1A1A1A;margin-bottom:16px;'>"
    "Cluster Comparison</div>",
    unsafe_allow_html=True,
)
ca, cb = st.columns(2)

with ca:
    box_df = ldf[ldf["primary_cluster"] != "unknown"][[
        "primary_cluster", REV_COL
    ]].dropna()
    if len(box_df) >= 5:
        medians = box_df.groupby("primary_cluster")[REV_COL].median().sort_values()
        box_df["primary_cluster"] = pd.Categorical(
            box_df["primary_cluster"],
            categories=medians.index.tolist(),
            ordered=True,
        )
        fig = px.box(
            box_df.sort_values("primary_cluster"),
            x="primary_cluster",
            y=REV_COL,
            color="primary_cluster",
            color_discrete_map=CLUSTER_COLORS,
            points=False,
        )
        fig.update_yaxes(type="log", title="Revenue (th EUR, log scale)")
        fig.update_xaxes(title="", tickangle=-35)
        apply_design(fig, "Revenue Distribution by Cluster (log scale)")
        fig.update_layout(height=400, showlegend=False)
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(data_coverage_note(ldf, REV_COL))
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Not enough data for box plot.")

with cb:
    eq_df = ldf[["Company name (Latin alphabet)", EQ_COL]].dropna().copy()
    eq_df = eq_df.rename(columns={"Company name (Latin alphabet)": "Company"})
    eq_df["Equity Ratio"] = pd.to_numeric(eq_df[EQ_COL], errors="coerce")
    eq_df = eq_df.dropna(subset=["Equity Ratio"])

    if len(eq_df) >= 10:
        top10_eq  = eq_df.nlargest(10, "Equity Ratio")
        bot10_eq  = eq_df.nsmallest(10, "Equity Ratio")
        combined  = pd.concat([top10_eq, bot10_eq]).drop_duplicates()
        combined  = combined.sort_values("Equity Ratio")
        colors    = [
            DESIGN["color_success"] if v >= 0 else DESIGN["color_error"]
            for v in combined["Equity Ratio"]
        ]

        fig = go.Figure(go.Bar(
            y=combined["Company"].str[:40],
            x=combined["Equity Ratio"],
            orientation="h",
            marker_color=colors,
            hovertemplate="<b>%{y}</b><br>Equity Ratio: %{x:.1f}%<extra></extra>",
        ))
        apply_design(fig, "Equity Ratio – Top/Bottom 10")
        fig.update_layout(
            height=400,
            xaxis_title="Equity Ratio (%)",
            yaxis_title="",
            showlegend=False,
        )
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(data_coverage_note(ldf, EQ_COL))
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Not enough equity data.")

st.markdown("<hr style='border-color:#E5E5E5;margin:32px 0'>", unsafe_allow_html=True)

# ── Growth Type Analysis ──────────────────────────────────────────────────────
with st.expander("🚀 Growth Type Analysis", expanded=False):
    growth_types_available = {
        "Scaleup 2024":            "Scaleup",
        "Gazelle 2024":            "Gazelle",
        "HighGrowthFirm 2024":     "High Growth",
        "VeryHighGrowthFirm 2024": "Very High Growth",
        "Superstar 2024":          "Superstar",
    }
    sel_type = st.selectbox(
        "Growth Type", list(growth_types_available.values()),
        key="fin_growth_type_sel",
    )
    col_name = [k for k, v in growth_types_available.items() if v == sel_type][0]

    if col_name in ldf.columns:
        labeled   = ldf[ldf[col_name] == 1]
        unlabeled = ldf[ldf[col_name] != 1]

        if len(labeled) > 0:
            g1, g2, g3 = st.columns(3)
            avg_rev_lbl  = labeled[REV_COL].mean() / 1000 if labeled[REV_COL].notna().any() else 0
            avg_rev_rest = unlabeled[REV_COL].mean() / 1000 if unlabeled[REV_COL].notna().any() else 0
            avg_emp_lbl  = labeled[EMP_COL].mean() if labeled[EMP_COL].notna().any() else 0
            avg_emp_rest = unlabeled[EMP_COL].mean() if unlabeled[EMP_COL].notna().any() else 0
            delta_rev = f"vs. {avg_rev_rest:.1f} rest" if avg_rev_rest > 0 else None
            delta_emp = f"vs. {avg_emp_rest:.0f} rest" if avg_emp_rest > 0 else None

            g1.metric(f"{sel_type} 2024",    f"{len(labeled)} companies")
            g2.metric("Avg Revenue",          f"{avg_rev_lbl:.1f} M EUR", delta=delta_rev)
            g3.metric("Avg Employees 2024",   f"{avg_emp_lbl:.0f}",       delta=delta_emp)

            bar_data = pd.DataFrame({
                "Group": [sel_type, "Others"],
                "Avg Revenue (M EUR)": [avg_rev_lbl, avg_rev_rest],
            })
            fig = px.bar(
                bar_data, x="Group", y="Avg Revenue (M EUR)",
                color="Group",
                color_discrete_map={sel_type: DESIGN["color_brand"], "Others": "#E5E5E5"},
            )
            apply_design(fig, f"Avg Revenue: {sel_type} vs Others")
            fig.update_layout(showlegend=False, height=300)
            with st.container():
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            tbl = labeled[[
                "Company name (Latin alphabet)", "primary_cluster",
                REV_COL, EMP_COL
            ]].copy()
            tbl["Revenue (M EUR)"] = (tbl[REV_COL] / 1000).round(1)
            tbl = tbl.rename(columns={
                "Company name (Latin alphabet)": "Company",
                "primary_cluster": "Cluster",
                EMP_COL: "Employees 2024",
            })[["Company", "Cluster", "Revenue (M EUR)", "Employees 2024"]]
            st.dataframe(tbl.sort_values("Revenue (M EUR)", ascending=False),
                         use_container_width=True, hide_index=True)
        else:
            st.info(f"No {sel_type} firms in current filter selection.")
    else:
        st.info("Column not available.")
