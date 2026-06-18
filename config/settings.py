"""Environment-driven configuration for GratuityETL."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

# Project root is one level above config/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

BQ_RAW_DATASET = os.getenv("BQ_RAW_DATASET", "gratuity_raw")
BQ_STAGING_DATASET = os.getenv("BQ_STAGING_DATASET", "gratuity_staging")
BQ_MARTS_DATASET = os.getenv("BQ_MARTS_DATASET", "gratuity_marts")

DATA_SOURCE = os.getenv("DATA_SOURCE", "sample").lower()

GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
SHEETS_SHIFTS_TAB = os.getenv("SHEETS_SHIFTS_TAB", "Shifts")
SHEETS_DAILY_TIPS_TAB = os.getenv("SHEETS_DAILY_TIPS_TAB", "DailyTips")

AUTO_GRATUITY_RATE = float(os.getenv("AUTO_GRATUITY_RATE", "0.19"))
EXPECTED_SHIFT_HOURS = float(os.getenv("EXPECTED_SHIFT_HOURS", "8.0"))

SAMPLE_DATA_DIR = PROJECT_ROOT / "data" / "sample"
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt"


def get_pipeline_run_date() -> date:
    """Return the business date this pipeline run processes (default: yesterday)."""
    override = os.getenv("PIPELINE_RUN_DATE", "").strip()
    if override:
        return datetime.strptime(override, "%Y-%m-%d").date()
    return date.today() - timedelta(days=1)


def bigquery_connection_url(dataset: str) -> str:
    """SQLAlchemy connection string for a BigQuery dataset."""
    if not GCP_PROJECT_ID:
        raise ValueError("GCP_PROJECT_ID is required. Set it in your .env file.")
    return f"bigquery://{GCP_PROJECT_ID}/{dataset}"
