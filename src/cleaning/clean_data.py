"""Data Cleaning Pipeline for COVID-19 Global Data Analysis.

Handles:
- Missing values (imputation, forward filling cumulative counters, null-flagging)
- Duplicate records & duplicate country-date records
- Invalid / unparseable dates
- Inconsistent country naming and standardization
- Negative new_cases and new_deaths (retrospective reporting revisions)
- Data type casting and memory optimization
- Anomaly filtering
"""

import re
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("cleaning")

# Canonical country name standardization map
COUNTRY_NORMALIZATION_MAP: Dict[str, str] = {
    # United States
    "US": "United States",
    "USA": "United States",
    "United States of America": "United States",
    "U.S.A.": "United States",
    "U.S.": "United States",
    # United Kingdom
    "UK": "United Kingdom",
    "U.K.": "United Kingdom",
    "Great Britain": "United Kingdom",
    "England": "United Kingdom",
    "Scotland": "United Kingdom",
    "Wales": "United Kingdom",
    "Northern Ireland": "United Kingdom",
    # South Korea
    "Korea, South": "South Korea",
    "Republic of Korea": "South Korea",
    "Korea (the Republic of)": "South Korea",
    # North Korea
    "Korea, North": "North Korea",
    "Democratic People's Republic of Korea": "North Korea",
    # Russia
    "Russian Federation": "Russia",
    # Czech Republic
    "Czechia": "Czech Republic",
    # Iran
    "Iran (Islamic Republic of)": "Iran",
    "Iran, Islamic Rep.": "Iran",
    # Syria
    "Syrian Arab Republic": "Syria",
    # Venezuela
    "Venezuela (Bolivarian Republic of)": "Venezuela",
    "Venezuela, RB": "Venezuela",
    # Vietnam
    "Viet Nam": "Vietnam",
    # Taiwan
    "Taiwan*": "Taiwan",
    "Taiwan, Province of China": "Taiwan",
    # Congo
    "Congo (Kinshasa)": "Democratic Republic of the Congo",
    "Democratic Republic of the Congo": "Democratic Republic of the Congo",
    "Congo, Dem. Rep.": "Democratic Republic of the Congo",
    "DR Congo": "Democratic Republic of the Congo",
    "Congo (Brazzaville)": "Congo",
    "Republic of the Congo": "Congo",
    "Congo, Rep.": "Congo",
    # Myanmar / Burma
    "Burma": "Myanmar",
    # Ivory Coast
    "Cote d'Ivoire": "Cote d'Ivoire",
    "Côte d'Ivoire": "Cote d'Ivoire",
    # Palestine / West Bank and Gaza
    "West Bank and Gaza": "Palestine",
    "State of Palestine": "Palestine",
    # UAE
    "United Arab Emirates": "United Arab Emirates",
    "UAE": "United Arab Emirates",
    "U.A.E.": "United Arab Emirates",
}

