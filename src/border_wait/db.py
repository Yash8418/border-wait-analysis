"""Load the cleaned datasets into an in-process DuckDB database.

Timestamps are converted to local (America/Toronto) wall-clock time before loading,
so SQL can group by hour of day without needing timezone extensions.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from border_wait.holidays import holidays_between, long_weekend_days

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
LOCAL_TZ = "America/Toronto"


def load_hourly(path: Path = PROCESSED / "windsor_hourly.csv.gz") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(LOCAL_TZ).dt.tz_localize(None)
    return df


def load_monthly(path: Path = PROCESSED / "windsor_monthly.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m")
    return df


def holiday_days(first_year: int = 2010, last_year: int = 2025) -> pd.DataFrame:
    """One row per day that is a holiday or part of the long weekend it creates."""
    rows = [
        {"day": day, "holiday": h.name, "country": h.country, "is_holiday": day == h.day}
        for h in holidays_between(first_year, last_year)
        for day in long_weekend_days(h)
    ]
    df = pd.DataFrame(rows)
    df["day"] = pd.to_datetime(df["day"])
    return df


def connect(hourly: pd.DataFrame | None = None, monthly: pd.DataFrame | None = None) -> duckdb.DuckDBPyConnection:
    """Create an in-memory database with `hourly`, `monthly`, `holiday_days` and the `readings` view."""
    con = duckdb.connect()
    hourly = load_hourly() if hourly is None else hourly
    monthly = load_monthly() if monthly is None else monthly
    for name, frame in (("hourly", hourly), ("monthly", monthly), ("holiday_days", holiday_days())):
        con.register(f"{name}_df", frame)
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM {name}_df")
        con.unregister(f"{name}_df")

    # Only hours where CBSA actually reported a wait (including "No delay" = 0).
    con.execute(
        """
        CREATE VIEW readings AS
        SELECT
            crossing,
            timestamp,
            travellers_wait_min AS wait_min,
            travellers_wait_min > 0 AS delayed,
            hour(timestamp) AS hour,
            isodow(timestamp) AS weekday,          -- 1 = Monday ... 7 = Sunday
            dayname(timestamp) AS weekday_name,
            month(timestamp) AS month,
            year(timestamp) AS year
        FROM hourly
        WHERE travellers_status = 'reported'
        """
    )
    return con
