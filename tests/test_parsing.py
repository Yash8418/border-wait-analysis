from datetime import timedelta

import pytest

from border_wait.parsing import fiscal_to_calendar_month, normalize_crossing, parse_timestamp, parse_wait


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("No delay", ("reported", 0.0)),
        ("No Delay", ("reported", 0.0)),
        ("  no delay ", ("reported", 0.0)),
        ("15", ("reported", 15.0)),
        ("10 minutes", ("reported", 10.0)),
        ("1 minute", ("reported", 1.0)),
        ("Missed entry", ("missed", None)),
        ("Temporarily closed", ("closed", None)),
        ("Closed", ("closed", None)),
        ("Not Applicable", ("not_applicable", None)),
        ("--", ("unknown", None)),
        ("", ("unknown", None)),
    ],
)
def test_parse_wait(raw, expected):
    assert parse_wait(raw) == expected


def test_both_tunnel_names_map_to_one_crossing():
    assert normalize_crossing("Windsor and Detroit Tunnel") == "Detroit-Windsor Tunnel"
    assert normalize_crossing("Detroit and Canada Tunnel") == "Detroit-Windsor Tunnel"
    assert normalize_crossing(" Ambassador Bridge ") == "Ambassador Bridge"
    assert normalize_crossing("Peace Bridge") is None


def test_parse_timestamp_keeps_daylight_and_standard_offsets():
    summer = parse_timestamp("2014-07-04 13:52 EDT")
    winter = parse_timestamp("2014-12-24 13:52 EST")
    assert summer.utcoffset() == timedelta(hours=-4)
    assert winter.utcoffset() == timedelta(hours=-5)
    assert (summer.hour, summer.minute) == (13, 52)


@pytest.mark.parametrize("bad", ["2014-07-04 13:52", "2014-07-04 13:52 PST", "yesterday"])
def test_parse_timestamp_rejects_bad_values(bad):
    with pytest.raises(ValueError):
        parse_timestamp(bad)


@pytest.mark.parametrize(
    "month, fiscal, expected",
    [("April", "2019-20", (2019, 4)), ("December", "2019-20", (2019, 12)),
     ("January", "2019-20", (2020, 1)), ("March", "2024-25", (2025, 3))],
)
def test_fiscal_to_calendar_month(month, fiscal, expected):
    assert fiscal_to_calendar_month(month, fiscal) == expected
