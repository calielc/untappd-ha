"""Data update coordinator for Untappd."""

from __future__ import annotations

import logging
from datetime import timedelta

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import BASE_URL, CONF_SCAN_INTERVAL, CONF_USERNAME, DEFAULT_SCAN_INTERVAL, DOMAIN, USER_AGENT
from .parser import ProfileData, parse_profile

_LOGGER = logging.getLogger(__name__)


async def async_fetch_profile(hass: HomeAssistant, username: str) -> ProfileData:
    """Fetch and parse a public profile.

    Raises ValueError for an unknown user or an unreadable page, and
    ClientError/TimeoutError for network problems.
    """
    session = async_get_clientsession(hass)
    async with session.get(
        f"{BASE_URL}/user/{username}",
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en"},
        timeout=30,
    ) as resp:
        if resp.status == 404:
            raise ValueError("user_not_found")
        resp.raise_for_status()
        html = await resp.text()
    return parse_profile(html, username)


class UntappdCoordinator(DataUpdateCoordinator[ProfileData]):
    """Poll the profile page."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        minutes = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.data[CONF_USERNAME]}",
            update_interval=timedelta(minutes=minutes),
        )
        self.username: str = entry.data[CONF_USERNAME]

    async def _async_update_data(self) -> ProfileData:
        try:
            return await async_fetch_profile(self.hass, self.username)
        except (ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Could not read Untappd profile: {err}") from err
