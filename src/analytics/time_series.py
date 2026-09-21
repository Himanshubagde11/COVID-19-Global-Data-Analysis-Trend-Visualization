"""Time-Series Modeling and Epidemiological Wave Detection Module.

Implements:
- Multi-window rolling averages (7-day, 14-day, 30-day) for cases, deaths, and vaccinations
- Empirical wave peak identification using signal processing (prominence and distance filtering)
- Country trajectory alignment and comparative epidemic phase modeling
"""

from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from src.utils.logger import get_logger

logger = get_logger("time_series")

BENCHMARK_COUNTRIES = [
    "United States",
    "India",
    "United Kingdom",
    "Germany",
    "Brazil",
    "Italy",
    "France",
    "Japan",
    "Canada",
    "Australia",
]


def get_rolling_averages(
    df: pd.DataFrame,
    country: Optional[str] = None,
    country_col: str = "country",
    date_col: str = "date",
    metric_col: str = "new_cases",
    windows: Tuple[int, ...] = (7, 14, 30),
) -> pd.DataFrame:
    """Extracts a continuous time-series DataFrame with multi-window rolling averages.

    Args:
        df: Input DataFrame.
        country: Optional specific country to filter by. If None, computes global aggregate.
        country_col: Name of country column.
        date_col: Name of date column.
        metric_col: Metric to calculate rolling windows on.
        windows: Tuple of rolling window lengths in days.

    Returns:
        pd.DataFrame indexed by date.
    """
    df = df.copy()

    if country:
        c_series = df[df[country_col] == country].copy()
        if c_series.empty:
            raise ValueError(f"Country '{country}' not found in dataset.")
        c_series[date_col] = pd.to_datetime(c_series[date_col])
        ts = c_series.sort_values(by=date_col).set_index(date_col)[[metric_col]]
    else:
        # Global daily sum
        df[date_col] = pd.to_datetime(df[date_col])
        ts = df.groupby(date_col)[[metric_col]].sum().sort_index()

    for w in windows:
        ts[f"{w}d_avg"] = ts[metric_col].rolling(window=w, min_periods=1).mean().round(2)

    return ts


def detect_pandemic_waves(
    ts_series: pd.Series,
    distance_days: int = 45,
    prominence_factor: float = 0.25,
) -> pd.DataFrame:
    """Detects pandemic wave peaks using topological prominence filtering on rolling time series.

    Args:
        ts_series: 7-day smoothed time-series (indexed by datetime).
        distance_days: Minimum spacing required between consecutive wave peaks.
        prominence_factor: Fraction of peak height required for prominence qualification.

    Returns:
        pd.DataFrame of identified wave peaks with dates, peak values, and prominence.
    """
    clean_series = ts_series.dropna()
    if len(clean_series) < distance_days:
        return pd.DataFrame()

    values = clean_series.values
    max_val = np.max(values)
    min_prominence = max_val * prominence_factor

    peak_indices, properties = find_peaks(
        values,
        distance=distance_days,
        prominence=min_prominence,
    )

    if len(peak_indices) == 0:
        logger.info("No distinct wave peaks detected with given prominence thresholds.")
        return pd.DataFrame()

    peak_dates = clean_series.index[peak_indices]
    peak_values = values[peak_indices]
    prominences = properties.get("prominences", np.zeros_like(peak_values))

    wave_df = pd.DataFrame({
        "wave_number": range(1, len(peak_dates) + 1),
        "peak_date": peak_dates,
        "peak_smoothed_daily_metric": np.round(peak_values, 2),
        "prominence": np.round(prominences, 2),
    })

    logger.info(f"Identified {len(wave_df)} distinct epidemic waves.")
    return wave_df


def compare_country_trajectories(
    df: pd.DataFrame,
    countries: Optional[List[str]] = None,
    metric_col: str = "7_day_cases_avg",
    country_col: str = "country",
    date_col: str = "date",
) -> pd.DataFrame:
    """Pivots multi-country smoothed time series for side-by-side comparative analysis."""
    if countries is None:
        countries = BENCHMARK_COUNTRIES

    filtered = df[df[country_col].isin(countries)].copy()
    if filtered.empty:
        logger.warning("None of the specified benchmark countries found in dataset.")
        return pd.DataFrame()

    pivoted = filtered.pivot_table(
        index=date_col,
        columns=country_col,
        values=metric_col,
        aggfunc="first",
    ).sort_index()

    return pivoted
