from openai import OpenAI
import streamlit as st
import pandas as pd
import os


def build_system_prompt(df) -> str:
    rev    = pd.to_numeric(df["Revenue th EUR last avail. year"],            errors="coerce")
    profit = pd.to_numeric(df["Profit/loss before tax th EUR last avail. year"], errors="coerce")
    emp24  = pd.to_numeric(df["Number of employees 2024"],                   errors="coerce")

    top10 = df.nlargest(10, "Revenue th EUR last avail. year")[[
        "Company name (Latin alphabet)",
        "Revenue th EUR last avail. year",
        "primary_cluster",
        "Number of employees 2024",
    ]].to_string(index=False)

    cluster_summary = df["primary_cluster"].value_counts().to_string()

    gender_counts = df["DM Gender"].value_counts()
    f_n = gender_counts.get("F", 0)
    m_n = gender_counts.get("M", 0)
    female_pct = f_n / (f_n + m_n) * 100 if (f_n + m_n) > 0 else 0

    scaleup_2024 = pd.to_numeric(df.get("Scaleup 2024", pd.Series(0)),        errors="coerce").sum()
    hgf_2024     = pd.to_numeric(df.get("HighGrowthFirm 2024", pd.Series(0)), errors="coerce").sum()
    gazelle_2024 = pd.to_numeric(df.get("Gazelle 2024", pd.Series(0)),         errors="coerce").sum()

    return f"""You are a company analyst for the Essen Company Intelligence database.
You have access to data on 879 companies from Essen, Germany (Bureau van Dijk).

DATASET OVERVIEW:
- 879 companies, all in Essen, Germany
- Active companies: {(df["Status"] == "Active").sum()}
- Companies with revenue data: {rev.notna().sum()}
- Total revenue: {rev.sum() / 1e6:.1f} Bn EUR
- Median revenue: {rev.median() / 1000:.1f} M EUR

TOP 10 COMPANIES BY REVENUE:
{top10}

CLUSTER DISTRIBUTION:
{cluster_summary}

GROWTH STATISTICS 2024:
- Scaleups: {int(scaleup_2024)}
- High-Growth Firms: {int(hgf_2024)}
- Gazelles: {int(gazelle_2024)}

KEY FINDINGS:
- Top 10 firms = 87.5% of total revenue
- High-Growth firms: 7 (2020) → 36 (2024), +414%
- Only 13 firms classified as Scaleup multiple times
- Female leadership: {female_pct:.1f}%
- 53% of firms founded after 2000
- Food & Hospitality: +31% employment 2020-2024
- Construction: median profit margin 4.8%
- Media/Marketing: median -3.3% (structurally loss-making)

PROFITABILITY BY CLUSTER (Median Margin):
Construction 4.8% | Financial 4.6% | Tech ICT 3.9%
Manufacturing 3.3% | Energy 3.2% | Consulting 0.1%
Education -0.9% | Transport -1.8% | Media -3.3%

Always reply in English. Cite concrete numbers.
Reference dashboard pages: 💰 Financials | 📊 Analytics | 🗂️ Clusters | 👥 People
If you don't know something, say so directly."""


def get_groq_response(question: str, system_prompt: str, history: list) -> str:
    try:
        api_key = st.session_state.get("groq_api_key", "")
        if not api_key:
            try:
                api_key = st.secrets.get("GROQ_API_KEY", "")
            except Exception:
                api_key = ""
        if not api_key:
            api_key = os.environ.get("GROQ_API_KEY", "")

        if not api_key:
            return (
                "⚠️ No API key found.\n\n"
                "Please paste your Groq API key in the sidebar under **AI Agent**.\n"
                "Get your key at: **console.groq.com/keys**"
            )

        if not api_key.startswith("gsk_"):
            return (
                f"⚠️ Invalid API key (starts with `{api_key[:4]}...`).\n\n"
                "Groq keys always start with **`gsk_`**.\n"
                "Please copy the correct key from **console.groq.com/keys**."
            )

        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        messages = [{"role": "system", "content": system_prompt}]
        messages += history[-10:]
        messages.append({"role": "user", "content": question})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=1024,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ Groq API error: {str(e)}"
