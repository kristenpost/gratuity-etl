# GratuityETL — Full-Stack Tip Proration Pipeline

Restaurant tip distribution is often manual and error-prone. **GratuityETL** automates fair tip proration based on hours worked per shift, with an audit trail for mid-shift clock-outs.

**Stack:** Python · SQLAlchemy · dbt · BigQuery · Apache Airflow · Google Sheets API

---

## Problem and solution

| Challenge | GratuityETL approach |
|-----------|---------------------|
| Shift data lives in spreadsheets | Google Sheets API extract (sample CSV for demo) |
| Mid-shift departures need a record | Append-only `audit_log` snapshots |
| Tips combine auto-gratuity + cash/credit | dbt models compute pool and prorate by hours |
| Manual recalculation is risky | Daily Airflow DAG + dbt tests validate payout totals |

### Architecture

```mermaid
flowchart LR
  subgraph extract [Extract]
    Sheets[GoogleSheetsAPI]
    Sample[SampleCSV]
  end
  subgraph python [Python_ETL]
    Audit[ClockOutAudit]
    Loader[SQLAlchemy_BigQuery_Loader]
  end
  subgraph bq [BigQuery]
    Raw[gratuity_raw]
    Marts[gratuity_marts]
  end
  subgraph transform [dbt]
    Stg[staging]
    Mart[fct_daily_employee_payouts]
  end
  Airflow[Airflow_DAG]
  Sheets --> Loader
  Sample --> Loader
  Loader --> Raw
  Audit --> Raw
  Airflow --> python
  Airflow --> transform
  Raw --> Stg --> Mart
  Mart --> Marts
```

---

## Business logic

### Tip pool

```
total_tip_pool = (gross_sales × 0.19) + cash_tips + credit_tips
```

- **19%** = pooled auto-gratuity from daily gross sales
- **Cash/credit tips** = additional amounts entered on the `DailyTips` tab

### Proration

```
employee_payout = (employee_hours_on_day / total_hours_all_staff_on_day) × total_tip_pool
```

The mart table `fct_daily_employee_payouts` also exposes `hours_share_pct`, `auto_gratuity_share`, `cash_share`, `credit_share`, and `total_payout`.

### Mid-shift clock-out audit

A snapshot is written when:

- `is_mid_shift_clockout = true` in source data, **or**
- `hours_worked` is greater than 0 but less than `EXPECTED_SHIFT_HOURS` (default 8)

---

## Cost and free-tier guardrails

| Component | Cost |
|-----------|------|
| Apache Airflow (local Docker only — not pip) | Free |
| dbt Core | Free |
| BigQuery (sample data volume) | Free tier — pennies at most |
| Google Sheets API | Free for prototype read volume |
| Cloud Composer | **Not used** (would cost ~$300+/month) |

**Tips to stay at $0:**

1. Use local Airflow via `docker-compose.yml`, not Cloud Composer
2. Set a GCP budget alert at $1–$5
3. Keep sample data small (included CSVs cover 5 days)
4. Delete unused BigQuery tables if you experiment heavily

GCP signup typically requires a credit card for verification even on the free tier.

---

## GCP setup checklist

1. Create a GCP project and enable **BigQuery API**
2. Create a service account with roles:
   - `BigQuery Data Editor`
   - `BigQuery Job User`
3. Download JSON key → save as `credentials/service-account.json`
4. (Optional) Enable **Google Sheets API** and share your sheet with the service account email
5. Run bootstrap DDL: [`sql/ddl/bootstrap_datasets.sql`](sql/ddl/bootstrap_datasets.sql) (replace project id)
6. Copy [`.env.example`](.env.example) → `.env` and fill in values

---

## Quick start

### 1. Install dependencies

**Important:** Do not install Apache Airflow with pip on your Mac. Airflow runs inside Docker (step 7). Including Airflow in pip causes long `google-auth` version conflicts.

If a previous `pip install` is stuck, press **Ctrl+C**, then run:

```bash
cd "Gratuity ETL"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install "dbt-core>=1.9,<2" "dbt-bigquery>=1.9,<1.10"
python -c "import pandas, sqlalchemy, google.auth; print('OK')"
dbt --version
```

The ETL install usually finishes in 1–3 minutes. `dbt-bigquery` may take another 2–5 minutes — that is normal.

