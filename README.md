# COVID-19 Global Data Analysis & Trend Visualization

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Database: SQLite & PostgreSQL](https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-336791.svg)](https://www.postgresql.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458.svg)](https://pandas.pydata.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25+-FF4B4B.svg)](https://streamlit.io/)
[![Tests: Pytest](https://img.shields.io/badge/Tests-15%20Passed%20(100%25)-brightgreen.svg)](https://docs.pytest.org/)
[![Data Quality: PASS](https://img.shields.io/badge/Data%20Quality-PASS%20(8%2F8%20Gates)-success.svg)](reports/data_quality_report.html)

An end-to-end, production-grade data engineering, epidemiological analytics, and interactive BI visualization system processing multi-year global COVID-19 surveillance feeds across **233 sovereign nations** and **386,000+ daily observations** (scalable to 5M+ granular records).

---

## 📑 Table of Contents
- [Executive Overview](#executive-overview)
- [Skills Demonstrated](#skills-demonstrated)
- [Architecture & Data Pipeline](#architecture--data-pipeline)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Key Analytical Metrics & Findings](#key-analytical-metrics--findings)
- [Database Architecture & SQL Queries](#database-architecture--sql-queries)
- [Automated Data Quality & Validation](#automated-data-quality--validation)
- [Interactive BI Dashboards](#interactive-bi-dashboards)
- [Publication-Grade Visualizations](#publication-grade-visualizations)
- [Installation & Setup](#installation--setup)
- [Execution Instructions](#execution-instructions)
- [Testing Suite](#testing-suite)
- [Data Limitations & Technical Challenges](#data-limitations--technical-challenges)
- [Author & Attribution](#author--attribution)

---

## 🌟 Executive Overview

During public health crises, raw surveillance datasets suffer from severe inconsistencies: retrospective negative adjustments, unharmonized geopolitical naming, weekend administrative reporting pauses, and disparate demographic controls.

This project delivers a resilient, modular data platform that:
1. **Ingests** global feeds from Our World in Data (OWID), WHO, and Johns Hopkins CSSE with automated schema auditing.
2. **Cleans & Sanitizes** messy records (harmonizing 9,000+ country entity variations and resolving duplicate reporting keys).
3. **Validates** data hygiene using an automated 8-gate quality suite generating interactive HTML compliance reports.
4. **Transforms** raw figures into epidemiological indicators (Case Fatality Rate, population-adjusted rates per 100k, 7/14/30-day windowed rolling averages, and growth velocities).
5. **Persists** processed data into a normalized 3NF relational data warehouse with composite B-tree indexing.
6. **Analyzes & Visualizes** longitudinal trends, wave inflection points, and vaccine decoupling via 25 production SQL queries, 18 high-resolution charts (300 DPI), and an interactive Streamlit BI dashboard.

---

## 🛠️ Skills Demonstrated

| Competency Area | Tools & Techniques Implemented |
| :--- | :--- |
| **Python & Software Engineering** | Modular OOP architecture, type hints, docstrings, centralized logging (`pipeline.log`), exception management. |
| **Data Cleaning & Hygiene** | Canonical entity mapping, ISO-8601 validation, deduplication, negative flow remediation, domain imputation. |
| **Data Quality & Governance** | Automated assertion suite, threshold gating, PASS/WARN/FAIL compliance reporting in HTML and Markdown. |
| **Data Warehousing & SQL** | Normalized 3NF schema, primary/foreign keys, B-tree indexes, CTEs, Window Functions (`DENSE_RANK`, `LAG`, `AVG OVER`). |
| **Time-Series & Epidemiology** | Multi-window rolling averages (7/14/30d), topological peak detection (`scipy.signal.find_peaks`), wave modeling. |
| **Data Visualization & BI** | Matplotlib & Seaborn publication styling (300 DPI), Streamlit dashboard, glassmorphic standalone web dashboard. |
| **Automated Testing & CI/CD** | 15 deterministic unit tests with `pytest` covering metrics, division-by-zero resilience, and data hygiene. |

---

## 🏗️ Architecture & Data Pipeline

```
Raw Sources (OWID / WHO / JHU)
               │
               ▼
┌─────────────────────────────────────────┐
│     1. Ingestion Layer (Stream/Chunk)   │  ──> Preserves Raw Data (data/raw/)
└─────────────────────────────────────────┘      Generates Ingestion Metadata JSON
               │
               ▼
┌─────────────────────────────────────────┐
│     2. Data Cleaning & Normalization    │  ──> Harmonizes 9k+ Country Aliases
└─────────────────────────────────────────┘      Smooths Retrospective Negative Flows
               │
               ▼
┌─────────────────────────────────────────┐
│     3. Automated Data Quality Gates     │  ──> 8 Automated Quality Rules
└─────────────────────────────────────────┘      Generates HTML/MD Audit Reports
               │
               ▼
┌─────────────────────────────────────────┐
│     4. Transformation & Feature Engine  │  ──> CFR, Per-100k, 7/14/30d Rolling Avgs
└─────────────────────────────────────────┘      Exports Parquet & CSV to data/processed/
               │
               ▼
┌─────────────────────────────────────────┐
│     5. Relational Data Warehouse        │  ──> Normalized Schema (regions, countries,
└─────────────────────────────────────────┘      daily_stats, vax_stats) with Indexes
               │
               ▼
┌─────────────────────────────────────────┐
│     6. Analytics, Visuals & BI Dash     │  ──> 25 SQL Analytical Queries
└─────────────────────────────────────────┘      18 Publication Plots & Streamlit BI
```

---

## 💻 Tech Stack

- **Core Language:** Python 3.10+ (Tested through Python 3.14)
- **Data Manipulation:** Pandas 2.0+, NumPy 1.24+
- **Database Engine:** SQLite 3 (Default zero-dependency WAL-mode warehouse) & PostgreSQL compatible
- **Mathematical & Signal Modeling:** SciPy (Topological peak prominence detection)
- **Visual Analytics:** Matplotlib 3.7+, Seaborn 0.12+, Altair 5.0+
- **Interactive Dashboards:** Streamlit 1.25+, HTML5/CSS3 with Chart.js
- **Testing & Quality:** Pytest 7.3+, Automated HTML Report Engine
- **Data Formats:** Apache Parquet (Snappy compressed), CSV, JSON, SQLite

---

## 📁 Repository Structure

```
COVID-19-Global-Data-Analysis-Trend-Visualization/
├── config/
│   ├── config.yaml                 # Centralized configuration (paths, windows, thresholds)
│   └── .env.example                # Template for database credentials and env settings
├── data/
│   ├── raw/                        # Raw, immutable upstream data (owid-covid-data.csv)
│   ├── processed/                  # Transformed datasets (covid_processed.parquet & .csv)
│   └── covid_analytics.db          # Normalized SQLite relational database
├── src/
│   ├── ingestion/
│   │   └── load_data.py            # Stream loaders, remote fetchers, schema auditor
│   ├── cleaning/
│   │   └── clean_data.py           # Country normalization, date validation, negative smoothing
│   ├── validation/
│   │   └── validate_data.py        # Automated DQ suite, PASS/WARN/FAIL reporting
│   ├── transformation/
│   │   └── transform_data.py       # CFR, per-100k rates, rolling averages, growth rates
│   ├── database/
│   │   └── db_manager.py           # Relational schema DDL runner, WAL-mode batch loader
│   ├── analytics/
│   │   ├── statistical_analysis.py # Parametric & non-parametric statistics, correlation matrix
│   │   └── time_series.py          # Rolling windows, wave peak detection, trajectory alignment
│   ├── visualization/
│   │   └── plots.py                # 18 publication-quality figures at 300 DPI
│   └── utils/
│       ├── logger.py               # Centralized logging configuration
│       └── generate_notebooks.py   # Automated generator for all 6 Jupyter notebooks
├── sql/
│   ├── schema.sql                  # Normalized 3NF DDL with primary/foreign keys & indexes
│   ├── data_quality.sql            # Integrity audit queries (orphaned keys, non-monotonic drops)
│   ├── global_analysis.sql         # Global daily/monthly totals, windowed rolling sums
│   ├── country_analysis.sql        # Country rankings, DENSE_RANK(), CFR leaderboards
│   ├── vaccination_analysis.sql    # Rollout velocity, LAG() 30-day progression, coverage tiers
│   └── advanced_analysis.sql       # Month-over-Month (MoM) growth rates, Day-0 alignment
├── notebooks/
│   ├── 01_data_exploration.ipynb   # Raw schema, dimensional shapes, missingness profiling
│   ├── 02_data_cleaning.ipynb      # Step-by-step cleaning, entity mapping, deduplication
│   ├── 03_eda.ipynb                # Distribution analysis, regional breakdown, correlations
│   ├── 04_time_series_analysis.ipynb # Rolling averages, wave peaks, inflection points
│   ├── 05_vaccination_analysis.ipynb # Vaccine coverage velocity vs mortality decoupling
│   └── 06_final_insights.ipynb     # Executive synthesis, limitations, strategic conclusions
├── dashboards/
│   ├── app.py                      # Interactive Streamlit analytics application
│   └── index.html                  # Standalone zero-dependency HTML5/Chart.js dashboard
├── reports/
│   ├── figures/                    # 18 exported high-resolution PNG charts (300 DPI)
│   ├── data_quality_report.html    # Interactive HTML Data Quality compliance report
│   ├── data_quality_report.md      # Markdown Data Quality audit report
│   ├── final_report.md             # Comprehensive 14-section epidemiological report
│   ├── project_summary.md          # Resume and LinkedIn executive summary
│   └── interview_questions.md      # 30 technical interview Q&As grounded in this project
├── tests/
│   ├── test_cleaning.py            # Unit tests for country normalization and data hygiene
│   ├── test_metrics.py             # Unit tests for CFR, rates per 100k, rolling avgs
│   └── test_validation.py         # Unit tests for quality thresholds and assertion rules
├── logs/
│   └── pipeline.log                # System execution log
├── run_pipeline.py                 # Master end-to-end execution script
├── requirements.txt                # Pinned production dependencies
├── DATA_SOURCES.md                 # Full dataset attribution, methodology, and licensing
├── LICENSE                         # MIT open source license
└── README.md                       # Main project documentation
```

---

## 📈 Key Analytical Metrics & Findings

All figures calculated directly from verified data:

| Metric | Measured Value | Significance |
| :--- | :--- | :--- |
| **Sovereign Entities Analyzed** | **233 Sovereign States** | Complete global coverage excluding non-country aggregates |
| **Cumulative Global Cases** | **763,238,764** | Total laboratory-confirmed infections |
| **Cumulative Attributed Deaths** | **6,997,955** | Attributed clinical mortality |
| **Global Aggregate CFR** | **0.92%** | Case Fatality Rate: $(\text{Total Deaths} / \text{Total Cases}) \times 100$ |
| **Total Vaccinated (&ge;1 Dose)** | **5.62 Billion** | ~70.5% of monitored global population |
| **Fully Vaccinated (Primary Series)**| **5.18 Billion** | ~65.1% complete primary coverage |

### Top 5 Nations by Cumulative Infection Burden:
1. **United States:** 103,436,829 cases | 1,193,165 deaths | 1.15% CFR
2. **China:** 99,373,219 cases | 122,304 deaths | 0.12% CFR
3. **India:** 45,041,748 cases | 533,623 deaths | 1.18% CFR
4. **France:** 38,997,490 cases | 168,091 deaths | 0.43% CFR
5. **Germany:** 38,437,756 cases | 174,979 deaths | 0.46% CFR

---

## 🗄️ Database Architecture & SQL Queries

The database is built on a normalized 3NF schema in `data/covid_analytics.db`:

```sql
-- Sample DDL extract from sql/schema.sql
CREATE TABLE countries (
    country_id INTEGER PRIMARY KEY,
    iso_code VARCHAR(10),
    country_name VARCHAR(150) NOT NULL UNIQUE,
    region_id INTEGER,
    population BIGINT,
    population_density NUMERIC(10, 2),
    median_age NUMERIC(5, 2),
    FOREIGN KEY (region_id) REFERENCES regions(region_id)
);

CREATE TABLE daily_covid_stats (
    record_id INTEGER PRIMARY KEY,
    country_id INTEGER NOT NULL,
    date DATE NOT NULL,
    new_cases NUMERIC(12, 2) DEFAULT 0,
    total_cases NUMERIC(14, 2) DEFAULT 0,
    new_deaths NUMERIC(12, 2) DEFAULT 0,
    total_deaths NUMERIC(14, 2) DEFAULT 0,
    case_fatality_rate NUMERIC(6, 4) DEFAULT 0,
    cases_per_100k NUMERIC(10, 4) DEFAULT 0,
    deaths_per_100k NUMERIC(10, 4) DEFAULT 0,
    rolling_7day_cases NUMERIC(12, 2) DEFAULT 0,
    rolling_7day_deaths NUMERIC(12, 2) DEFAULT 0,
    FOREIGN KEY (country_id) REFERENCES countries(country_id)
);

CREATE INDEX idx_daily_country_date ON daily_covid_stats(country_id, date);
```

### Advanced SQL Query Showcase:
- **`sql/global_analysis.sql`:** 7-day rolling averages computed with window framing:
  ```sql
  AVG(daily_cases) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
  ```
- **`sql/country_analysis.sql`:** Multi-criteria country rankings using `DENSE_RANK()`:
  ```sql
  DENSE_RANK() OVER (ORDER BY (d.total_cases * 100000.0) / NULLIF(c.population, 0) DESC) AS case_per_capita_rank
  ```
- **`sql/vaccination_analysis.sql`:** 30-day vaccination acceleration using `LAG()`:
  ```sql
  (v.people_fully_vaccinated - LAG(v.people_fully_vaccinated, 30) OVER (PARTITION BY v.country_id ORDER BY v.date))
  ```
- **`sql/advanced_analysis.sql`:** Month-over-Month growth calculations and Day-0 outbreak alignment from 100th confirmed case.

---

## 🛡️ Automated Data Quality & Validation

The pipeline executes automated validation before database loading. View the generated report:
[Open Data Quality Report](reports/data_quality_report.html)

```
================================================================================
   DATA QUALITY SUITE RESULTS: [PASS]
================================================================================
  ✓ Missing Country Names             : 0 errors            [PASS - CRITICAL]
  ✓ Missing Dates                     : 0 errors            [PASS - CRITICAL]
  ✓ Invalid Date Formats              : 0 errors            [PASS - CRITICAL]
  ✓ Duplicate (Country, Date) Records : 0 errors            [PASS - HIGH]
  ✓ Exact Duplicate Rows              : 0 errors            [PASS - MEDIUM]
  ✓ Negative New Cases                : 0 errors            [PASS - MEDIUM]
  ✓ Negative New Deaths               : 0 errors            [PASS - MEDIUM]
  ✓ Sovereign Country Coverage        : 233 (>=150 target)  [PASS - MEDIUM]
================================================================================
```

---

## 📊 Publication-Grade Visualizations

All 18 figures are exported to `reports/figures/` at 300 DPI:

| Figure | Metric / Focus | Chart Type |
| :--- | :--- | :--- |
| `01_global_daily_cases.png` | Global Daily Reported Cases & 7-Day Trend | Time Series Dual Line |
| `02_global_daily_deaths.png` | Global Daily Attributed Mortality & Smoothed Trend | Time Series Line |
| `03_rolling_cases.png` | 7-Day Smoothed Case Curves (Top 5 Affected Nations) | Multi-Line Comparison |
| `04_rolling_deaths.png` | 7-Day Smoothed Mortality Trajectories | Multi-Line Comparison |
| `05_top_countries_cases.png` | Top 15 Sovereign Nations by Cumulative Cases | Horizontal Bar Chart |
| `06_top_countries_deaths.png` | Top 15 Sovereign Nations by Cumulative Mortality | Horizontal Bar Chart |
| `07_cfr_comparison.png` | Case Fatality Rate (CFR %) Comparison (&ge;250k Cases) | Ranked Bar Chart |
| `08_vaccination_coverage.png`| Global Single-Dose vs Fully Vaccinated Trajectory | Cumulative Area / Line |
| `09_cases_per_100k.png` | Cumulative Cases per 100k Population (Pop &ge;1M) | Per-Capita Ranked Bar |
| `10_deaths_per_100k.png` | Cumulative Deaths per 100k Population (Pop &ge;1M) | Per-Capita Ranked Bar |
| `11_country_comparisons.png`| Longitudinal Trajectory of Major World Economies | Multi-Line Plot |
| `12_regional_trends.png` | 14-Day Smoothed Regional Transmission by Continent | Continental Facet Plot |
| `13_vaccination_vs_cases.png`| Vaccination Coverage (%) vs Cumulative Cases per 100k | Bubble Scatter Plot |
| `14_vaccination_vs_deaths.png`| Vaccination Coverage (%) vs Case Fatality Rate (CFR) | Regression Scatter Plot |
| `15_monthly_cases.png` | Monthly Aggregated Global Inflow of Confirmed Cases | Monthly Bar Chart |
| `16_monthly_deaths.png` | Monthly Aggregated Global COVID-19 Mortality Inflow | Monthly Bar Chart |
| `17_pandemic_waves.png` | Wave Peak Identification using Topological Prominence | Signal Annotation Plot |
| `18_cases_heatmap.png` | Monthly Inflow Matrix Heatmap across Hardest-Hit Nations | 2D Density Heatmap |

---

## 🖥️ Interactive BI Dashboards

### Option 1: Streamlit Interactive Web Application
Launch the full interactive dashboard with KPI cards, multi-select filters, and dynamic insights:
```bash
python -m streamlit run dashboards/app.py
```

### Option 2: Standalone Zero-Dependency HTML5 Dashboard
Double-click or open `dashboards/index.html` in any web browser to view the responsive glassmorphic dashboard with Chart.js.

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.14
- Git

### 1. Clone Repository
```bash
git clone https://github.com/Himanshubagde11/COVID-19-Global-Data-Analysis-Trend-Visualization.git
cd COVID-19-Global-Data-Analysis-Trend-Visualization
```

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

---

## ⚡ Execution Instructions

### Run Master End-to-End Pipeline
Executes ingestion, cleaning, validation, transformation, SQL database loading, query execution, and visualization generation:
```bash
python run_pipeline.py
```

### Execute Jupyter Notebooks
Run the interactive analysis notebooks in order:
```bash
jupyter notebook notebooks/
```
1. `01_data_exploration.ipynb`
2. `02_data_cleaning.ipynb`
3. `03_eda.ipynb`
4. `04_time_series_analysis.ipynb`
5. `05_vaccination_analysis.ipynb`
6. `06_final_insights.ipynb`

---

## 🧪 Testing Suite

Execute the automated unit test suite with `pytest`:
```bash
python -m pytest tests/ -v
```
All 15 automated unit tests pass in under 1 second:
- `tests/test_cleaning.py`: Column snake_casing, country normalization, date parsing, deduplication, negative flow clamping.
- `tests/test_metrics.py`: CFR calculations, division-by-zero resilience, per-100k scaling, rolling averages, growth rates.
- `tests/test_validation.py`: Data quality assertions, duplicate key detection, negative flow thresholds.

---

## ⚠️ Data Limitations & Technical Challenges

1. **Ascertainment Disparities:** Confirmed cases understate true cumulative SARS-CoV-2 infections due to asymptomatic transmission and differing national testing capabilities.
2. **Mortality Definition Differences:** National registries varied between "deaths within 28 days of positive test" and clinical death certificate attribution.
3. **Transition to Weekly Reporting:** Beginning in late 2022, numerous health agencies reduced reporting frequency from daily to weekly/monthly, creating artificial discrete step-functions in daily flow time series.

---

## 👤 Author & Attribution

**Himanshu Bagde**  
- **GitHub:** [@Himanshubagde11](https://github.com/Himanshubagde11)  
- **Portfolio Project:** COVID-19 Global Data Analysis & Trend Visualization  

### Data Sources
Surveillance feeds provided under Creative Commons Attribution 4.0 by **Our World in Data (University of Oxford)**, **Johns Hopkins University (CSSE)**, and the **World Health Organization**. See [DATA_SOURCES.md](DATA_SOURCES.md) for detailed attribution and methodology.

### License
This project is licensed under the [MIT License](LICENSE).
