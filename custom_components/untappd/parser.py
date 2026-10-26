"""Parse a public Untappd profile page. No Home Assistant imports, so it is testable alone."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape

from .const import BASE_URL

_STAT_RE = re.compile(r'<span class="stat">\s*([\d,\.]+)\s*</span>\s*<span class="title">\s*([^<]+?)\s*</span>')
_ITEM_SPLIT_RE = re.compile(r'<div class="item\s*"\s+id="checkin_(\d+)"')
_BEER_RE = re.compile(r'<a\s+href="(/b/[^"]+)">([^<]+)</a>\s*by\s*<a\s+href="([^"]+)">([^<]+)</a>')
_VENUE_RE = re.compile(r'\sat\s*<a\s+href="(/v/[^"]+)"[^>]*>([^<]+)</a>')
_RATING_RE = re.compile(r'data-rating="([\d.]+)"')
_TIME_RE = re.compile(r'class="time timezoner[^"]*"[^>]*>([^<]+)<')
_IMAGE_RE = re.compile(r'class="label">\s*<img[^>]*src="([^"]+)"')
_COMMENT_RE = re.compile(r'<p class="comment-text"[^>]*>(.*?)</p>', re.S)


@dataclass
class Checkin:
    """One check-in."""

    checkin_id: str
    beer: str | None = None
    brewery: str | None = None
    rating: float | None = None
    venue: str | None = None
    comment: str | None = None
    checkin_time: datetime | None = None
    url: str | None = None
    beer_url: str | None = None
    image: str | None = None


@dataclass
class ProfileData:
    """Everything scraped from a profile."""

    username: str
    stats: dict[str, int] = field(default_factory=dict)
    checkins: list[Checkin] = field(default_factory=list)

    @property
    def last_checkin(self) -> Checkin | None:
        return self.checkins[0] if self.checkins else None


def _int(value: str) -> int | None:
    try:
        return int(value.replace(",", "").split(".")[0])
    except ValueError:
        return None


def _parse_checkin(checkin_id: str, block: str, username: str) -> Checkin:
    checkin = Checkin(checkin_id=checkin_id)
    checkin.url = f"{BASE_URL}/user/{username}/checkin/{checkin_id}"

    if m := _BEER_RE.search(block):
        checkin.beer_url = BASE_URL + m.group(1)
        checkin.beer = unescape(m.group(2)).strip()
        checkin.brewery = unescape(m.group(4)).strip()
    if m := _VENUE_RE.search(block):
        checkin.venue = unescape(m.group(2)).strip()
    if m := _RATING_RE.search(block):
        rating = float(m.group(1))
        checkin.rating = rating if rating > 0 else None
    if m := _TIME_RE.search(block):
        try:
            checkin.checkin_time = parsedate_to_datetime(m.group(1).strip())
        except (TypeError, ValueError):
            checkin.checkin_time = None
    if m := _IMAGE_RE.search(block):
        checkin.image = unescape(m.group(1))
    if m := _COMMENT_RE.search(block):
        text = unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
        checkin.comment = text or None
    return checkin


def parse_profile(html: str, username: str) -> ProfileData:
    """Parse profile HTML. Raises ValueError if it does not look like a profile."""
    stats: dict[str, int] = {}
    for value, title in _STAT_RE.findall(html):
        if (number := _int(value)) is not None:
            stats[title.strip().lower()] = number

    if not stats:
        raise ValueError("No profile stats found (private profile, wrong user, or page changed)")

    data = ProfileData(username=username, stats=stats)

    parts = _ITEM_SPLIT_RE.split(html)
    # parts = [prefix, id1, block1, id2, block2, ...]
    for checkin_id, block in zip(parts[1::2], parts[2::2], strict=True):
        data.checkins.append(_parse_checkin(checkin_id, block, username))
    return data
