"""Fires an event for every new check-in seen on the profile."""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UntappdConfigEntry
from .const import EVENT_NEW_CHECKIN
from .coordinator import UntappdCoordinator
from .entity import UntappdEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: UntappdConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([UntappdCheckinEvent(entry.runtime_data)])


class UntappdCheckinEvent(UntappdEntity, EventEntity):
    _attr_translation_key = "checkin"

    def __init__(self, coordinator: UntappdCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_event_types = [EVENT_NEW_CHECKIN]
        self._attr_unique_id = f"{coordinator.username.lower()}_checkin_event"
        # Start from what is already on the page so a restart never replays old check-ins.
        self._seen: set[str] = {c.checkin_id for c in coordinator.data.checkins}

    @callback
    def _handle_coordinator_update(self) -> None:
        new = [c for c in self.coordinator.data.checkins if c.checkin_id not in self._seen]
        # Oldest first so the entity ends on the newest check-in.
        for c in reversed(new):
            self._seen.add(c.checkin_id)
            self._trigger_event(
                EVENT_NEW_CHECKIN,
                {
                    "checkin_id": c.checkin_id,
                    "beer": c.beer,
                    "brewery": c.brewery,
                    "rating": c.rating,
                    "venue": c.venue,
                    "comment": c.comment,
                    "url": c.url,
                },
            )
        super()._handle_coordinator_update()
