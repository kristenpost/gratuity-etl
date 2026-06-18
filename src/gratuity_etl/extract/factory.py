"""Unified extract interface for sample CSV and Google Sheets sources."""

from __future__ import annotations

from datetime import date
from typing import Optional

from config import settings
from gratuity_etl.extract.sample_loader import load_daily_tips as load_daily_tips_csv
from gratuity_etl.extract.sample_loader import load_shifts as load_shifts_csv
from gratuity_etl.extract.sheets_client import SheetsClient
from gratuity_etl.schemas import DailyTipsRow, ShiftRow


def extract_shifts(run_date: Optional[date] = None) -> list[ShiftRow]:
    if settings.DATA_SOURCE == "sheets":
        return SheetsClient().fetch_shifts(run_date=run_date)
    return load_shifts_csv(run_date=run_date)


def extract_daily_tips(run_date: Optional[date] = None) -> list[DailyTipsRow]:
    if settings.DATA_SOURCE == "sheets":
        return SheetsClient().fetch_daily_tips(run_date=run_date)
    return load_daily_tips_csv(run_date=run_date)
