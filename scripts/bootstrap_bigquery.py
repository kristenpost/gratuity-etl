"""Create BigQuery datasets required by GratuityETL (run once)."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from google.cloud import bigquery

from config import settings

DATASETS = [
    (settings.BQ_RAW_DATASET, "Raw shift and tip data loaded by Python ETL"),
    (settings.BQ_STAGING_DATASET, "dbt staging views"),
    (settings.BQ_MARTS_DATASET, "dbt mart tables for tip payouts"),
]


def main() -> None:
    client = bigquery.Client(project=settings.GCP_PROJECT_ID)
    for dataset_id, description in DATASETS:
        dataset = bigquery.Dataset(f"{settings.GCP_PROJECT_ID}.{dataset_id}")
        dataset.location = "US"
        dataset.description = description
        client.create_dataset(dataset, exists_ok=True)
        print(f"Ready: {settings.GCP_PROJECT_ID}.{dataset_id}")


if __name__ == "__main__":
    main()
