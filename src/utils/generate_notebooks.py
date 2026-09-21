"""Automated Notebook Generation Utility.

Constructs 6 production-grade Jupyter Notebooks:
 01_data_exploration.ipynb
 02_data_cleaning.ipynb
 03_eda.ipynb
 04_time_series_analysis.ipynb
 05_vaccination_analysis.ipynb
 06_final_insights.ipynb

Each notebook contains detailed Markdown pedagogical context, structured code cells,
and reproducible analytical workflows.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def make_notebook(cells: List[Dict[str, Any]], output_path: Path):
    """Creates and saves a valid .ipynb Jupyter notebook file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.10"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)


def md_cell(source: str) -> Dict[str, Any]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")]
    }


def code_cell(source: str) -> Dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.split("\n")]
    }


def generate_all_notebooks(notebooks_dir: str = "notebooks"):
    n_dir = Path(notebooks_dir)
    n_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------------------
    # 01_data_exploration.ipynb
    # --------------------------------------------------------------------------
    nb1_cells = [
        md_cell("""# COVID-19 Global Data Analysis: Data Exploration
## Part 1: Dataset Overview, Schema Discovery, and Data Profiling

This notebook performs initial exploratory profiling on the raw COVID-19 global dataset (sourced from Our World in Data / WHO).

### Objectives:
1. Load the raw dataset and inspect dimensional shape.
2. Examine column inventory and underlying data types.
3. Quantify missing value rates and patterns across features.
4. Detect duplicate records across spatial and temporal keys.
5. Determine global temporal bounds and country/territory coverage.
"""),
        code_cell("""import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
ROOT_DIR = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(ROOT_DIR))

from src.ingestion.load_data import load_csv, get_dataset_summary

DATA_PATH = ROOT_DIR / "data" / "raw" / "owid-covid-data.csv"
print(f"Loading raw dataset from: {DATA_PATH}")
"""),
        md_cell("### 1. Load Raw Dataset and Inspect Shape"),
        code_cell("""df_raw = load_csv(DATA_PATH)
print(f"Dataset Shape: {df_raw.shape[0]:,} rows x {df_raw.shape[1]} columns")
df_raw.head(5)
"""),
        md_cell("### 2. Column Inventory & Data Types"),
        code_cell("""summary = get_dataset_summary(df_raw)
print(f"Memory footprint: {summary['memory_usage_mb']:.2f} MB")
dtypes_df = pd.DataFrame(list(summary['data_types'].items()), columns=['Column', 'Data_Type'])
dtypes_df.head(20)
"""),
        md_cell("### 3. Missing Value Profiling"),
        code_cell("""null_df = pd.DataFrame({
    'Column': list(summary['null_counts'].keys()),
    'Null_Count': list(summary['null_counts'].values()),
    'Null_Pct': list(summary['null_percentages'].values())
}).sort_values('Null_Pct', ascending=False)

null_df.head(25)
"""),
        md_cell("### 4. Duplicate Record Analysis"),
        code_cell("""c_col = 'location' if 'location' in df_raw.columns else 'country'
d_col = 'date'

dup_keys = df_raw.duplicated(subset=[c_col, d_col]).sum()
print(f"Duplicate ({c_col}, {d_col}) pairs: {dup_keys:,}")
"""),
        md_cell("### 5. Geographic and Temporal Coverage"),
        code_cell("""distinct_locations = df_raw[c_col].nunique()
min_date = df_raw[d_col].min()
max_date = df_raw[d_col].max()

print(f"Distinct Reporting Locations: {distinct_locations}")
print(f"Temporal Window: {min_date} to {max_date}")
""")
    ]
    make_notebook(nb1_cells, n_dir / "01_data_exploration.ipynb")

    # --------------------------------------------------------------------------
    # 02_data_cleaning.ipynb
    # --------------------------------------------------------------------------
    nb2_cells = [
        md_cell("""# COVID-19 Global Data Analysis: Data Cleaning & Hygiene
## Part 2: Standardization, Missing Value Handling & Quality Validation

This notebook documents the systematic data cleaning pipeline applied to the COVID-19 dataset.

### Cleaning Decisions Documented:
1. **Column Standardization:** Transformed all column headers to `snake_case`.
2. **Entity Normalization:** Standardized country names (e.g. US/USA -> United States, UK -> United Kingdom, Czechia -> Czech Republic) and isolated national entities from continental/income-group aggregates.
3. **Date Harmonization:** Parsed dates to strict ISO 8601 (`YYYY-MM-DD`).
4. **Deduplication:** Dropped conflicting duplicates on `(country, date)`, retaining latest observations.
5. **Flow Anomaly Smoothing:** Addressed retrospective negative reporting adjustments in `new_cases` and `new_deaths`.
6. **Domain-Specific Imputation:** Forward-filled cumulative metrics per country and filled flow NaNs with 0.
"""),
        code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT_DIR = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(ROOT_DIR))

