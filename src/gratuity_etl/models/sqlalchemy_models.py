"""SQLAlchemy ORM models for BigQuery raw tables."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Shift(Base):
    __tablename__ = "shifts"

    shift_date: Mapped[date] = mapped_column(Date, primary_key=True)
    employee_name: Mapped[str] = mapped_column(String, primary_key=True)
    clock_in: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    clock_out: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    hours_worked: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_mid_shift_clockout: Mapped[bool] = mapped_column(Boolean, default=False)
    loaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DailyTips(Base):
    __tablename__ = "daily_tips"

    shift_date: Mapped[date] = mapped_column(Date, primary_key=True)
    gross_sales: Mapped[float] = mapped_column(Float)
    cash_tips: Mapped[float] = mapped_column(Float, default=0.0)
    credit_tips: Mapped[float] = mapped_column(Float, default=0.0)
    loaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_name: Mapped[str] = mapped_column(String)
    shift_date: Mapped[date] = mapped_column(Date)
    snapshot_timestamp: Mapped[datetime] = mapped_column(DateTime)
    clock_in: Mapped[datetime] = mapped_column(DateTime)
    clock_out: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    hours_at_snapshot: Mapped[float] = mapped_column(Float)
    event_type: Mapped[str] = mapped_column(String, default="mid_shift_clockout")
    loaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
