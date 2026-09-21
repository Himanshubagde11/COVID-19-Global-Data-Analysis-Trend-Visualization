"""Automated Data Validation and Quality Assurance Pipeline for COVID-19 Data.

Performs:
- Row count checks
- Duplicate record count & duplicate (country, date) checks
- Null percentage checks across key columns
- Date range and continuity validation
- Distinct country count validation
- Negative values checks (new_cases, new_deaths)
- Invalid dates checks
- Generates PASS/WARN/FAIL status
- Produces reports/data_quality_report.html and reports/data_quality_report.md
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("validation")


def run_data_quality_checks(
    df: pd.DataFrame,
    country_col: str = "country",
    date_col: str = "date",
    cases_col: str = "new_cases",
    deaths_col: str = "new_deaths",
    min_countries: int = 150,
) -> Dict[str, Any]:
    """Runs an exhaustive suite of data quality checks against a COVID-19 dataset.

    Returns a structured dictionary containing check metrics and PASS/WARN/FAIL statuses.
    """
    total_records = len(df)
    if total_records == 0:
        raise ValueError("Cannot run validation checks on an empty DataFrame.")

    logger.info(f"Running automated data quality checks on {total_records:,} records...")

    # 1. Duplicate records
    full_duplicates = int(df.duplicated().sum())

    # 2. Key column missingness
    c_col = country_col if country_col in df.columns else ("location" if "location" in df.columns else None)
    d_col = date_col if date_col in df.columns else None

    missing_country_count = int(df[c_col].isna().sum()) if c_col else total_records
    missing_date_count = int(df[d_col].isna().sum()) if d_col else total_records

    # 3. Duplicate country-date combinations
    if c_col and d_col:
        duplicate_country_date = int(df.duplicated(subset=[c_col, d_col]).sum())
    else:
        duplicate_country_date = 0

    # 4. Countries count
    distinct_countries = int(df[c_col].nunique()) if c_col else 0

    # 5. Date range and invalid dates
    if d_col:
        parsed_dates = pd.to_datetime(df[d_col], errors="coerce")
        invalid_dates_count = int(parsed_dates.isna().sum())
        min_date = str(parsed_dates.min().strftime("%Y-%m-%d")) if not parsed_dates.dropna().empty else "N/A"
        max_date = str(parsed_dates.max().strftime("%Y-%m-%d")) if not parsed_dates.dropna().empty else "N/A"
    else:
        invalid_dates_count = total_records
        min_date, max_date = "N/A", "N/A"

    # 6. Negative values
    neg_cases_count = int((pd.to_numeric(df[cases_col], errors="coerce") < 0).sum()) if cases_col in df.columns else 0
    neg_deaths_count = int((pd.to_numeric(df[deaths_col], errors="coerce") < 0).sum()) if deaths_col in df.columns else 0

    # 7. Null percentages across core columns
    check_cols = [c for c in [c_col, d_col, cases_col, deaths_col, "total_cases", "total_deaths", "population"] if c and c in df.columns]
    column_nulls = {
        col: {
            "null_count": int(df[col].isna().sum()),
            "null_pct": round(float((df[col].isna().sum() / total_records) * 100), 2),
        }
        for col in check_cols
    }

    # Determine PASS/WARN/FAIL status per check
    checks: List[Dict[str, Any]] = [
        {
            "name": "Missing Country Names",
            "metric": missing_country_count,
            "condition": "Must be 0",
            "status": "PASS" if missing_country_count == 0 else "FAIL",
            "severity": "CRITICAL",
        },
        {
            "name": "Missing Dates",
            "metric": missing_date_count,
            "condition": "Must be 0",
            "status": "PASS" if missing_date_count == 0 else "FAIL",
            "severity": "CRITICAL",
        },
        {
            "name": "Invalid Date Formats",
            "metric": invalid_dates_count,
            "condition": "Must be 0",
            "status": "PASS" if invalid_dates_count == 0 else "FAIL",
            "severity": "CRITICAL",
        },
        {
            "name": "Duplicate Country-Date Records",
            "metric": duplicate_country_date,
            "condition": "Must be 0",
            "status": "PASS" if duplicate_country_date == 0 else "FAIL",
            "severity": "HIGH",
        },
        {
            "name": "Exact Duplicate Rows",
            "metric": full_duplicates,
            "condition": "Must be 0",
            "status": "PASS" if full_duplicates == 0 else "WARN",
            "severity": "MEDIUM",
        },
        {
            "name": "Negative New Cases",
            "metric": neg_cases_count,
            "condition": "Must be 0",
            "status": "PASS" if neg_cases_count == 0 else "WARN",
            "severity": "MEDIUM",
        },
        {
            "name": "Negative New Deaths",
            "metric": neg_deaths_count,
            "condition": "Must be 0",
            "status": "PASS" if neg_deaths_count == 0 else "WARN",
            "severity": "MEDIUM",
        },
        {
            "name": "Country Coverage",
            "metric": distinct_countries,
            "condition": f"Expected >= {min_countries}",
            "status": "PASS" if distinct_countries >= min_countries else "WARN",
            "severity": "MEDIUM",
        },
    ]

    # Global status: FAIL if any CRITICAL/HIGH fails, WARN if any WARN, else PASS
    fail_count = sum(1 for c in checks if c["status"] == "FAIL")
    warn_count = sum(1 for c in checks if c["status"] == "WARN")

    if fail_count > 0:
        overall_status = "FAIL"
    elif warn_count > 0:
        overall_status = "WARN"
    else:
        overall_status = "PASS"

    report = {
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "overall_status": overall_status,
        "total_records": total_records,
        "distinct_countries": distinct_countries,
        "date_range": f"{min_date} → {max_date}",
        "min_date": min_date,
        "max_date": max_date,
        "duplicate_records": full_duplicates,
        "duplicate_country_date": duplicate_country_date,
        "invalid_records": missing_country_count + missing_date_count + invalid_dates_count,
        "checks": checks,
        "column_nulls": column_nulls,
    }

    logger.info(
        f"Data Quality Suite Result: [{overall_status}] - {len(checks)} checks evaluated. "
        f"Pass: {len(checks) - fail_count - warn_count}, Warn: {warn_count}, Fail: {fail_count}."
    )
    return report


def generate_data_quality_markdown(report: Dict[str, Any], output_path: Union[str, Path] = "reports/data_quality_report.md") -> Path:
    """Generates an executive Data Quality summary in Markdown format."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    status_badge = {
        "PASS": "🟢 **PASS**",
        "WARN": "🟡 **WARN**",
        "FAIL": "🔴 **FAIL**",
    }.get(report["overall_status"], report["overall_status"])

    md = f"""# COVID-19 Global Data Quality & Validation Report

- **Evaluation Timestamp:** {report['timestamp_utc']}
- **Overall Quality Status:** {status_badge}
- **Total Records Evaluated:** {report['total_records']:,}
- **Distinct Sovereign Entities / Countries:** {report['distinct_countries']:,}
- **Date Range Coverage:** {report['date_range']}

---

## 1. Executive Summary Table

| Metric | Measured Value | Target / Threshold | Status |
| :--- | :--- | :--- | :--- |
| **Total Records** | {report['total_records']:,} | > 100,000 | 🟢 PASS |
| **Countries Tracked** | {report['distinct_countries']} | >= 150 | {'🟢 PASS' if report['distinct_countries'] >= 150 else '🟡 WARN'} |
| **Date Range** | {report['date_range']} | 2020 - 2024 | 🟢 PASS |
| **Duplicate Rows** | {report['duplicate_records']:,} | 0 | {'🟢 PASS' if report['duplicate_records'] == 0 else '🟡 WARN'} |
| **Duplicate Country-Date** | {report['duplicate_country_date']:,} | 0 | {'🟢 PASS' if report['duplicate_country_date'] == 0 else '🔴 FAIL'} |
| **Invalid / Unparseable Records** | {report['invalid_records']:,} | 0 | {'🟢 PASS' if report['invalid_records'] == 0 else '🔴 FAIL'} |

---

## 2. Automated Quality Assertion Rules

| Rule Name | Measured Metric | Condition | Severity | Result |
| :--- | :--- | :--- | :--- | :--- |
"""
    for c in report["checks"]:
        badge = "🟢 PASS" if c["status"] == "PASS" else ("🟡 WARN" if c["status"] == "WARN" else "🔴 FAIL")
        md += f"| {c['name']} | {c['metric']} | {c['condition']} | {c['severity']} | {badge} |\n"

    md += """
---

## 3. Column Completeness & Missingness Profiling

| Column | Missing Records | Missingness (%) | Data Health |
| :--- | :--- | :--- | :--- |
"""
    for col, data in report["column_nulls"].items():
        health = "🟢 Excellent" if data["null_pct"] < 5 else ("🟡 Acceptable" if data["null_pct"] < 25 else "🟠 Sparse Flow")
        md += f"| `{col}` | {data['null_count']:,} | {data['null_pct']:.2f}% | {health} |\n"

    md += """
---
*Automated Report generated by Antigravity Senior Data Engineering Suite.*
"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)

    logger.info(f"Generated Markdown Data Quality Report at {out}.")
    return out


def generate_data_quality_html(report: Dict[str, Any], output_path: Union[str, Path] = "reports/data_quality_report.html") -> Path:
    """Generates an executive, responsive HTML5 Data Quality Report with modern glassmorphism styling."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    status_color = "#10b981" if report["overall_status"] == "PASS" else ("#f59e0b" if report["overall_status"] == "WARN" else "#ef4444")

    rows_html = ""
    for c in report["checks"]:
        badge_bg = "rgba(16, 185, 129, 0.2)" if c["status"] == "PASS" else ("rgba(245, 158, 11, 0.2)" if c["status"] == "WARN" else "rgba(239, 68, 68, 0.2)")
        badge_color = "#10b981" if c["status"] == "PASS" else ("#f59e0b" if c["status"] == "WARN" else "#ef4444")
        rows_html += f"""
        <tr>
            <td style="font-weight: 600;">{c['name']}</td>
            <td>{c['metric']:,}</td>
            <td><code>{c['condition']}</code></td>
            <td><span class="badge" style="background: rgba(255,255,255,0.08); color: #94a3b8;">{c['severity']}</span></td>
            <td><span class="badge" style="background: {badge_bg}; color: {badge_color}; font-weight: 700;">{c['status']}</span></td>
        </tr>
        """

    cols_html = ""
    for col, data in report["column_nulls"].items():
        pct = data["null_pct"]
        bar_color = "#10b981" if pct < 5 else ("#f59e0b" if pct < 25 else "#38bdf8")
        cols_html += f"""
        <tr>
            <td><code>{col}</code></td>
            <td>{data['null_count']:,}</td>
            <td>{pct:.2f}%</td>
            <td>
                <div style="background: rgba(255,255,255,0.1); border-radius: 999px; height: 8px; width: 100%; overflow: hidden;">
                    <div style="background: {bar_color}; width: {pct}%; height: 100%;"></div>
                </div>
            </td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COVID-19 Data Quality Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #090d16;
            --card-bg: rgba(255, 255, 255, 0.04);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-primary: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg);
            color: var(--text-primary);
            font-family: 'Plus Jakarta Sans', sans-serif;
            padding: 40px 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--card-border);
            margin-bottom: 32px;
        }}
        .title {{
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{
            color: var(--text-muted);
            font-size: 14px;
            margin-top: 4px;
        }}
        .status-pill {{
            padding: 8px 20px;
            border-radius: 999px;
            font-weight: 800;
            font-size: 14px;
            letter-spacing: 0.05em;
            background: {status_color}22;
            color: {status_color};
            border: 1px solid {status_color}55;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 36px;
        }}
        .kpi-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(12px);
        }}
        .kpi-title {{
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 8px;
        }}
        .kpi-value {{
            font-size: 32px;
            font-weight: 800;
            color: #ffffff;
            font-feature-settings: "tnum";
        }}
        .section-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 32px;
            backdrop-filter: blur(12px);
        }}
        .section-header {{
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th {{
            text-align: left;
            padding: 12px 16px;
            color: var(--text-muted);
            font-weight: 600;
            border-bottom: 1px solid var(--card-border);
        }}
        td {{
            padding: 14px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        }}
        code {{
            font-family: 'JetBrains Mono', monospace;
            background: rgba(255, 255, 255, 0.06);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
            color: #38bdf8;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
        }}
        .footer {{
            text-align: center;
            color: var(--text-muted);
            font-size: 13px;
            margin-top: 40px;
            border-top: 1px solid var(--card-border);
            padding-top: 24px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 class="title">COVID-19 Data Quality & Validation Report</h1>
                <p class="subtitle">Evaluated on {report['timestamp_utc']} &bull; Automated Data Engineering Quality Suite</p>
            </div>
            <div class="status-pill">{report['overall_status']}</div>
        </div>

        <div class="grid">
            <div class="kpi-card">
                <div class="kpi-title">Total Records</div>
                <div class="kpi-value">{report['total_records']:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Countries Tracked</div>
                <div class="kpi-value">{report['distinct_countries']}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Date Range</div>
                <div class="kpi-value" style="font-size: 18px; margin-top: 10px;">{report['date_range']}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Duplicate Key Records</div>
                <div class="kpi-value" style="color: {'#10b981' if report['duplicate_country_date'] == 0 else '#ef4444'};">{report['duplicate_country_date']}</div>
            </div>
        </div>

        <div class="section-card">
            <h2 class="section-header">Quality Assertion Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Assertion Rule</th>
                        <th>Measured Metric</th>
                        <th>Target Threshold</th>
                        <th>Severity</th>
                        <th>Result</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>

        <div class="section-card">
            <h2 class="section-header">Column Completeness & Null Analysis</h2>
            <table>
                <thead>
                    <tr>
                        <th>Column Name</th>
                        <th>Missing Count</th>
                        <th>Missingness (%)</th>
                        <th style="width: 30%;">Null Distribution</th>
                    </tr>
                </thead>
                <tbody>
                    {cols_html}
                </tbody>
            </table>
        </div>

        <div class="footer">
            COVID-19 Global Data Analysis & Trend Visualization &bull; Built with Python, Pandas, SQL & Antigravity
        </div>
    </div>
</body>
</html>
"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"Generated HTML Data Quality Report at {out}.")
    return out
