"""Unit tests for metrics and epidemiological transformation calculations."""

import numpy as np
import pandas as pd
import pytest

from src.transformation.transform_data import (
    calculate_case_fatality_rate,
    calculate_growth_rates,
    calculate_per_capita_metrics,
    calculate_rolling_averages,
    calculate_vaccination_rates,
)


def test_calculate_case_fatality_rate_scalar():
    # Regular CFR calculation: (20 / 1000) * 100 = 2.0%
    assert calculate_case_fatality_rate(20, 1000) == 2.0
    # Division by zero safety
    assert calculate_case_fatality_rate(0, 0) == 0.0
    assert calculate_case_fatality_rate(10, 0) == 0.0
    assert calculate_case_fatality_rate(np.nan, 100) == 0.0


def test_calculate_case_fatality_rate_series():
    deaths = pd.Series([20, 0, 50, np.nan])
    cases = pd.Series([1000, 0, 1000, 500])
    cfr = calculate_case_fatality_rate(deaths, cases)
    assert cfr.iloc[0] == 2.0
    assert cfr.iloc[1] == 0.0
    assert cfr.iloc[2] == 5.0
    assert cfr.iloc[3] == 0.0


def test_calculate_per_capita_metrics():
    # 5,000 cases in 10,000,000 population = 50 per 100,000
    metric = pd.Series([5000, 0])
    pop = pd.Series([10000000, 0])
    per_100k = calculate_per_capita_metrics(metric, pop, multiplier=100000.0)
    assert per_100k.iloc[0] == 50.0
    assert per_100k.iloc[1] == 0.0


def test_calculate_vaccination_rates():
    # 7,000,000 vaccinated in 10,000,000 population = 70.0%
    vax = pd.Series([7000000, 0])
    pop = pd.Series([10000000, 0])
    rate = calculate_vaccination_rates(vax, pop)
    assert rate.iloc[0] == 70.0
    assert rate.iloc[1] == 0.0


def test_calculate_rolling_averages():
    df = pd.DataFrame({
        "country": ["Germany"] * 7,
        "date": [f"2021-01-0{i}" for i in range(1, 8)],
        "new_cases": [10, 20, 30, 40, 50, 60, 70],
    })
    rolled = calculate_rolling_averages(df, group_col="country", date_col="date", target_cols=["new_cases"], windows=[7])
    # 7th day rolling avg of 10..70 is (280 / 7) = 40.0
    assert "7_day_cases_avg" in rolled.columns
    assert rolled.iloc[-1]["7_day_cases_avg"] == 40.0


def test_calculate_growth_rates():
    df = pd.DataFrame({
        "country": ["Canada", "Canada"],
        "date": ["2021-01-01", "2021-01-02"],
        "7_day_cases_avg": [100.0, 150.0],
    })
    growth = calculate_growth_rates(df, group_col="country", date_col="date", metric_col="7_day_cases_avg")
    assert growth.iloc[0]["daily_growth_rate"] == 0.0
    assert growth.iloc[1]["daily_growth_rate"] == 50.0
