"""Load the cleaned datasets into an in-process DuckDB database.

Timestamps are converted to local (America/Toronto) wall-clock time before loading,
so SQL can group by hour of day without needing timezone extensions.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

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


def connect(hourly: pd.DataFrame | None = None, monthly: pd.DataFrame | None = None) -> duckdb.DuckDBPyConnection:
    """Create an in-memory database with `hourly`, `monthly` and the `readings` view."""
    con = duckdb.connect()
    hourly = load_hourly() if hourly is None else hourly
    monthly = load_monthly() if monthly is None else monthly
    con.register("hourly_df", hourly)
    con.register("monthly_df", monthly)
    con.execute("CREATE TABLE hourly AS SELECT * FROM hourly_df")
    con.execute("CREATE TABLE monthly AS SELECT * FROM monthly_df")
    con.unregister("hourly_df")
    con.unregister("monthly_df")

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
