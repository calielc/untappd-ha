"""Diagnostics for Untappd."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.core import HomeAssistant

from . import UntappdConfigEntry


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: UntappdConfigEntry) -> dict[str, Any]:
    """Return diagnostics. The username is left out."""
    data = entry.runtime_data.data
    return {
        "stats": data.stats,
        "checkin_count_on_page": len(data.checkins),
        "last_checkin": asdict(data.last_checkin) if data.last_checkin else None,
        "update_interval": str(entry.runtime_data.update_interval),
        "last_update_success": entry.runtime_data.last_update_success,
    }
