-- Bootstrap BigQuery datasets and raw tables for GratuityETL.
-- Run once in the BigQuery console or via `bq query`.
-- Replace `your-gcp-project-id` with your project.

CREATE SCHEMA IF NOT EXISTS `your-gcp-project-id.gratuity_raw`
OPTIONS (description = 'Raw shift and tip data loaded by Python ETL');

CREATE SCHEMA IF NOT EXISTS `your-gcp-project-id.gratuity_staging`
OPTIONS (description = 'dbt staging views');

CREATE SCHEMA IF NOT EXISTS `your-gcp-project-id.gratuity_marts`
OPTIONS (description = 'dbt mart tables for tip payouts');

CREATE TABLE IF NOT EXISTS `your-gcp-project-id.gratuity_raw.shifts` (
  shift_date DATE NOT NULL,
  employee_name STRING NOT NULL,
  clock_in TIMESTAMP NOT NULL,
  clock_out TIMESTAMP,
  hours_worked FLOAT64,
  is_mid_shift_clockout BOOL,
  loaded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `your-gcp-project-id.gratuity_raw.daily_tips` (
  shift_date DATE NOT NULL,
  gross_sales FLOAT64 NOT NULL,
  cash_tips FLOAT64,
  credit_tips FLOAT64,
  loaded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `your-gcp-project-id.gratuity_raw.audit_log` (
  audit_id STRING NOT NULL,
  employee_name STRING NOT NULL,
  shift_date DATE NOT NULL,
  snapshot_timestamp TIMESTAMP NOT NULL,
  clock_in TIMESTAMP NOT NULL,
  clock_out TIMESTAMP,
  hours_at_snapshot FLOAT64 NOT NULL,
  event_type STRING NOT NULL,
  loaded_at TIMESTAMP
);
