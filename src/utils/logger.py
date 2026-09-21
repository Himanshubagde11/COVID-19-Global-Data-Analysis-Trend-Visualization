"""Centralized logging module for COVID-19 Analytics pipeline.

Formats logs cleanly to both console and a rotating or persistent log file.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_file: Optional[str] = "logs/pipeline.log",
    level: int = logging.INFO,
    format_str: str = "[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
    date_format: str = "%Y-%m-%d %H:%M:%S",
) -> logging.Logger:
    """Configures the root and package logger with file and console handlers.

    Args:
        log_file: Path to write the log file. If None, only console handler is used.
        level: Logging level (e.g. logging.INFO, logging.DEBUG).
        format_str: Custom logging format string.
        date_format: Date format for timestamps.

    Returns:
        logging.Logger: Configured base logger.
    """
    logger = logging.getLogger("covid_analytics")
    logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(fmt=format_str, datefmt=date_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "covid_analytics") -> logging.Logger:
    """Retrieves a named logger child of the base covid_analytics logger."""
    if not logging.getLogger("covid_analytics").handlers:
        setup_logging()
    return logging.getLogger(f"covid_analytics.{name}")
