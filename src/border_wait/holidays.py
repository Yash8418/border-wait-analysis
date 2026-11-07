"""Canadian (Ontario) and US federal holidays, computed from their rules.

Computed rather than hard-coded so any year works without a third-party library.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

MON, THU, FRI, SAT, SUN = 0, 3, 4, 5, 6


@dataclass(frozen=True)
class Holiday:
    day: date
    name: str
    country: str  # "CA" or "US"


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """The n-th given weekday of a month (n = 1..5), e.g. the 3rd Monday of February."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def last_weekday(year: int, month: int, weekday: int) -> date:
    """The last given weekday of a month, e.g. the last Monday of May."""
    next_month = date(year + (month == 12), month % 12 + 1, 1)
    last = next_month - timedelta(days=1)
    return last - timedelta(days=(last.weekday() - weekday) % 7)


def easter_sunday(year: int) -> date:
    """Western Easter, using the anonymous Gregorian algorithm."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741 - name from the published algorithm
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return date(year, month, day)


def victoria_day(year: int) -> date:
    """The Monday before May 25."""
    may_24 = date(year, 5, 24)
    return may_24 - timedelta(days=may_24.weekday())


def canadian_holidays(year: int) -> list[Holiday]:
    days = [
        (date(year, 1, 1), "New Year's Day"),
        (nth_weekday(year, 2, MON, 3), "Family Day"),  # Ontario
        (easter_sunday(year) - timedelta(days=2), "Good Friday"),
        (victoria_day(year), "Victoria Day"),
        (date(year, 7, 1), "Canada Day"),
        (nth_weekday(year, 8, MON, 1), "Civic Holiday"),
        (nth_weekday(year, 9, MON, 1), "Labour Day"),
        (nth_weekday(year, 10, MON, 2), "Thanksgiving (Canada)"),
        (date(year, 12, 25), "Christmas Day"),
        (date(year, 12, 26), "Boxing Day"),
    ]
    return [Holiday(day, name, "CA") for day, name in days]


def us_holidays(year: int) -> list[Holiday]:
    days = [
        (date(year, 1, 1), "New Year's Day"),
        (nth_weekday(year, 1, MON, 3), "Martin Luther King Jr. Day"),
        (nth_weekday(year, 2, MON, 3), "Presidents' Day"),
        (last_weekday(year, 5, MON), "Memorial Day"),
        (date(year, 7, 4), "Independence Day"),
        (nth_weekday(year, 9, MON, 1), "Labor Day"),
        (nth_weekday(year, 10, MON, 2), "Columbus Day"),
        (date(year, 11, 11), "Veterans Day"),
        (nth_weekday(year, 11, THU, 4), "Thanksgiving (US)"),
        (date(year, 12, 25), "Christmas Day"),
    ]
    return [Holiday(day, name, "US") for day, name in days]


def holidays_between(first_year: int, last_year: int) -> list[Holiday]:
    result = []
    for year in range(first_year, last_year + 1):
        result += canadian_holidays(year) + us_holidays(year)
    return sorted(result, key=lambda h: (h.day, h.country))


def long_weekend_days(holiday: Holiday) -> list[date]:
    """The days of the long weekend a holiday creates (just the day itself if it's midweek)."""
    day = holiday.day
    if day.weekday() == MON:
        return [day - timedelta(days=2), day - timedelta(days=1), day]
    if day.weekday() == FRI:
        return [day, day + timedelta(days=1), day + timedelta(days=2)]
    if day.weekday() == THU:  # US Thanksgiving: many people take Friday off too
        return [day + timedelta(days=i) for i in range(4)]
    return [day]
