"""Load raw data into BigQuery using SQLAlchemy."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from gratuity_etl.models.sqlalchemy_models import AuditLog, Base, DailyTips, Shift
from gratuity_etl.schemas import DailyTipsRow, ShiftRow


class BigQueryLoader:
    """Idempotent loader for raw GratuityETL tables in BigQuery."""

    def __init__(self, raw_dataset: Optional[str] = None) -> None:
        self.raw_dataset = raw_dataset or settings.BQ_RAW_DATASET
        self.engine = create_engine(settings.bigquery_connection_url(self.raw_dataset))
        Base.metadata.create_all(self.engine)
        self._session_factory = sessionmaker(bind=self.engine)

    def _session(self) -> Session:
        return self._session_factory()

    def load_shifts(self, rows: list[ShiftRow], run_date: date) -> int:
        """Replace shift rows for a given business date (idempotent daily load)."""
        now = datetime.utcnow()
        with self._session() as session:
            session.execute(delete(Shift).where(Shift.shift_date == run_date))
            for row in rows:
                session.add(
                    Shift(
                        shift_date=row.shift_date,
                        employee_name=row.employee_name,
                        clock_in=row.clock_in,
                        clock_out=row.clock_out,
                        hours_worked=row.hours_worked,
                        is_mid_shift_clockout=row.is_mid_shift_clockout,
                        loaded_at=now,
                    )
                )
            session.commit()
        return len(rows)

    def load_daily_tips(self, rows: list[DailyTipsRow], run_date: date) -> int:
        """Replace daily tip totals for a given business date."""
        now = datetime.utcnow()
        with self._session() as session:
            session.execute(delete(DailyTips).where(DailyTips.shift_date == run_date))
            for row in rows:
                session.add(
                    DailyTips(
                        shift_date=row.shift_date,
                        gross_sales=row.gross_sales,
                        cash_tips=row.cash_tips,
                        credit_tips=row.credit_tips,
                        loaded_at=now,
                    )
                )
            session.commit()
        return len(rows)

    def append_audit_logs(self, rows: list[AuditLog]) -> int:
        """Append-only insert for audit snapshots."""
        if not rows:
            return 0
        with self._session() as session:
            session.add_all(rows)
            session.commit()
        return len(rows)
