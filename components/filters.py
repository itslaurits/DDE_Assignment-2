import streamlit as st
import pandas as pd
from components.charts import CLUSTER_LABELS


def render_global_filters(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.markdown(
            """
            <div style="
                font-family: Inter, sans-serif;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.08em;
                color: #999999;
                text-transform: uppercase;
                margin-bottom: 12px;
            ">Filters</div>
            """,
            unsafe_allow_html=True
        )

        all_clusters_raw = sorted(df['primary_cluster'].dropna().unique())
        cluster_display  = {c: CLUSTER_LABELS.get(c, c.replace("_", " ").title()) for c in all_clusters_raw}
        display_to_raw   = {v: k for k, v in cluster_display.items()}

        selected_labels = st.multiselect(
            "Cluster / Industry",
            options=list(cluster_display.values()),
            default=[cluster_display[c] for c in all_clusters_raw if c != 'unknown'],
            key="filter_clusters"
        )
        selected_clusters = [display_to_raw.get(l, l) for l in selected_labels]

        status_options = sorted(df['Status'].dropna().unique())
        selected_status = st.multiselect(
            "Company Status",
            options=status_options,
            default=["Active"],
            key="filter_status"
        )

        min_dec = int(df['decade_founded'].dropna().min())
        max_dec = int(df['decade_founded'].dropna().max())
        decade_range = st.slider(
            "Founding Decade",
            min_value=min_dec, max_value=max_dec,
            value=(1970, max_dec), step=10,
            key="filter_decade"
        )

        nace_options = sorted(df['NACE Rev. 2 main section'].dropna().unique())
        selected_nace = st.multiselect(
            "NACE Sector",
            options=nace_options,
            default=[],
            placeholder="All sectors",
            key="filter_nace"
        )

        growth_map = {
            'Scaleup':          'Scaleup 2024',
            'Gazelle':          'Gazelle 2024',
            'High Growth':      'HighGrowthFirm 2024',
            'Very High Growth': 'VeryHighGrowthFirm 2024',
            'Superstar':        'Superstar 2024',
        }
        selected_growth = st.multiselect(
            "Growth Type 2024",
            options=list(growth_map.keys()),
            default=[],
            placeholder="All types",
            key="filter_growth"
        )

        st.divider()
        if st.button("↺  Reset Filters", use_container_width=True):
            for k in ["filter_clusters", "filter_status", "filter_decade",
                      "filter_nace", "filter_growth"]:
                st.session_state.pop(k, None)
            st.rerun()

    fdf = df.copy()
    if selected_clusters:
        fdf = fdf[fdf['primary_cluster'].isin(selected_clusters)]
    if selected_status:
        fdf = fdf[fdf['Status'].isin(selected_status)]
    fdf = fdf[
        (fdf['decade_founded'] >= decade_range[0]) &
        (fdf['decade_founded'] <= decade_range[1])
    ]
    if selected_nace:
        fdf = fdf[fdf['NACE Rev. 2 main section'].isin(selected_nace)]
    if selected_growth:
        mask = pd.Series(False, index=fdf.index)
        for g in selected_growth:
            col = growth_map[g]
            if col in fdf.columns:
                mask |= (fdf[col] == 1)
        fdf = fdf[mask]

    st.session_state["filtered_df"] = fdf

    n = len(fdf)
    total = len(df)
    badge_color = "#2563EB" if n < total else "#42C366"
    badge_text  = f"{n} / {total} Companies"
    st.sidebar.markdown(
        f"""<div style="
            background:{badge_color}14;
            border:1px solid {badge_color}40;
            border-radius:6px;
            padding:6px 12px;
            font-size:13px;
            font-weight:600;
            color:{badge_color};
            text-align:center;
            font-family:Inter,sans-serif;
        ">📊 {badge_text}</div>""",
        unsafe_allow_html=True
    )
    return fdf


def render_page_filter_banner(filtered_df, total=879):
    n = len(filtered_df)
    if n >= total:
        return
    parts = []
    clusters = st.session_state.get("filter_clusters", [])
    if clusters and len(clusters) < 14:
        preview = ", ".join(clusters[:2]) + ("…" if len(clusters) > 2 else "")
        parts.append(f"Cluster: {preview}")
    growth = st.session_state.get("filter_growth", [])
    if growth:
        parts.append(f"Growth: {', '.join(growth)}")
    label = " · ".join(parts) if parts else "Filters active"
    st.markdown(
        f"""<div style="
            background:#EFF6FF;
            border-left:3px solid #2563EB;
            border-radius:0 6px 6px 0;
            padding:8px 16px;
            margin-bottom:16px;
            font-family:Inter,sans-serif;
            font-size:13px;
            color:#1D4ED8;
        ">🔍 <strong>{label}</strong> → <strong>{n}</strong> companies</div>""",
        unsafe_allow_html=True
    )
