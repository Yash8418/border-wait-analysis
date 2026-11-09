"""Bundle the analysis results into one JSON file for the web dashboard.

Usage:
    python -m border_wait.export
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "results"
SITE_DATA = ROOT / "site" / "data" / "dashboard.json"


def _records(df: pd.DataFrame) -> list[dict]:
    # NaN isn't valid JSON; send null instead.
    return json.loads(df.to_json(orient="records", date_format="iso"))


def build_dashboard(results: Path = RESULTS) -> dict:
    read = lambda name, **kw: pd.read_csv(results / f"{name}.csv", **kw)  # noqa: E731

    weekday_hour = read("weekday_hour")
    by_month = read("by_month")
    service = read("service_standard_trend", parse_dates=["month"])
    service["month"] = service["month"].dt.strftime("%Y-%m")
    holidays = read("holiday_effect").dropna(subset=["times_usual"])
    holidays = holidays[holidays.hours_reported >= 200].head(12)

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "period": {"hourly": "2010-2019", "monthly": f"{service['month'].min()} to {service['month'].max()}"},
        "crossings": sorted(weekday_hour.crossing.unique().tolist()),
        "summary": _records(read("crossing_summary")),
        "weekday_hour": _records(weekday_hour[["crossing", "weekday", "hour", "pct_hours_delayed", "avg_wait_min"]]),
        "by_month": _records(by_month[["crossing", "month", "month_name", "pct_hours_delayed"]]),
        "bridge_vs_tunnel": _records(read("bridge_vs_tunnel")),
        "holiday_effect": _records(holidays),
        "long_weekend_vs_regular": _records(read("long_weekend_vs_regular")),
        "service_standard": _records(service[["crossing", "month", "pct_met_service_standard", "period"]]),
    }


def main() -> None:
    SITE_DATA.parent.mkdir(parents=True, exist_ok=True)
    data = build_dashboard()
    SITE_DATA.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {SITE_DATA.relative_to(ROOT)} ({SITE_DATA.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
