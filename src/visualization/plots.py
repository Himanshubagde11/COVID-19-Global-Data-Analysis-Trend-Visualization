"""Publication-Quality Epidemiological Visualizations using Matplotlib & Seaborn.

Generates 18 required figures:
 1. Global daily cases line chart
 2. Global daily deaths line chart
 3. 7-day rolling average cases
 4. 7-day rolling average deaths
 5. Top countries by total cases
 6. Top countries by total deaths
 7. CFR comparison across major affected countries
 8. Global vaccination coverage (%) over time
 9. Top countries by cases per 100k
10. Top countries by deaths per 100k
11. Multi-country comparative trajectory line chart
12. Regional trend chart (stacked/faceted)
13. Scatter plot: Vaccination coverage vs cases per 100k
14. Scatter plot: Vaccination coverage vs CFR / mortality
15. Monthly aggregated global cases bar chart
16. Monthly aggregated global deaths bar chart
17. Pandemic wave timeline with detected peaks
18. Heatmap of monthly new cases by country
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns

from src.analytics.time_series import detect_pandemic_waves
from src.utils.logger import get_logger

logger = get_logger("visualization")

# Professional Theme Configuration
plt.rcParams.update({
    "figure.facecolor": "#ffffff",
    "axes.facecolor": "#f8fafc",
    "axes.edgecolor": "#cbd5e1",
    "axes.labelcolor": "#1e293b",
    "axes.labelsize": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "grid.color": "#e2e8f0",
    "grid.linestyle": "--",
    "grid.alpha": 0.7,
    "xtick.color": "#475569",
    "ytick.color": "#475569",
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "font.family": "sans-serif",
    "figure.autolayout": True,
})

SOURCE_TEXT = "Source: Our World in Data / WHO | Data Pipeline & Analytics by Himanshu Bagde"


def _add_source_footer(ax: plt.Axes, text: str = SOURCE_TEXT) -> None:
    """Adds standard source attribution footer to bottom right of figure."""
    ax.figure.text(0.99, 0.01, text, ha="right", va="bottom", fontsize=8, color="#94a3b8", fontstyle="italic")


# 1. Global Daily Cases
def plot_global_daily_cases(df: pd.DataFrame, output_path: Union[str, Path]) -> Path:
    daily = df.groupby("date")["new_cases"].sum().reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date")

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(daily["date"], daily["new_cases"], color="#3b82f6", alpha=0.35, linewidth=1, label="Daily Reported Cases")
    ax.plot(daily["date"], daily["new_cases"].rolling(7).mean(), color="#1d4ed8", linewidth=2.2, label="7-Day Rolling Average")

    ax.set_title("Global Daily COVID-19 Cases (2020 - 2024)", pad=15)
    ax.set_xlabel("Timeline")
    ax.set_ylabel("Daily Confirmed Cases (Millions)")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x*1e-6:.1f}M"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_minor_locator(mdates.MonthLocator((1, 7)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.grid(True)
    ax.legend(loc="upper right", frameon=True)
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 2. Global Daily Deaths
def plot_global_daily_deaths(df: pd.DataFrame, output_path: Union[str, Path]) -> Path:
    daily = df.groupby("date")["new_deaths"].sum().reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date")

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(daily["date"], daily["new_deaths"], color="#ef4444", alpha=0.35, linewidth=1, label="Daily Reported Deaths")
    ax.plot(daily["date"], daily["new_deaths"].rolling(7).mean(), color="#b91c1c", linewidth=2.2, label="7-Day Rolling Average")

    ax.set_title("Global Daily COVID-19 Deaths (2020 - 2024)", pad=15)
    ax.set_xlabel("Timeline")
    ax.set_ylabel("Daily Confirmed Deaths (Thousands)")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x*1e-3:.1f}K"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_minor_locator(mdates.MonthLocator((1, 7)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.grid(True)
    ax.legend(loc="upper right", frameon=True)
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 3. 7-Day Rolling Average Cases Comparison
def plot_rolling_cases(df: pd.DataFrame, output_path: Union[str, Path], top_n: int = 5) -> Path:
    latest = df.groupby("country")["total_cases"].max().nlargest(top_n).index.tolist()
    filtered = df[df["country"].isin(latest)].copy()
    filtered["date"] = pd.to_datetime(filtered["date"])

    fig, ax = plt.subplots(figsize=(12, 6))
    palette = sns.color_palette("tab10", n_colors=top_n)

    for idx, c in enumerate(latest):
        c_data = filtered[filtered["country"] == c].sort_values("date")
        ax.plot(c_data["date"], c_data["7_day_cases_avg"], label=c, color=palette[idx], linewidth=1.8)

    ax.set_title(f"7-Day Rolling Average Cases: Top {top_n} Cumulative Affected Countries", pad=15)
    ax.set_xlabel("Timeline")
    ax.set_ylabel("7-Day Avg New Cases")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x*1e-3:.0f}K"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.grid(True)
    ax.legend(title="Country", loc="upper right", frameon=True)
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 4. 7-Day Rolling Average Deaths Comparison
def plot_rolling_deaths(df: pd.DataFrame, output_path: Union[str, Path], top_n: int = 5) -> Path:
    latest = df.groupby("country")["total_deaths"].max().nlargest(top_n).index.tolist()
    filtered = df[df["country"].isin(latest)].copy()
    filtered["date"] = pd.to_datetime(filtered["date"])

    fig, ax = plt.subplots(figsize=(12, 6))
    palette = sns.color_palette("Set2", n_colors=top_n)

    for idx, c in enumerate(latest):
        c_data = filtered[filtered["country"] == c].sort_values("date")
        ax.plot(c_data["date"], c_data["7_day_deaths_avg"], label=c, color=palette[idx], linewidth=1.8)

    ax.set_title(f"7-Day Rolling Average Deaths: Top {top_n} Cumulative Mortality Countries", pad=15)
    ax.set_xlabel("Timeline")
    ax.set_ylabel("7-Day Avg New Deaths")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.grid(True)
    ax.legend(title="Country", loc="upper right", frameon=True)
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 5. Top Countries by Total Cases
def plot_top_countries_cases(df: pd.DataFrame, output_path: Union[str, Path], top_n: int = 15) -> Path:
    top = df.groupby("country")["total_cases"].max().nlargest(top_n).sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(top.index, top.values, color="#2563eb", height=0.65)

    ax.set_title(f"Top {top_n} Countries by Cumulative COVID-19 Cases", pad=15)
    ax.set_xlabel("Total Confirmed Cases (Millions)")
    ax.set_ylabel("Country")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x*1e-6:.1f}M"))

    for bar in bars:
        w = bar.get_width()
        ax.text(w * 1.01, bar.get_y() + bar.get_height() / 2, f"{w*1e-6:.1f}M", va="center", fontsize=9, color="#1e293b")

    ax.grid(axis="x")
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 6. Top Countries by Total Deaths
def plot_top_countries_deaths(df: pd.DataFrame, output_path: Union[str, Path], top_n: int = 15) -> Path:
    top = df.groupby("country")["total_deaths"].max().nlargest(top_n).sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(top.index, top.values, color="#dc2626", height=0.65)

    ax.set_title(f"Top {top_n} Countries by Cumulative COVID-19 Deaths", pad=15)
    ax.set_xlabel("Total Confirmed Deaths (Thousands)")
    ax.set_ylabel("Country")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x*1e-3:.0f}K"))

    for bar in bars:
        w = bar.get_width()
        ax.text(w * 1.01, bar.get_y() + bar.get_height() / 2, f"{w*1e-3:.0f}K", va="center", fontsize=9, color="#1e293b")

    ax.grid(axis="x")
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 7. CFR Comparison across Top Countries
def plot_cfr_comparison(df: pd.DataFrame, output_path: Union[str, Path], top_n: int = 15) -> Path:
    latest = df.groupby("country").agg({"total_cases": "max", "total_deaths": "max", "case_fatality_rate": "last"})
    # Filter countries with substantial case count (> 250k) to prevent small-sample bias
    filtered = latest[latest["total_cases"] >= 250000].nlargest(top_n, "case_fatality_rate").sort_values("case_fatality_rate", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(filtered.index, filtered["case_fatality_rate"], color="#d97706", height=0.65)

    ax.set_title(f"Case Fatality Rate (CFR %) Comparison (Countries with >= 250k Cases)", pad=15)
    ax.set_xlabel("Case Fatality Rate (%)")
    ax.set_ylabel("Country")

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.05, bar.get_y() + bar.get_height() / 2, f"{w:.2f}%", va="center", fontsize=9, color="#1e293b")

    ax.grid(axis="x")
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 8. Vaccination Coverage Over Time
def plot_vaccination_coverage(df: pd.DataFrame, output_path: Union[str, Path]) -> Path:
    vax_df = df.groupby("date").agg({
        "people_vaccinated": "sum",
        "people_fully_vaccinated": "sum",
        "population": "sum"
    }).reset_index()
    vax_df["date"] = pd.to_datetime(vax_df["date"])
    # Filter when vaccination campaign began
    vax_df = vax_df[vax_df["date"] >= "2020-12-01"].sort_values("date")

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(vax_df["date"], vax_df["people_vaccinated"] * 1e-9, color="#10b981", linewidth=2.2, label="At Least 1 Dose (Billions)")
    ax.plot(vax_df["date"], vax_df["people_fully_vaccinated"] * 1e-9, color="#059669", linestyle="--", linewidth=2.2, label="Fully Vaccinated (Billions)")

    ax.set_title("Global Cumulative COVID-19 Vaccination Progress (2020 - 2024)", pad=15)
    ax.set_xlabel("Timeline")
    ax.set_ylabel("People Vaccinated (Billions)")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:.1f}B"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.grid(True)
    ax.legend(loc="upper left", frameon=True)
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 9. Cases per 100k
def plot_cases_per_100k(df: pd.DataFrame, output_path: Union[str, Path], top_n: int = 15) -> Path:
    latest = df[df["population"] >= 1000000].groupby("country").agg({
        "cases_per_100k": "max"
    }).nlargest(top_n, "cases_per_100k").sort_values("cases_per_100k", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(latest.index, latest["cases_per_100k"], color="#6366f1", height=0.65)

    ax.set_title(f"Top {top_n} Countries by Cases per 100,000 Population (Pop >= 1M)", pad=15)
    ax.set_xlabel("Cumulative Cases per 100k Citizens")
    ax.set_ylabel("Country")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))

    for bar in bars:
        w = bar.get_width()
        ax.text(w * 1.01, bar.get_y() + bar.get_height() / 2, f"{w:,.0f}", va="center", fontsize=9)

    ax.grid(axis="x")
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 10. Deaths per 100k
def plot_deaths_per_100k(df: pd.DataFrame, output_path: Union[str, Path], top_n: int = 15) -> Path:
    latest = df[df["population"] >= 1000000].groupby("country").agg({
        "deaths_per_100k": "max"
    }).nlargest(top_n, "deaths_per_100k").sort_values("deaths_per_100k", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(latest.index, latest["deaths_per_100k"], color="#b91c1c", height=0.65)

    ax.set_title(f"Top {top_n} Countries by Mortality per 100,000 Population (Pop >= 1M)", pad=15)
    ax.set_xlabel("Cumulative Deaths per 100k Citizens")
    ax.set_ylabel("Country")

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 5, bar.get_y() + bar.get_height() / 2, f"{w:,.0f}", va="center", fontsize=9)

    ax.grid(axis="x")
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 11. Multi-Country Trajectory Comparison
def plot_country_comparisons(df: pd.DataFrame, output_path: Union[str, Path]) -> Path:
    benchmarks = ["United States", "India", "United Kingdom", "Germany", "Brazil", "France", "Japan"]
    filtered = df[df["country"].isin(benchmarks)].copy()
    filtered["date"] = pd.to_datetime(filtered["date"])

    fig, ax = plt.subplots(figsize=(12, 6))
    palette = sns.color_palette("tab10", n_colors=len(benchmarks))

    for idx, c in enumerate(benchmarks):
        c_df = filtered[filtered["country"] == c].sort_values("date")
        ax.plot(c_df["date"], c_df["7_day_cases_avg"] / 1000, label=c, color=palette[idx], linewidth=1.8)

    ax.set_title("Comparative 7-Day Average Cases Trajectory: Selected Global Economies", pad=15)
    ax.set_xlabel("Timeline")
    ax.set_ylabel("7-Day Avg Daily Cases (Thousands)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.grid(True)
    ax.legend(title="Country", loc="upper right", frameon=True)
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 12. Regional Trends Chart
def plot_regional_trends(df: pd.DataFrame, output_path: Union[str, Path]) -> Path:
    if "region" not in df.columns:
        return Path(output_path)

    regional = df.groupby(["date", "region"])["new_cases"].sum().reset_index()
    regional["date"] = pd.to_datetime(regional["date"])
    regional = regional[regional["region"].notna() & (regional["region"] != "")]

    pivoted = regional.pivot_table(index="date", columns="region", values="new_cases", aggfunc="sum").fillna(0)
    smoothed = pivoted.rolling(14).mean()

    fig, ax = plt.subplots(figsize=(12, 6))
    smoothed.plot(ax=ax, linewidth=2, colormap="tab10")

    ax.set_title("Regional 14-Day Smoothed Case Trajectories by Continent", pad=15)
    ax.set_xlabel("Timeline")
    ax.set_ylabel("Daily New Cases (14-Day Average)")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x*1e-3:.0f}K"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.grid(True)
    ax.legend(title="Region", loc="upper right", frameon=True)
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 13. Vaccination vs Cases per 100k
def plot_vaccination_vs_cases(df: pd.DataFrame, output_path: Union[str, Path]) -> Path:
    latest = df[df["population"] >= 2000000].groupby("country").agg({
        "fully_vaccinated_rate": "max",
        "cases_per_100k": "max",
        "population": "max",
        "region": "first"
    }).dropna()

    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = sns.scatterplot(
        data=latest,
        x="fully_vaccinated_rate",
        y="cases_per_100k",
        hue="region",
        size="population",
        sizes=(40, 400),
        alpha=0.75,
        ax=ax
    )

    ax.set_title("Vaccination Coverage (%) vs Cumulative Cases per 100k Population", pad=15)
    ax.set_xlabel("Fully Vaccinated Rate (%)")
    ax.set_ylabel("Total Cases per 100k Population")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:,.0f}"))
    ax.grid(True)
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", frameon=True)
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 14. Vaccination vs Deaths / CFR
def plot_vaccination_vs_deaths(df: pd.DataFrame, output_path: Union[str, Path]) -> Path:
    latest = df[(df["population"] >= 2000000) & (df["total_cases"] >= 50000)].groupby("country").agg({
        "fully_vaccinated_rate": "max",
        "case_fatality_rate": "last",
        "population": "max",
        "region": "first"
    }).dropna()

    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = sns.scatterplot(
        data=latest,
        x="fully_vaccinated_rate",
        y="case_fatality_rate",
        hue="region",
        size="population",
        sizes=(40, 400),
        alpha=0.75,
        ax=ax
    )

    # Add trendline
    if len(latest) > 5:
        sns.regplot(
            data=latest,
            x="fully_vaccinated_rate",
            y="case_fatality_rate",
            scatter=False,
            ax=ax,
            color="#475569",
            line_kws={"linestyle": "--", "linewidth": 1.5}
        )

    ax.set_title("Vaccination Coverage (%) vs Case Fatality Rate (CFR %)", pad=15)
    ax.set_xlabel("Fully Vaccinated Rate (%)")
    ax.set_ylabel("Case Fatality Rate (%)")
    ax.grid(True)
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", frameon=True)
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 15. Monthly Aggregated Cases
def plot_monthly_cases(df: pd.DataFrame, output_path: Union[str, Path]) -> Path:
    df_m = df.copy()
    df_m["ym"] = df_m["date"].str.slice(0, 7)
    monthly = df_m.groupby("ym")["new_cases"].sum().reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(monthly["ym"], monthly["new_cases"] * 1e-6, color="#0284c7", width=0.7)

    ax.set_title("Global Monthly Confirmed COVID-19 Inflow (Millions)", pad=15)
    ax.set_xlabel("Year-Month")
    ax.set_ylabel("New Cases (Millions)")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:.0f}M"))
    plt.xticks(rotation=45, ha="right", fontsize=9)
    ax.grid(axis="y")
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 16. Monthly Aggregated Deaths
def plot_monthly_deaths(df: pd.DataFrame, output_path: Union[str, Path]) -> Path:
    df_m = df.copy()
    df_m["ym"] = df_m["date"].str.slice(0, 7)
    monthly = df_m.groupby("ym")["new_deaths"].sum().reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(monthly["ym"], monthly["new_deaths"] * 1e-3, color="#e11d48", width=0.7)

    ax.set_title("Global Monthly COVID-19 Mortality Inflow (Thousands)", pad=15)
    ax.set_xlabel("Year-Month")
    ax.set_ylabel("New Deaths (Thousands)")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:.0f}K"))
    plt.xticks(rotation=45, ha="right", fontsize=9)
    ax.grid(axis="y")
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 17. Pandemic Wave Timeline & Peak Identification
def plot_pandemic_waves(df: pd.DataFrame, output_path: Union[str, Path]) -> Path:
    global_cases = df.groupby("date")["new_cases"].sum().reset_index()
    global_cases["date"] = pd.to_datetime(global_cases["date"])
    global_cases = global_cases.sort_values("date").set_index("date")
    smoothed = global_cases["new_cases"].rolling(14, min_periods=1).mean()

    waves = detect_pandemic_waves(smoothed, distance_days=60, prominence_factor=0.2)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(smoothed.index, smoothed.values * 1e-6, color="#4f46e5", linewidth=2.2, label="14-Day Smoothed Global Cases")

    if not waves.empty:
        for idx, row in waves.iterrows():
            p_date = pd.to_datetime(row["peak_date"])
            p_val = row["peak_smoothed_daily_metric"] * 1e-6
            ax.scatter(p_date, p_val, color="#ef4444", s=80, zorder=5)
            ax.annotate(
                f"Wave {int(row['wave_number'])}\n({p_val:.2f}M/d)",
                (p_date, p_val),
                textcoords="offset points",
                xytext=(0, 12),
                ha="center",
                fontsize=8,
                weight="bold",
                color="#b91c1c",
                arrowprops=dict(arrowstyle="->", color="#ef4444", lw=1)
            )

    ax.set_title("Global Pandemic Wave Timeline & Empirical Peak Identification", pad=15)
    ax.set_xlabel("Timeline")
    ax.set_ylabel("Daily Cases (Millions / Day)")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x:.1f}M"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.grid(True)
    ax.legend(loc="upper left", frameon=True)
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


# 18. Heatmap of Monthly Cases by Country
def plot_cases_heatmap(df: pd.DataFrame, output_path: Union[str, Path], top_n: int = 15) -> Path:
    top_countries = df.groupby("country")["total_cases"].max().nlargest(top_n).index.tolist()
    filtered = df[df["country"].isin(top_countries)].copy()
    filtered["ym"] = filtered["date"].str.slice(0, 7)

    pivot = filtered.pivot_table(index="country", columns="ym", values="new_cases", aggfunc="sum").fillna(0)
    pivot_m = pivot / 1e6  # in Millions

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(
        pivot_m,
        cmap="YlOrRd",
        linewidths=0.5,
        linecolor="#ffffff",
        cbar_kws={"label": "Monthly Cases (Millions)"},
        ax=ax
    )

    ax.set_title(f"Monthly Infection Heatmap: Top {top_n} Hardest Hit Nations (Millions of Cases)", pad=15)
    ax.set_xlabel("Year-Month")
    ax.set_ylabel("Country")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    _add_source_footer(ax)

    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return Path(output_path)


def generate_all_visualizations(df: pd.DataFrame, output_dir: Union[str, Path] = "reports/figures") -> Dict[str, Path]:
    """Generates and saves all 18 publication-quality figures at 300 DPI."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    logger.info(f"Generating all 18 publication figures into {out}...")

    figures = {
        "01_global_daily_cases": plot_global_daily_cases(df, out / "01_global_daily_cases.png"),
        "02_global_daily_deaths": plot_global_daily_deaths(df, out / "02_global_daily_deaths.png"),
        "03_rolling_cases": plot_rolling_cases(df, out / "03_rolling_cases.png"),
        "04_rolling_deaths": plot_rolling_deaths(df, out / "04_rolling_deaths.png"),
        "05_top_countries_cases": plot_top_countries_cases(df, out / "05_top_countries_cases.png"),
        "06_top_countries_deaths": plot_top_countries_deaths(df, out / "06_top_countries_deaths.png"),
        "07_cfr_comparison": plot_cfr_comparison(df, out / "07_cfr_comparison.png"),
        "08_vaccination_coverage": plot_vaccination_coverage(df, out / "08_vaccination_coverage.png"),
        "09_cases_per_100k": plot_cases_per_100k(df, out / "09_cases_per_100k.png"),
        "10_deaths_per_100k": plot_deaths_per_100k(df, out / "10_deaths_per_100k.png"),
        "11_country_comparisons": plot_country_comparisons(df, out / "11_country_comparisons.png"),
        "12_regional_trends": plot_regional_trends(df, out / "12_regional_trends.png"),
        "13_vaccination_vs_cases": plot_vaccination_vs_cases(df, out / "13_vaccination_vs_cases.png"),
        "14_vaccination_vs_deaths": plot_vaccination_vs_deaths(df, out / "14_vaccination_vs_deaths.png"),
        "15_monthly_cases": plot_monthly_cases(df, out / "15_monthly_cases.png"),
        "16_monthly_deaths": plot_monthly_deaths(df, out / "16_monthly_deaths.png"),
        "17_pandemic_waves": plot_pandemic_waves(df, out / "17_pandemic_waves.png"),
        "18_cases_heatmap": plot_cases_heatmap(df, out / "18_cases_heatmap.png"),
    }

    logger.info(f"Successfully generated all {len(figures)} visualization figures at 300 DPI.")
    return figures
