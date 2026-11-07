import pandas as pd
import pytest

from border_wait.db import connect
from border_wait.queries import QUERIES, run


def hourly_rows(rows):
    """rows: (crossing, local timestamp string, wait minutes or None for a missed hour)"""
    return pd.DataFrame(
        {
            "crossing": [r[0] for r in rows],
            "timestamp": pd.to_datetime([r[1] for r in rows]),
            "travellers_wait_min": [r[2] for r in rows],
            "travellers_status": ["missed" if r[2] is None else "reported" for r in rows],
        }
    )


MONTHLY = pd.DataFrame(
    {
        "crossing": ["Ambassador Bridge"] * 3,
        "month": pd.to_datetime(["2019-12-01", "2020-06-01", "2022-06-01"]),
        "pct_met_service_standard": [97.0, 100.0, 92.5],
    }
)

BRIDGE, TUNNEL = "Ambassador Bridge", "Detroit-Windsor Tunnel"


@pytest.fixture
def con():
    rows = [
        # Friday 2015-07-03, 16:00 and 17:00
        (BRIDGE, "2015-07-03 16:00", 20.0),
        (BRIDGE, "2015-07-03 17:00", 0.0),
        (TUNNEL, "2015-07-03 16:00", 5.0),
        (TUNNEL, "2015-07-03 17:00", 0.0),
        # Saturday 2015-07-04 16:00
        (BRIDGE, "2015-07-04 16:00", 10.0),
        (TUNNEL, "2015-07-04 16:00", 15.0),
        # A missed hour must be ignored entirely
        (BRIDGE, "2015-07-05 16:00", None),
    ]
    return connect(hourly_rows(rows), MONTHLY)


def test_every_query_runs(con):
    for name in QUERIES:
        assert isinstance(run(con, name), pd.DataFrame)


def test_missed_hours_are_excluded(con):
    count = con.execute("SELECT count(*) FROM readings WHERE crossing = ?", [BRIDGE]).fetchone()[0]
    assert count == 3


def test_crossing_summary(con):
    summary = run(con, "crossing_summary").set_index("crossing")
    assert summary.loc[BRIDGE, "pct_hours_delayed"] == pytest.approx(66.7)
    assert summary.loc[BRIDGE, "avg_delay_min"] == 15.0
    assert summary.loc[TUNNEL, "max_wait_min"] == 15.0


def test_by_hour_groups_by_local_hour(con):
    by_hour = run(con, "by_hour")
    bridge_16 = by_hour[(by_hour.crossing == BRIDGE) & (by_hour.hour == 16)].iloc[0]
    assert bridge_16.pct_hours_delayed == 100.0
    assert bridge_16.avg_wait_min == 15.0


def test_weekday_numbering_starts_monday(con):
    grid = run(con, "weekday_hour")
    friday = grid[(grid.crossing == BRIDGE) & (grid.weekday_name == "Friday")]
    assert set(friday.weekday) == {5}


def test_bridge_vs_tunnel_only_compares_paired_hours(con):
    h2h = run(con, "bridge_vs_tunnel").set_index("hour")
    assert h2h.loc[16, "paired_hours"] == 2
    assert h2h.loc[16, "pct_tunnel_faster"] == 50.0  # Friday: tunnel 5 < bridge 20
    assert h2h.loc[16, "pct_bridge_faster"] == 50.0  # Saturday: bridge 10 < tunnel 15
    assert h2h.loc[17, "pct_same"] == 100.0


def test_service_standard_periods(con):
    periods = run(con, "service_standard_trend")["period"].tolist()
    assert periods == ["Before COVID", "Border restrictions", "After reopening"]


def test_holiday_days_table_includes_long_weekends(con):
    labour_day_weekend = con.execute(
        "SELECT count(*) FROM holiday_days WHERE holiday = 'Labour Day' AND year(day) = 2015"
    ).fetchone()[0]
    assert labour_day_weekend == 3  # Sat, Sun and the Monday


def test_independence_day_counts_as_holiday(con):
    # The fixture's 2015-07-04 (Saturday) rows fall on US Independence Day.
    effect = run(con, "holiday_effect")
    july_4 = effect[effect.holiday == "Independence Day"].iloc[0]
    assert july_4.hours_reported == 2
    split = run(con, "long_weekend_vs_regular")
    assert set(split.day_type) == {"Holiday or long weekend", "Regular day"}
