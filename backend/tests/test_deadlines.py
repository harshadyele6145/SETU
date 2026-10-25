import pytest
from datetime import datetime, date, timedelta, timezone
from backend.app.services.deadline_service import (
    is_business_day, 
    add_business_days, 
    calculate_days_difference,
    INDIAN_PUBLIC_HOLIDAYS_2026
)


def test_business_day_determination():
    # Saturday (2026-03-21) and Sunday (2026-03-22)
    sat = date(2026, 3, 21)
    sun = date(2026, 3, 22)
    assert not is_business_day(sat)
    assert not is_business_day(sun)

    # Monday (2026-03-23) - regular workday
    mon = date(2026, 3, 23)
    assert is_business_day(mon)

    # Republic Day (2026-01-26 is Monday but a Gazetted holiday)
    rep_day = date(2026, 1, 26)
    assert not is_business_day(rep_day)


def test_add_business_days_skips_weekends_and_holidays():
    # Start on Friday 2026-01-23 at 10:00 UTC
    # Jan 24 (Sat) - skipped
    # Jan 25 (Sun) - skipped
    # Jan 26 (Mon, Republic Day) - skipped
    # Jan 27 (Tue) - Day 1
    # Jan 28 (Wed) - Day 2
    # Jan 29 (Thu) - Day 3
    start = datetime(2026, 1, 23, 10, 0, tzinfo=timezone.utc)
    target = add_business_days(start, 3)
    assert target.date() == date(2026, 1, 29)


def test_calculate_days_difference():
    now = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)

    # 10 days in the future
    future_dt = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)
    assert calculate_days_difference(future_dt, now) == 10

    # 5 days in the past (overdue)
    past_dt = datetime(2026, 4, 26, 12, 0, tzinfo=timezone.utc)
    assert calculate_days_difference(past_dt, now) == -5

    # Date object difference
    future_date = date(2026, 5, 8)
    assert calculate_days_difference(future_date, now) == 7
