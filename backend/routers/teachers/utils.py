"""
Utility functions for teachers routers.
"""
from datetime import datetime, timedelta, date
from typing import Any, Optional
import re


# Test subscription whitelist (shared across modules)
TEST_SUBSCRIPTION_WHITELIST = [
    "demo@duotopia.com",
    "expired@duotopia.com",
    "trial@duotopia.com",
    "purpleice9765@msn.com",
    "kaddyeunice@apps.ntpc.edu.tw",
    "ceeks.edu@gmail.com",
]


def parse_birthdate(birthdate_value: Any) -> Optional[date]:
    """Parse various date formats into a date object"""
    if birthdate_value is None:
        return None

    # Convert to string for processing
    date_str = str(birthdate_value).strip()

    # Handle Excel serial date numbers (days since 1900-01-01)
    if date_str.isdigit() and len(date_str) == 5:
        try:
            excel_serial = int(date_str)
            # Excel uses 1900-01-01 as day 1, but has a bug counting 1900 as leap year
            # So we use 1899-12-30 as base
            base_date = datetime(1899, 12, 30)
            result_date = base_date + timedelta(days=excel_serial)
            return result_date.date()
        except Exception:
            pass

    # Handle YYYYMMDD format
    if re.match(r"^\d{8}$", date_str):
        try:
            return datetime.strptime(date_str, "%Y%m%d").date()
        except Exception:
            pass

    # Handle YYYY-MM-DD format
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            pass

    # Handle YYYY/MM/DD format
    if re.match(r"^\d{4}/\d{2}/\d{2}$", date_str):
        try:
            return datetime.strptime(date_str, "%Y/%m/%d").date()
        except Exception:
            pass

    # Handle MM/DD/YYYY format (common in US)
    if re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
        try:
            return datetime.strptime(date_str, "%m/%d/%Y").date()
        except Exception:
            pass

    return None