from src.ingestion.load_data import load_csv
from src.cleaning.clean_data import clean_covid_data
from src.validation.validate_data import run_data_quality_checks

DATA_PATH = ROOT_DIR / "data" / "raw" / "owid-covid-data.csv"
df_raw = load_csv(DATA_PATH)
print(f"Raw records loaded: {len(df_raw):,}")
"""),
        md_cell("### 1. Execute Production Cleaning Pipeline"),
        code_cell("""df_clean = clean_covid_data(df_raw, remove_aggregates=True, negative_strategy="zero")
print(f"Cleaned records: {len(df_clean):,}")
df_clean[['country', 'region', 'date', 'new_cases', 'total_cases', 'new_deaths', 'total_deaths']].head()
"""),
        md_cell("### 2. Verify Country Normalization"),
        code_cell("""sample_countries = ['United States', 'United Kingdom', 'South Korea', 'Czech Republic', 'Russia']
for c in sample_countries:
    count = (df_clean['country'] == c).sum()
    print(f"Canonical Country '{c}': {count:,} records found.")
"""),
        md_cell("### 3. Verify Absence of Negative Inflows"),
        code_cell("""neg_cases = (df_clean['new_cases'] < 0).sum()
neg_deaths = (df_clean['new_deaths'] < 0).sum()
print(f"Negative new_cases remaining: {neg_cases}")
print(f"Negative new_deaths remaining: {neg_deaths}")
"""),
        md_cell("### 4. Execute Automated Data Quality Assertion Suite"),
        code_cell("""dq_report = run_data_quality_checks(df_clean)
print(f"Overall DQ Status: [{dq_report['overall_status']}]")
for c in dq_report['checks']:
    print(f"- {c['name']}: {c['metric']} ({c['condition']}) -> [{c['status']}]")
""")
    ]
    make_notebook(nb2_cells, n_dir / "02_data_cleaning.ipynb")

    # --------------------------------------------------------------------------
    # 03_eda.ipynb
    # --------------------------------------------------------------------------
    nb3_cells = [
        md_cell("""# COVID-19 Global Data Analysis: Exploratory Data Analysis (EDA)
## Part 3: Distributions, Regional Disparities, and Global Burden Rankings

In this notebook, we perform deep exploratory data analysis on the validated, transformed dataset.
"""),
        code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

ROOT_DIR = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(ROOT_DIR))

from src.transformation.transform_data import transform_covid_data
from src.analytics.statistical_analysis import calculate_descriptive_stats, calculate_correlation_matrix

DATA_PATH = ROOT_DIR / "data" / "processed" / "covid_processed.csv"
df = pd.read_csv(DATA_PATH)
print(f"Loaded processed dataset: {len(df):,} records")
"""),
        md_cell("### 1. Parametric and Non-Parametric Summary Statistics"),
        code_cell("""stats_table = calculate_descriptive_stats(df)
stats_table
"""),
        md_cell("### 2. Top 15 Countries by Cumulative Infection Burden"),
        code_cell("""top_cases = df.groupby('country')['total_cases'].max().nlargest(15)
plt.figure(figsize=(10, 6))
sns.barplot(x=top_cases.values / 1e6, y=top_cases.index, palette='Blues_r')
plt.title("Top 15 Countries by Cumulative COVID-19 Cases (Millions)", fontsize=13, weight='bold')
plt.xlabel("Total Cases (Millions)")
plt.ylabel("Country")
plt.show()
"""),
        md_cell("### 3. Regional Distribution of Cases and Mortality"),
        code_cell("""regional = df.groupby('region').agg({
    'total_cases': 'max',
    'total_deaths': 'max',
    'population': 'first'
}).reset_index()

regional['cfr'] = (regional['total_deaths'] / regional['total_cases']) * 100
regional
"""),
        md_cell("### 4. Correlation Matrix across Demographic & Epidemiological Variables"),
        code_cell("""corr = calculate_correlation_matrix(df)
plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', vmin=-1, vmax=1)
plt.title("Epidemiological Correlation Matrix", fontsize=13, weight='bold')
plt.show()
""")
    ]
    make_notebook(nb3_cells, n_dir / "03_eda.ipynb")

    # --------------------------------------------------------------------------
    # 04_time_series_analysis.ipynb
    # --------------------------------------------------------------------------
    nb4_cells = [
        md_cell("""# COVID-19 Global Data Analysis: Time-Series Analysis
## Part 4: Multi-Window Rolling Averages, Wave Identification, and Growth Dynamics

This notebook examines the longitudinal time-series properties of the pandemic:
- 7-day, 14-day, and 30-day smoothing to filter weekend reporting lags.
- Empirical wave peak detection using topological prominence filtering.
- Trajectory comparisons among major global economies.
"""),
        code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT_DIR = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(ROOT_DIR))

