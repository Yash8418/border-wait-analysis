"""Helpers that turn CBSA's free-text values into clean, typed values."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

# The tunnel has been published under two names; map both to one.
CROSSING_NAMES = {
    "ambassador bridge": "Ambassador Bridge",
    "windsor and detroit tunnel": "Detroit-Windsor Tunnel",
    "detroit and canada tunnel": "Detroit-Windsor Tunnel",
}

# Wait values that aren't a number of minutes, and what they mean.
STATUS_VALUES = {
    "no delay": ("reported", 0.0),
    "missed entry": ("missed", None),
    "temporarily closed": ("closed", None),
    "closed": ("closed", None),
    "not applicable": ("not_applicable", None),
}

TZ_OFFSETS = {
    "EDT": timezone(timedelta(hours=-4)),
    "EST": timezone(timedelta(hours=-5)),
}

_MINUTES = re.compile(r"^(\d+)(?:\s*min(?:ute)?s?)?$", re.IGNORECASE)
_TIMESTAMP = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+([A-Z]{3})$")


def normalize_crossing(name: str) -> str | None:
    """Return the canonical crossing name, or None for a crossing we don't track."""
    return CROSSING_NAMES.get(name.strip().lower())


def parse_wait(value: str) -> tuple[str, float | None]:
    """Parse a wait value into (status, minutes).

    >>> parse_wait("No delay")
    ('reported', 0.0)
    >>> parse_wait("10 minutes")
    ('reported', 10.0)
    >>> parse_wait("Missed entry")
    ('missed', None)
    """
    text = value.strip()
    known = STATUS_VALUES.get(text.lower())
    if known:
        return known
    match = _MINUTES.match(text)
    if match:
        return "reported", float(match.group(1))
    return "unknown", None


def parse_timestamp(value: str) -> datetime:
    """Parse '2014-04-04 13:52 EDT' into a timezone-aware datetime."""
    match = _TIMESTAMP.match(value.strip())
    if not match:
        raise ValueError(f"Unrecognised timestamp: {value!r}")
    local, zone = match.groups()
    if zone not in TZ_OFFSETS:
        raise ValueError(f"Unrecognised timezone {zone!r} in {value!r}")
    return datetime.strptime(local, "%Y-%m-%d %H:%M").replace(tzinfo=TZ_OFFSETS[zone])


MONTHS = {
    name: number
    for number, name in enumerate(
        ["January", "February", "March", "April", "May", "June", "July",
         "August", "September", "October", "November", "December"],
        start=1,
    )
}


def fiscal_to_calendar_month(month_name: str, fiscal_year: str) -> tuple[int, int]:
    """Convert a Government of Canada fiscal month to (year, month).

    The federal fiscal year runs April to March, so 'January' of '2019-20' is January 2020.

    >>> fiscal_to_calendar_month("April", "2019-20")
    (2019, 4)
    >>> fiscal_to_calendar_month("January", "2019-20")
    (2020, 1)
    """
    month = MONTHS[month_name.strip().title()]
    start_year = int(fiscal_year.split("-")[0])
    return (start_year, month) if month >= 4 else (start_year + 1, month)