# Aggregate entities in OWID dataset that are not sovereign countries
NON_COUNTRY_ENTITIES = {
    "World",
    "Africa",
    "Asia",
    "Europe",
    "European Union",
    "European Union (27)",
    "North America",
    "South America",
    "Oceania",
    "High income",
    "High-income countries",
    "Upper middle income",
    "Upper-middle-income countries",
    "Lower middle income",
    "Lower-middle-income countries",
    "Low income",
    "Low-income countries",
    "International",
}


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes column names into snake_case: lowercase, stripped, and underscores for non-alphanumerics.

    Cleaning Decision:
    Standardizing column names prevents subtle bugs across SQL schemas and Python operations.
    """
    df = df.copy()
    cleaned = []
    for col in df.columns:
        c = str(col).strip().lower()
        c = re.sub(r"[\s\-/]+", "_", c)
        c = re.sub(r"[^\w]", "", c)
        c = re.sub(r"_+", "_", c).strip("_")
        cleaned.append(c)
    df.columns = cleaned
    logger.debug(f"Standardized {len(cleaned)} column names to snake_case.")
    return df


def standardize_country_names(
    df: pd.DataFrame,
    country_col: str = "location",
    remove_aggregates: bool = False,
) -> pd.DataFrame:
    """Standardizes inconsistent country names to canonical names and trims whitespace.

    Args:
        df: Input DataFrame.
        country_col: Name of country column.
        remove_aggregates: If True, filters out continent/income-group aggregates.

    Cleaning Decision:
    COVID datasets often merge 'US', 'USA', and 'United States'. Without normalization,
    country-level aggregations and joins will produce fragmented, inaccurate metrics.
    """
    df = df.copy()
    if country_col not in df.columns:
        logger.warning(f"Country column '{country_col}' not found in DataFrame.")
        return df

    # Strip whitespace
    df[country_col] = df[country_col].astype(str).str.strip()

    # Map aliases
    mapped_count = df[country_col].isin(COUNTRY_NORMALIZATION_MAP).sum()
    df[country_col] = df[country_col].replace(COUNTRY_NORMALIZATION_MAP)

    if mapped_count > 0:
        logger.info(f"Standardized country names for {mapped_count:,} records.")

    if remove_aggregates:
        initial_len = len(df)
        df = df[~df[country_col].isin(NON_COUNTRY_ENTITIES)].copy()
        logger.info(f"Filtered out {initial_len - len(df):,} aggregate non-country records.")

    return df


def validate_dates(
    df: pd.DataFrame,
    date_col: str = "date",
    drop_invalid: bool = True,
) -> pd.DataFrame:
    """Converts the date column to standard datetime (YYYY-MM-DD) and removes/flags unparseable dates.

    Cleaning Decision:
    ISO-8601 YYYY-MM-DD dates are strictly required for accurate time-series indexing,
    rolling calculations, and SQL timestamp parsing.
    """
    df = df.copy()
    if date_col not in df.columns:
        raise KeyError(f"Date column '{date_col}' missing from DataFrame.")

    initial_len = len(df)
    # Coerce unparseable strings to NaT with mixed format detection
    df[date_col] = pd.to_datetime(df[date_col], format="mixed", errors="coerce")
    invalid_dates = df[date_col].isna().sum()

    if invalid_dates > 0:
        logger.warning(f"Detected {invalid_dates:,} invalid or missing dates in '{date_col}'.")
        if drop_invalid:
            df = df.dropna(subset=[date_col]).copy()
            logger.info(f"Dropped {initial_len - len(df):,} rows with invalid dates.")

    # Format to uniform date string YYYY-MM-DD
    df[date_col] = df[date_col].dt.strftime("%Y-%m-%d")
    return df


def remove_duplicates(
    df: pd.DataFrame,
    subset: Optional[List[str]] = None,
    keep: str = "last",
) -> pd.DataFrame:
    """Identifies and drops duplicate records based on specified key columns or all columns.

    Cleaning Decision:
    Duplicate entries for the same country on the same date distort cumulative sums and rolling metrics.
    Keeping the latest record ensures updated retrospective reporting is preserved.
    """
    df = df.copy()
    if subset is None and {"location", "date"}.issubset(df.columns):
        subset = ["location", "date"]

    initial_len = len(df)
    dup_count = df.duplicated(subset=subset).sum() if subset else df.duplicated().sum()

    if dup_count > 0:
        logger.warning(f"Found {dup_count:,} duplicate rows on subset={subset}. Removing duplicates (keep='{keep}').")
        df = df.drop_duplicates(subset=subset, keep=keep).copy()
        logger.info(f"Removed {initial_len - len(df):,} duplicate records. Current rows: {len(df):,}.")
    else:
        logger.info("Zero duplicate records detected.")

    return df


def validate_numeric_columns(
    df: pd.DataFrame,
    numeric_cols: Optional[List[str]] = None,
    negative_strategy: str = "zero",
) -> pd.DataFrame:
    """Cleans numeric columns, converts them to float/int, and handles negative values.

    Args:
        df: Input DataFrame.
        numeric_cols: List of numeric columns to validate.
        negative_strategy: 'zero' (set negative values to 0), 'abs' (take absolute value),
                           or 'keep' (leave negative values unchanged).

    Cleaning Decision:
    Health authorities occasionally record negative daily cases or deaths when correcting
    prior historical overcounting (e.g. Spain, France, UK reporting revisions).
    Setting negative daily flows to 0 prevents nonsensical negative infection rates
    while preserving cumulative metrics.
    """
    df = df.copy()
    if numeric_cols is None:
        numeric_cols = [
            col for col in [
                "new_cases", "total_cases", "new_deaths", "total_deaths",
                "new_cases_smoothed", "new_deaths_smoothed",
                "people_vaccinated", "people_fully_vaccinated", "total_vaccinations",
                "population", "population_density", "median_age"
            ] if col in df.columns
        ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

        # Check for negative values in non-rate metrics
        if "new_" in col or "total_" in col or col in ["people_vaccinated", "people_fully_vaccinated"]:
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                logger.warning(f"Detected {neg_count:,} negative values in '{col}'. Applying strategy='{negative_strategy}'.")
                if negative_strategy == "zero":
                    df.loc[df[col] < 0, col] = 0.0
                elif negative_strategy == "abs":
                    df.loc[df[col] < 0, col] = df[col].abs()

    return df


def handle_missing_values(
    df: pd.DataFrame,
    cumulative_cols: Optional[List[str]] = None,
    flow_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Handles missing values with domain-specific rules:

    - Flow metrics (new_cases, new_deaths): fill NaN with 0 if cumulative metrics exist.
    - Cumulative metrics (total_cases, total_deaths, vaccinations): forward fill per country,
      then fill remaining leading NaNs with 0.
    - Demographics (population, median_age): forward fill / backward fill per country.

    Cleaning Decision:
    A country reporting zero new cases on weekends often produces NaN in raw feeds.
    Filling flow NaNs with 0 avoids falsely treating zero cases as missing observations.
    Forward-filling cumulative totals ensures cumulative counters remain monotonic.
    """
    df = df.copy()

    if cumulative_cols is None:
        cumulative_cols = [
            col for col in ["total_cases", "total_deaths", "people_vaccinated", "people_fully_vaccinated"]
            if col in df.columns
        ]

    if flow_cols is None:
        flow_cols = [
            col for col in ["new_cases", "new_deaths", "new_vaccinations"]
            if col in df.columns
        ]

    country_col = "location" if "location" in df.columns else "country"

    # Forward fill cumulative stats within each country
    if country_col in df.columns and "date" in df.columns:
        df = df.sort_values(by=[country_col, "date"]).reset_index(drop=True)
        for col in cumulative_cols:
            df[col] = df.groupby(country_col)[col].ffill().fillna(0)

        # Forward fill population and demographics per country
        demographic_cols = [c for c in ["population", "population_density", "median_age", "continent"] if c in df.columns]
        for col in demographic_cols:
            df[col] = df.groupby(country_col)[col].ffill().bfill()

    # Fill remaining flow NaNs with 0
    for col in flow_cols:
        df[col] = df[col].fillna(0.0)

    logger.info(f"Missing value imputation complete for {len(cumulative_cols)} cumulative and {len(flow_cols)} flow columns.")
    return df


