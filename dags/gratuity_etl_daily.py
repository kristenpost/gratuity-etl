"""GratuityETL daily pipeline — extract, load, audit, dbt."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = Path(os.environ.get("GRATUITY_PROJECT_ROOT", "/opt/gratuity_etl"))
ETL_PYTHON = os.environ.get("ETL_PYTHON", "/opt/etl-venv/bin/python")
DBT_DIR = PROJECT_ROOT / "dbt"

COMMON_ENV = {
    "GCP_PROJECT_ID": os.environ.get("GCP_PROJECT_ID", "gratuity-etl"),
    "GOOGLE_APPLICATION_CREDENTIALS": "/opt/gratuity_etl/credentials/service-account.json",
    "PYTHONPATH": f"{PROJECT_ROOT}:{PROJECT_ROOT / 'src'}",
    "DATA_SOURCE": os.environ.get("DATA_SOURCE", "sample"),
    "PIPELINE_RUN_DATE": os.environ.get("PIPELINE_RUN_DATE", ""),
    "DBT_PROFILES_DIR": str(DBT_DIR),
}

DEFAULT_ARGS = {
    "owner": "gratuity_etl",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def pipeline_cmd(step: str) -> str:
    return f"cd {PROJECT_ROOT} && {ETL_PYTHON} -m gratuity_etl.pipeline {step}"


with DAG(
    dag_id="gratuity_etl_daily",
    default_args=DEFAULT_ARGS,
    description="Daily restaurant tip proration pipeline",
    schedule="@daily",
    start_date=datetime(2025, 6, 1),
    catchup=False,
    tags=["gratuity", "etl", "bigquery", "dbt"],
) as dag:
    extract_shifts = BashOperator(
        task_id="extract_shifts",
        bash_command=pipeline_cmd("extract_shifts"),
        env=COMMON_ENV,
    )

    extract_daily_tips = BashOperator(
        task_id="extract_daily_tips",
        bash_command=pipeline_cmd("extract_daily_tips"),
        env=COMMON_ENV,
    )

    load_raw_tables = BashOperator(
        task_id="load_raw_tables",
        bash_command=pipeline_cmd("load_raw_tables"),
        env=COMMON_ENV,
    )

    capture_audit_snapshots = BashOperator(
        task_id="capture_audit_snapshots",
        bash_command=pipeline_cmd("capture_audit_snapshots"),
        env=COMMON_ENV,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_DIR} && /opt/etl-venv/bin/dbt deps && /opt/etl-venv/bin/dbt run",
        env=COMMON_ENV,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && /opt/etl-venv/bin/dbt test",
        env=COMMON_ENV,
    )

    [extract_shifts, extract_daily_tips] >> load_raw_tables >> capture_audit_snapshots >> dbt_run >> dbt_test
