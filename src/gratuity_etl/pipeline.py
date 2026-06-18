"""CLI entry points used by Airflow tasks and local runs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path for `config` and `gratuity_etl` imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config import settings  # noqa: E402
from gratuity_etl.audit.clockout_audit import capture_mid_shift_snapshots  # noqa: E402
from gratuity_etl.extract.factory import extract_daily_tips, extract_shifts  # noqa: E402
from gratuity_etl.load.bigquery_loader import BigQueryLoader  # noqa: E402


def run_extract_shifts() -> None:
    run_date = settings.get_pipeline_run_date()
    rows = extract_shifts(run_date=run_date)
    print(f"Extracted {len(rows)} shift rows for {run_date}")


def run_extract_daily_tips() -> None:
    run_date = settings.get_pipeline_run_date()
    rows = extract_daily_tips(run_date=run_date)
    print(f"Extracted {len(rows)} daily tip rows for {run_date}")


def run_load_raw_tables() -> None:
    run_date = settings.get_pipeline_run_date()
    loader = BigQueryLoader()
    shifts = extract_shifts(run_date=run_date)
    tips = extract_daily_tips(run_date=run_date)
    shift_count = loader.load_shifts(shifts, run_date=run_date)
    tip_count = loader.load_daily_tips(tips, run_date=run_date)
    print(f"Loaded {shift_count} shifts and {tip_count} daily_tips rows for {run_date}")


def run_capture_audit_snapshots() -> None:
    run_date = settings.get_pipeline_run_date()
    shifts = extract_shifts(run_date=run_date)
    snapshots = capture_mid_shift_snapshots(shifts)
    loader = BigQueryLoader()
    count = loader.append_audit_logs(snapshots)
    print(f"Appended {count} audit_log snapshots for {run_date}")


def run_full_pipeline() -> None:
    run_load_raw_tables()
    run_capture_audit_snapshots()
    print("Raw load + audit complete. Run dbt separately: cd dbt && dbt run && dbt test")


def main() -> None:
    parser = argparse.ArgumentParser(description="GratuityETL pipeline commands")
    parser.add_argument(
        "command",
        choices=[
            "extract_shifts",
            "extract_daily_tips",
            "load_raw_tables",
            "capture_audit_snapshots",
            "run_full_pipeline",
        ],
    )
    args = parser.parse_args()

    commands = {
        "extract_shifts": run_extract_shifts,
        "extract_daily_tips": run_extract_daily_tips,
        "load_raw_tables": run_load_raw_tables,
        "capture_audit_snapshots": run_capture_audit_snapshots,
        "run_full_pipeline": run_full_pipeline,
    }
    commands[args.command]()


if __name__ == "__main__":
    main()
