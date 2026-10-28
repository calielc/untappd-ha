"""Pick the update interval from the time of day. No Home Assistant imports."""

from __future__ import annotations

from datetime import time


def in_happy_hour(now: time, start: time, end: time) -> bool:
    """True when `now` is inside [start, end); the window may wrap past midnight."""
    if start == end:
        return False
    if start < end:
        return start <= now < end
    return now >= start or now < end


def pick_interval_minutes(now: time, normal: int, happy: int, start: time, end: time) -> int:
    """Faster interval inside the happy-hour window, normal interval outside it."""
    return happy if in_happy_hour(now, start, end) else normal
