"""Untappd sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UntappdConfigEntry
from .coordinator import UntappdCoordinator
from .entity import UntappdEntity
from .parser import ProfileData


@dataclass(frozen=True, kw_only=True)
class UntappdSensorDescription(SensorEntityDescription):
    value_fn: Callable[[ProfileData], Any]
    attrs_fn: Callable[[ProfileData], dict[str, Any]] | None = None


def _last(data: ProfileData, attr: str) -> Any:
    return getattr(data.last_checkin, attr, None) if data.last_checkin else None


def _last_attrs(data: ProfileData) -> dict[str, Any]:
    c = data.last_checkin
    if not c:
        return {}
    return {
        "checkin_id": c.checkin_id,
        "beer": c.beer,
        "brewery": c.brewery,
        "rating": c.rating,
        "venue": c.venue,
        "comment": c.comment,
        "url": c.url,
        "beer_url": c.beer_url,
        "entity_picture": c.image,
    }


def _stat(key: str) -> Callable[[ProfileData], int | None]:
    return lambda d: d.stats.get(key)


SENSORS: tuple[UntappdSensorDescription, ...] = (
    UntappdSensorDescription(
        key="total",
        translation_key="total",
        icon="mdi:beer",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_stat("total"),
    ),
    UntappdSensorDescription(
        key="unique",
        translation_key="unique",
        icon="mdi:beer-outline",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_stat("unique"),
    ),
    UntappdSensorDescription(
        key="badges",
        translation_key="badges",
        icon="mdi:medal",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_stat("badges"),
    ),
    UntappdSensorDescription(
        key="friends",
        translation_key="friends",
        icon="mdi:account-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_stat("friends"),
    ),
    UntappdSensorDescription(
        key="last_checkin",
        translation_key="last_checkin",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _last(d, "checkin_time"),
        attrs_fn=_last_attrs,
    ),
    UntappdSensorDescription(
        key="last_beer",
        translation_key="last_beer",
        icon="mdi:glass-mug-variant",
        value_fn=lambda d: _last(d, "beer"),
        attrs_fn=_last_attrs,
    ),
    UntappdSensorDescription(
        key="last_rating",
        translation_key="last_rating",
        icon="mdi:star",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _last(d, "rating"),
    ),
)


PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: UntappdConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(UntappdSensor(coordinator, d) for d in SENSORS)


class UntappdSensor(UntappdEntity, SensorEntity):
    entity_description: UntappdSensorDescription

    def __init__(self, coordinator: UntappdCoordinator, description: UntappdSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.username.lower()}_{description.key}"

    @property
    def native_value(self) -> int | float | str | datetime | None:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        fn = self.entity_description.attrs_fn
        return fn(self.coordinator.data) if fn else None
