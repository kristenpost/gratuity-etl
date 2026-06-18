"""GratuityETL daily pipeline — extract, load, audit, dbt."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# Project paths available inside the Airflow container
PROJECT_ROOT = Path(os.environ.get("GRATUITY_PROJECT_ROOT", "/opt/gratuity_etl"))
SRC_PATH = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from gratuity_etl.pipeline import (  # noqa: E402
    run_capture_audit_snapshots,
    run_extract_daily_tips,
    run_extract_shifts,
    run_load_raw_tables,
)

DEFAULT_ARGS = {
    "owner": "gratuity_etl",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

DBT_PROJECT_DIR = PROJECT_ROOT / "dbt"


with DAG(
    dag_id="gratuity_etl_daily",
    default_args=DEFAULT_ARGS,
    description="Daily restaurant tip proration pipeline",
    schedule_interval="@daily",
    start_date=datetime(2025, 6, 1),
    catchup=False,
    tags=["gratuity", "etl", "bigquery", "dbt"],
) as dag:
    extract_shifts = PythonOperator(
        task_id="extract_shifts",
        python_callable=run_extract_shifts,
    )

    extract_daily_tips = PythonOperator(
        task_id="extract_daily_tips",
        python_callable=run_extract_daily_tips,
    )

    load_raw_tables = PythonOperator(
        task_id="load_raw_tables",
        python_callable=run_load_raw_tables,
    )

    capture_audit_snapshots = PythonOperator(
        task_id="capture_audit_snapshots",
        python_callable=run_capture_audit_snapshots,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt deps && dbt run",
        env={
            "GCP_PROJECT_ID": os.environ.get("GCP_PROJECT_ID", ""),
            "GOOGLE_APPLICATION_CREDENTIALS": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""),
        },
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt test",
        env={
            "GCP_PROJECT_ID": os.environ.get("GCP_PROJECT_ID", ""),
            "GOOGLE_APPLICATION_CREDENTIALS": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""),
        },
    )

    [extract_shifts, extract_daily_tips] >> load_raw_tables >> capture_audit_snapshots >> dbt_run >> dbt_test