Install **both** `dbt-core` and `dbt-bigquery` together. If you only downgrade `dbt-bigquery`, `dbt-core` can stay on `2.0.0-alpha` and cause odd errors.

**Python 3.9 on macOS:** If you see `Failed building wheel for cryptography`, the pinned version in `requirements.txt` fixes it. Upgrade pip first, then re-run the commands above.

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with GCP_PROJECT_ID and GOOGLE_APPLICATION_CREDENTIALS
```

### 3. Configure dbt

```bash
cp dbt/profiles.yml.example ~/.dbt/profiles.yml
# Edit project id and keyfile path
cd dbt && dbt deps
```

### 4. Create BigQuery datasets (one-time)

```bash
export GCP_PROJECT_ID=gratuity-etl
export GOOGLE_APPLICATION_CREDENTIALS="/Users/kristen/Gratuity ETL/credentials/service-account.json"
python scripts/bootstrap_bigquery.py
```

### 5. Load sample data to BigQuery

**Billing required:** GCP must have a billing account linked to run writes (INSERT/DELETE). You still get BigQuery free tier (~10 GB storage, ~1 TB queries/month). Set a $1 budget alert in GCP Console.

```bash
export PYTHONPATH=".:src"
export GCP_PROJECT_ID=gratuity-etl
export GOOGLE_APPLICATION_CREDENTIALS="/Users/kristen/Gratuity ETL/credentials/service-account.json"
python scripts/load_all_sample_days.py
```

### 6. Run dbt transforms

```bash
cd dbt
export GCP_PROJECT_ID=your-project-id
dbt run
dbt test
```

### 7. Query results in BigQuery

```sql
SELECT *
FROM `your-project-id.gratuity_marts.fct_daily_employee_payouts`
ORDER BY shift_date, employee_name;
```

### 8. Start Airflow (optional orchestration)

**Prerequisite:** Install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) and make sure it is **running** (whale icon in the menu bar). Airflow runs inside Docker containers, not in your Python venv.

In Terminal, from the project folder:

```bash
cd "/Users/kristen/Gratuity ETL"
docker compose down -v
docker compose build
docker compose up airflow-init
```

**macOS note:** Do **not** set `AIRFLOW_UID=$(id -u)` — that breaks Airflow in Docker on Mac. The compose file uses the default container user (`50000`).

When `airflow-init` finishes without errors:

```bash
docker compose up -d
```

First run downloads images and can take **5–15 minutes**. When ready:

1. Open http://localhost:8080
2. Login: `admin` / `admin`
3. Toggle **gratuity_etl_daily** ON (unpause)
4. Click the play button → **Trigger DAG**

For sample data, set `PIPELINE_RUN_DATE=2025-06-01` in `.env` before starting Docker (default "yesterday" may not match your CSV dates).

To stop Airflow later: `docker compose down`

---

## Project structure

```
GratuityETL/
├── config/settings.py          # Environment configuration
├── src/gratuity_etl/
│   ├── extract/                # Google Sheets + sample CSV
│   ├── load/                   # SQLAlchemy → BigQuery
│   ├── audit/                  # Mid-shift clock-out snapshots
│   └── pipeline.py             # CLI entry points
├── dbt/                        # Staging → marts transformations
├── dags/gratuity_etl_daily.py  # Airflow DAG
├── data/sample/                # Prototype CSV data
├── scripts/                    # Helper scripts
└── docker-compose.yml          # Local Airflow
```

---

## Sample data edge cases

| Scenario | Date | What happens |
|----------|------|--------------|
| Standard 3-person day | 2025-06-01 | Hours prorated 8 / 6 / 6 |
| Mid-shift clock-out + second shift | 2025-06-02 | Alex 4h audit + 6h shift → 10h total |
| Zero-hour shift | 2025-06-02 | Sam excluded from payouts (`hours_worked = 0`) |
| Uneven cash vs credit tips | 2025-06-02 | High cash day; shares split by hours |
| Mid-shift only (no return) | 2025-06-05 | Alex 3h audit snapshot |

### Example output (2025-06-01)

| employee | hours | share | total_payout |
|----------|-------|-------|--------------|
| Alex | 8.0 | 40% | ~$356.25 |
| Jordan | 6.0 | 30% | ~$267.19 |
| Sam | 6.0 | 30% | ~$267.19 |

*Pool: $2,500 × 19% + $120 + $180 = $890.75*

---

## Assumptions

- All tipped staff share one pool (no role-based weighting yet)
- Proration uses **hours worked only**
- 19% auto-gratuity applies to **gross sales**
- One business date per pipeline run (default: yesterday)
- Shift reload for a date is idempotent (delete + insert for that date)
- `audit_log` is append-only

---

## Edge cases handled

- Multiple shifts per employee per day (hours summed)
- Mid-shift clock-out audit snapshots
- Zero-hour employees excluded from mart
- Missing `hours_worked` computed from clock in/out in dbt
- Rounding: dbt test allows ≤ $0.02 daily variance across employees

---

## Google Sheets format

**Shifts tab** columns: `shift_date`, `employee_name`, `clock_in`, `clock_out`, `hours_worked`, `is_mid_shift_clockout`

**DailyTips tab** columns: `shift_date`, `gross_sales`, `cash_tips`, `credit_tips`

Set `DATA_SOURCE=sheets` and `GOOGLE_SHEETS_ID` in `.env` to use live Sheets instead of CSV.

---

## Troubleshooting pip installs

| Message | What it means | What to do |
|---------|---------------|------------|
| `looking at multiple versions of google-auth` | pip is resolving conflicts, often from Airflow + Google libs | Cancel with Ctrl+C; use `requirements.txt` as written (no Airflow) |
| `This is taking longer than usual` | Resolver is backtracking across many versions | Wait 2–3 min, or cancel and upgrade pip first |
| `Dataset gratuity_raw was not found` | Datasets not created yet | Run `python scripts/bootstrap_bigquery.py` |
| `Billing has not been enabled` | No billing account linked to GCP project | Link billing in GCP Console (free tier still applies) |

---

| `dbt_run` failed: `Path '/home/airflow/.dbt' does not exist` | dbt profiles not visible inside Docker | `dbt/profiles.yml` exists in project; DAG sets `DBT_PROFILES_DIR` |

---

## Finding failed tasks in the Airflow UI

1. Open http://localhost:8080 → click DAG **`gratuity_etl_daily`**
2. On the **Grid** or **Graph** view, click the **red** (failed) task square — usually `dbt_run`
3. Click **Log** in the popup (or top menu) to see the real error
4. Scroll to lines with `ERROR` or `Error:` near the bottom

Logs are also saved on your Mac under `logs/dag_id=gratuity_etl_daily/...`.

---

## Pipeline CLI

```bash
export PYTHONPATH=".:src"
python -m gratuity_etl.pipeline extract_shifts
python -m gratuity_etl.pipeline load_raw_tables
python -m gratuity_etl.pipeline capture_audit_snapshots
python -m gratuity_etl.pipeline run_full_pipeline
```

---

## Future enhancements

- Role-based tip weights (bartender vs server)
- Looker / Metabase dashboard on `fct_daily_employee_payouts`
- Cloud Composer deployment for managed Airflow
- CI/CD (GitHub Actions: dbt test on PR)
- Terraform for GCP resources
- Real-time clock-out webhooks instead of batch snapshots

---

## Resume bullets

Copy-paste (adjust project name/company as needed):

- Built **GratuityETL**, an end-to-end tip proration pipeline for restaurant shift data using **Python**, **SQLAlchemy**, **dbt**, **BigQuery**, and **Apache Airflow**
- Designed **Google Sheets API** extraction and idempotent raw loads into BigQuery with an **append-only audit log** for mid-shift clock-out events
- Implemented **dbt** staging/intermediate/mart models applying hours-based tip pool proration (19% auto-gratuity + cash/credit tips)
- Orchestrated daily pipeline runs with **Airflow**, including dbt tests validating payout totals match tip pool amounts

---

## Interview talking points

1. **Why delete+insert per day?** Idempotent replays if a DAG retries; avoids duplicate shift rows.
2. **Why audit log is append-only?** Preserves point-in-time evidence if tips are recalculated after early departures.
3. **Why dbt for proration?** Business logic is versioned SQL with tests — easier for analysts to review than buried Python.
4. **Why Airflow?** Explicit dependencies, retries, and scheduling for a daily finance workflow.
5. **Data quality:** `not_null`, `unique`, and custom test that daily payouts sum to the tip pool.

---

## License

MIT — portfolio / educational use.