from src.analytics.time_series import get_rolling_averages, detect_pandemic_waves, compare_country_trajectories

DATA_PATH = ROOT_DIR / "data" / "processed" / "covid_processed.csv"
df = pd.read_csv(DATA_PATH)
"""),
        md_cell("### 1. Global Multi-Window Rolling Averages"),
        code_cell("""global_ts = get_rolling_averages(df, country=None, metric_col="new_cases")

plt.figure(figsize=(12, 6))
plt.plot(global_ts.index, global_ts['new_cases'] / 1e6, alpha=0.3, label='Daily Raw Cases')
plt.plot(global_ts.index, global_ts['7d_avg'] / 1e6, label='7-Day Rolling Avg', linewidth=2)
plt.plot(global_ts.index, global_ts['30d_avg'] / 1e6, label='30-Day Rolling Avg', linewidth=2, linestyle='--')
plt.title("Global Daily Infection Inflow: Multi-Window Smoothing", fontsize=13, weight='bold')
plt.ylabel("Cases (Millions / Day)")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.show()
"""),
        md_cell("### 2. Empirical Pandemic Wave Peak Detection"),
        code_cell("""smoothed_cases = global_ts['7d_avg']
waves = detect_pandemic_waves(smoothed_cases, distance_days=60, prominence_factor=0.25)
print("Detected Global Pandemic Waves:")
waves
"""),
        md_cell("### 3. Trajectory Comparisons across Selected Economies"),
        code_cell("""benchmarks = ['United States', 'India', 'United Kingdom', 'Germany', 'Brazil']
trajectories = compare_country_trajectories(df, countries=benchmarks)

plt.figure(figsize=(12, 6))
for col in trajectories.columns:
    plt.plot(pd.to_datetime(trajectories.index), trajectories[col] / 1000, label=col, linewidth=1.8)
plt.title("Comparative 7-Day Smoothed Daily Cases (Thousands)", fontsize=13, weight='bold')
plt.ylabel("7-Day Avg Daily Cases (K)")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.show()
""")
    ]
    make_notebook(nb4_cells, n_dir / "04_time_series_analysis.ipynb")

    # --------------------------------------------------------------------------
    # 05_vaccination_analysis.ipynb
    # --------------------------------------------------------------------------
    nb5_cells = [
        md_cell("""# COVID-19 Global Data Analysis: Vaccination Dynamics
## Part 5: Rollout Velocity, Global Coverage & Mortality Decoupling

