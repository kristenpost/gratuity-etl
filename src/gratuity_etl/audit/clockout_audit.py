"""Detect mid-shift clock-outs and build audit snapshot records."""

from __future__ import annotations

import uuid
from datetime import datetime

from config import settings
from gratuity_etl.models.sqlalchemy_models import AuditLog
from gratuity_etl.schemas import ShiftRow


def _compute_hours(shift: ShiftRow) -> float:
    if shift.hours_worked is not None:
        return float(shift.hours_worked)
    if shift.clock_out is None:
        return 0.0
    delta = shift.clock_out - shift.clock_in
    return round(delta.total_seconds() / 3600, 2)


def is_mid_shift_clockout(shift: ShiftRow) -> bool:
    """
    Return True when an employee clocks out before a full shift ends.

    Uses an explicit flag from source data, or infers from hours worked
    versus the configured expected shift length.
    """
    if shift.is_mid_shift_clockout:
        return True
    if shift.clock_out is None:
        return False
    hours = _compute_hours(shift)
    return 0 < hours < settings.EXPECTED_SHIFT_HOURS


def capture_mid_shift_snapshots(shifts: list[ShiftRow]) -> list[AuditLog]:
    """Build append-only audit rows for mid-shift clock-out events."""
    snapshots: list[AuditLog] = []
    snapshot_time = datetime.utcnow()

    for shift in shifts:
        if not is_mid_shift_clockout(shift):
            continue

        snapshots.append(
            AuditLog(
                audit_id=str(uuid.uuid4()),
                employee_name=shift.employee_name,
                shift_date=shift.shift_date,
                snapshot_timestamp=snapshot_time,
                clock_in=shift.clock_in,
                clock_out=shift.clock_out,
                hours_at_snapshot=_compute_hours(shift),
                event_type="mid_shift_clockout",
                loaded_at=snapshot_time,
            )
        )
    return snapshots
