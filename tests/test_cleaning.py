"""Unit tests for data cleaning module."""

import numpy as np
import pandas as pd
import pytest

from src.cleaning.clean_data import (
    clean_column_names,
    handle_missing_values,
    remove_duplicates,
    standardize_country_names,
    validate_dates,
    validate_numeric_columns,
)


def test_clean_column_names():
    df = pd.DataFrame(columns=["Country/Region", "New-Cases", " Total Deaths "])
    cleaned = clean_column_names(df)
    assert list(cleaned.columns) == ["country_region", "new_cases", "total_deaths"]


def test_standardize_country_names():
    df = pd.DataFrame({
        "location": ["US", "USA", "UK", "Great Britain", "Czechia", "South Korea", " France "]
    })
    standardized = standardize_country_names(df, country_col="location")
    expected = [
        "United States",
        "United States",
        "United Kingdom",
        "United Kingdom",
        "Czech Republic",
        "South Korea",
        "France",
    ]
    assert standardized["location"].tolist() == expected


def test_validate_dates():
    df = pd.DataFrame({
        "date": ["2021-01-01", "2021/05/15", "invalid_date", "2022-12-31"]
    })
    cleaned = validate_dates(df, date_col="date", drop_invalid=True)
    assert len(cleaned) == 3
    assert cleaned["date"].tolist() == ["2021-01-01", "2021-05-15", "2022-12-31"]


def test_remove_duplicates():
    df = pd.DataFrame({
        "location": ["India", "India", "India"],
        "date": ["2021-01-01", "2021-01-01", "2021-01-02"],
        "new_cases": [100, 150, 200]
    })
    deduped = remove_duplicates(df, subset=["location", "date"], keep="last")
    assert len(deduped) == 2
    assert deduped.iloc[0]["new_cases"] == 150


def test_validate_numeric_columns_negative_strategy():
    df = pd.DataFrame({
        "new_cases": [100.0, -25.0, 50.0],
        "new_deaths": [-5.0, 10.0, 0.0]
    })
    cleaned = validate_numeric_columns(df, negative_strategy="zero")
    assert cleaned["new_cases"].tolist() == [100.0, 0.0, 50.0]
    assert cleaned["new_deaths"].tolist() == [0.0, 10.0, 0.0]


def test_handle_missing_values():
    df = pd.DataFrame({
        "location": ["Brazil", "Brazil", "Brazil"],
        "date": ["2020-01-01", "2020-01-02", "2020-01-03"],
        "total_cases": [10.0, np.nan, 30.0],
        "new_cases": [10.0, np.nan, 20.0],
    })
    imputed = handle_missing_values(df)
    assert imputed["total_cases"].tolist() == [10.0, 10.0, 30.0]
    assert imputed["new_cases"].tolist() == [10.0, 0.0, 20.0]