This notebook evaluates:
1. Cumulative global vaccination trajectory across doses.
2. Cross-country inequality in immunization coverage.
3. Epidemiological decoupling: The mathematical relationship between vaccination rate and Case Fatality Rate (CFR).
"""),
        code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

ROOT_DIR = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(ROOT_DIR))

DATA_PATH = ROOT_DIR / "data" / "processed" / "covid_processed.csv"
df = pd.read_csv(DATA_PATH)
df['date'] = pd.to_datetime(df['date'])
"""),
        md_cell("### 1. Global Vaccination Timeline"),
        code_cell("""global_vax = df.groupby('date')[['people_vaccinated', 'people_fully_vaccinated']].sum().reset_index()
global_vax = global_vax[global_vax['date'] >= '2020-12-01']

plt.figure(figsize=(12, 6))
plt.plot(global_vax['date'], global_vax['people_vaccinated'] / 1e9, label='At Least 1 Dose (Billions)', color='#10b981', linewidth=2.2)
plt.plot(global_vax['date'], global_vax['people_fully_vaccinated'] / 1e9, label='Fully Vaccinated (Billions)', color='#059669', linestyle='--', linewidth=2.2)
plt.title("Global Cumulative Vaccine Administration Progress", fontsize=13, weight='bold')
plt.ylabel("People Vaccinated (Billions)")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.6)
plt.show()
"""),
        md_cell("### 2. Cross-Sectional Analysis: Vaccination Coverage vs Case Fatality Rate"),
        code_cell("""latest = df[(df['population'] >= 2000000) & (df['total_cases'] >= 50000)].groupby('country').agg({
    'fully_vaccinated_rate': 'max',
    'case_fatality_rate': 'last',
    'population': 'max',
    'region': 'first'
}).dropna()

plt.figure(figsize=(10, 6))
sns.scatterplot(data=latest, x='fully_vaccinated_rate', y='case_fatality_rate', hue='region', size='population', sizes=(40, 400), alpha=0.8)
sns.regplot(data=latest, x='fully_vaccinated_rate', y='case_fatality_rate', scatter=False, color='gray', line_kws={'linestyle': '--'})
plt.title("Vaccine Coverage (%) vs Case Fatality Rate (CFR %)", fontsize=13, weight='bold')
plt.xlabel("Fully Vaccinated Rate (%)")
plt.ylabel("Case Fatality Rate (%)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.show()
""")
    ]
    make_notebook(nb5_cells, n_dir / "05_vaccination_analysis.ipynb")

    # --------------------------------------------------------------------------
    # 06_final_insights.ipynb
    # --------------------------------------------------------------------------
    nb6_cells = [
        md_cell("""# COVID-19 Global Data Analysis: Final Insights & Synthesis
## Part 6: Executive Synthesis, Limitations, and Strategic Takeaways

This concluding notebook synthesizes findings from SQL queries, statistical models, and time-series analyses.

### Key Dimensions Explored:
1. Overall Pandemic Scale & Mortality Burden.
2. Wave Severity vs Decoupling Phase.
3. Systemic Data Quality & Under-Ascertainment Limitations.
4. Strategic Lessons for Global Health Surveillance.
"""),
        code_cell("""import sys
from pathlib import Path
import pandas as pd
import sqlite3

ROOT_DIR = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(ROOT_DIR))

DB_PATH = ROOT_DIR / "data" / "covid_analytics.db"
conn = sqlite3.connect(DB_PATH)
"""),
        md_cell("### 1. Cumulative Global Epidemiological Totals from SQL Database"),
        code_cell("""query = '''
SELECT 
    COUNT(DISTINCT c.country_id) AS total_countries,
    SUM(c.population) AS monitored_population,
    MAX(d.total_cases) AS global_total_cases_approx,
    MAX(d.total_deaths) AS global_total_deaths_approx
FROM countries c
JOIN daily_covid_stats d ON c.country_id = d.country_id;
'''
pd.read_sql_query(query, conn)
"""),
        md_cell("### 2. Regional Health System Stress Metrics"),
        code_cell("""query_regional = '''
WITH LatestStats AS (
    SELECT country_id, MAX(date) AS max_date FROM daily_covid_stats GROUP BY country_id
)
SELECT 
    r.region_name,
    COUNT(DISTINCT c.country_id) AS country_count,
    ROUND(SUM(d.total_cases) / 1e6, 2) AS cases_millions,
    ROUND(SUM(d.total_deaths) / 1e3, 2) AS deaths_thousands,
    ROUND((SUM(d.total_deaths) * 100.0) / SUM(d.total_cases), 3) AS regional_cfr
FROM daily_covid_stats d
JOIN LatestStats l ON d.country_id = l.country_id AND d.date = l.max_date
JOIN countries c ON d.country_id = c.country_id
JOIN regions r ON c.region_id = r.region_id
GROUP BY r.region_name
ORDER BY cases_millions DESC;
'''
pd.read_sql_query(query_regional, conn)
"""),
        md_cell("""### 3. Synthesis of Major Findings & Known Limitations

#### Findings:
1. **Omicron Volume Apex vs Decoupling:** Winter 2021-2022 generated unprecedented daily infection spikes, but mortality remained decoupled compared to early 2020 wild-type outbreaks.
2. **Vaccination Protective Threshold:** High-income and upper-middle income nations achieving >70% vaccination observed persistent downward shifts in CFR.
3. **Surveillance Fragility:** Testing capacity dictates recorded cases; CFR in lower testing regimes is artificially elevated due to denominator under-ascertainment.

#### Data Limitations:
- Variable testing rates across countries distort raw case comparisons.
- Mortality attribution differences (excess deaths vs laboratory-confirmed deaths).
- Reporting latency, backlogs, and transitions from daily to weekly reporting in 2023–2024.
""")
    ]
    make_notebook(nb6_cells, n_dir / "06_final_insights.ipynb")
    print(f"Generated all 6 notebooks into {n_dir}.")


if __name__ == "__main__":
    generate_all_notebooks()
