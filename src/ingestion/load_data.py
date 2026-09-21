"""Data Ingestion Pipeline for COVID-19 Global Data Analysis.

Responsible for:
- Fetching remote raw datasets (OWID, JHU, WHO)
- Loading CSV and CSV.GZ files efficiently with chunked reading
- Validating source schema columns
- Profiling dataset summaries (row counts, memory, dtypes)
- Storing raw datasets immutably
- Generating ingestion metadata JSON
"""

import gzip
import json
import os
import shutil
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("ingestion")

# Essential schema columns expected in Our World in Data (OWID) dataset
EXPECTED_OWID_COLUMNS = [
    "iso_code",
    "continent",
    "location",
    "date",
    "total_cases",
    "new_cases",
    "total_deaths",
    "new_deaths",
    "population",
]


def fetch_remote_dataset(
    url: str,
    destination_path: Union[str, Path],
    timeout: int = 60,
    chunk_size: int = 1024 * 1024,
    force_download: bool = False,
) -> Path:
    """Downloads a remote dataset to a local path with progress tracking.

    Args:
        url: Remote HTTP/HTTPS URL.
        destination_path: Local target filepath.
        timeout: HTTP timeout in seconds.
        chunk_size: Streaming chunk size in bytes (default: 1 MB).
        force_download: If True, re-downloads even if the file exists.

    Returns:
        Path: Destination path of downloaded file.
    """
    dest = Path(destination_path)
    if dest.exists() and not force_download and dest.stat().st_size > 0:
        logger.info(f"Dataset already exists at {dest} ({dest.stat().st_size / (1024*1024):.2f} MB). Skipping download.")
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Initiating download from {url} to {dest}...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) COVID-19-Analytics-Pipeline/1.0"
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response, open(dest, "wb") as out_file:
            total_size_hdr = response.headers.get("Content-Length")
            total_size = int(total_size_hdr) if total_size_hdr else None
            downloaded = 0

            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    pct = (downloaded / total_size) * 100
                    logger.debug(f"Downloaded {downloaded / (1024*1024):.1f}/{total_size / (1024*1024):.1f} MB ({pct:.1f}%)")

        logger.info(f"Successfully downloaded {dest.name} ({dest.stat().st_size / (1024*1024):.2f} MB).")
        return dest

    except urllib.error.URLError as e:
        logger.error(f"Network error downloading {url}: {e.reason}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        raise


def load_csv(
    filepath: Union[str, Path],
    chunksize: Optional[int] = None,
    usecols: Optional[List[str]] = None,
    dtype: Optional[Dict[str, Any]] = None,
    low_memory: bool = False,
) -> Union[pd.DataFrame, Iterator[pd.DataFrame]]:
    """Loads a CSV file into a pandas DataFrame or chunk iterator.

    Args:
        filepath: Path to CSV file.
        chunksize: Number of rows per chunk if streaming.
        usecols: Specific columns to load for memory optimization.
        dtype: Explicit column data types dictionary.
        low_memory: Internally process the file in chunks when False.

    Returns:
        Union[pd.DataFrame, Iterator[pd.DataFrame]]
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    logger.info(f"Loading CSV from {path.name} (chunksize={chunksize})...")
    try:
        df = pd.read_csv(
            path,
            chunksize=chunksize,
            usecols=usecols,
            dtype=dtype,
            low_memory=low_memory,
        )
        return df
    except Exception as e:
        logger.error(f"Failed to read CSV at {path}: {e}")
        raise


def load_csv_gz(
    filepath: Union[str, Path],
    chunksize: Optional[int] = None,
    usecols: Optional[List[str]] = None,
    dtype: Optional[Dict[str, Any]] = None,
) -> Union[pd.DataFrame, Iterator[pd.DataFrame]]:
    """Loads a gzip-compressed CSV (.csv.gz) into a pandas DataFrame or chunk iterator.

    Args:
        filepath: Path to .csv.gz file.
        chunksize: Number of rows per chunk.
        usecols: Specific columns to load.
        dtype: Explicit column data types.

    Returns:
        Union[pd.DataFrame, Iterator[pd.DataFrame]]
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    logger.info(f"Loading gzip compressed CSV from {path.name}...")
    try:
        df = pd.read_csv(
            path,
            compression="gzip",
            chunksize=chunksize,
            usecols=usecols,
            dtype=dtype,
            low_memory=False,
        )
        return df
    except Exception as e:
        logger.error(f"Failed to read compressed CSV at {path}: {e}")
        raise


def validate_source_columns(
    df_or_cols: Union[pd.DataFrame, List[str]],
    required_columns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Validates that incoming dataset contains all required schema columns.

    Args:
        df_or_cols: DataFrame or list of column name strings.
        required_columns: List of columns required. Defaults to EXPECTED_OWID_COLUMNS.

    Returns:
        Dict: Validation status summary including missing columns.
    """
    if required_columns is None:
        required_columns = EXPECTED_OWID_COLUMNS

    actual_columns = set(df_or_cols.columns if isinstance(df_or_cols, pd.DataFrame) else df_or_cols)
    required_set = set(required_columns)

    missing = list(required_set - actual_columns)
    present = list(required_set.intersection(actual_columns))
    status = "PASS" if len(missing) == 0 else "FAIL"

    result = {
        "status": status,
        "total_columns_found": len(actual_columns),
        "required_columns_count": len(required_columns),
        "missing_columns": missing,
        "present_required_columns": present,
    }

    if status == "PASS":
        logger.info(f"Column validation PASSED. All {len(required_columns)} required columns found.")
    else:
        logger.warning(f"Column validation FAILED. Missing required columns: {missing}")

    return result


def get_dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Profiles a DataFrame to extract records count, column types, memory usage, and null counts.

    Args:
        df: Input DataFrame.

    Returns:
        Dict[str, Any]: Comprehensive summary profile.
    """
    memory_bytes = df.memory_usage(deep=True).sum()
    memory_mb = memory_bytes / (1024 * 1024)

    summary = {
        "row_count": int(len(df)),
        "column_count": int(df.shape[1]),
        "memory_usage_mb": round(memory_mb, 2),
        "columns": list(df.columns),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": {col: int(df[col].isna().sum()) for col in df.columns},
        "null_percentages": {
            col: round(float((df[col].isna().sum() / len(df)) * 100), 2)
            for col in df.columns
        },
    }

    logger.info(
        f"Dataset Summary: {summary['row_count']:,} rows, {summary['column_count']} columns, "
        f"{summary['memory_usage_mb']} MB in memory."
    )
    return summary


def save_raw_data(
    df: pd.DataFrame,
    destination_path: Union[str, Path],
    source_name: str,
    metadata_dir: Optional[Union[str, Path]] = "data/raw",
) -> Path:
    """Saves raw data immutably and logs an audit metadata JSON file.

    Args:
        df: DataFrame to save.
        destination_path: Path to target raw CSV.
        source_name: Name/identifier of data source.
        metadata_dir: Directory where ingestion metadata JSON will be created.

    Returns:
        Path: Saved filepath.
    """
    dest = Path(destination_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(dest, index=False)
    logger.info(f"Saved raw dataset to {dest} ({len(df):,} records).")

    # Generate Ingestion Metadata
    meta = {
        "source_name": source_name,
        "saved_path": str(dest.as_posix()),
        "record_count": int(len(df)),
        "column_count": int(df.shape[1]),
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
        "file_size_bytes": dest.stat().st_size,
        "columns": list(df.columns),
    }

    meta_file = Path(metadata_dir) / "ingestion_metadata.json"
    existing_meta = {}
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                existing_meta = json.load(f)
        except Exception:
            existing_meta = {}

    existing_meta[source_name] = meta
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(existing_meta, f, indent=2)

    logger.info(f"Ingestion metadata updated at {meta_file}.")
    return dest


def load_owid_data(
    data_dir: str = "data/raw",
    force_download: bool = False,
    url: str = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv",
) -> pd.DataFrame:
    """Master convenience loader for the Our World in Data dataset.

    Fetches from remote if not locally present, validates columns, and returns DataFrame.
    """
    raw_path = Path(data_dir) / "owid-covid-data.csv"
    if not raw_path.exists() or force_download:
        fetch_remote_dataset(url=url, destination_path=raw_path, force_download=force_download)

    df = load_csv(raw_path)
    validation = validate_source_columns(df)
    if validation["status"] == "FAIL":
        logger.warning(f"OWID data missing columns: {validation['missing_columns']}")

    get_dataset_summary(df)
    return df
