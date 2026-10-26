"""The Untappd integration (reads a public profile; Untappd closed its public API)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import UntappdCoordinator

PLATFORMS = ["sensor", "event"]

type UntappdConfigEntry = ConfigEntry[UntappdCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: UntappdConfigEntry) -> bool:
    coordinator = UntappdCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_reload(hass: HomeAssistant, entry: UntappdConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: UntappdConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
