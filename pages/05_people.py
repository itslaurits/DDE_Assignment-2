import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from components.filters import render_page_filter_banner
from components.charts import (
    CLUSTER_COLORS, PLOTLY_TEMPLATE, PLOTLY_LAYOUT,
    apply_design, data_coverage_note, DESIGN,
)

df = st.session_state["filtered_df"]
render_page_filter_banner(df)

REV_COL  = "Revenue th EUR last avail. year"
EMP_COL  = "Number of employees 2024"
NAME_COL = "Company name (Latin alphabet)"
COMP_COL = "DM Total compensation USD"
AGE_COL  = "DM Age"

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div class="page-title">👥 People &amp; Leadership</div>
    <div class="page-subtitle">Decision Makers &amp; Executives · Bureau van Dijk</div>
</div>""", unsafe_allow_html=True)
st.caption("People = board members / managing directors per company")

# ── Local Filters ─────────────────────────────────────────────────────────────
with st.expander("⚙️ People Filters", expanded=False):
    pf1, pf2, pf3 = st.columns(3)
    with pf1:
        gender_radio = st.radio(
            "Gender", ["All", "Male only", "Female only"],
            horizontal=True, key="ppl_gender"
        )
    with pf2:
        age_min = int(df[AGE_COL].dropna().min()) if df[AGE_COL].notna().any() else 20
        age_max = int(df[AGE_COL].dropna().max()) if df[AGE_COL].notna().any() else 80
        age_range = st.slider(
            "Age (DM Age)", min_value=max(20, age_min), max_value=min(90, age_max),
            value=(max(20, age_min), min(80, age_max)), key="ppl_age"
        )
    with pf3:
        only_current    = st.toggle("Current DMs only", value=False, key="ppl_current")
        only_with_comp  = st.toggle("With compensation data only", value=False, key="ppl_comp")

    top_nat = df["DM Nationality"].dropna().str.split(";").explode().str.strip().value_counts().head(10).index.tolist()
    sel_nat = st.multiselect(
        "Nationality (Top 10)", top_nat if top_nat else ["Germany"],
        default=[], placeholder="All", key="ppl_nat"
    )

# Apply local filters
pdf = df.copy()
if gender_radio == "Male only":
    pdf = pdf[pdf["DM Gender"] == "M"]
elif gender_radio == "Female only":
    pdf = pdf[pdf["DM Gender"] == "F"]
if pdf[AGE_COL].notna().any():
    pdf = pdf[(pdf[AGE_COL] >= age_range[0]) | pdf[AGE_COL].isna()]
    pdf = pdf[(pdf[AGE_COL] <= age_range[1]) | pdf[AGE_COL].isna()]
if only_current:
    pdf = pdf[pdf["DM Current or former"] == "Current"]
if only_with_comp:
    pdf = pdf[pdf[COMP_COL].notna()]
if sel_nat:
    pdf = pdf[pdf["DM Nationality"].str.contains("|".join(sel_nat), na=False, case=False)]

# ── KPI Row ───────────────────────────────────────────────────────────────────
dm_known  = pdf["DM Full name"].notna().sum()
avg_age   = pdf[AGE_COL].mean()
f_n       = pdf["DM Gender"].eq("F").sum()
m_n       = pdf["DM Gender"].eq("M").sum()
female_rt = f"{f_n / (f_n + m_n) * 100:.1f}%" if (f_n + m_n) > 0 else "–"
comp_n    = pdf[COMP_COL].notna().sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Known DMs",        f"{dm_known:,}")
k2.metric("Avg Age",          f"{avg_age:.1f} yrs" if pd.notna(avg_age) else "–")
k3.metric("Female Rate",      female_rt, delta=f"of {f_n + m_n} DMs")
k4.metric("Avg Compensation", "n/a", delta=f"{comp_n} firms with data" if comp_n > 0 else "No data")

st.markdown("<hr style='border-color:#E5E5E5;margin:24px 0'>", unsafe_allow_html=True)

# ── Demographics ──────────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-size:15px;font-weight:600;color:#1A1A1A;margin-bottom:16px;'>"
    "Demographics</div>", unsafe_allow_html=True
)
d1, d2, d3 = st.columns(3)

# Gender Donut
with d1:
    gc = pdf["DM Gender"].value_counts()
    total_dm = gc.sum()
    f_pct  = gc.get("F", 0) / (gc.get("F", 0) + gc.get("M", 0)) * 100 if (gc.get("F", 0) + gc.get("M", 0)) > 0 else 0
    color_map_g = {"M": "#2A6DFB", "F": "#9061FF"}
    g_colors = [color_map_g.get(str(l), "#D0D0D0") for l in gc.index]

    fig = go.Figure(go.Pie(
        labels=[str(l) for l in gc.index],
        values=gc.values,
        hole=0.6,
        marker_colors=g_colors,
        textinfo="none",
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    ))
    fig.add_annotation(
        text=f"{f_pct:.1f}%<br><span style='font-size:12px'>F</span>",
        x=0.5, y=0.5,
        font=dict(size=18, color="#1A1A1A", family="Inter"),
        showarrow=False,
    )
    apply_design(fig, "Gender Distribution")
    fig.update_layout(height=300, showlegend=True, margin=dict(l=0, r=0, t=40, b=0))
    with st.container():
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Age Histogram
with d2:
    age_data = pdf[AGE_COL].dropna()
    if len(age_data) >= 5:
        fig = go.Figure(go.Histogram(
            x=age_data, nbinsx=14,
            marker_color=DESIGN["color_brand"], opacity=0.85,
            hovertemplate="Age %{x}: %{y} DMs<extra></extra>",
        ))
        mean_age = age_data.mean()
        fig.add_vline(x=mean_age, line_color=DESIGN["color_warning"],
                      line_dash="dash", line_width=2,
                      annotation_text=f"Avg {mean_age:.0f}",
                      annotation_position="top right",
                      annotation_font_size=11)
        apply_design(fig, "Age Distribution of Decision Makers")
        fig.update_layout(
            xaxis_title="Age", yaxis_title="Count",
            height=300, showlegend=False,
        )
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(data_coverage_note(pdf, AGE_COL))
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Too few age data available.")

# Top 10 Nationalities
with d3:
    nat_raw = pdf["DM Nationality"].dropna().str.split(";").explode().str.strip()
    nat_counts = nat_raw.value_counts().head(10).reset_index()
    nat_counts.columns = ["Nationality", "Count"]
    if len(nat_counts) > 0:
        n_blues = len(nat_counts)
        blues = [
            f"rgba(37,99,235,{max(0.35, 1 - i * 0.06):.2f})"
            for i in range(n_blues)
        ]
        fig = px.bar(
            nat_counts, x="Count", y="Nationality", orientation="h",
            color_discrete_sequence=[DESIGN["color_brand"]],
        )
        fig.update_traces(marker_color=blues)
        apply_design(fig, "Top 10 Nationalities")
        fig.update_layout(
            yaxis_title="", xaxis_title="No. of DMs",
            height=300, showlegend=False,
        )
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Data available for {pdf['DM Nationality'].notna().sum()} of {len(pdf)} DMs")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No nationality data available.")

st.markdown("<hr style='border-color:#E5E5E5;margin:24px 0'>", unsafe_allow_html=True)

# ── Positions ─────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-size:15px;font-weight:600;color:#1A1A1A;margin-bottom:16px;'>"
    "Positions</div>", unsafe_allow_html=True
)
p1, p2 = st.columns(2)

with p1:
    job_counts = pdf["DM Job title"].value_counts().head(15).reset_index()
    job_counts.columns = ["Position", "Count"]
    job_counts["Position"] = job_counts["Position"].str[:40]
    if len(job_counts) > 0:
        n_j = len(job_counts)
        job_colors = [
            f"rgba(37,99,235,{max(0.3, 1 - i / max(n_j - 1, 1) * 0.65):.2f})"
            for i in range(n_j)
        ]
        fig = go.Figure(go.Bar(
            y=job_counts["Position"],
            x=job_counts["Count"],
            orientation="h",
            marker_color=job_colors[::-1],
            hovertemplate="<b>%{y}</b><br>%{x} DMs<extra></extra>",
        ))
        apply_design(fig, "Top 15 Job Titles")
        fig.update_layout(
            yaxis_title="", xaxis_title="Count",
            height=420, showlegend=False,
            yaxis=dict(autorange="reversed"),
        )
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(data_coverage_note(pdf, "DM Job title"))
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No job title data available.")

with p2:
    nat_raw2 = pdf["DM Nationality"].dropna().str.split(";").explode().str.strip()
    nat_counts2 = nat_raw2.value_counts().head(10).reset_index()
    nat_counts2.columns = ["Nationality", "Count"]
    if len(nat_counts2) > 0:
        fig = px.bar(
            nat_counts2.sort_values("Count"),
            y="Nationality", x="Count",
            orientation="h",
            color_discrete_sequence=[DESIGN["color_brand"]],
        )
        apply_design(fig, "Top 10 Nationalities (sorted)")
        fig.update_layout(
            yaxis_title="", xaxis_title="No. of DMs",
            height=420, showlegend=False,
        )
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No nationality data available.")

st.markdown("<hr style='border-color:#E5E5E5;margin:24px 0'>", unsafe_allow_html=True)

# ── Gender × Cluster ──────────────────────────────────────────────────────────
st.markdown("""
<div style='font-size:15px;font-weight:600;color:#1A1A1A;margin-bottom:4px;'>
Female Leadership by Sector &amp; Growth Type</div>
<div style='font-size:13px;color:#666666;margin-bottom:16px;'>
Responds to global filters – e.g. select only scaleups</div>
""", unsafe_allow_html=True)

gc_df = (
    pdf[pdf["primary_cluster"] != "unknown"]
    .groupby("primary_cluster")["DM Gender"]
    .value_counts()
    .unstack(fill_value=0)
)

if "F" in gc_df.columns and "M" in gc_df.columns:
    gc_df["female_pct"] = gc_df["F"] / (gc_df["F"] + gc_df["M"]) * 100
    gc_df = gc_df.reset_index().sort_values("female_pct", ascending=False)

    bar_colors = [
        DESIGN["color_success"] if p >= 30
        else DESIGN["color_warning"] if p >= 15
        else DESIGN["color_error"]
        for p in gc_df["female_pct"]
    ]
    fig = go.Figure(go.Bar(
        x=gc_df["primary_cluster"],
        y=gc_df["female_pct"],
        marker_color=bar_colors,
        hovertemplate="<b>%{x}</b><br>Female: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(
        y=30, line_dash="dash", line_color="#D0D0D0", line_width=1.5,
        annotation_text="Target: 30%",
        annotation_position="top right",
        annotation_font_size=10,
    )
    apply_design(fig, "Female Leadership % by Cluster")
    fig.update_layout(
        xaxis_title="", yaxis_title="Female Leadership (%)",
        height=320, showlegend=False, xaxis_tickangle=-25,
    )
    with st.container():
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if "M" in gc_df.columns:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=gc_df["primary_cluster"],
            y=gc_df["M"],
            name="Male",
            marker_color="#2A6DFB",
            text=gc_df["M"],
            textposition="inside",
        ))
        fig2.add_trace(go.Bar(
            x=gc_df["primary_cluster"],
            y=gc_df["F"],
            name="Female",
            marker_color="#9061FF",
            text=gc_df["F"],
            textposition="inside",
        ))
        fig2.update_layout(barmode="stack")
        apply_design(fig2, "M vs F by Cluster (absolute)")
        fig2.update_layout(
            height=320, xaxis_title="", yaxis_title="No. of DMs",
            xaxis_tickangle=-25,
        )
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No gender data available for cluster analysis.")

st.markdown("<hr style='border-color:#E5E5E5;margin:24px 0'>", unsafe_allow_html=True)

# ── Education ─────────────────────────────────────────────────────────────────
with st.expander("🎓 Education Background", expanded=False):
    uni_counts = pdf["DM University"].value_counts().head(15).reset_index()
    uni_counts.columns = ["University", "Count"]

    deg_counts = pdf["DM Degree"].value_counts().reset_index()
    deg_counts.columns = ["Degree", "Count"]

    maj_counts = pdf["DM Major"].value_counts().head(10).reset_index()
    maj_counts.columns = ["Subject", "Count"]

    e1, e2, e3 = st.columns(3)

    with e1:
        if len(uni_counts) > 0:
            fig = px.bar(uni_counts.sort_values("Count"),
                         y="University", x="Count", orientation="h",
                         color_discrete_sequence=[DESIGN["color_brand"]])
            apply_design(fig, "Top Universities")
            fig.update_layout(height=300, showlegend=False, yaxis_title="")
            with st.container():
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)
                st.caption(f"Data available for {pdf['DM University'].notna().sum()} DMs")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No university data available.")

    with e2:
        if len(deg_counts) > 0:
            fig = px.pie(
                values=deg_counts["Count"],
                names=deg_counts["Degree"],
                color_discrete_sequence=["#2A6DFB","#9061FF","#42C366","#ECB730","#EB3424"],
            )
            fig.update_traces(textinfo="none",
                hovertemplate="<b>%{label}</b>: %{value} (%{percent})<extra></extra>")
            apply_design(fig, "Degrees")
            fig.update_layout(height=300)
            with st.container():
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No degree data available.")

    with e3:
        if len(maj_counts) > 0:
            fig = px.bar(maj_counts.sort_values("Count"),
                         y="Subject", x="Count", orientation="h",
                         color_discrete_sequence=[DESIGN["accent_amethyst"]])
            apply_design(fig, "Fields of Study")
            fig.update_layout(height=300, showlegend=False, yaxis_title="")
            with st.container():
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No subject data available.")

# ── Compensation ──────────────────────────────────────────────────────────────
with st.expander("💵 Compensation Analysis", expanded=False):
    comp_df = pdf[[
        "DM Full name", AGE_COL, COMP_COL, "DM Job title",
        NAME_COL, "primary_cluster"
    ]].copy()
    comp_df[COMP_COL] = pd.to_numeric(comp_df[COMP_COL], errors="coerce")
    comp_valid = comp_df.dropna(subset=[AGE_COL, COMP_COL])

    if len(comp_valid) < 3:
        st.info(
            f"Compensation data not available ({len(pdf)} entries stored as 'n/a'). "
            "Bureau van Dijk did not collect compensation figures for these companies."
        )
    else:
        c_a, c_b = st.columns(2)
        with c_a:
            fig = px.scatter(
                comp_valid,
                x=AGE_COL,
                y=COMP_COL,
                color="primary_cluster",
                color_discrete_map=CLUSTER_COLORS,
                hover_name="DM Full name",
                hover_data={"DM Job title": True, NAME_COL: True},
                log_y=True,
            )
            apply_design(fig, "DM Age vs. Total Compensation (USD)")
            fig.update_layout(height=360)
            with st.container():
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

        with c_b:
            box_comp = comp_df.dropna(subset=[COMP_COL])
            min_n = 3
            valid_clusters_comp = (
                box_comp.groupby("primary_cluster").size()[
                    box_comp.groupby("primary_cluster").size() >= min_n
                ].index.tolist()
            )
            box_comp_f = box_comp[box_comp["primary_cluster"].isin(valid_clusters_comp)]
            if len(box_comp_f) >= 3:
                fig = px.box(
                    box_comp_f,
                    x="primary_cluster", y=COMP_COL,
                    color="primary_cluster", color_discrete_map=CLUSTER_COLORS,
                    points=False, log_y=True,
                )
                apply_design(fig, "Compensation by Cluster (log scale)")
                fig.update_layout(height=360, showlegend=False, xaxis_tickangle=-25)
                with st.container():
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info(f"Too few compensation data for box plot (min. {min_n} per cluster).")

        st.caption(f"Compensation data: {len(comp_valid)} DMs")

st.markdown("<hr style='border-color:#E5E5E5;margin:24px 0'>", unsafe_allow_html=True)

# ── Decision Maker Database ───────────────────────────────────────────────────
st.markdown(
    "<div style='font-size:15px;font-weight:600;color:#1A1A1A;margin-bottom:12px;'>"
    "Decision Maker Database</div>",
    unsafe_allow_html=True,
)

people_cols = {
    NAME_COL:          "Company",
    "DM Full name":    "Name",
    "DM Job title":    "Position",
    AGE_COL:           "Age",
    "DM Gender":       "Gender",
    "DM University":   "University",
    COMP_COL:          "Compensation (USD)",
    "primary_cluster": "Cluster",
}
people_display = pdf[list(people_cols.keys())].copy().rename(columns=people_cols)

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

    gb = GridOptionsBuilder.from_dataframe(people_display)
    gb.configure_default_column(
        sortable=True, filter=True, resizable=True, minWidth=80
    )
    gb.configure_selection("single", use_checkbox=False)
    gb.configure_grid_options(rowHeight=40)
    gb.configure_column("Company",    width=200)
    gb.configure_column("Name",       width=160)
    gb.configure_column("Position",   width=200)
    gb.configure_column("Age",        width=80)
    gb.configure_column("Gender",     width=100)
    gb.configure_column("University", width=160)
    gb.configure_column("Cluster",    width=160)
    grid_options = gb.build()

    response = AgGrid(
        people_display,
        gridOptions=grid_options,
        height=450,
        theme="alpine",
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        enable_enterprise_modules=False,
        allow_unsafe_jscode=False,
    )
    selected_rows = response.get("selected_rows", [])

    # ── Detail panel on row selection ─────────────────────────────────────────
    if selected_rows is not None and len(selected_rows) > 0:
        row = selected_rows[0] if isinstance(selected_rows, list) else selected_rows.iloc[0].to_dict()
        company_name = row.get("Company", "")
        dm_name      = row.get("Name", "")

        firm_data = pdf[pdf[NAME_COL] == company_name].iloc[0] if len(pdf[pdf[NAME_COL] == company_name]) > 0 else None

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="insight-card">', unsafe_allow_html=True)
            dp1, dp2 = st.columns(2)
            with dp1:
                st.markdown(f"**👤 DM Profile: {dm_name}**")
                st.write(f"Position: {row.get('Position', '–')}")
                st.write(f"Age: {row.get('Age', '–')}")
                st.write(f"Gender: {row.get('Gender', '–')}")
                st.write(f"University: {row.get('University', '–')}")
                st.write(f"Compensation: {row.get('Compensation (USD)', '–')}")
            with dp2:
                st.markdown(f"**🏢 Company: {company_name}**")
                if firm_data is not None:
                    rev_val = firm_data[REV_COL]
                    st.write(f"Cluster: {firm_data['primary_cluster']}")
                    st.write(f"Status: {'✅ Active' if firm_data['Status'] == 'Active' else firm_data['Status']}")
                    st.write(f"Revenue: {rev_val/1000:.1f} M EUR" if pd.notna(rev_val) else "Revenue: –")
                    st.write(f"Employees 2024: {firm_data[EMP_COL]:.0f}" if pd.notna(firm_data[EMP_COL]) else "Employees: –")
            st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.caption(f"AgGrid unavailable ({e}) – showing standard table.")
    st.dataframe(people_display, use_container_width=True, hide_index=True)
