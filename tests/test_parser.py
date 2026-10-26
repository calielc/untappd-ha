"""Parser tests. The parser has no Home Assistant imports, so these run with plain pytest."""

from __future__ import annotations

import importlib.util
import sys
import types
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent / "custom_components" / "untappd"


def _load_parser():
    """Load parser.py without importing the package (its __init__ needs Home Assistant)."""
    pkg = types.ModuleType("untappd_pkg")
    pkg.__path__ = [str(ROOT)]
    sys.modules["untappd_pkg"] = pkg
    for name in ("const", "parser"):
        spec = importlib.util.spec_from_file_location(f"untappd_pkg.{name}", ROOT / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"untappd_pkg.{name}"] = module
        spec.loader.exec_module(module)
    return sys.modules["untappd_pkg.parser"]


parser = _load_parser()
HTML = (Path(__file__).parent / "fixtures" / "profile.html").read_text(encoding="utf-8")


def test_stats() -> None:
    data = parser.parse_profile(HTML, "testuser")
    assert data.stats == {"total": 1321, "unique": 1227, "badges": 1621, "friends": 28}


def test_checkins_in_page_order() -> None:
    data = parser.parse_profile(HTML, "testuser")
    assert [c.checkin_id for c in data.checkins] == ["200", "199"]
    assert data.last_checkin.checkin_id == "200"


def test_full_checkin_fields() -> None:
    c = parser.parse_profile(HTML, "testuser").checkins[0]
    assert c.beer == "Dark Ale & Co."
    assert c.brewery == "Example Brewery"
    assert c.venue == "The Pub"
    assert c.rating == 4.25
    assert c.comment == "Roasty & smooth"
    assert c.checkin_time == datetime(2026, 10, 17, 21, 5, 51, tzinfo=UTC)
    assert c.url == "https://untappd.com/user/testuser/checkin/200"
    assert c.beer_url == "https://untappd.com/b/example-brewery-dark-ale/111"
    assert c.image.endswith("beer-111_sm.jpeg")


def test_checkin_without_venue_comment_or_rating() -> None:
    c = parser.parse_profile(HTML, "testuser").checkins[1]
    assert c.venue is None
    assert c.comment is None
    assert c.rating is None


def test_page_without_stats_raises() -> None:
    with pytest.raises(ValueError):
        parser.parse_profile("<html><body>Private profile</body></html>", "testuser")


def test_profile_without_checkins() -> None:
    stats_only = HTML.split('<div class="item ')[0] + "</body></html>"
    data = parser.parse_profile(stats_only, "testuser")
    assert data.checkins == []
    assert data.last_checkin is None
