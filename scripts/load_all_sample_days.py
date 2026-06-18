"""Load all sample business dates into BigQuery for initial demo."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import os

os.environ.setdefault("DATA_SOURCE", "sample")

from config import settings  # noqa: E402
from gratuity_etl.audit.clockout_audit import capture_mid_shift_snapshots  # noqa: E402
from gratuity_etl.extract.factory import extract_daily_tips, extract_shifts  # noqa: E402
from gratuity_etl.load.bigquery_loader import BigQueryLoader  # noqa: E402

SAMPLE_DATES = [
    date(2025, 6, 1),
    date(2025, 6, 2),
    date(2025, 6, 3),
    date(2025, 6, 4),
    date(2025, 6, 5),
]


def main() -> None:
    loader = BigQueryLoader()
    for run_date in SAMPLE_DATES:
        os.environ["PIPELINE_RUN_DATE"] = run_date.isoformat()
        shifts = extract_shifts(run_date=run_date)
        tips = extract_daily_tips(run_date=run_date)
        loader.load_shifts(shifts, run_date=run_date)
        loader.load_daily_tips(tips, run_date=run_date)
        snapshots = capture_mid_shift_snapshots(shifts)
        loader.append_audit_logs(snapshots)
        print(f"Loaded {run_date}: {len(shifts)} shifts, {len(tips)} tip rows, {len(snapshots)} audits")

    print("Done. Next: cd dbt && dbt deps && dbt run && dbt test")


if __name__ == "__main__":
    main()
