"""Happy-hour interval selection (no Home Assistant needed)."""

from __future__ import annotations

import importlib.util
from datetime import time
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "untappd_schedule", Path(__file__).parent.parent / "custom_components" / "untappd" / "schedule.py"
)
schedule = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(schedule)

START, END = time(17, 0), time(1, 0)  # wraps past midnight


def test_inside_wrapping_window() -> None:
    for t in (time(17, 0), time(21, 30), time(23, 59), time(0, 0), time(0, 59)):
        assert schedule.in_happy_hour(t, START, END), t


def test_outside_wrapping_window() -> None:
    for t in (time(1, 0), time(8, 0), time(16, 59)):
        assert not schedule.in_happy_hour(t, START, END), t


def test_same_day_window() -> None:
    assert schedule.in_happy_hour(time(18, 0), time(17, 0), time(20, 0))
    assert not schedule.in_happy_hour(time(20, 0), time(17, 0), time(20, 0))


def test_equal_start_and_end_disables() -> None:
    assert not schedule.in_happy_hour(time(12, 0), time(17, 0), time(17, 0))


def test_pick_interval() -> None:
    assert schedule.pick_interval_minutes(time(22, 0), 30, 15, START, END) == 15
    assert schedule.pick_interval_minutes(time(9, 0), 30, 15, START, END) == 30
