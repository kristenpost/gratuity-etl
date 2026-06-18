"""Shared row schemas for extract sources (CSV and Google Sheets)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ShiftRow(BaseModel):
    shift_date: date
    employee_name: str
    clock_in: datetime
    clock_out: Optional[datetime] = None
    hours_worked: Optional[float] = None
    is_mid_shift_clockout: bool = False

    @field_validator("employee_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("is_mid_shift_clockout", mode="before")
    @classmethod
    def parse_bool(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in {"true", "1", "yes", "y"}


class DailyTipsRow(BaseModel):
    shift_date: date
    gross_sales: float
    cash_tips: float = 0.0
    credit_tips: float = 0.0

    @property
    def auto_gratuity_amount(self) -> float:
        return round(self.gross_sales * 0.19, 2)

    @property
    def total_tip_pool(self) -> float:
        return round(self.auto_gratuity_amount + self.cash_tips + self.credit_tips, 2)


class EmployeeRow(BaseModel):
    employee_name: str
    role: str = "server"
    is_active: bool = True
