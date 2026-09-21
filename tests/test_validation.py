"""Unit tests for automated data quality checks."""

import pandas as pd
import pytest

from src.validation.validate_data import run_data_quality_checks


def test_run_data_quality_checks_pass():
    df = pd.DataFrame({
        "country": [f"Country_{i}" for i in range(160)],
        "date": ["2021-01-01"] * 160,
        "new_cases": [10.0] * 160,
        "new_deaths": [1.0] * 160,
        "total_cases": [100.0] * 160,
        "total_deaths": [5.0] * 160,
        "population": [1000000] * 160,
    })
    report = run_data_quality_checks(df, min_countries=150)
    assert report["overall_status"] == "PASS"
    assert report["total_records"] == 160
    assert report["distinct_countries"] == 160
    assert report["duplicate_country_date"] == 0


def test_run_data_quality_checks_duplicate_fail():
    df = pd.DataFrame({
        "country": ["India", "India"],
        "date": ["2021-01-01", "2021-01-01"],
        "new_cases": [100.0, 100.0],
        "new_deaths": [2.0, 2.0],
    })
    report = run_data_quality_checks(df, min_countries=1)
    assert report["duplicate_country_date"] == 1
    # Duplicate country-date is HIGH severity, fails the check
    assert report["overall_status"] == "FAIL"


def test_run_data_quality_checks_negative_warn():
    df = pd.DataFrame({
        "country": ["USA"],
        "date": ["2021-01-01"],
        "new_cases": [-50.0],
        "new_deaths": [0.0],
    })
    report = run_data_quality_checks(df, min_countries=1)
    assert any(c["name"] == "Negative New Cases" and c["status"] == "WARN" for c in report["checks"])
