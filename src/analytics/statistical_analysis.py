"""Statistical Analysis Module for COVID-19 Global Data.

Provides:
- Parametric and non-parametric descriptive statistics (Mean, Median, Std, IQR, Percentiles, Skewness)
- Detailed narrative explanations of epidemiological relevance for each statistical metric
- Correlation analysis (Pearson and Spearman rank correlations) across transmission, mortality, and vaccination variables
"""

from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from scipy import stats

from src.utils.logger import get_logger

logger = get_logger("statistical_analysis")


def explain_statistical_metrics() -> Dict[str, str]:
    """Returns domain-grounded explanations of why each statistical metric is used in epidemiology."""
    return {
        "mean": (
            "Mean: Represents the mathematical center of daily observations. However, because infectious disease "
            "data is heavily right-skewed by superspreading events and reporting delays, mean alone is sensitive to outliers."
        ),
        "median": (
            "Median (50th Percentile): Represents the typical daily count resilient to massive weekend backlogs or data dumps. "
            "In epidemiology, median provides a robust baseline of baseline community transmission."
        ),
        "std_dev": (
            "Standard Deviation: Quantifies the volatility and dispersion of daily infections. High standard deviation "
            "signals erratic epidemic surges, explosive variant waves, or inconsistent testing reporting cadence."
        ),
        "iqr": (
            "Interquartile Range (IQR = Q3 - Q1): Measures the spread of the middle 50% of daily observations. "
            "It is the non-parametric counterpart to standard deviation, ideal for heavy-tailed epidemic distributions."
        ),
        "percentiles": (
            "Percentiles (25th, 75th, 90th, 95th, 99th): 95th and 99th percentiles capture peak surge capacity demands "
            "on healthcare systems, critical for hospital ICU bed and oxygen allocation planning."
        ),
        "min_max": (
            "Min/Max: Defines the absolute empirical boundaries. In daily data, a min of 0 reflects eradicated transmission "
            "or reporting holidays, while max indicates the historical single-day pandemic apex."
        ),
        "skewness": (
            "Skewness: Measures distributional asymmetry. COVID-19 daily flows typically exhibit positive (right) skewness, "
            "where most days have low-to-moderate transmission followed by severe, rapid-peaking variant outbreaks."
        ),
    }


def calculate_descriptive_stats(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    percentiles: Optional[List[float]] = None,
) -> pd.DataFrame:
    """Calculates comprehensive parametric and non-parametric descriptive statistics.

    Args:
        df: Input DataFrame.
        columns: Target numeric columns.
        percentiles: Quantiles to evaluate (default: [0.25, 0.50, 0.75, 0.90, 0.95, 0.99]).

    Returns:
        pd.DataFrame: Formatted statistical summary table.
    """
    if percentiles is None:
        percentiles = [0.25, 0.50, 0.75, 0.90, 0.95, 0.99]

    if columns is None:
        default_cols = [
            "new_cases", "new_deaths", "total_cases", "total_deaths",
            "case_fatality_rate", "cases_per_100k", "deaths_per_100k",
            "vaccination_rate", "fully_vaccinated_rate"
        ]
        columns = [c for c in default_cols if c in df.columns]

    logger.info(f"Computing descriptive statistics for {len(columns)} columns...")

    stats_dict = {}
    for col in columns:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty:
            continue

        q25 = float(series.quantile(0.25))
        q50 = float(series.quantile(0.50))
        q75 = float(series.quantile(0.75))
        iqr = q75 - q25

        col_stats = {
            "Count": int(len(series)),
            "Mean": round(float(series.mean()), 2),
            "Std Dev": round(float(series.std()), 2),
            "Median (Q2)": round(q50, 2),
            "IQR": round(iqr, 2),
            "Min": round(float(series.min()), 2),
            "25th Pct": round(q25, 2),
            "75th Pct": round(q75, 2),
            "90th Pct": round(float(series.quantile(0.90)), 2),
            "95th Pct": round(float(series.quantile(0.95)), 2),
            "99th Pct": round(float(series.quantile(0.99)), 2),
            "Max": round(float(series.max()), 2),
            "Skewness": round(float(stats.skew(series)), 2),
            "Kurtosis": round(float(stats.kurtosis(series)), 2),
        }
        stats_dict[col] = col_stats

    result_df = pd.DataFrame(stats_dict).T
    logger.info(f"Descriptive statistics successfully generated for {len(result_df)} metrics.")
    return result_df


def calculate_correlation_matrix(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    method: str = "pearson",
) -> pd.DataFrame:
    """Calculates pairwise correlation coefficients (Pearson linear or Spearman monotonic rank).

    Epidemiological relevance:
    Allows quantifying the relationship between vaccination coverage and mortality rates,
    or population density vs case transmission per capita.
    """
    if columns is None:
        target_cols = [
            "cases_per_100k", "deaths_per_100k", "case_fatality_rate",
            "vaccination_rate", "fully_vaccinated_rate",
            "population_density", "median_age", "gdp_per_capita"
        ]
        columns = [c for c in target_cols if c in df.columns]

    numeric_df = df[columns].apply(pd.to_numeric, errors="coerce")
    corr_df = numeric_df.corr(method=method).round(4)
    logger.info(f"Computed {method.capitalize()} correlation matrix across {len(columns)} dimensions.")
    return corr_df
