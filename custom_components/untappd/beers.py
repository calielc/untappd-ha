"""Parse the logged-in beer history pages and derive statistics. No Home Assistant imports."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from html import unescape

from .const import BASE_URL

_ITEM_SPLIT_RE = re.compile(r'<div class="beer-item"[^>]*data-bid="(\d+)"')
_NAME_RE = re.compile(r'<p class="name">.*?<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', re.S)
_BREWERY_RE = re.compile(r'<p class="brewery">.*?<a[^>]*>([^<]+)</a>', re.S)
_STYLE_RE = re.compile(r'<p class="style">([^<]*)</p>')
_YOUR_RE = re.compile(r"Your Rating \(([\d.]+)\)")
_GLOBAL_RE = re.compile(r"Global Rating \(([\d.]+)\)")
_ABV_RE = re.compile(r"([\d.]+)%\s*ABV")
_IBU_RE = re.compile(r"(\d+)\s*IBU")
_FIRST_RE = re.compile(r"First:.*?<abbr[^>]*>([\d/]+)</abbr>", re.S)
_RECENT_RE = re.compile(r"Recent:.*?<abbr[^>]*>([\d/]+)</abbr>", re.S)
_TOTAL_RE = re.compile(r"Total:\s*(\d+)")
_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class Beer:
    """One distinct beer from the beer history."""

    bid: str
    name: str | None = None
    brewery: str | None = None
    style: str | None = None
    rating: float | None = None
    global_rating: float | None = None
    abv: float | None = None
    ibu: int | None = None
    first: date | None = None
    recent: date | None = None
    total: int | None = None
    url: str | None = None

    @property
    def primary_style(self) -> str | None:
        """'IPA - Imperial / Double' -> 'IPA'."""
        return self.style.split(" - ")[0].strip() if self.style else None


def _date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%m/%d/%y").date()
    except ValueError:
        return None


def _float(regex: re.Pattern[str], block: str) -> float | None:
    return float(m.group(1)) if (m := regex.search(block)) else None


def parse_beers(html: str) -> list[Beer]:
    """Parse any page or fragment that contains beer-item blocks."""
    parts = _ITEM_SPLIT_RE.split(html)
    beers: list[Beer] = []
    for bid, block in zip(parts[1::2], parts[2::2], strict=True):
        beer = Beer(bid=bid)
        if m := _NAME_RE.search(block):
            beer.url = BASE_URL + m.group(1)
            beer.name = unescape(m.group(2)).strip()
        if m := _BREWERY_RE.search(block):
            beer.brewery = unescape(m.group(1)).strip()
        if m := _STYLE_RE.search(block):
            beer.style = unescape(m.group(1)).strip() or None
        beer.rating = _float(_YOUR_RE, block)
        beer.global_rating = _float(_GLOBAL_RE, block)
        beer.abv = _float(_ABV_RE, block)
        if m := _IBU_RE.search(block):
            beer.ibu = int(m.group(1))
        if m := _FIRST_RE.search(block):
            beer.first = _date(m.group(1))
        if m := _RECENT_RE.search(block):
            beer.recent = _date(m.group(1))
        if m := _TOTAL_RE.search(_TAG_RE.sub(" ", block)):
            beer.total = int(m.group(1))
        beers.append(beer)
    return beers


def _top(counter: Counter[str], n: int = 10) -> list[dict[str, int | str]]:
    return [{"name": name, "count": count} for name, count in counter.most_common(n)]


def _brief(beer: Beer) -> dict[str, object]:
    return {"beer": beer.name, "brewery": beer.brewery, "rating": beer.rating, "abv": beer.abv, "url": beer.url}


def compute_stats(beers: Iterable[Beer], today: date | None = None) -> dict[str, object]:
    """Aggregate statistics over the whole beer history."""
    beers = list(beers)
    today = today or date.today()
    rated = [b for b in beers if b.rating]
    with_abv = [b for b in beers if b.abv]
    with_ibu = [b for b in beers if b.ibu]
    breweries = Counter(b.brewery for b in beers if b.brewery)
    styles = Counter(b.primary_style for b in beers if b.primary_style)
    full_styles = {b.style for b in beers if b.style}
    recent_cut = today - timedelta(days=30)

    def mean(values: list[float]) -> float | None:
        return round(sum(values) / len(values), 2) if values else None

    best = sorted(rated, key=lambda b: (b.rating, b.global_rating or 0), reverse=True)[:5]
    strongest = max(with_abv, key=lambda b: b.abv, default=None)
    return {
        "beers_in_history": len(beers),
        "rated_beers": len(rated),
        "average_rating": mean([b.rating for b in rated]),
        "average_global_rating": mean([b.global_rating for b in beers if b.global_rating]),
        "average_abv": mean([b.abv for b in with_abv]),
        "average_ibu": mean([float(b.ibu) for b in with_ibu]),
        "unique_breweries": len(breweries),
        "unique_styles": len(styles),
        "unique_substyles": len(full_styles),
        "top_style": styles.most_common(1)[0][0] if styles else None,
        "top_styles": _top(styles),
        "top_brewery": breweries.most_common(1)[0][0] if breweries else None,
        "top_breweries": _top(breweries),
        "highest_rated": best[0].name if best else None,
        "highest_rated_beers": [_brief(b) for b in best],
        "strongest_beer": strongest.name if strongest else None,
        "strongest_beer_details": _brief(strongest) if strongest else None,
        "beers_this_year": sum(1 for b in beers if b.first and b.first.year == today.year),
        "beers_last_30_days": sum(1 for b in beers if b.first and b.first >= recent_cut),
        "rating_distribution": dict(sorted(Counter(str(b.rating) for b in rated).items())),
    }


def beer_to_dict(beer: Beer) -> dict[str, object]:
    """JSON-friendly form for the on-disk cache."""
    data = asdict(beer)
    for key in ("first", "recent"):
        data[key] = data[key].isoformat() if data[key] else None
    return data


def beer_from_dict(data: dict[str, object]) -> Beer:
    data = dict(data)
    for key in ("first", "recent"):
        value = data.get(key)
        data[key] = date.fromisoformat(value) if isinstance(value, str) else None
    return Beer(**data)  # type: ignore[arg-type]
