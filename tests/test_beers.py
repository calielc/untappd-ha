"""Beer history parser and statistics tests (no Home Assistant needed)."""

from __future__ import annotations

import importlib.util
import sys
import types
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent / "custom_components" / "untappd"


def _load():
    pkg = types.ModuleType("untappd_pkg2")
    pkg.__path__ = [str(ROOT)]
    sys.modules["untappd_pkg2"] = pkg
    for name in ("const", "beers"):
        spec = importlib.util.spec_from_file_location(f"untappd_pkg2.{name}", ROOT / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"untappd_pkg2.{name}"] = module
        spec.loader.exec_module(module)
    return sys.modules["untappd_pkg2.beers"]


beers = _load()
HTML = (Path(__file__).parent / "fixtures" / "beers.html").read_text(encoding="utf-8")
TODAY = date(2026, 10, 26)


def test_parse_full_item() -> None:
    b = beers.parse_beers(HTML)[0]
    assert (b.bid, b.name, b.brewery) == ("111", "Dark Ale & Co.", "Example Brewery")
    assert b.style == "Stout - Russian Imperial"
    assert b.primary_style == "Stout"
    assert (b.rating, b.global_rating, b.abv, b.ibu, b.total) == (3.75, 3.8, 11.0, 80, 2)
    assert b.first == date(2026, 10, 17)
    assert b.recent == date(2026, 10, 20)
    assert b.url == "https://untappd.com/b/example-dark-ale/111"


def test_unrated_beer_and_missing_ibu() -> None:
    b = beers.parse_beers(HTML)[1]
    assert b.rating is None
    assert b.global_rating == 3.2
    assert b.ibu is None


def test_empty_fragment() -> None:
    assert beers.parse_beers("<div>no more</div>") == []


def test_stats() -> None:
    s = beers.compute_stats(beers.parse_beers(HTML), today=TODAY)
    assert s["beers_in_history"] == 3
    assert s["rated_beers"] == 2
    assert s["average_rating"] == 3.88
    assert s["average_abv"] == 7.83
    assert s["average_ibu"] == 60.0
    assert s["unique_breweries"] == 2
    assert s["unique_styles"] == 3
    assert s["top_brewery"] == "Example Brewery"
    assert s["highest_rated"] == "Hazy IPA"
    assert s["strongest_beer"] == "Dark Ale & Co."
    assert s["beers_this_year"] == 3
    assert s["beers_last_30_days"] == 2
    assert s["rating_distribution"] == {"3.75": 1, "4.0": 1}


def test_stats_empty() -> None:
    s = beers.compute_stats([], today=TODAY)
    assert s["average_rating"] is None
    assert s["top_style"] is None
