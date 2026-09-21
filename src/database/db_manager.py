"""Database Manager for COVID-19 Analytics.

Handles:
- SQLite and PostgreSQL connection abstractions
- Schema creation from sql/schema.sql
- Normalized data loading into relational tables (regions, countries, population_stats, daily_covid_stats, vaccination_stats)
- Batch-wise high performance insertion
- SQL query execution and results extraction as pandas DataFrames
"""

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("database")


def get_db_connection(db_path: Union[str, Path] = "data/covid_analytics.db") -> sqlite3.Connection:
    """Creates or connects to the SQLite database with WAL mode and foreign keys enabled."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    # Enable WAL mode for high concurrency and performance
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_database(
    schema_path: Union[str, Path] = "sql/schema.sql",
    db_path: Union[str, Path] = "data/covid_analytics.db",
) -> None:
    """Executes schema DDL to create tables and indexes."""
    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    logger.info(f"Initializing database at {db_path} using {schema_file.name}...")
    with open(schema_file, "r", encoding="utf-8") as f:
        ddl_script = f.read()

    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.executescript(ddl_script)
        conn.commit()
        logger.info("Schema DDL executed successfully. Normalized tables and indexes created.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to execute schema DDL: {e}")
        raise
    finally:
        conn.close()


def load_dataframe_to_sql(
    df: pd.DataFrame,
    db_path: Union[str, Path] = "data/covid_analytics.db",
    batch_size: int = 20000,
) -> Dict[str, int]:
    """Populates normalized relational tables from a cleaned and transformed DataFrame.

    Tables populated:
    - regions
    - countries
    - population_stats
    - daily_covid_stats
    - vaccination_stats
    """
    logger.info(f"Loading {len(df):,} records into normalized SQL database...")
    df = df.copy()

    # Column name safety
    country_col = "country" if "country" in df.columns else "location"
    region_col = "region" if "region" in df.columns else ("continent" if "continent" in df.columns else None)

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    counts = {}

    try:
        # 0. Populate Pipeline Metadata (Data Curation & Author Credit)
        cursor.execute(
            """INSERT OR REPLACE INTO pipeline_metadata 
            (metadata_id, project_name, lead_data_engineer, dataset_curator, pipeline_version, data_attribution)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                1,
                "COVID-19 Global Data Analysis & Trend Visualization",
                "Himanshu Bagde",
                "Himanshu Bagde",
                "1.0.0",
                "Raw surveillance data from Our World in Data / WHO; Pipeline, Quality Assurance, Feature Engineering & Relational Warehouse by Himanshu Bagde"
            )
        )
        conn.commit()
        counts["pipeline_metadata"] = 1

        # 1. Populate Regions
        if region_col and region_col in df.columns:
            unique_regions = [r for r in df[region_col].dropna().unique() if str(r).strip() != ""]
        else:
            unique_regions = ["Global"]

        cursor.executemany(
            "INSERT OR IGNORE INTO regions (region_id, region_name) VALUES (?, ?)",
            [(i + 1, str(r)) for i, r in enumerate(unique_regions)]
        )
        conn.commit()

        # Fetch region mapping
        cursor.execute("SELECT region_name, region_id FROM regions")
        region_map = dict(cursor.fetchall())
        counts["regions"] = len(region_map)

        # 2. Populate Countries
        country_df = df[[country_col]].drop_duplicates().copy()
        country_records = []

        for idx, row in enumerate(country_df.itertuples(index=False), start=1):
            c_name = getattr(row, country_col)
            # Find representative record for country metadata
            c_sample = df[df[country_col] == c_name].iloc[0]
            iso = str(c_sample.get("iso_code", "")) if pd.notna(c_sample.get("iso_code")) else ""
            r_name = str(c_sample.get(region_col, "Global")) if region_col else "Global"
            r_id = region_map.get(r_name)
            pop = int(c_sample["population"]) if pd.notna(c_sample.get("population")) and c_sample["population"] > 0 else None
            density = float(c_sample["population_density"]) if pd.notna(c_sample.get("population_density")) else None
            med_age = float(c_sample["median_age"]) if pd.notna(c_sample.get("median_age")) else None

            country_records.append((idx, iso, str(c_name), r_id, pop, density, med_age))

        cursor.executemany(
            """INSERT OR REPLACE INTO countries 
            (country_id, iso_code, country_name, region_id, population, population_density, median_age)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            country_records
        )
        conn.commit()

        # Fetch country mapping
        cursor.execute("SELECT country_name, country_id FROM countries")
        country_map = dict(cursor.fetchall())
        counts["countries"] = len(country_map)

        # 3. Populate Population Stats
        pop_records = []
        for c_rec in country_records:
            cid, _, cname, _, pop, density, med_age = c_rec
            c_sample = df[df[country_col] == cname].iloc[0]
            gdp = float(c_sample["gdp_per_capita"]) if pd.notna(c_sample.get("gdp_per_capita")) else None
            life_exp = float(c_sample["life_expectancy"]) if pd.notna(c_sample.get("life_expectancy")) else None
            beds = float(c_sample["hospital_beds_per_thousand"]) if pd.notna(c_sample.get("hospital_beds_per_thousand")) else None

            pop_records.append((cid, pop, density, med_age, gdp, life_exp, beds))

        cursor.executemany(
            """INSERT OR REPLACE INTO population_stats 
            (country_id, population, population_density, median_age, gdp_per_capita, life_expectancy, hospital_beds_per_thousand)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            pop_records
        )
        conn.commit()
        counts["population_stats"] = len(pop_records)

        # 4. Populate Daily COVID Stats & Vaccination Stats in optimized Batches
        logger.info(f"Inserting daily stats and vaccination records in batches of {batch_size:,}...")

        # Pre-map country_id
        df["mapped_country_id"] = df[country_col].map(country_map)
        valid_df = df.dropna(subset=["mapped_country_id", "date"]).copy()
        valid_df["mapped_country_id"] = valid_df["mapped_country_id"].astype(int)

        daily_rows = []
        vax_rows = []
        total_daily_inserted = 0
        total_vax_inserted = 0

        for i, row in enumerate(valid_df.itertuples(index=False), start=1):
            cid = row.mapped_country_id
            dt = str(row.date)
            nc = float(getattr(row, "new_cases", 0.0) or 0.0)
            tc = float(getattr(row, "total_cases", 0.0) or 0.0)
            nd = float(getattr(row, "new_deaths", 0.0) or 0.0)
            td = float(getattr(row, "total_deaths", 0.0) or 0.0)
            cfr = float(getattr(row, "case_fatality_rate", 0.0) or 0.0)
            cp100 = float(getattr(row, "cases_per_100k", 0.0) or 0.0)
            dp100 = float(getattr(row, "deaths_per_100k", 0.0) or 0.0)
            r7c = float(getattr(row, "7_day_cases_avg", 0.0) or 0.0)
            r7d = float(getattr(row, "7_day_deaths_avg", 0.0) or 0.0)

            daily_rows.append((i, cid, dt, nc, tc, nd, td, cfr, cp100, dp100, r7c, r7d))

            # Vaccination record
            tot_vax = float(getattr(row, "total_vaccinations", 0.0) or 0.0)
            p_vax = float(getattr(row, "people_vaccinated", 0.0) or 0.0)
            pf_vax = float(getattr(row, "people_fully_vaccinated", 0.0) or 0.0)
            new_v = float(getattr(row, "new_vaccinations", 0.0) or 0.0)
            v_rate = float(getattr(row, "vaccination_rate", 0.0) or 0.0)
            fv_rate = float(getattr(row, "fully_vaccinated_rate", 0.0) or 0.0)

            vax_rows.append((i, cid, dt, tot_vax, p_vax, pf_vax, new_v, v_rate, fv_rate))

            if len(daily_rows) >= batch_size:
                cursor.executemany(
                    """INSERT INTO daily_covid_stats 
                    (record_id, country_id, date, new_cases, total_cases, new_deaths, total_deaths, case_fatality_rate, cases_per_100k, deaths_per_100k, rolling_7day_cases, rolling_7day_deaths)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    daily_rows
                )
                cursor.executemany(
                    """INSERT INTO vaccination_stats 
                    (record_id, country_id, date, total_vaccinations, people_vaccinated, people_fully_vaccinated, new_vaccinations, vaccination_rate, fully_vaccinated_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    vax_rows
                )
                conn.commit()
                total_daily_inserted += len(daily_rows)
                total_vax_inserted += len(vax_rows)
                daily_rows.clear()
                vax_rows.clear()

        # Insert remaining rows
        if daily_rows:
            cursor.executemany(
                """INSERT INTO daily_covid_stats 
                (record_id, country_id, date, new_cases, total_cases, new_deaths, total_deaths, case_fatality_rate, cases_per_100k, deaths_per_100k, rolling_7day_cases, rolling_7day_deaths)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                daily_rows
            )
            cursor.executemany(
                """INSERT INTO vaccination_stats 
                (record_id, country_id, date, total_vaccinations, people_vaccinated, people_fully_vaccinated, new_vaccinations, vaccination_rate, fully_vaccinated_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                vax_rows
            )
            conn.commit()
            total_daily_inserted += len(daily_rows)
            total_vax_inserted += len(vax_rows)

        counts["daily_covid_stats"] = total_daily_inserted
        counts["vaccination_stats"] = total_vax_inserted

        logger.info(f"Database loading complete: {counts}")
        return counts

    except Exception as e:
        conn.rollback()
        logger.error(f"Error during database bulk loading: {e}")
        raise
    finally:
        conn.close()


def execute_query(
    sql_query: str,
    db_path: Union[str, Path] = "data/covid_analytics.db",
    params: Optional[Tuple[Any, ...]] = None,
) -> pd.DataFrame:
    """Executes a SQL query and returns results as a pandas DataFrame."""
    conn = get_db_connection(db_path)
    try:
        df = pd.read_sql_query(sql_query, conn, params=params)
        return df
    finally:
        conn.close()


def execute_sql_file(
    file_path: Union[str, Path],
    db_path: Union[str, Path] = "data/covid_analytics.db",
) -> List[pd.DataFrame]:
    """Reads a .sql file containing multiple semicolon-separated queries and returns a list of DataFrames."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    raw_blocks = content.split(";")
    queries = []
    for block in raw_blocks:
        # Remove single-line comments
        lines = [line for line in block.splitlines() if not line.strip().startswith("--")]
        clean_q = "\n".join(lines).strip()
        if clean_q:
            queries.append(clean_q)

    results = []
    conn = get_db_connection(db_path)
    try:
        for idx, q in enumerate(queries, start=1):
            try:
                df = pd.read_sql_query(q, conn)
                results.append(df)
            except Exception as e:
                logger.warning(f"Error running query #{idx} in {path.name}: {e}")
        return results
    finally:
        conn.close()
