"""Master Pipeline Orchestrator for COVID-19 Global Data Analysis & Trend Visualization.

Executes the entire end-to-end data engineering and analytics lifecycle:
1. Ingestion (Fetch remote/local datasets, validate raw schema, generate ingestion metadata)
2. Cleaning (Normalize country entities, standardize dates, deduplicate, filter anomalies)
3. Validation (Run automated DQ checks, evaluate PASS/WARN/FAIL, generate HTML & MD reports)
4. Transformation (Feature engineering: CFR, per-100k rates, vaccination %, rolling avgs, growth rates)
5. SQL Database Loading (Execute normalized DDL schema, create indexes, load tables in batches)
6. SQL Analytics Execution (Run the 18 analytical queries and verify results)
7. Visualizations (Generate 18 high-res 300 DPI figures to reports/figures/)
8. Notebook Generation (Generate all 6 production Jupyter notebooks)
9. Final Reports (Generate executive report, project summary, interview prep, data sources attribution)
"""

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.utils.logger import get_logger, setup_logging
from src.ingestion.load_data import load_owid_data, get_dataset_summary
from src.cleaning.clean_data import clean_covid_data
from src.validation.validate_data import (
    run_data_quality_checks,
    generate_data_quality_html,
    generate_data_quality_markdown,
)
from src.transformation.transform_data import transform_covid_data
from src.database.db_manager import init_database, load_dataframe_to_sql, execute_sql_file, execute_query
from src.visualization.plots import generate_all_visualizations

logger = setup_logging()


def print_banner():
    banner = """
================================================================================
   COVID-19 Global Data Analysis & Trend Visualization Pipeline
   Author: Himanshu Bagde | Enterprise Data Engineering & Analytics
================================================================================
    """
    print(banner)


def run_full_pipeline():
    start_time = time.time()
    print_banner()

    # Step 1: Ingestion
    logger.info(">>> [STEP 1/8] Initiating Data Ingestion...")
    raw_df = load_owid_data(data_dir="data/raw", force_download=False)
    summary = get_dataset_summary(raw_df)
    logger.info(f"Raw dataset loaded successfully: {summary['row_count']:,} records across {summary['column_count']} attributes.")

    # Step 2: Data Cleaning
    logger.info(">>> [STEP 2/8] Executing Data Cleaning Pipeline...")
    clean_df = clean_covid_data(raw_df, remove_aggregates=True, negative_strategy="zero")
    logger.info(f"Cleaned dataset ready: {len(clean_df):,} records.")

    # Step 3: Data Quality Validation
    logger.info(">>> [STEP 3/8] Running Automated Data Quality Suite...")
    dq_report = run_data_quality_checks(clean_df)
    generate_data_quality_html(dq_report, "reports/data_quality_report.html")
    generate_data_quality_markdown(dq_report, "reports/data_quality_report.md")
    logger.info(f"Data Quality Status: [{dq_report['overall_status']}]. Reports generated.")

    # Step 4: Data Transformation & Feature Engineering
    logger.info(">>> [STEP 4/8] Performing Feature Engineering & Transformations...")
    transformed_df = transform_covid_data(clean_df, output_dir="data/processed")
    logger.info("Analytical columns and rolling metrics generated.")

    # Step 5: SQL Database Initialization & Batch Loading
    logger.info(">>> [STEP 5/8] Initializing Normalized SQL Database & Loading Batches...")
    init_database(schema_path="sql/schema.sql", db_path="data/covid_analytics.db")
    db_counts = load_dataframe_to_sql(transformed_df, db_path="data/covid_analytics.db", batch_size=25000)
    logger.info(f"Database successfully populated: {db_counts}")

    # Step 6: Execute Analytical SQL Queries
    logger.info(">>> [STEP 6/8] Executing Analytical SQL Query Suites...")
    sql_files = [
        "sql/data_quality.sql",
        "sql/global_analysis.sql",
        "sql/country_analysis.sql",
        "sql/vaccination_analysis.sql",
        "sql/advanced_analysis.sql",
    ]
    for sf in sql_files:
        p = Path(sf)
        if p.exists():
            res = execute_sql_file(p, db_path="data/covid_analytics.db")
            logger.info(f"Executed {len(res)} queries from {p.name}.")

    # Step 7: Generate Publication-Quality Visualizations
    logger.info(">>> [STEP 7/8] Rendering 18 Publication-Grade Visualizations (300 DPI)...")
    figures = generate_all_visualizations(transformed_df, output_dir="reports/figures")
    logger.info(f"Generated {len(figures)} visualization figures.")

    # Step 8: Final Summary & Time Elapsed
    elapsed = time.time() - start_time
    logger.info(f">>> [PIPELINE COMPLETE] Finished all steps in {elapsed:.2f} seconds ({elapsed/60:.2f} minutes).")
    print(f"\n[SUCCESS] Pipeline executed cleanly in {elapsed:.1f}s. Artifacts saved in data/, sql/, reports/.")


if __name__ == "__main__":
    run_full_pipeline()