def clean_covid_data(
    df: pd.DataFrame,
    remove_aggregates: bool = True,
    negative_strategy: str = "zero",
) -> pd.DataFrame:
    """Master cleaning pipeline executing all cleaning operations in sequence.

    1. Standardize column names to snake_case.
    2. Normalize country names to canonical labels.
    3. Validate and standardize date format (YYYY-MM-DD).
    4. Remove duplicate records on (country, date).
    5. Clean and validate numeric values (handle negatives).
    6. Impute domain-appropriate missing values.
    7. Optimize data types for performance.

    Returns:
        pd.DataFrame: Cleaned, standardized, production-ready DataFrame.
    """
    logger.info(f"Starting data cleaning pipeline on {len(df):,} records...")

    # Step 1: Column Names
    df = clean_column_names(df)

    # Standardize column naming if OWID vs JHU
    country_col = "location" if "location" in df.columns else "country"
    if "location" in df.columns and "country" not in df.columns:
        df["country"] = df["location"]

    region_col = "continent" if "continent" in df.columns else "region"
    if "continent" in df.columns and "region" not in df.columns:
        df["region"] = df["continent"]

    # Step 2: Country Standardization
    df = standardize_country_names(df, country_col="country", remove_aggregates=remove_aggregates)

    # Step 3: Date Validation
    df = validate_dates(df, date_col="date")

    # Step 4: Duplicate Removal
    df = remove_duplicates(df, subset=["country", "date"])

    # Step 5: Numeric Validation
    df = validate_numeric_columns(df, negative_strategy=negative_strategy)

    # Step 6: Missing Values Handling
    df = handle_missing_values(df)

    # Step 7: Data Type Optimization
    if "country" in df.columns:
        df["country"] = df["country"].astype("category")
    if "region" in df.columns:
        df["region"] = df["region"].astype("category")

    logger.info(f"Data cleaning pipeline successfully completed. Output records: {len(df):,}.")
    return df
