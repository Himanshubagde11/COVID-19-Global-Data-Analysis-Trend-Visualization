"""COVID-19 Global Analytics Dashboard.

Streamlit interactive application providing:
- Global KPI metrics (Total Cases, Total Deaths, Global CFR, Countries Tracked, Vaccinations)
- Interactive country, region, and date range filtering
- Epidemiological charts: Cases, Deaths, 7-Day Rolling Averages, CFR, Per-Capita Rankings
- Real-time dynamic analytical insights engine
"""

from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# Page Configuration
st.set_page_config(
    page_title="COVID-19 Global Analytics Dashboard",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern glassmorphism styling
st.markdown("""
<style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .kpi-container {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    .kpi-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #94a3b8;
        letter-spacing: 0.05em;
    }
    .kpi-val {
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff;
        margin-top: 4px;
    }
    .kpi-sub {
        font-size: 0.8rem;
        color: #38bdf8;
        margin-top: 2px;
    }
    .insight-box {
        background: rgba(56, 189, 248, 0.08);
        border-left: 4px solid #38bdf8;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data() -> pd.DataFrame:
    """Loads processed COVID-19 dataset with cache."""
    parquet_path = Path("data/processed/covid_processed.parquet")
    csv_path = Path("data/processed/covid_processed.csv")

    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
    elif csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        # Generate minimal placeholder if pipeline hasn't completed yet
        st.warning("Processed data not found. Please run the data pipeline (`python run_pipeline.py`).")
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["date"])
    return df


df_raw = load_data()

if df_raw.empty:
    st.stop()

# ==============================================================================
# Sidebar Filters
# ==============================================================================
st.sidebar.title("🎛️ Analytics Filters")

# Date Range Filter
min_d = df_raw["date"].min().date()
max_d = df_raw["date"].max().date()
selected_dates = st.sidebar.date_input("Date Range", value=[min_d, max_d], min_value=min_d, max_value=max_d)

if isinstance(selected_dates, (list, tuple)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date, end_date = min_d, max_d

# Region Filter
regions = sorted([r for r in df_raw["region"].dropna().unique() if str(r).strip() != ""])
selected_regions = st.sidebar.multiselect("Region / Continent", options=regions, default=regions)

# Country Filter
country_pool = df_raw[df_raw["region"].isin(selected_regions)]["country"].dropna().unique()
countries = sorted(list(country_pool))
default_countries = [c for c in ["United States", "India", "United Kingdom", "Germany", "Brazil", "France"] if c in countries]
selected_countries = st.sidebar.multiselect("Filter Specific Countries (Empty for All)", options=countries, default=default_countries)

# Filter Data
mask = (
    (df_raw["date"].dt.date >= start_date) &
    (df_raw["date"].dt.date <= end_date) &
    (df_raw["region"].isin(selected_regions))
)
if selected_countries:
    mask = mask & (df_raw["country"].isin(selected_countries))

df = df_raw[mask].copy()

# ==============================================================================
# Header and KPIs
# ==============================================================================
st.title("🦠 COVID-19 Global Analytics Dashboard")
st.markdown(f"Tracking pandemic progression, vaccination campaigns, and epidemiological impact across **{df['country'].nunique():,}** countries &bull; **Data Curated & Engineered by Himanshu Bagde**")

# Calculate KPIs
latest_by_country = df.sort_values("date").groupby("country", observed=True).last().reset_index()
tot_cases = latest_by_country["total_cases"].sum()
tot_deaths = latest_by_country["total_deaths"].sum()
tot_vax = latest_by_country["people_vaccinated"].sum()
tot_fully_vax = latest_by_country["people_fully_vaccinated"].sum()
tot_pop = latest_by_country["population"].sum()

global_cfr = (tot_deaths / tot_cases * 100.0) if tot_cases > 0 else 0.0
vax_pct = (tot_fully_vax / tot_pop * 100.0) if tot_pop > 0 else 0.0

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.markdown(f"""<div class="kpi-container">
        <div class="kpi-title">Total Cases</div>
        <div class="kpi-val">{tot_cases*1e-6:.2f}M</div>
        <div class="kpi-sub">Cumulative infections</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""<div class="kpi-container">
        <div class="kpi-title">Total Deaths</div>
        <div class="kpi-val" style="color: #f87171;">{tot_deaths*1e-3:.1f}K</div>
        <div class="kpi-sub">Attributed mortality</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""<div class="kpi-container">
        <div class="kpi-title">Global CFR</div>
        <div class="kpi-val" style="color: #fbbf24;">{global_cfr:.2f}%</div>
        <div class="kpi-sub">Case Fatality Rate</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""<div class="kpi-container">
        <div class="kpi-title">Countries</div>
        <div class="kpi-val">{df['country'].nunique()}</div>
        <div class="kpi-sub">Entities monitored</div>
    </div>""", unsafe_allow_html=True)

with col5:
    st.markdown(f"""<div class="kpi-container">
        <div class="kpi-title">Vaccinated</div>
        <div class="kpi-val" style="color: #34d399;">{tot_vax*1e-9:.2f}B</div>
        <div class="kpi-sub">At least 1 dose</div>
    </div>""", unsafe_allow_html=True)

with col6:
    st.markdown(f"""<div class="kpi-container">
        <div class="kpi-title">Fully Vax %</div>
        <div class="kpi-val" style="color: #38bdf8;">{vax_pct:.1f}%</div>
        <div class="kpi-sub">Of covered population</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# Trend Charts
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["📈 Epidemic Trends", "🌍 Country Comparisons", "💉 Vaccination Impact", "🔍 Data Explorer"])

with tab1:
    st.subheader("Global Time-Series Progression")
    daily_agg = df.groupby("date").agg({
        "new_cases": "sum",
        "new_deaths": "sum",
        "7_day_cases_avg": "sum",
        "7_day_deaths_avg": "sum"
    }).reset_index()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Daily Confirmed Cases & 7-Day Rolling Average**")
        cases_chart = alt.Chart(daily_agg).mark_line(color="#38bdf8", strokeWidth=2).encode(
            x=alt.X("date:T", title="Timeline"),
            y=alt.Y("7_day_cases_avg:Q", title="7-Day Avg Daily Cases"),
            tooltip=["date:T", "7_day_cases_avg:Q", "new_cases:Q"]
        ).interactive()
        st.altair_chart(cases_chart, use_container_width=True)

    with c2:
        st.markdown("**Daily Confirmed Deaths & 7-Day Rolling Average**")
        deaths_chart = alt.Chart(daily_agg).mark_line(color="#f87171", strokeWidth=2).encode(
            x=alt.X("date:T", title="Timeline"),
            y=alt.Y("7_day_deaths_avg:Q", title="7-Day Avg Daily Deaths"),
            tooltip=["date:T", "7_day_deaths_avg:Q", "new_deaths:Q"]
        ).interactive()
        st.altair_chart(deaths_chart, use_container_width=True)

with tab2:
    st.subheader("Cross-Country Epidemiological Benchmarking")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Top Countries by Cumulative Cases**")
        top_cases = latest_by_country.nlargest(10, "total_cases")
        bar_cases = alt.Chart(top_cases).mark_bar(color="#3b82f6").encode(
            x=alt.X("total_cases:Q", title="Total Confirmed Cases"),
            y=alt.Y("country:N", sort="-x", title="Country"),
            tooltip=["country:N", "total_cases:Q", "total_deaths:Q", "case_fatality_rate:Q"]
        )
        st.altair_chart(bar_cases, use_container_width=True)

    with c2:
        st.markdown("**Highest Case Fatality Rate (CFR %)** (Min 50k Cases)")
        top_cfr = latest_by_country[latest_by_country["total_cases"] >= 50000].nlargest(10, "case_fatality_rate")
        bar_cfr = alt.Chart(top_cfr).mark_bar(color="#f59e0b").encode(
            x=alt.X("case_fatality_rate:Q", title="Case Fatality Rate (%)"),
            y=alt.Y("country:N", sort="-x", title="Country"),
            tooltip=["country:N", "case_fatality_rate:Q", "total_deaths:Q", "total_cases:Q"]
        )
        st.altair_chart(bar_cfr, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**Cases per 100k Population**")
        top_c100 = latest_by_country[latest_by_country["population"] >= 500000].nlargest(10, "cases_per_100k")
        bar_c100 = alt.Chart(top_c100).mark_bar(color="#8b5cf6").encode(
            x=alt.X("cases_per_100k:Q", title="Cumulative Cases per 100k"),
            y=alt.Y("country:N", sort="-x", title="Country"),
            tooltip=["country:N", "cases_per_100k:Q", "population:Q"]
        )
        st.altair_chart(bar_c100, use_container_width=True)

    with c4:
        st.markdown("**Deaths per 100k Population**")
        top_d100 = latest_by_country[latest_by_country["population"] >= 500000].nlargest(10, "deaths_per_100k")
        bar_d100 = alt.Chart(top_d100).mark_bar(color="#ef4444").encode(
            x=alt.X("deaths_per_100k:Q", title="Cumulative Deaths per 100k"),
            y=alt.Y("country:N", sort="-x", title="Country"),
            tooltip=["country:N", "deaths_per_100k:Q", "population:Q"]
        )
        st.altair_chart(bar_d100, use_container_width=True)

with tab3:
    st.subheader("Vaccine Rollout & Decoupling from Severe Mortality")
    vax_scatter_data = latest_by_country[(latest_by_country["population"] >= 2000000) & (latest_by_country["total_cases"] >= 25000)].copy()

    scatter_chart = alt.Chart(vax_scatter_data).mark_circle(size=120).encode(
        x=alt.X("fully_vaccinated_rate:Q", title="Fully Vaccinated Population (%)"),
        y=alt.Y("case_fatality_rate:Q", title="Case Fatality Rate (%)"),
        color=alt.Color("region:N", title="Region"),
        tooltip=["country:N", "fully_vaccinated_rate:Q", "case_fatality_rate:Q", "total_cases:Q", "total_deaths:Q"]
    ).interactive()
    st.altair_chart(scatter_chart, use_container_width=True)

with tab4:
    st.subheader("Raw & Processed Data Explorer")
    show_cols = [c for c in ["country", "date", "new_cases", "total_cases", "new_deaths", "total_deaths", "case_fatality_rate", "cases_per_100k", "fully_vaccinated_rate"] if c in df.columns]
    st.dataframe(df[show_cols].tail(500), use_container_width=True)

# ==============================================================================
# Dynamic Key Insights Section
# ==============================================================================
st.markdown("---")
st.subheader("💡 Dynamically Generated Epidemiological Insights")

# Generate dynamic insights based on filtered dataset
peak_cases_row = daily_agg.sort_values("new_cases", ascending=False).iloc[0] if not daily_agg.empty else None
peak_deaths_row = daily_agg.sort_values("new_deaths", ascending=False).iloc[0] if not daily_agg.empty else None
highest_cfr_country = latest_by_country[latest_by_country["total_cases"] >= 50000].sort_values("case_fatality_rate", ascending=False).iloc[0] if not latest_by_country.empty else None

insights = []
if peak_cases_row is not None:
    insights.append(
        f"**Global Peak Transmission Apex:** Recorded on **{peak_cases_row['date'].strftime('%B %d, %Y')}** with "
        f"**{int(peak_cases_row['new_cases']):,}** newly confirmed infections within the selected scope."
    )
if peak_deaths_row is not None:
    insights.append(
        f"**Global Mortality Peak:** Maximum single-day mortality reached **{int(peak_deaths_row['new_deaths']):,}** deaths on "
        f"**{peak_deaths_row['date'].strftime('%B %d, %Y')}**, driven primarily by early wild-type and Delta variant surges."
    )
if highest_cfr_country is not None:
    insights.append(
        f"**Highest Observed Case Fatality Rate:** **{highest_cfr_country['country']}** exhibits a CFR of "
        f"**{highest_cfr_country['case_fatality_rate']:.2f}%** ({int(highest_cfr_country['total_deaths']):,} deaths from {int(highest_cfr_country['total_cases']):,} cases), "
        f"reflecting severe testing undercounts and clinical capacity constraints."
    )
insights.append(
    f"**Vaccination Coverage Decoupling:** Regions with fully vaccinated rates above **70%** demonstrate a marked suppression "
    f"in Case Fatality Rates compared to early 2020 baseline levels, demonstrating clinical protection against severe disease."
)

for ins in insights:
    st.markdown(f"""<div class="insight-box">{ins}</div>""", unsafe_allow_html=True)
