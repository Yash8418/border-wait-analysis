from datetime import date

import pytest

from border_wait.holidays import (
    Holiday,
    canadian_holidays,
    easter_sunday,
    holidays_between,
    long_weekend_days,
    us_holidays,
    victoria_day,
)


@pytest.mark.parametrize(
    "year, expected",
    [(2015, date(2015, 4, 5)), (2016, date(2016, 3, 27)), (2019, date(2019, 4, 21)), (2024, date(2024, 3, 31))],
)
def test_easter_sunday(year, expected):
    assert easter_sunday(year) == expected


@pytest.mark.parametrize(
    "year, expected",
    [(2015, date(2015, 5, 18)), (2016, date(2016, 5, 23)), (2019, date(2019, 5, 20)), (2021, date(2021, 5, 24))],
)
def test_victoria_day_is_monday_before_may_25(year, expected):
    assert victoria_day(year) == expected


def test_known_canadian_dates_2018():
    days = {h.name: h.day for h in canadian_holidays(2018)}
    assert days["Family Day"] == date(2018, 2, 19)
    assert days["Good Friday"] == date(2018, 3, 30)
    assert days["Civic Holiday"] == date(2018, 8, 6)
    assert days["Labour Day"] == date(2018, 9, 3)
    assert days["Thanksgiving (Canada)"] == date(2018, 10, 8)


def test_known_us_dates_2018():
    days = {h.name: h.day for h in us_holidays(2018)}
    assert days["Martin Luther King Jr. Day"] == date(2018, 1, 15)
    assert days["Memorial Day"] == date(2018, 5, 28)
    assert days["Thanksgiving (US)"] == date(2018, 11, 22)


def test_holidays_between_covers_both_countries():
    holidays = holidays_between(2015, 2016)
    assert len(holidays) == 2 * (10 + 10)
    assert {h.country for h in holidays} == {"CA", "US"}
    assert holidays == sorted(holidays, key=lambda h: (h.day, h.country))


def test_long_weekend_days():
    monday = Holiday(date(2018, 9, 3), "Labour Day", "CA")
    assert long_weekend_days(monday) == [date(2018, 9, 1), date(2018, 9, 2), date(2018, 9, 3)]
    friday = Holiday(date(2018, 3, 30), "Good Friday", "CA")
    assert long_weekend_days(friday) == [date(2018, 3, 30), date(2018, 3, 31), date(2018, 4, 1)]
    thanksgiving = Holiday(date(2018, 11, 22), "Thanksgiving (US)", "US")
    assert len(long_weekend_days(thanksgiving)) == 4
    wednesday = Holiday(date(2018, 7, 4), "Independence Day", "US")
    assert long_weekend_days(wednesday) == [date(2018, 7, 4)]
