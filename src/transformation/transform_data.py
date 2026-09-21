"""Data Transformation and Feature Engineering Pipeline for COVID-19 Analytics.

Calculates:
- Case Fatality Rate (CFR = (total_deaths / total_cases) * 100)
- Mortality Rate (death_rate = (total_deaths / population) * 100)
- Cases per 100,000 population
- Deaths per 100,000 population
- Vaccination coverage rates (at least 1 dose & fully vaccinated)
- 7-day, 14-day, and 30-day rolling averages per country
- Daily, weekly, and monthly growth rates
- Handles division by zero gracefully with np.where
"""

from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("transformation")


def calculate_case_fatality_rate(
    total_deaths: Union[pd.Series, float, int, np.ndarray],
    total_cases: Union[pd.Series, float, int, np.ndarray],
) -> Union[pd.Series, float, np.ndarray]:
    """Calculates Case Fatality Rate (CFR): (total_deaths / total_cases) * 100.

    Safely handles zero total_cases and null values by returning 0.0.
    """
    if isinstance(total_deaths, (int, float)) and isinstance(total_cases, (int, float)):
        if total_cases <= 0 or pd.isna(total_cases) or pd.isna(total_deaths):
            return 0.0
        return round((float(total_deaths) / float(total_cases)) * 100.0, 4)

    # Vectorized Series calculation
    deaths = pd.Series(total_deaths).fillna(0.0).astype(float)
    cases = pd.Series(total_cases).fillna(0.0).astype(float)

    cfr = np.where(cases > 0, (deaths / cases) * 100.0, 0.0)
    # CFR cannot logically exceed 100% in consistent cumulative reporting
    cfr = np.clip(cfr, 0.0, 100.0)
    return pd.Series(cfr, index=deaths.index).round(4)


def calculate_per_capita_metrics(
    metric_series: pd.Series,
    population_series: pd.Series,
    multiplier: float = 100000.0,
) -> pd.Series:
    """Calculates population-normalized metrics (e.g., cases or deaths per 100,000 population)."""
    metric = pd.Series(metric_series).fillna(0.0).astype(float)
    pop = pd.Series(population_series).fillna(0.0).astype(float)

    per_capita = np.where(pop > 0, (metric / pop) * multiplier, 0.0)
    return pd.Series(per_capita, index=metric.index).round(4)


def calculate_vaccination_rates(
    vaccinated: pd.Series,
    population: pd.Series,
) -> pd.Series:
    """Calculates vaccination coverage percentage: (vaccinated / population) * 100."""
    vax = pd.Series(vaccinated).fillna(0.0).astype(float)
    pop = pd.Series(population).fillna(0.0).astype(float)

    rate = np.where(pop > 0, (vax / pop) * 100.0, 0.0)
    # Clip rate to 100% max for realistic single/double dose coverage
    rate = np.clip(rate, 0.0, 100.0)
    return pd.Series(rate, index=vax.index).round(4)


def calculate_rolling_averages(
    df: pd.DataFrame,
    group_col: str = "country",
    date_col: str = "date",
    target_cols: Optional[List[str]] = None,
    windows: Optional[List[int]] = None,
) -> pd.DataFrame:
    """Calculates rolling averages grouped by country and sorted by date.

    Args:
        df: Input DataFrame.
        group_col: Entity column to group by (e.g. country).
        date_col: Timestamp column.
        target_cols: Numerical columns to compute rolling averages for.
        windows: Rolling window sizes in days (default: [7, 14, 30]).

    Returns:
        pd.DataFrame with added rolling average columns.
    """
    df = df.copy()
    if windows is None:
        windows = [7, 14, 30]

    if target_cols is None:
        target_cols = [c for c in ["new_cases", "new_deaths", "new_vaccinations"] if c in df.columns]

    # Ensure sorted by group and date
    df = df.sort_values(by=[group_col, date_col]).reset_index(drop=True)

    for target in target_cols:
        for w in windows:
            col_name = f"{w}_day_{target}_avg" if not target.startswith("new_") else f"{w}_day_{target.replace('new_', '')}_avg"
            df[col_name] = (
                df.groupby(group_col, observed=True)[target]
                .transform(lambda s: s.rolling(window=w, min_periods=1).mean())
                .round(2)
            )

    logger.info(f"Calculated rolling averages for {target_cols} over windows {windows}.")
    return df


