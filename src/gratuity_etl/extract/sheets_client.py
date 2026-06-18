"""Google Sheets API extraction for shift and daily tip data."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import settings
from gratuity_etl.schemas import DailyTipsRow, ShiftRow

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class SheetsClient:
    """Read restaurant shift and tip data from a Google Spreadsheet."""

    def __init__(
        self,
        spreadsheet_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
    ) -> None:
        self.spreadsheet_id = spreadsheet_id or settings.GOOGLE_SHEETS_ID
        credentials_path = credentials_path or settings.GOOGLE_APPLICATION_CREDENTIALS
        if not self.spreadsheet_id:
            raise ValueError("GOOGLE_SHEETS_ID is required when DATA_SOURCE=sheets")
        if not credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is required for Sheets API")

        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=SCOPES,
        )
        self._service = build("sheets", "v4", credentials=credentials, cache_discovery=False)

    def _read_tab(self, tab_name: str) -> list[dict[str, Any]]:
        result = (
            self._service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range=f"{tab_name}!A:Z")
            .execute()
        )
        values = result.get("values", [])
        if not values:
            return []

        headers = [header.strip() for header in values[0]]
        records: list[dict[str, Any]] = []
        for row in values[1:]:
            padded = row + [""] * (len(headers) - len(row))
            records.append(dict(zip(headers, padded)))
        return records

    @staticmethod
    def _parse_date(value: str) -> date:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        value = value.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unsupported datetime format: {value}")

    def fetch_shifts(self, run_date: Optional[date] = None) -> list[ShiftRow]:
        records = self._read_tab(settings.SHEETS_SHIFTS_TAB)
        rows: list[ShiftRow] = []
        for record in records:
            row = ShiftRow(
                shift_date=self._parse_date(record["shift_date"]),
                employee_name=record["employee_name"],
                clock_in=self._parse_datetime(record["clock_in"]),
                clock_out=self._parse_datetime(record["clock_out"]) if record.get("clock_out") else None,
                hours_worked=float(record["hours_worked"]) if record.get("hours_worked") else None,
                is_mid_shift_clockout=record.get("is_mid_shift_clockout", False),
            )
            if run_date is None or row.shift_date == run_date:
                rows.append(row)
        return rows

    def fetch_daily_tips(self, run_date: Optional[date] = None) -> list[DailyTipsRow]:
        records = self._read_tab(settings.SHEETS_DAILY_TIPS_TAB)
        rows: list[DailyTipsRow] = []
        for record in records:
            row = DailyTipsRow(
                shift_date=self._parse_date(record["shift_date"]),
                gross_sales=float(record["gross_sales"]),
                cash_tips=float(record.get("cash_tips", 0) or 0),
                credit_tips=float(record.get("credit_tips", 0) or 0),
            )
            if run_date is None or row.shift_date == run_date:
                rows.append(row)
        return rows
