import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from components.filters import render_page_filter_banner
from components.charts import (
    CLUSTER_COLORS, CLUSTER_LABELS, PLOTLY_TEMPLATE, PLOTLY_LAYOUT,
    apply_design, data_coverage_note, DESIGN, format_kpi,
)

df = st.session_state["filtered_df"]
render_page_filter_banner(df)

REV_COL = "Revenue th EUR last avail. year"
EMP_COL = "Number of employees 2024"
NAME_COL = "Company name (Latin alphabet)"

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div class="page-title">🗂️ Cluster Analysis</div>
    <div class="page-subtitle">Industry segmentation of Essen companies</div>
</div>""", unsafe_allow_html=True)

# ── KPI Row ───────────────────────────────────────────────────────────────────
valid_clusters = df[~df["primary_cluster"].isin(["unknown", "other"])]
n_clusters     = valid_clusters["primary_cluster"].nunique()
cluster_sizes  = valid_clusters["primary_cluster"].value_counts()
largest_raw    = cluster_sizes.idxmax() if len(cluster_sizes) > 0 else "–"
largest_name   = CLUSTER_LABELS.get(largest_raw, largest_raw)
largest_n      = cluster_sizes.max() if len(cluster_sizes) > 0 else 0
unknown_n      = (df["primary_cluster"] == "unknown").sum()
unknown_pct    = unknown_n / len(df) * 100 if len(df) > 0 else 0
avg_rev        = (df[REV_COL].mean() / 1000) if df[REV_COL].notna().any() else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Clusters (excl. unknown)", f"{n_clusters}")
k2.metric("Largest Cluster", f"{largest_name}", delta=f"{largest_n} companies")
k3.metric("Share unknown",   f"{unknown_pct:.1f}%  ({unknown_n})",
          delta="⚠ > 20%" if unknown_pct > 20 else None,
          delta_color="inverse" if unknown_pct > 20 else "normal")
k4.metric("Avg Revenue", format_kpi(avg_rev * 1e6, prefix="€"))

st.markdown("<hr style='border-color:#E5E5E5;margin:24px 0'>", unsafe_allow_html=True)

# ── Treemap ───────────────────────────────────────────────────────────────────
cluster_agg = (
    df.groupby("primary_cluster")
    .agg(
        count       =(NAME_COL, "size"),
        avg_rev_mio =(REV_COL,  lambda x: x.mean() / 1000),
        avg_emp     =(EMP_COL,  "mean"),
    )
    .reset_index()
)
cluster_agg["label"] = cluster_agg["primary_cluster"].map(CLUSTER_LABELS).fillna(
    cluster_agg["primary_cluster"]
)

if len(cluster_agg) >= 2:
    fig_tree = px.treemap(
        cluster_agg,
        path=[px.Constant("Essen"), "label"],
        values="count",
        color="avg_rev_mio",
        color_continuous_scale=[[0, "#EFF6FF"], [1, "#1D4ED8"]],
        custom_data=["avg_rev_mio", "avg_emp", "count"],
    )
    fig_tree.update_traces(
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Companies: %{customdata[2]}<br>"
            "Avg Revenue: %{customdata[0]:.1f} M EUR<br>"
            "Avg Employees: %{customdata[1]:.0f}<extra></extra>"
        )
    )
    fig_tree.update_coloraxes(colorbar_title="Avg Rev<br>(M EUR)")
    apply_design(fig_tree, "Cluster Distribution by Company Count (colour = Avg Revenue)")
    fig_tree.update_layout(height=420, margin=dict(l=0, r=0, t=40, b=0))
    with st.container():
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig_tree, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("Not enough cluster data for treemap.")

st.markdown("<hr style='border-color:#E5E5E5;margin:24px 0'>", unsafe_allow_html=True)

# ── 2 Columns: Grouped Bar + Radar ───────────────────────────────────────────
col_bar, col_radar = st.columns(2)

with col_bar:
    cluster_rev = (
        df[~df["primary_cluster"].isin(["unknown"])]
        .groupby("primary_cluster")
        .agg(
            avg_rev=(REV_COL, lambda x: x.mean() / 1000),
            avg_emp=(EMP_COL, "mean"),
        )
        .dropna(subset=["avg_rev"])
        .sort_values("avg_rev", ascending=True)
        .reset_index()
    )

    if len(cluster_rev) >= 2:
        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
        fig_dual.add_trace(
            go.Bar(
                x=cluster_rev["primary_cluster"],
                y=cluster_rev["avg_rev"],
                name="Avg Revenue (M EUR)",
                marker_color=DESIGN["color_brand"],
                opacity=0.9,
            ),
            secondary_y=False,
        )
        fig_dual.add_trace(
            go.Scatter(
                x=cluster_rev["primary_cluster"],
                y=cluster_rev["avg_emp"],
                name="Avg Employees 2024",
                mode="lines+markers",
                line=dict(color=DESIGN["color_warning"], width=2),
                marker=dict(size=7),
            ),
            secondary_y=True,
        )
        apply_design(fig_dual, "Avg Revenue & Employees by Cluster")
        fig_dual.update_yaxes(title_text="Avg Revenue (M EUR)", secondary_y=False,
                               gridcolor="#E5E5E5", linecolor="#D0D0D0", tickfont_color="#666666")
        fig_dual.update_yaxes(title_text="Avg Employees 2024",  secondary_y=True,
                               gridcolor=None,     linecolor="#D0D0D0", tickfont_color="#666666")
        fig_dual.update_xaxes(tickangle=-30)
        fig_dual.update_layout(height=420, legend=dict(orientation="h", y=-0.25))
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig_dual, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Not enough data for cluster comparison.")

with col_radar:
    radar_clusters = df[~df["primary_cluster"].isin(["unknown", "other"])]["primary_cluster"].unique()
    radar_cluster_list = sorted(radar_clusters.tolist())

    metrics_raw = {}
    for c in radar_cluster_list:
        cdf = df[df["primary_cluster"] == c]
        n   = len(cdf)
        metrics_raw[c] = {
            "Revenue":      cdf[REV_COL].mean() / 1000 if cdf[REV_COL].notna().any() else 0,
            "Employees":    cdf[EMP_COL].mean() if cdf[EMP_COL].notna().any() else 0,
            "Profit Margin":cdf["profit_margin"].median() * 100 if cdf["profit_margin"].notna().any() else 0,
            "% Scaleup":    cdf["Scaleup 2024"].eq(1).sum() / n * 100 if "Scaleup 2024" in cdf.columns else 0,
            "% HighGrowth": cdf["HighGrowthFirm 2024"].eq(1).sum() / n * 100 if "HighGrowthFirm 2024" in cdf.columns else 0,
            "Emp Growth":   cdf["emp_growth_2020_2024"].mean() if cdf["emp_growth_2020_2024"].notna().any() else 0,
        }

    metrics_df = pd.DataFrame(metrics_raw).T

    def minmax_norm(s):
        mn, mx = s.min(), s.max()
        if mx == mn:
            return pd.Series(50.0, index=s.index)
        return (s - mn) / (mx - mn) * 100

    norm_df  = metrics_df.apply(minmax_norm)
    avg_vals = norm_df.mean().tolist()
    cats     = norm_df.columns.tolist()

    cluster_labels_list = [CLUSTER_LABELS.get(c, c) for c in radar_cluster_list]
    sel_cluster_label = st.selectbox("Cluster for Radar", cluster_labels_list, key="cluster_radar_sel")
    sel_cluster = radar_cluster_list[cluster_labels_list.index(sel_cluster_label)] if sel_cluster_label in cluster_labels_list else None

    if sel_cluster and sel_cluster in norm_df.index:
        sel_vals = norm_df.loc[sel_cluster].tolist()

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=sel_vals + [sel_vals[0]],
            theta=cats + [cats[0]],
            fill="toself",
            fillcolor="rgba(37,99,235,0.12)",
            line=dict(color=DESIGN["color_brand"], width=2),
            name=sel_cluster_label,
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=avg_vals + [avg_vals[0]],
            theta=cats + [cats[0]],
            fill="toself",
            fillcolor="rgba(0,0,0,0)",
            line=dict(color="#D0D0D0", dash="dash", width=1.5),
            name="Ø All clusters",
        ))
        apply_design(fig_radar, f"Cluster Profile: {sel_cluster_label}")
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            height=420,
        )
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig_radar, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No data for radar chart.")

st.markdown("<hr style='border-color:#E5E5E5;margin:24px 0'>", unsafe_allow_html=True)

# ── Cluster Detail ────────────────────────────────────────────────────────────
with st.expander("🔍 Cluster Profile & Detail Analysis", expanded=False):
    all_clusters_detail = sorted(df["primary_cluster"].unique().tolist())
    detail_labels = [CLUSTER_LABELS.get(c, c) for c in all_clusters_detail]
    sel_detail_label = st.selectbox("Show cluster detail", detail_labels, key="cluster_detail_sel")
    sel_detail = all_clusters_detail[detail_labels.index(sel_detail_label)] if sel_detail_label in detail_labels else all_clusters_detail[0]

    cluster_firms = df[df["primary_cluster"] == sel_detail]
    n_f      = len(cluster_firms)
    avg_rev_d = cluster_firms[REV_COL].mean() / 1000 if cluster_firms[REV_COL].notna().any() else 0
    med_rev_d = cluster_firms[REV_COL].median() / 1000 if cluster_firms[REV_COL].notna().any() else 0

    if n_f > 0:
        top3_nace = cluster_firms["NACE Rev. 2 main section"].value_counts().head(3)
        nace_str  = " · ".join(top3_nace.index.tolist()[:3]) if len(top3_nace) > 0 else "–"

        st.markdown(
            f"""<div class="insight-card-accent" style="margin-bottom:16px">
            <strong>📋 {sel_detail_label}</strong> &nbsp;·&nbsp; {n_f} companies
            &nbsp;·&nbsp; Avg Revenue: {avg_rev_d:.1f} M EUR
            &nbsp;·&nbsp; Median Revenue: {med_rev_d:.1f} M EUR<br>
            <span style='font-size:12px;color:#4B5563'>Top NACE: {nace_str}</span>
            </div>""",
            unsafe_allow_html=True,
        )

        det1, det2 = st.columns(2)

        with det1:
            growth_types_h = ["Scaleup","Gazelle","HighGrowthFirm","VeryHighGrowthFirm","Scaler","Superstar"]
            years_h        = [2020, 2021, 2022, 2023, 2024]
            z_vals = []
            for gtype in growth_types_h:
                row = []
                for yr in years_h:
                    col_name = f"{gtype} {yr}"
                    row.append(int(cluster_firms[col_name].sum()) if col_name in cluster_firms.columns else 0)
                z_vals.append(row)

            fig_heat = go.Figure(go.Heatmap(
                z=z_vals,
                x=[str(y) for y in years_h],
                y=growth_types_h,
                colorscale=[[0, "#F7F7F7"], [1, "#2563EB"]],
                texttemplate="%{z}",
                textfont=dict(size=11),
                hovertemplate="%{y} %{x}: %{z} companies<extra></extra>",
            ))
            apply_design(fig_heat, "Growth Classifications 2020–2024")
            fig_heat.update_layout(height=280, margin=dict(l=0, r=0, t=40, b=0))
            with st.container():
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.plotly_chart(fig_heat, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

        with det2:
            nace_data = cluster_firms["NACE Rev. 2 main section"].value_counts().head(8)
            if len(nace_data) > 0:
                accent_colors = [
                    "#2A6DFB","#9061FF","#42C366","#ECB730","#EB3424",
                    "#5B8FFC","#B08AFF","#7DD99A",
                ]
                fig_pie = px.pie(
                    values=nace_data.values,
                    names=nace_data.index.str[:30],
                    color_discrete_sequence=accent_colors,
                )
                fig_pie.update_traces(textinfo="none",
                    hovertemplate="<b>%{label}</b><br>%{value} companies (%{percent})<extra></extra>")
                apply_design(fig_pie, "NACE Distribution in Cluster")
                fig_pie.update_layout(
                    height=280,
                    legend=dict(font=dict(size=10), orientation="v"),
                    margin=dict(l=0, r=0, t=40, b=0),
                )
                with st.container():
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    st.plotly_chart(fig_pie, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No NACE data available.")

        st.markdown(
            f"<div style='font-size:14px;font-weight:600;color:#1A1A1A;margin:16px 0 8px;'>"
            f"Top 10 Companies in {sel_detail_label}</div>",
            unsafe_allow_html=True,
        )
        top10_c = cluster_firms.nlargest(10, REV_COL) if cluster_firms[REV_COL].notna().any() else cluster_firms.head(10)
        top10_c = top10_c[[NAME_COL, REV_COL, EMP_COL, "Status"]].copy()
        top10_c["Revenue (M EUR)"] = (top10_c[REV_COL] / 1000).round(1)
        top10_c["Status"] = top10_c["Status"].apply(
            lambda v: "✅ Active" if v == "Active" else f"⚪ {v}"
        )
        top10_c = top10_c.rename(columns={NAME_COL: "Company", EMP_COL: "Emp. 2024"})[
            ["Company", "Revenue (M EUR)", "Emp. 2024", "Status"]
        ]
        st.dataframe(top10_c, use_container_width=True, hide_index=True)
    else:
        st.info("No companies in selected cluster.")

# ── Multi-Cluster Comparison ──────────────────────────────────────────────────
with st.expander("⚖️ Multi-Cluster Comparison", expanded=False):
    all_named = sorted(
        df[~df["primary_cluster"].isin(["unknown", "other"])]["primary_cluster"].unique().tolist()
    )
    all_named_labels = [CLUSTER_LABELS.get(c, c) for c in all_named]
    sel_multi_labels = st.multiselect(
        "Select 2–4 clusters",
        all_named_labels,
        default=all_named_labels[:3] if len(all_named_labels) >= 3 else all_named_labels,
        max_selections=4,
        key="multi_cluster_sel",
    )
    label_to_raw = {CLUSTER_LABELS.get(c, c): c for c in all_named}
    sel_multi = [label_to_raw.get(l, l) for l in sel_multi_labels]

    if len(sel_multi) >= 2:
        multi_df = df[df["primary_cluster"].isin(sel_multi)]
        multi_agg = (
            multi_df.groupby("primary_cluster")
            .agg(
                avg_rev  =(REV_COL, lambda x: x.mean() / 1000),
                avg_emp  =(EMP_COL, "mean"),
                n        =(NAME_COL, "size"),
            )
            .reset_index()
        )
        for gt, col_name in [("Scaleup", "Scaleup 2024"), ("HighGrowthFirm", "HighGrowthFirm 2024")]:
            if col_name in multi_df.columns:
                rates = (
                    multi_df.groupby("primary_cluster")
                    .apply(lambda g: g[col_name].eq(1).sum() / len(g) * 100)
                    .reset_index(name=f"pct_{gt}")
                )
                multi_agg = multi_agg.merge(rates, on="primary_cluster", how="left")

        multi_agg["label"] = multi_agg["primary_cluster"].map(CLUSTER_LABELS).fillna(
            multi_agg["primary_cluster"]
        )

        metric_cols = [
            ("avg_rev",      "Avg Revenue (M EUR)"),
            ("avg_emp",      "Avg Employees 2024"),
            ("pct_Scaleup",  "% Scaleups 2024"),
            ("pct_HighGrowthFirm", "% HighGrowth 2024"),
        ]
        m_cols = st.columns(4)
        for (col_key, col_label), mc in zip(metric_cols, m_cols):
            with mc:
                if col_key in multi_agg.columns:
                    fig_m = px.bar(
                        multi_agg,
                        x="label", y=col_key,
                        color="primary_cluster",
                        color_discrete_map=CLUSTER_COLORS,
                    )
                    apply_design(fig_m, col_label)
                    fig_m.update_layout(
                        height=280, showlegend=False,
                        xaxis_title="", yaxis_title=col_label,
                        xaxis_tickangle=-20,
                    )
                    with st.container():
                        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                        st.plotly_chart(fig_m, use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.caption(f"{col_label}: No data")
    else:
        st.info("Please select at least 2 clusters.")
