import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

from components.filters import render_page_filter_banner
from components.charts import (
    CLUSTER_COLORS, PLOTLY_TEMPLATE, PLOTLY_LAYOUT,
    apply_design, data_coverage_note, DESIGN,
)

df = st.session_state["filtered_df"]
render_page_filter_banner(df)

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div class="page-title">📊 Analytics &amp; Insights</div>
    <div class="page-subtitle">Statistical Analysis · All charts respond to global filters</div>
</div>""", unsafe_allow_html=True)

REV_COL    = "Revenue th EUR last avail. year"
PROFIT_COL = "Profit/loss before tax th EUR last avail. year"
EMP_COL    = "Number of employees 2024"
NAME_COL   = "Company name (Latin alphabet)"

# ── Constants ─────────────────────────────────────────────────────────────────
GROWTH_TYPES = ["Scaleup", "Gazelle", "HighGrowthFirm", "VeryHighGrowthFirm", "Scaler", "Superstar"]
YEARS        = [2020, 2021, 2022, 2023, 2024]
EMP_YEARS    = list(range(2017, 2025))
STACKED_COLORS = {
    "Scaleup":           "#2A6DFB",
    "Gazelle":           "#9061FF",
    "HighGrowthFirm":    "#42C366",
    "VeryHighGrowthFirm":"#ECB730",
    "Scaler":            "#EB3424",
    "Superstar":         "#1A4FBF",
}

def section(title):
    st.markdown(
        f"<div style='font-size:14px;font-weight:600;color:#1A1A1A;"
        f"margin-bottom:10px;'>{title}</div>",
        unsafe_allow_html=True,
    )

def divider():
    st.markdown("<hr style='border-color:#E5E5E5;margin:24px 0'>", unsafe_allow_html=True)

def chart_wrap(fig, coverage_col=None):
    with st.container():
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        if coverage_col:
            st.caption(data_coverage_note(df, coverage_col))
        st.markdown("</div>", unsafe_allow_html=True)

# ── dominant growth type helper ───────────────────────────────────────────────
def dominant_growth_type(df_in):
    out = pd.Series("Standard", index=df_in.index)
    for col, label in [
        ("Superstar 2024", "Superstar"),
        ("Scaleup 2024",   "Scaleup"),
        ("VeryHighGrowthFirm 2024", "Very High Growth"),
        ("HighGrowthFirm 2024",     "High Growth"),
        ("Gazelle 2024",            "Gazelle"),
        ("Scaler 2024",             "Scaler"),
    ]:
        if col in df_in.columns:
            out = out.where(df_in[col] != 1, label)
    return out

# ════════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "🔬 Explorer",
    "📈 Pareto",
    "🚀 Growth",
    "💹 Profitability",
    "👷 Employment",
    "🏛️ Foundings",
    "👥 Gender",
    "📅 Age & Perf.",
    "⭐ Star Finder",
])

# ────────────────────────────────────────────────────────────────────────────────
# TAB 1 – Free Explorer
# ────────────────────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown("""
    <div class="insight-card-accent" style="margin-bottom:20px">
        <strong>🔬 Free Explorer</strong> – Combine any dimensions and
        analyse every aspect of the dataset.
    </div>""", unsafe_allow_html=True)

    exp_cols = st.columns([1.2, 1.2, 1.4, 1.2])

    groupby_options = {
        "Cluster":          "primary_cluster",
        "Gender":           "DM Gender",
        "Founding Decade":  "decade_founded",
        "Status":           "Status",
        "NACE Sector":      "NACE Rev. 2 main section",
        "Growth Type 2024": "__growth_type__",
    }
    split_options = {
        "None":             None,
        "Gender":           "DM Gender",
        "Cluster":          "primary_cluster",
        "Growth Type 2024": "__growth_type__",
        "Status":           "Status",
    }
    kpi_options = [
        "No. of Companies",
        "Avg Revenue (M EUR)",
        "Avg Employees 2024",
        "Median Profit Margin (%)",
        "Female Leadership (%)",
        "Avg Employment Growth 2020-2024 (%)",
        "% Scaleup 2024",
        "% HighGrowth 2024",
        "% Gazelle 2024",
    ]
    chart_type_options = ["Grouped Bar", "Heatmap", "Treemap"]

    with exp_cols[0]:
        sel_groupby = st.selectbox("Group by", list(groupby_options.keys()), key="exp_groupby")
    with exp_cols[1]:
        sel_split   = st.selectbox("Split by (optional)", list(split_options.keys()), key="exp_split")
    with exp_cols[2]:
        sel_kpi     = st.selectbox("KPI", kpi_options, key="exp_kpi")
    with exp_cols[3]:
        sel_chart   = st.selectbox("Chart type", chart_type_options, key="exp_chart")

    run_explorer = st.button("📊 Run analysis", type="primary", key="exp_run")

    st.caption(
        "💡 Example: Gender × Cluster → Female Leadership by sector | "
        "Growth Type × Decade → When did scaleups emerge?"
    )

    if run_explorer:
        st.toast("Running analysis…", icon="⏳")
        edf = df.copy()
        if groupby_options[sel_groupby] == "__growth_type__":
            edf["__growth_type__"] = dominant_growth_type(edf)
        if split_options.get(sel_split) == "__growth_type__":
            edf["__growth_type__"] = dominant_growth_type(edf)

        gb_col    = groupby_options[sel_groupby]
        split_col = split_options[sel_split]
        group_cols = [gb_col] + ([split_col] if split_col else [])
        group_cols = [c for c in group_cols if c in edf.columns or c == "__growth_type__"]

        def compute_kpi(grp):
            if sel_kpi == "No. of Companies":
                return grp.shape[0]
            elif sel_kpi == "Avg Revenue (M EUR)":
                return grp[REV_COL].mean() / 1000 if grp[REV_COL].notna().any() else np.nan
            elif sel_kpi == "Avg Employees 2024":
                return grp[EMP_COL].mean()
            elif sel_kpi == "Median Profit Margin (%)":
                return grp["profit_margin"].median() * 100 if grp["profit_margin"].notna().any() else np.nan
            elif sel_kpi == "Female Leadership (%)":
                genders = grp["DM Gender"]
                total = genders.isin(["M", "F"]).sum()
                return genders.eq("F").sum() / total * 100 if total > 0 else np.nan
            elif sel_kpi == "Avg Employment Growth 2020-2024 (%)":
                return grp["emp_growth_2020_2024"].mean()
            elif sel_kpi == "% Scaleup 2024":
                return grp["Scaleup 2024"].eq(1).sum() / grp.shape[0] * 100 if "Scaleup 2024" in grp.columns else np.nan
            elif sel_kpi == "% HighGrowth 2024":
                return grp["HighGrowthFirm 2024"].eq(1).sum() / grp.shape[0] * 100 if "HighGrowthFirm 2024" in grp.columns else np.nan
            elif sel_kpi == "% Gazelle 2024":
                return grp["Gazelle 2024"].eq(1).sum() / grp.shape[0] * 100 if "Gazelle 2024" in grp.columns else np.nan
            return np.nan

        result = edf.groupby(group_cols, dropna=False).apply(compute_kpi).reset_index()
        result.columns = group_cols + [sel_kpi]
        result = result.dropna(subset=[sel_kpi])
        result["n"] = edf.groupby(group_cols, dropna=False).size().reset_index(name="n")["n"]

        if len(result) == 0:
            st.info("No data for this selection.")
        elif sel_chart == "Grouped Bar":
            if split_col:
                fig = px.bar(
                    result, x=gb_col, y=sel_kpi, color=split_col,
                    barmode="group",
                    color_discrete_map=CLUSTER_COLORS if split_col == "primary_cluster" else None,
                )
            else:
                fig = px.bar(
                    result.sort_values(sel_kpi, ascending=True),
                    x=sel_kpi, y=gb_col, orientation="h",
                    color_discrete_sequence=[DESIGN["color_brand"]],
                )
            apply_design(fig, f"{sel_kpi} by {sel_groupby}")
            fig.update_layout(height=420)
            chart_wrap(fig)

        elif sel_chart == "Heatmap" and split_col:
            pivot = result.pivot(index=split_col, columns=gb_col, values=sel_kpi)
            fig = go.Figure(go.Heatmap(
                z=pivot.values.round(2),
                x=[str(c) for c in pivot.columns],
                y=pivot.index.tolist(),
                colorscale=[[0, "#EFF6FF"], [1, "#1D4ED8"]],
                hovertemplate="%{y} / %{x}: %{z:.1f}<extra></extra>",
            ))
            apply_design(fig, f"{sel_kpi}: {sel_groupby} × {sel_split}")
            fig.update_layout(height=420)
            chart_wrap(fig)

        elif sel_chart == "Treemap":
            path = group_cols
            fig = px.treemap(result, path=path, values=sel_kpi)
            apply_design(fig, f"{sel_kpi} – Treemap")
            fig.update_layout(height=480)
            chart_wrap(fig)
        else:
            fig = px.bar(
                result.sort_values(sel_kpi, ascending=True),
                x=sel_kpi, y=gb_col, orientation="h",
                color_discrete_sequence=[DESIGN["color_brand"]],
            )
            apply_design(fig, f"{sel_kpi} by {sel_groupby}")
            fig.update_layout(height=420)
            chart_wrap(fig)

# ────────────────────────────────────────────────────────────────────────────────
# TAB 2 – Pareto / Revenue Concentration
# ────────────────────────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown("""
    <div class="insight-card-accent" style="margin-bottom:20px">
        <strong>📈 Revenue Concentration:</strong> The top 10 firms generate
        87.5% of total revenue across all Essen companies (€200B total).
    </div>""", unsafe_allow_html=True)

    rev_sorted = df[REV_COL].dropna().sort_values()

    if len(rev_sorted) < 10:
        st.info("Too few revenue records for Pareto analysis.")
    else:
        n = len(rev_sorted)
        cum_firms = np.arange(1, n + 1) / n * 100
        cum_rev   = rev_sorted.cumsum() / rev_sorted.sum() * 100
        top10_rev_share = rev_sorted.iloc[-10:].sum() / rev_sorted.sum() * 100

        p1, p2 = st.columns(2)

        with p1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=cum_firms, y=cum_rev,
                mode="lines",
                fill="tozeroy",
                fillcolor="rgba(239,246,255,0.4)",
                line=dict(color=DESIGN["color_brand"], width=2),
                name="Lorenz Curve",
                hovertemplate="Top %{x:.1f}% firms → %{y:.1f}% revenue<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=[0, 100], y=[0, 100],
                mode="lines",
                line=dict(color="#D0D0D0", dash="dash", width=1.5),
                name="Equal distribution",
            ))
            ann_x = (n - 10) / n * 100
            ann_y = rev_sorted.iloc[:n - 10].sum() / rev_sorted.sum() * 100
            fig.add_annotation(
                x=ann_x, y=ann_y,
                text=f"Top 10 = {top10_rev_share:.1f}%",
                showarrow=True, arrowhead=2,
                arrowcolor=DESIGN["color_brand"],
                font=dict(size=12, color=DESIGN["color_brand"]),
            )
            apply_design(fig, "Lorenz Curve – Revenue Concentration")
            fig.update_layout(
                xaxis_title="Share of Firms (%)",
                yaxis_title="Cumulative Revenue (%)",
                height=400,
            )
            chart_wrap(fig)

        with p2:
            top10_val  = rev_sorted.iloc[-10:].sum() / 1e6
            mid40_val  = rev_sorted.iloc[-(min(50, n)):-(10)].sum() / 1e6 if n > 10 else 0
            rest_val   = rev_sorted.iloc[:-(min(50, n))].sum() / 1e6 if n > 50 else (rev_sorted.sum() - rev_sorted.iloc[-min(50,n):].sum()) / 1e6

            seg_fig = go.Figure(go.Bar(
                x=[top10_val, mid40_val, rest_val],
                y=["Revenue"],
                orientation="h",
                name="",
                marker_color=[DESIGN["color_brand"], "#5B8FFC", "#E5E5E5"],
                text=[f"Top 10: {top10_val:.1f} Bn EUR",
                      f"11–50: {mid40_val:.1f} Bn EUR",
                      f"Rest: {rest_val:.1f} Bn EUR"],
                textposition="inside",
                hovertemplate="%{text}<extra></extra>",
            ))
            apply_design(seg_fig, "Revenue by Segment")
            seg_fig.update_layout(
                barmode="stack",
                height=180,
                xaxis_title="Revenue (Bn EUR)",
                showlegend=False,
            )
            chart_wrap(seg_fig)

            top10_firms = df.nlargest(10, REV_COL)[[
                NAME_COL, REV_COL, "primary_cluster"
            ]].copy()
            top10_firms["Revenue (Bn EUR)"] = (top10_firms[REV_COL] / 1e6).round(3)
            top10_firms = top10_firms.rename(columns={
                NAME_COL: "Company",
                "primary_cluster": "Cluster",
            })[["Company", "Revenue (Bn EUR)", "Cluster"]]
            st.dataframe(top10_firms, use_container_width=True, hide_index=True)

# ────────────────────────────────────────────────────────────────────────────────
# TAB 3 – Growth Momentum
# ────────────────────────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown("""
    <div class="insight-card-accent" style="margin-bottom:20px">
        <strong>🚀 Growth Momentum:</strong>
        High-Growth firms: 7 → 36 (+414%). Gazelles: 3 → 11. Scaleups: 2 → 7.
    </div>""", unsafe_allow_html=True)

    w1, w2 = st.columns(2)

    with w1:
        fig = go.Figure()
        for gtype, color in STACKED_COLORS.items():
            counts = [df[f"{gtype} {y}"].sum() for y in YEARS if f"{gtype} {y}" in df.columns]
            valid_years = [y for y in YEARS if f"{gtype} {y}" in df.columns]
            if counts:
                fig.add_trace(go.Scatter(
                    x=valid_years,
                    y=counts,
                    name=gtype,
                    stackgroup="one",
                    line=dict(color=color),
                    fillcolor="rgba({},{},{},0.6)".format(int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)),
                    hovertemplate=f"<b>{gtype}</b> %{{x}}: %{{y:.0f}} firms<extra></extra>",
                ))
        apply_design(fig, "Growth Types 2020–2024 (stacked)")
        fig.update_layout(
            xaxis_title="Year",
            yaxis_title="No. of Firms",
            height=380,
        )
        chart_wrap(fig)

    with w2:
        bar_rows = []
        for gtype in GROWTH_TYPES:
            c20 = df[f"{gtype} 2020"].sum() if f"{gtype} 2020" in df.columns else 0
            c24 = df[f"{gtype} 2024"].sum() if f"{gtype} 2024" in df.columns else 0
            bar_rows.append({"Type": gtype, "Year": "2020", "Count": c20})
            bar_rows.append({"Type": gtype, "Year": "2024", "Count": c24})
        bar_df = pd.DataFrame(bar_rows)

        fig = px.bar(
            bar_df, x="Type", y="Count", color="Year",
            barmode="group",
            color_discrete_map={"2020": "#D0D0D0", "2024": DESIGN["color_brand"]},
        )
        for gtype in GROWTH_TYPES:
            c20 = df[f"{gtype} 2020"].sum() if f"{gtype} 2020" in df.columns else 0
            c24 = df[f"{gtype} 2024"].sum() if f"{gtype} 2024" in df.columns else 0
            if c20 > 0 and c24 > c20:
                pct = (c24 - c20) / c20 * 100
                fig.add_annotation(
                    x=gtype, y=c24,
                    text=f"+{pct:.0f}%",
                    showarrow=False,
                    yshift=10,
                    font=dict(size=10, color=DESIGN["color_brand"]),
                )
        apply_design(fig, "2020 vs 2024 by Growth Type")
        fig.update_layout(height=380, xaxis_tickangle=-20)
        chart_wrap(fig)

    divider()
    section("⭐ Consistent Stars – Classified as Scaleup Multiple Times")
    stars = df[df["scaleup_years_count"] >= 2].copy()
    if len(stars) > 0:
        stars["Revenue (M EUR)"] = (stars[REV_COL] / 1000).round(1)
        stars_tbl = stars[[
            NAME_COL, "primary_cluster", "Revenue (M EUR)", EMP_COL,
            "scaleup_years_count", "highgrowthfirm_years_count", "gazelle_years_count"
        ]].rename(columns={
            NAME_COL: "Company",
            "primary_cluster": "Cluster",
            EMP_COL: "Emp. 2024",
            "scaleup_years_count": "Scaleup Yrs",
            "highgrowthfirm_years_count": "HGF Yrs",
            "gazelle_years_count": "Gazelle Yrs",
        }).sort_values("Scaleup Yrs", ascending=False)
        st.dataframe(stars_tbl, use_container_width=True, hide_index=True)
    else:
        st.info("No consistent scaleup stars in current filter selection.")

# ────────────────────────────────────────────────────────────────────────────────
# TAB 4 – Cluster Profitability
# ────────────────────────────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown("""
    <div class="insight-card-accent" style="margin-bottom:20px">
        <strong>💹 Profitability:</strong> Construction (4.8%) and Tech &amp; ICT (3.9%) lead.
        Media &amp; Marketing (−3.3%) is structurally loss-making.
    </div>""", unsafe_allow_html=True)

    cluster_stats = (
        df[df["primary_cluster"] != "unknown"]
        .groupby("primary_cluster")
        .agg(
            median_rev   =(REV_COL,     lambda x: x.median() / 1000),
            median_margin=("profit_margin", "median"),
            count        =(NAME_COL,    "size"),
        )
        .reset_index()
        .dropna(subset=["median_rev", "median_margin"])
    )
    cluster_stats = cluster_stats[cluster_stats["median_rev"] > 0]

    if len(cluster_stats) >= 3:
        size_min, size_max = cluster_stats["count"].min(), cluster_stats["count"].max()
        if size_max > size_min:
            cluster_stats["bubble_size"] = 15 + (cluster_stats["count"] - size_min) / (size_max - size_min) * 45
        else:
            cluster_stats["bubble_size"] = 30

        fig = go.Figure()
        for _, row in cluster_stats.iterrows():
            fig.add_trace(go.Scatter(
                x=[row["median_rev"]],
                y=[row["median_margin"] * 100],
                mode="markers",
                marker=dict(
                    size=row["bubble_size"],
                    color=CLUSTER_COLORS.get(row["primary_cluster"], "#A0A0A0"),
                    line=dict(width=1, color="white"),
                    opacity=0.85,
                ),
                name=row["primary_cluster"],
                hovertemplate=(
                    f"<b>{row['primary_cluster']}</b><br>"
                    f"Median Revenue: {row['median_rev']:.1f} M EUR<br>"
                    f"Median Margin: {row['median_margin']*100:.1f}%<br>"
                    f"n={row['count']}<extra></extra>"
                ),
            ))

        fig.add_hline(y=0, line_color=DESIGN["color_error"],
                      line_dash="dash", line_width=1.5)
        for text, x_domain, y_domain in [
            ("⭐ Stars",           0.85, 0.90),
            ("📦 Volume",         0.85, 0.10),
            ("💎 Niche",          0.05, 0.90),
            ("⚠️ Under Pressure", 0.05, 0.10),
        ]:
            fig.add_annotation(
                xref="x domain", yref="y domain",
                x=x_domain, y=y_domain,
                text=text, showarrow=False,
                font=dict(size=11, color="#999999"),
            )
        apply_design(fig, "Cluster Profitability: Revenue vs. Margin")
        fig.update_xaxes(type="log", title="Median Revenue (M EUR, Log)")
        fig.update_yaxes(title="Median Profit Margin (%)")
        fig.update_layout(height=480, showlegend=True, legend_title_text="Cluster")
        chart_wrap(fig)

        divider()
        tbl = cluster_stats.copy()
        tbl["Avg Margin (%)"]   = (tbl["median_margin"] * 100).round(2)
        tbl["Median Rev (M)"]   = tbl["median_rev"].round(1)
        tbl = tbl.rename(columns={
            "primary_cluster": "Cluster",
            "count": "Companies",
        })[["Cluster", "Companies", "Avg Margin (%)", "Median Rev (M)"]].sort_values(
            "Avg Margin (%)", ascending=False
        )
        st.dataframe(tbl, use_container_width=True, hide_index=True)
    else:
        st.info("Too few cluster data for bubble chart.")

# ────────────────────────────────────────────────────────────────────────────────
# TAB 5 – Employment
# ────────────────────────────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown("""
    <div class="insight-card-accent" style="margin-bottom:20px">
        <strong>👷 Employment:</strong> Food &amp; Hospitality: +31% (post-COVID).
        Manufacturing: 0%. Retail: −1.1%.
    </div>""", unsafe_allow_html=True)

    b1, b2 = st.columns(2)

    with b1:
        growth_data = (
            df[df["primary_cluster"] != "unknown"]
            .groupby("primary_cluster")["emp_growth_2020_2024"]
            .agg(["median", "std"])
            .reset_index()
            .dropna(subset=["median"])
            .sort_values("median")
        )
        if len(growth_data) >= 3:
            colors = [
                DESIGN["color_success"] if m > 0 else DESIGN["color_error"]
                for m in growth_data["median"]
            ]
            fig = go.Figure(go.Bar(
                y=growth_data["primary_cluster"],
                x=growth_data["median"],
                orientation="h",
                marker_color=colors,
                error_x=dict(
                    type="data",
                    array=growth_data["std"].fillna(0).tolist(),
                    visible=True,
                    color="#D0D0D0",
                ),
                hovertemplate="<b>%{y}</b><br>Median Growth: %{x:.1f}%<extra></extra>",
            ))
            apply_design(fig, "Employment Growth 2020–2024 by Cluster (%)")
            fig.update_layout(
                xaxis_title="Median Growth (%)",
                yaxis_title="",
                height=400, showlegend=False,
            )
            chart_wrap(fig, coverage_col="emp_growth_2020_2024")
        else:
            st.info("Too few data for employment growth.")

    with b2:
        top6 = (
            df.groupby("primary_cluster")[EMP_COL]
            .sum()
            .nlargest(6)
            .index.tolist()
        )
        line_rows = []
        for cluster in top6:
            cdf = df[df["primary_cluster"] == cluster]
            for y in EMP_YEARS:
                col = f"Number of employees {y}"
                if col in cdf.columns:
                    line_rows.append({
                        "Cluster": cluster,
                        "Year": y,
                        "Employees": cdf[col].sum(),
                    })
        line_df = pd.DataFrame(line_rows)

        if len(line_df) > 0:
            fig = px.line(
                line_df, x="Year", y="Employees", color="Cluster",
                color_discrete_map=CLUSTER_COLORS,
                markers=True,
            )
            apply_design(fig, "Employment by Cluster 2017–2024 (Top 6)")
            fig.update_layout(
                xaxis_title="Year",
                yaxis_title="Employees (Total)",
                height=400,
            )
            chart_wrap(fig)
        else:
            st.info("No time-series data available.")

# ────────────────────────────────────────────────────────────────────────────────
# TAB 6 – Founding Waves
# ────────────────────────────────────────────────────────────────────────────────
with tabs[5]:
    st.markdown("""
    <div class="insight-card-accent" style="margin-bottom:20px">
        <strong>🏛️ Founding Waves:</strong> 2010s (247) and 2000s (215) are the strongest founding decades.
        53% of all firms founded after 2000.
    </div>""", unsafe_allow_html=True)

    decade_df = df.copy()
    decade_df = decade_df[decade_df["decade_founded"].notna() & (decade_df["decade_founded"] >= 1900)]

    decade_stats = (
        decade_df.groupby("decade_founded")
        .agg(
            count     =(NAME_COL, "size"),
            active    =("Status", lambda x: (x == "Active").sum()),
        )
        .reset_index()
    )
    decade_stats["survival_rate"] = decade_stats["active"] / decade_stats["count"]
    decade_stats["decade_label"]  = decade_stats["decade_founded"].astype(int).astype(str) + "s"

    g1, g2 = st.columns(2)

    with g1:
        if len(decade_stats) >= 3:
            fig = px.bar(
                decade_stats,
                x="decade_founded",
                y="count",
                color="survival_rate",
                color_continuous_scale=[[0, "#EB3424"], [0.5, "#ECB730"], [1, "#42C366"]],
                text=decade_stats.apply(
                    lambda r: f"{int(r['count'])}", axis=1
                ),
                hover_data={"survival_rate": ":.0%", "count": True},
            )
            fig.update_coloraxes(colorbar_title="Survival Rate")
            apply_design(fig, "Foundings by Decade (colour = survival rate)")
            fig.update_layout(
                xaxis_title="Decade",
                yaxis_title="No. of Firms",
                height=400,
            )
            chart_wrap(fig)
        else:
            st.info("Too few decade data.")

    with g2:
        heat_df = (
            df[
                (df["primary_cluster"] != "unknown") &
                df["decade_founded"].notna() &
                (df["decade_founded"] >= 1900)
            ]
            .groupby(["primary_cluster", "decade_founded"])
            .size()
            .reset_index(name="count")
        )
        if len(heat_df) > 0:
            heat_pivot = heat_df.pivot(
                index="primary_cluster", columns="decade_founded", values="count"
            ).fillna(0)
            fig = go.Figure(go.Heatmap(
                z=heat_pivot.values.astype(int),
                x=[str(int(c)) for c in heat_pivot.columns],
                y=heat_pivot.index.tolist(),
                colorscale=[[0, "#F7F7F7"], [1, DESIGN["color_brand"]]],
                hovertemplate="Cluster: %{y}<br>Decade: %{x}<br>Firms: %{z}<extra></extra>",
                texttemplate="%{z}",
                textfont=dict(size=10),
            ))
            apply_design(fig, "Founding Decade × Cluster")
            fig.update_layout(
                xaxis_title="Founding Decade",
                yaxis_title="",
                height=400,
            )
            chart_wrap(fig)
        else:
            st.info("No heatmap data available.")

# ────────────────────────────────────────────────────────────────────────────────
# TAB 7 – Gender Gap
# ────────────────────────────────────────────────────────────────────────────────
with tabs[6]:
    st.markdown("""
    <div class="insight-card-accent" style="margin-bottom:20px">
        <strong>👥 Gender Gap:</strong> 22.4% female decision makers (176 of 788).
        Large variation across sector and growth type.
    </div>""", unsafe_allow_html=True)

    gender_series = df["DM Gender"].dropna()
    gender_counts = gender_series.value_counts()
    total_dm  = gender_counts.sum()
    f_count   = gender_counts.get("F", 0)
    m_count   = gender_counts.get("M", 0)
    f_pct     = f_count / (f_count + m_count) * 100 if (f_count + m_count) > 0 else 0

    gd1, gd2 = st.columns([1, 2])

    with gd1:
        labels_g = [str(k) for k in gender_counts.index]
        color_map_g = {"M": "#2A6DFB", "F": "#9061FF"}
        colors_g = [color_map_g.get(l, "#D0D0D0") for l in labels_g]

        fig = go.Figure(go.Pie(
            labels=labels_g,
            values=gender_counts.values,
            hole=0.6,
            marker_colors=colors_g,
            textinfo="none",
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
        ))
        fig.add_annotation(
            text=f"{f_pct:.1f}%<br>F",
            x=0.5, y=0.5,
            font=dict(size=18, color="#1A1A1A", family="Inter"),
            showarrow=False,
        )
        apply_design(fig, "Gender Distribution")
        fig.update_layout(height=320, showlegend=True)
        chart_wrap(fig)

    with gd2:
        gbc = (
            df[df["primary_cluster"] != "unknown"]
            .groupby("primary_cluster")["DM Gender"]
            .value_counts()
            .unstack(fill_value=0)
        )
        if "F" in gbc.columns and "M" in gbc.columns:
            gbc["female_pct"] = gbc["F"] / (gbc["F"] + gbc["M"]) * 100
            gbc = gbc.reset_index().sort_values("female_pct", ascending=True)
            colors_bar = [
                DESIGN["color_success"] if p >= 30
                else DESIGN["color_warning"] if p >= 15
                else DESIGN["color_error"]
                for p in gbc["female_pct"]
            ]
            fig = go.Figure(go.Bar(
                y=gbc["primary_cluster"],
                x=gbc["female_pct"],
                orientation="h",
                marker_color=colors_bar,
                hovertemplate="<b>%{y}</b><br>Female: %{x:.1f}%<extra></extra>",
            ))
            fig.add_vline(x=30, line_dash="dash",
                          line_color="#D0D0D0", line_width=1.5,
                          annotation_text="30% Target",
                          annotation_position="top right",
                          annotation_font_size=10)
            apply_design(fig, "Female Leadership % by Cluster")
            fig.update_layout(
                xaxis_title="Female Leadership (%)",
                yaxis_title="",
                height=320, showlegend=False,
            )
            chart_wrap(fig)
        else:
            st.info("No gender data available.")

    divider()
    section("Age Distribution of Decision Makers by Gender")
    m_ages = df[df["DM Gender"] == "M"]["DM Age"].dropna()
    f_ages = df[df["DM Gender"] == "F"]["DM Age"].dropna()

    if len(m_ages) + len(f_ages) >= 10:
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=m_ages, name="Male",
            xbins=dict(size=5),
            marker_color="#2A6DFB",
            opacity=0.7,
        ))
        fig.add_trace(go.Histogram(
            x=f_ages, name="Female",
            xbins=dict(size=5),
            marker_color="#9061FF",
            opacity=0.7,
        ))
        fig.update_layout(barmode="overlay")
        apply_design(fig, "Age Distribution of Decision Makers (5-year bins)")
        fig.update_layout(
            xaxis_title="Age", yaxis_title="Count",
            height=320,
        )
        chart_wrap(fig, coverage_col="DM Age")
    else:
        st.info("Too few age data available.")

# ────────────────────────────────────────────────────────────────────────────────
# TAB 8 – Age & Performance
# ────────────────────────────────────────────────────────────────────────────────
with tabs[7]:
    st.markdown("""
    <div class="insight-card-accent" style="margin-bottom:20px">
        <strong>📅 Age &amp; Performance:</strong>
        Firm age correlates with revenue (r≈0.30) and profit (r≈0.38).
        Older firms tend to be more profitable.
    </div>""", unsafe_allow_html=True)

    ap1, ap2 = st.columns(2)

    with ap1:
        age_rev = df[[NAME_COL, "firm_age", REV_COL, "primary_cluster"]].dropna()
        age_rev = age_rev[age_rev[REV_COL] > 0]
        if len(age_rev) >= 10:
            age_rev = age_rev.copy()
            age_rev["Revenue (M EUR)"] = age_rev[REV_COL] / 1000

            fig = px.scatter(
                age_rev,
                x="firm_age",
                y="Revenue (M EUR)",
                color="primary_cluster",
                color_discrete_map=CLUSTER_COLORS,
                hover_name=NAME_COL,
                hover_data={"firm_age": True, "primary_cluster": True},
                log_y=True,
                opacity=0.7,
            )
            slope, intercept, r_val, _, _ = stats.linregress(
                age_rev["firm_age"],
                np.log10(age_rev["Revenue (M EUR)"].clip(lower=0.001)),
            )
            x_line = np.linspace(age_rev["firm_age"].min(), age_rev["firm_age"].max(), 100)
            y_line = 10 ** (intercept + slope * x_line)
            fig.add_trace(go.Scatter(
                x=x_line, y=y_line,
                mode="lines",
                line=dict(color=DESIGN["color_error"], dash="dash", width=2),
                name=f"Trend (r={r_val:.2f})",
            ))
            apply_design(fig, "Firm Age vs. Revenue")
            fig.update_layout(
                xaxis_title="Firm Age (Years)",
                yaxis_title="Revenue (M EUR, Log)",
                height=400,
            )
            chart_wrap(fig)
        else:
            st.info("Too few data points.")

    with ap2:
        age_prof = df[[NAME_COL, "firm_age", "profit_margin", "primary_cluster"]].dropna()
        if len(age_prof) >= 10:
            age_prof = age_prof.copy()
            age_prof["Profit Margin (%)"] = age_prof["profit_margin"] * 100

            fig = px.scatter(
                age_prof,
                x="firm_age",
                y="Profit Margin (%)",
                color="primary_cluster",
                color_discrete_map=CLUSTER_COLORS,
                hover_name=NAME_COL,
                opacity=0.7,
            )
            slope2, intercept2, r_val2, _, _ = stats.linregress(
                age_prof["firm_age"], age_prof["Profit Margin (%)"]
            )
            x_line2 = np.linspace(age_prof["firm_age"].min(), age_prof["firm_age"].max(), 100)
            y_line2 = intercept2 + slope2 * x_line2
            fig.add_trace(go.Scatter(
                x=x_line2, y=y_line2,
                mode="lines",
                line=dict(color=DESIGN["color_error"], dash="dash", width=2),
                name=f"Trend (r={r_val2:.2f})",
            ))
            fig.add_hline(y=0, line_color=DESIGN["color_error"],
                          line_dash="dot", line_width=1)
            apply_design(fig, "Firm Age vs. Profit Margin")
            fig.update_layout(
                xaxis_title="Firm Age (Years)",
                yaxis_title="Profit Margin (%)",
                height=400,
            )
            chart_wrap(fig)
        else:
            st.info("Too few data points.")

    divider()
    section("Correlation Matrix")
    corr_vars = {
        "Firm Age":         "firm_age",
        "Revenue (th EUR)": REV_COL,
        "Profit Margin":    "profit_margin",
        "Employees 2024":   EMP_COL,
    }
    corr_df = df[list(corr_vars.values())].dropna()
    if len(corr_df) >= 10:
        corr_df.columns = list(corr_vars.keys())
        corr_mat = corr_df.corr()
        fig = go.Figure(go.Heatmap(
            z=corr_mat.values.round(2),
            x=list(corr_vars.keys()),
            y=list(corr_vars.keys()),
            colorscale=[[0, "#EB3424"], [0.5, "#FFFFFF"], [1, "#2563EB"]],
            zmid=0,
            zmin=-1, zmax=1,
            text=corr_mat.values.round(2),
            texttemplate="%{text:.2f}",
            hovertemplate="%{y} × %{x}: %{z:.2f}<extra></extra>",
        ))
        apply_design(fig, "Pearson Correlation Matrix")
        fig.update_layout(height=360)
        chart_wrap(fig)
    else:
        st.info("Too few data for correlation matrix.")

# ────────────────────────────────────────────────────────────────────────────────
# TAB 9 – Star Finder
# ────────────────────────────────────────────────────────────────────────────────
with tabs[8]:
    st.markdown("""
    <div class="insight-card-accent" style="margin-bottom:20px">
        <strong>⭐ Star Finder:</strong> Only 13 firms were classified as a scaleup multiple times.
        Only 2 firms reached Superstar status.
    </div>""", unsafe_allow_html=True)

    STAR_THRESHOLD = 2
    stars_mask = df["scaleup_years_count"] >= STAR_THRESHOLD

    sf1, sf2 = st.columns(2)

    with sf1:
        np.random.seed(42)
        jitter = np.random.uniform(-0.15, 0.15, len(df))

        rev_vals = df[REV_COL].fillna(df[REV_COL].median())
        emp_vals = df[EMP_COL].fillna(df[EMP_COL].median())
        emp_min_s, emp_max_s = emp_vals.min(), emp_vals.max()
        if emp_max_s > emp_min_s:
            size_norm = 6 + (emp_vals - emp_min_s) / (emp_max_s - emp_min_s) * 14
        else:
            size_norm = pd.Series(10.0, index=df.index)

        non_stars = df[~stars_mask]
        stars_df  = df[stars_mask]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=non_stars["scaleup_years_count"] + jitter[:len(non_stars)],
            y=(non_stars[REV_COL] / 1000).clip(lower=0.001),
            mode="markers",
            marker=dict(color="#D0D0D0", size=7, opacity=0.5),
            name="Other",
            hovertext=non_stars[NAME_COL].fillna("–"),
            hovertemplate="<b>%{hovertext}</b><br>Scaleup Yrs: %{x:.0f}<br>Revenue: %{y:.1f} M EUR<extra></extra>",
        ))
        if len(stars_df) > 0:
            fig.add_trace(go.Scatter(
                x=stars_df["scaleup_years_count"] + jitter[:len(stars_df)],
                y=(stars_df[REV_COL] / 1000).clip(lower=0.001),
                mode="markers",
                marker=dict(
                    color=DESIGN["color_brand"],
                    symbol="star",
                    size=16,
                    line=dict(width=1, color="white"),
                ),
                name=f"Stars (≥{STAR_THRESHOLD} scaleup yrs)",
                hovertext=stars_df[NAME_COL].fillna("–"),
                hovertemplate="<b>%{hovertext}</b><br>Scaleup Yrs: %{x:.0f}<br>Revenue: %{y:.1f} M EUR<extra></extra>",
            ))
        fig.update_yaxes(type="log")
        apply_design(fig, "Star Finder – Scaleup Years vs. Revenue")
        fig.update_layout(
            xaxis_title="Scaleup Years (+ jitter)",
            yaxis_title="Revenue (M EUR, Log)",
            height=420,
        )
        chart_wrap(fig)

    with sf2:
        star_names = stars_df[NAME_COL].dropna().tolist() if len(stars_df) > 0 else []
        if star_names:
            sel_firm = st.selectbox("Select firm for radar chart", star_names, key="star_sel")
            firm_row = df[df[NAME_COL] == sel_firm].iloc[0]
            firm_cluster = firm_row["primary_cluster"]
            cluster_firms = df[df["primary_cluster"] == firm_cluster]

            def prank(series, val):
                s = series.dropna()
                return float((s < val).mean() * 100) if len(s) > 0 else 50.0

            def safe_get(row, col):
                v = row.get(col, 0)
                return 0 if pd.isna(v) else float(v)

            rev_rank   = prank(df[REV_COL], safe_get(firm_row, REV_COL))
            emp_rank   = prank(df[EMP_COL], safe_get(firm_row, EMP_COL))
            hgf_score  = min(100.0, safe_get(firm_row, "highgrowthfirm_years_count") / 5 * 100)
            sc_score   = min(100.0, safe_get(firm_row, "scaleup_years_count") / 5 * 100)
            mar_rank   = prank(df["profit_margin"], safe_get(firm_row, "profit_margin"))

            avg_rev_rank  = prank(df[REV_COL], cluster_firms[REV_COL].mean())
            avg_emp_rank  = prank(df[EMP_COL], cluster_firms[EMP_COL].mean())
            avg_hgf_score = min(100.0, cluster_firms["highgrowthfirm_years_count"].mean() / 5 * 100)
            avg_sc_score  = min(100.0, cluster_firms["scaleup_years_count"].mean() / 5 * 100)
            avg_mar_rank  = prank(df["profit_margin"], cluster_firms["profit_margin"].mean())

            cats   = ["Revenue Rank", "Emp. Rank", "HGF Yrs", "Scaleup Yrs", "Profit Rank"]
            vals_f = [rev_rank, emp_rank, hgf_score, sc_score, mar_rank]
            vals_c = [avg_rev_rank, avg_emp_rank, avg_hgf_score, avg_sc_score, avg_mar_rank]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=vals_f + [vals_f[0]],
                theta=cats + [cats[0]],
                fill="toself",
                fillcolor="rgba(37,99,235,0.15)",
                line=dict(color=DESIGN["color_brand"], width=2),
                name=sel_firm[:30],
            ))
            fig.add_trace(go.Scatterpolar(
                r=vals_c + [vals_c[0]],
                theta=cats + [cats[0]],
                fill="toself",
                fillcolor="rgba(0,0,0,0)",
                line=dict(color="#D0D0D0", dash="dash", width=1.5),
                name=f"Avg {firm_cluster}",
            ))
            apply_design(fig, f"Performance: {sel_firm[:25]}…")
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                height=420,
            )
            chart_wrap(fig)
        else:
            st.info("No star firms in current filter selection.")

    divider()
    section("⭐ Star Firms Overview")
    if len(stars_df) > 0:
        star_tbl = stars_df[[
            NAME_COL, "primary_cluster", REV_COL, EMP_COL,
            "scaleup_years_count", "highgrowthfirm_years_count", "gazelle_years_count"
        ]].copy()
        star_tbl["Revenue (M EUR)"] = (star_tbl[REV_COL] / 1000).round(1)
        star_tbl = star_tbl.rename(columns={
            NAME_COL: "Company",
            "primary_cluster": "Cluster",
            EMP_COL: "Emp. 2024",
            "scaleup_years_count": "Scaleup Yrs",
            "highgrowthfirm_years_count": "HGF Yrs",
            "gazelle_years_count": "Gazelle Yrs",
        })[["Company", "Cluster", "Revenue (M EUR)", "Emp. 2024",
             "Scaleup Yrs", "HGF Yrs", "Gazelle Yrs"]].sort_values("Scaleup Yrs", ascending=False)
        st.dataframe(star_tbl, use_container_width=True, hide_index=True)
    else:
        st.info("No star firms in current filter selection.")