def calculate_growth_rates(
    df: pd.DataFrame,
    group_col: str = "country",
    date_col: str = "date",
    metric_col: str = "7_day_cases_avg",
) -> pd.DataFrame:
    """Calculates daily, weekly (7-day lag), and monthly (30-day lag) percentage growth rates."""
    df = df.copy()
    if metric_col not in df.columns:
        if "new_cases" in df.columns:
            metric_col = "new_cases"
        else:
            return df

    df = df.sort_values(by=[group_col, date_col]).reset_index(drop=True)

    # Daily growth rate
    df["daily_growth_rate"] = (
        df.groupby(group_col, observed=True)[metric_col]
        .pct_change(periods=1, fill_method=None)
        .replace([np.inf, -np.inf], 0.0)
        .fillna(0.0)
        * 100.0
    ).round(2)

    # Weekly growth rate (7 periods)
    df["weekly_growth_rate"] = (
        df.groupby(group_col, observed=True)[metric_col]
        .pct_change(periods=7, fill_method=None)
        .replace([np.inf, -np.inf], 0.0)
        .fillna(0.0)
        * 100.0
    ).round(2)

    # Monthly growth rate (30 periods)
    df["monthly_growth_rate"] = (
        df.groupby(group_col, observed=True)[metric_col]
        .pct_change(periods=30, fill_method=None)
        .replace([np.inf, -np.inf], 0.0)
        .fillna(0.0)
        * 100.0
    ).round(2)

    return df


def transform_covid_data(
    df: pd.DataFrame,
    output_dir: Optional[Union[str, Path]] = "data/processed",
) -> pd.DataFrame:
    """Master feature transformation pipeline.

    Calculates:
    - case_fatality_rate
    - death_rate
    - cases_per_100k
    - deaths_per_100k
    - vaccination_rate
    - fully_vaccinated_rate
    - 7-day, 14-day, 30-day rolling averages
    - growth rates

    Saves processed outputs to data/processed/covid_processed.parquet and covid_processed.csv.
    """
    logger.info(f"Starting feature transformation on {len(df):,} records...")
    df = df.copy()

    # 1. CFR
    if "total_deaths" in df.columns and "total_cases" in df.columns:
        df["case_fatality_rate"] = calculate_case_fatality_rate(df["total_deaths"], df["total_cases"])

    # 2. Population-normalized metrics
    if "population" in df.columns:
        if "total_deaths" in df.columns:
            df["death_rate"] = calculate_per_capita_metrics(df["total_deaths"], df["population"], multiplier=100.0)
            df["deaths_per_100k"] = calculate_per_capita_metrics(df["total_deaths"], df["population"], multiplier=100000.0)
        if "total_cases" in df.columns:
            df["cases_per_100k"] = calculate_per_capita_metrics(df["total_cases"], df["population"], multiplier=100000.0)

        # 3. Vaccination Rates
        if "people_vaccinated" in df.columns:
            df["vaccination_rate"] = calculate_vaccination_rates(df["people_vaccinated"], df["population"])
        if "people_fully_vaccinated" in df.columns:
            df["fully_vaccinated_rate"] = calculate_vaccination_rates(df["people_fully_vaccinated"], df["population"])

    # 4. Rolling Averages
    country_col = "country" if "country" in df.columns else "location"
    df = calculate_rolling_averages(
        df,
        group_col=country_col,
        date_col="date",
        target_cols=[c for c in ["new_cases", "new_deaths"] if c in df.columns],
        windows=[7, 14, 30],
    )

    # 5. Growth Rates
    df = calculate_growth_rates(df, group_col=country_col, date_col="date", metric_col="7_day_cases_avg")

    # 6. Embedded Data Attribution
    df["data_curator"] = "Himanshu Bagde"
    df["data_engineer"] = "Himanshu Bagde"

    # 7. Save Processed Artifacts
    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        parquet_path = out_dir / "covid_processed.parquet"
        csv_path = out_dir / "covid_processed.csv"

        try:
            df.to_parquet(parquet_path, index=False, compression="snappy")
            logger.info(f"Exported processed data to Parquet: {parquet_path}")
        except Exception as e:
            logger.warning(f"Could not save parquet: {e}")

        # Export CSV for universal tool compatibility
        df.to_csv(csv_path, index=False)
        logger.info(f"Exported processed data to CSV: {csv_path} ({len(df):,} records).")

    logger.info("Feature engineering & transformation pipeline successfully completed.")
    return df
