import streamlit as st
import pandas as pd


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_excel("data/DDE_ESSEN_DATA_WITH_CLUSTERS.xlsx")

    for col in df.columns:
        if any(k in col for k in [
            'Revenue', 'Profit', 'Net income', 'Cash flow', 'Total assets',
            'equity', 'Equity ratio', 'employees', 'Growth', 'AAGR', 'Age',
            'Compensation', 'Graduation year', 'Founded year',
            'Scaler', 'HighGrowthFirm', 'ConsistentHighGrowthFirm',
            'VeryHighGrowthFirm', 'Gazelle', 'Mature', 'Scaleup', 'Superstar'
        ]):
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df['profit_margin'] = (
        df['Profit/loss before tax th EUR last avail. year'] /
        df['Revenue th EUR last avail. year']
    )
    df['firm_age'] = 2024 - df['Founded year']
    df['decade_founded'] = (df['Founded year'] // 10 * 10).astype('Int64')
    df['emp_growth_2020_2024'] = (
        (df['Number of employees 2024'] - df['Number of employees 2020']) /
        df['Number of employees 2020'] * 100
    )
    for prefix in ['Scaleup', 'Gazelle', 'HighGrowthFirm']:
        cols = [c for c in df.columns if c.startswith(prefix)]
        df[f'{prefix.lower()}_years_count'] = df[cols].sum(axis=1)

    return df.copy()
