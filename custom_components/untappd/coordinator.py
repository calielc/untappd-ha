"""Data update coordinator for Untappd."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta
from datetime import time as dtime

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .beers import Beer, beer_from_dict, beer_to_dict, compute_stats, parse_beers
from .const import (
    BASE_URL,
    BROWSER_USER_AGENT,
    CONF_COOKIE,
    CONF_HAPPY_END,
    CONF_HAPPY_INTERVAL,
    CONF_HAPPY_START,
    CONF_SCAN_INTERVAL,
    CONF_USER_AGENT,
    CONF_USERNAME,
    DEFAULT_HAPPY_END,
    DEFAULT_HAPPY_INTERVAL,
    DEFAULT_HAPPY_START,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FULL_SYNC_INTERVAL,
    MAX_PAGES,
    PAGE_DELAY,
    USER_AGENT,
)
from .parser import ProfileData, parse_profile, profile_url
from .schedule import pick_interval_minutes

_LOGGER = logging.getLogger(__name__)

_REDIRECTS = (301, 302, 303, 307, 308)


async def async_fetch_html(
    hass: HomeAssistant, url: str, *, cookie: str | None = None, user_agent: str | None = None
) -> str:
    """GET a page.

    Raises ValueError for 404 or an unexpected redirect, ConfigEntryAuthFailed when a
    cookie was sent but Untappd sends us to the login page, and ClientError/TimeoutError
    for network problems.
    """
    headers = {"User-Agent": user_agent or USER_AGENT, "Accept-Language": "en"}
    if cookie:
        headers["Cookie"] = cookie
    session = async_get_clientsession(hass)
    async with session.get(url, headers=headers, timeout=30, allow_redirects=False) as resp:
        if resp.status in _REDIRECTS:
            if "/login" in resp.headers.get("Location", ""):
                raise ConfigEntryAuthFailed("Untappd session cookie is missing or expired")
            raise ValueError(f"unexpected_redirect:{resp.status}")
        if resp.status == 404:
            raise ValueError("user_not_found")
        resp.raise_for_status()
        return await resp.text()


async def async_fetch_profile(hass: HomeAssistant, username: str) -> ProfileData:
    """Fetch and parse a public profile."""
    html = await async_fetch_html(hass, profile_url(username, int(time.time())))
    return parse_profile(html, username)


async def async_fetch_beer_page(
    hass: HomeAssistant, username: str, cookie: str, user_agent: str | None, offset: int = 0
) -> list[Beer]:
    """Fetch one page (25 beers) of the logged-in beer history, newest first."""
    if offset:
        url = f"{BASE_URL}/profile/more_beer/{username}/{offset}?sort=date"
    else:
        url = f"{BASE_URL}/user/{username}/beers?sort=date"
    html = await async_fetch_html(hass, url, cookie=cookie, user_agent=user_agent or BROWSER_USER_AGENT)
    beers = parse_beers(html)
    if not offset and not beers and "beer-item" not in html:
        # Not redirected to login, yet no beer list: most likely a bot-protection page.
        raise ValueError("beer_history_unreadable")
    return beers


class UntappdCoordinator(DataUpdateCoordinator[ProfileData]):
    """Poll the profile page, plus the beer history when a session cookie is set."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        options = entry.options
        self._normal_minutes: int = options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self._happy_minutes: int = options.get(CONF_HAPPY_INTERVAL, DEFAULT_HAPPY_INTERVAL)
        self._happy_start = dtime.fromisoformat(options.get(CONF_HAPPY_START, DEFAULT_HAPPY_START))
        self._happy_end = dtime.fromisoformat(options.get(CONF_HAPPY_END, DEFAULT_HAPPY_END))
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.data[CONF_USERNAME]}",
            update_interval=timedelta(minutes=self._current_minutes()),
        )
        self.username: str = entry.data[CONF_USERNAME]
        self.cookie: str | None = entry.data.get(CONF_COOKIE) or None
        self.user_agent: str | None = entry.data.get(CONF_USER_AGENT) or None
        self._beers: dict[str, Beer] = {}
        self._last_full_sync: datetime | None = None
        self._syncing = False
        self._store: Store[dict] = Store(hass, 1, f"{DOMAIN}.{self.username.lower()}.beers")

    def _current_minutes(self) -> int:
        """Local time decides: faster polling during happy hour, normal otherwise."""
        return pick_interval_minutes(
            dt_util.now().time(), self._normal_minutes, self._happy_minutes, self._happy_start, self._happy_end
        )

    async def async_load_library(self) -> None:
        """Restore the cached beer history so a restart does not need a full re-sync."""
        if not self.cookie:
            return
        stored = await self._store.async_load()
        if not stored:
            return
        self._beers = {b["bid"]: beer_from_dict(b) for b in stored.get("beers", [])}
        if synced := stored.get("synced"):
            self._last_full_sync = dt_util.parse_datetime(synced)

    async def _async_update_data(self) -> ProfileData:
        # The next refresh is scheduled after this one, using the interval set here.
        self.update_interval = timedelta(minutes=self._current_minutes())
        try:
            data = await async_fetch_profile(self.hass, self.username)
            if self.cookie:
                await self._async_refresh_beers(data)
        except ConfigEntryAuthFailed:
            raise
        except (ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Could not read Untappd data: {err}") from err
        return data

    async def _async_refresh_beers(self, data: ProfileData) -> None:
        # The newest page keeps recent beers current between full syncs.
        for beer in await async_fetch_beer_page(self.hass, self.username, self.cookie, self.user_agent):
            self._beers[beer.bid] = beer
        self._apply_stats(data)

        stale = self._last_full_sync is None or dt_util.utcnow() - self._last_full_sync > FULL_SYNC_INTERVAL
        if stale and not self._syncing:
            self._syncing = True
            self.config_entry.async_create_background_task(
                self.hass, self._async_full_sync(), name=f"untappd full sync {self.username}"
            )

    def _apply_stats(self, data: ProfileData) -> None:
        # Stats from a partial library would be misleading, so wait for the first full sync.
        data.beer_stats = compute_stats(self._beers.values()) if self._last_full_sync else {}

    async def _async_full_sync(self) -> None:
        """Walk the whole beer history, politely."""
        try:
            beers: dict[str, Beer] = {}
            offset = 0
            for _ in range(MAX_PAGES):
                page = await async_fetch_beer_page(self.hass, self.username, self.cookie, self.user_agent, offset)
                if not page:
                    break
                for beer in page:
                    beers[beer.bid] = beer
                offset += len(page)
                await asyncio.sleep(PAGE_DELAY)
            if not beers:
                return
            self._beers = beers
            self._last_full_sync = dt_util.utcnow()
            await self._store.async_save(
                {"synced": self._last_full_sync.isoformat(), "beers": [beer_to_dict(b) for b in beers.values()]}
            )
            _LOGGER.debug("Untappd full sync for %s finished: %d beers", self.username, len(beers))
            if self.data:
                self._apply_stats(self.data)
                self.async_set_updated_data(self.data)
        except ConfigEntryAuthFailed:
            self.config_entry.async_start_reauth(self.hass)
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.warning("Untappd full sync for %s failed, will retry: %s", self.username, err)
        finally:
            self._syncing = False
