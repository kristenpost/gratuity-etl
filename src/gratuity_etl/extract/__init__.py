"""Extract layer: Google Sheets API and sample CSV loaders."""

from gratuity_etl.extract.sample_loader import load_daily_tips, load_shifts

__all__ = ["load_daily_tips", "load_shifts", "SheetsClient"]


def __getattr__(name: str):
    if name == "SheetsClient":
        from gratuity_etl.extract.sheets_client import SheetsClient

        return SheetsClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
