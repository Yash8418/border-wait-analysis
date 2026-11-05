import pandas as pd

from border_wait.clean import clean_hourly, count_gaps


def raw_rows(*rows):
    return pd.DataFrame(rows, columns=["office", "location", "updated", "commercial", "travellers", "source_file"])


def test_clean_hourly_dedupes_readings_in_the_same_hour():
    raw = raw_rows(
        ("Ambassador Bridge", "x", "2015-07-03 16:05 EDT", "No delay", "5", "f.csv"),
        ("Ambassador Bridge", "x", "2015-07-03 16:52 EDT", "No delay", "20", "f.csv"),
        ("Ambassador Bridge", "x", "2015-07-03 17:52 EDT", "No delay", "No delay", "f.csv"),
    )
    clean, stats = clean_hourly(raw)
    assert len(clean) == 2
    assert stats["duplicates_removed"] == 1
    # The later reading in the 16:00 hour wins.
    assert clean.iloc[0]["travellers_wait_min"] == 20


def test_clean_hourly_merges_tunnel_names_and_drops_other_crossings():
    raw = raw_rows(
        ("Windsor and Detroit Tunnel", "x", "2016-01-01 10:52 EST", "No delay", "No delay", "f.csv"),
        ("Detroit and Canada Tunnel", "x", "2018-01-01 10:52 EST", "No delay", "No delay", "f.csv"),
        ("Peace Bridge", "x", "2018-01-01 10:52 EST", "No delay", "No delay", "f.csv"),
    )
    clean, stats = clean_hourly(raw)
    assert clean["crossing"].unique().tolist() == ["Detroit-Windsor Tunnel"]
    assert stats["dropped_other_crossings"] == 1


def test_missing_values_are_not_treated_as_zero():
    raw = raw_rows(("Ambassador Bridge", "x", "2015-07-03 16:52 EDT", "Missed entry", "Missed entry", "f.csv"))
    clean, _ = clean_hourly(raw)
    assert clean.iloc[0]["travellers_status"] == "missed"
    assert pd.isna(clean.iloc[0]["travellers_wait_min"])


def test_timestamps_are_local_toronto_time():
    raw = raw_rows(("Ambassador Bridge", "x", "2015-12-24 16:52 EST", "No delay", "No delay", "f.csv"))
    clean, _ = clean_hourly(raw)
    stamp = clean.iloc[0]["timestamp"]
    assert str(stamp.tz) == "America/Toronto"
    assert stamp.hour == 16


def test_count_gaps():
    times = pd.to_datetime(["2015-01-01 00:00", "2015-01-01 01:00", "2015-01-01 09:00"]).tz_localize("UTC")
    df = pd.DataFrame({"crossing": ["A"] * 3, "timestamp": times})
    assert count_gaps(df, hours=6) == {"A": 1}
