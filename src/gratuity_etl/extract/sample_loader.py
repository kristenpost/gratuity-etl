"""Load shift and tip data from local sample CSV files."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from config import settings
from gratuity_etl.schemas import DailyTipsRow, EmployeeRow, ShiftRow


def _parse_date_column(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series).dt.date


def _parse_datetime_column(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series)


def load_shifts(
    run_date: Optional[date] = None,
    data_dir: Optional[Path] = None,
) -> list[ShiftRow]:
    """Read shifts from sample CSV, optionally filtered to a single business date."""
    path = (data_dir or settings.SAMPLE_DATA_DIR) / "shifts.csv"
    frame = pd.read_csv(path)
    frame["shift_date"] = _parse_date_column(frame["shift_date"])
    frame["clock_in"] = _parse_datetime_column(frame["clock_in"])
    if "clock_out" in frame.columns:
        frame["clock_out"] = pd.to_datetime(frame["clock_out"], errors="coerce")

    if run_date:
        frame = frame[frame["shift_date"] == run_date]

    rows: list[ShiftRow] = []
    for record in frame.to_dict(orient="records"):
        if pd.isna(record.get("clock_out")):
            record["clock_out"] = None
        if pd.isna(record.get("hours_worked")):
            record["hours_worked"] = None
        rows.append(ShiftRow.model_validate(record))
    return rows


def load_daily_tips(
    run_date: Optional[date] = None,
    data_dir: Optional[Path] = None,
) -> list[DailyTipsRow]:
    """Read daily tip totals from sample CSV."""
    path = (data_dir or settings.SAMPLE_DATA_DIR) / "daily_tips.csv"
    frame = pd.read_csv(path)
    frame["shift_date"] = _parse_date_column(frame["shift_date"])

    if run_date:
        frame = frame[frame["shift_date"] == run_date]

    return [DailyTipsRow.model_validate(record) for record in frame.to_dict(orient="records")]


def load_employees(data_dir: Optional[Path] = None) -> list[EmployeeRow]:
    """Read employee reference data from sample CSV."""
    path = (data_dir or settings.SAMPLE_DATA_DIR) / "employees.csv"
    frame = pd.read_csv(path)
    return [EmployeeRow.model_validate(record) for record in frame.to_dict(orient="records")]
