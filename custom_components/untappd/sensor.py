"""Untappd sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
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
from .parser import Checkin, ProfileData

PARALLEL_UPDATES = 0

RECENT_CHECKINS = 5


@dataclass(frozen=True, kw_only=True)
class UntappdSensorDescription(SensorEntityDescription):
    value_fn: Callable[[ProfileData], Any]
    attrs_fn: Callable[[ProfileData], dict[str, Any]] | None = None
    requires_cookie: bool = False
    placeholders: dict[str, str] = field(default_factory=dict)


def _last(data: ProfileData, attr: str) -> Any:
    return getattr(data.last_checkin, attr, None) if data.last_checkin else None


def _checkin_attrs(c: Checkin | None) -> dict[str, Any]:
    if not c:
        return {}
    return {
        "checkin_id": c.checkin_id,
        "beer": c.beer,
        "brewery": c.brewery,
        "rating": c.rating,
        "venue": c.venue,
        "comment": c.comment,
        "checkin_time": c.checkin_time.isoformat() if c.checkin_time else None,
        "url": c.url,
        "beer_url": c.beer_url,
        "entity_picture": c.image,
    }


def _last_attrs(data: ProfileData) -> dict[str, Any]:
    return _checkin_attrs(data.last_checkin)


def _nth(data: ProfileData, index: int) -> Checkin | None:
    return data.checkins[index] if index < len(data.checkins) else None


def _recent_label(data: ProfileData, index: int) -> str | None:
    c = _nth(data, index)
    if not c or not c.beer:
        return None
    return f"{c.beer} by {c.brewery}" if c.brewery else c.beer


def _recent(index: int) -> UntappdSensorDescription:
    return UntappdSensorDescription(
        key=f"recent_checkin_{index + 1}",
        translation_key="recent_checkin",
        placeholders={"n": str(index + 1)},
        icon="mdi:beer",
        value_fn=lambda d: _recent_label(d, index),
        attrs_fn=lambda d: _checkin_attrs(_nth(d, index)),
    )


def _stat(key: str) -> Callable[[ProfileData], int | None]:
    return lambda d: d.stats.get(key)


def _beer(key: str) -> Callable[[ProfileData], Any]:
    return lambda d: d.beer_stats.get(key)


def _beer_attrs(*keys: str) -> Callable[[ProfileData], dict[str, Any]]:
    return lambda d: {k: d.beer_stats[k] for k in keys if k in d.beer_stats}


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
    *(_recent(i) for i in range(RECENT_CHECKINS)),
)

# Beer-history statistics. Only created when a session cookie is configured.
BEER_SENSORS: tuple[UntappdSensorDescription, ...] = (
    UntappdSensorDescription(
        key="average_rating",
        translation_key="average_rating",
        icon="mdi:star-half-full",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        requires_cookie=True,
        value_fn=_beer("average_rating"),
        attrs_fn=_beer_attrs("rating_distribution"),
    ),
    UntappdSensorDescription(
        key="average_global_rating",
        translation_key="average_global_rating",
        icon="mdi:star-outline",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        requires_cookie=True,
        value_fn=_beer("average_global_rating"),
    ),
    UntappdSensorDescription(
        key="rated_beers",
        translation_key="rated_beers",
        icon="mdi:star-check",
        state_class=SensorStateClass.TOTAL,
        requires_cookie=True,
        value_fn=_beer("rated_beers"),
    ),
    UntappdSensorDescription(
        key="average_abv",
        translation_key="average_abv",
        icon="mdi:percent",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        requires_cookie=True,
        value_fn=_beer("average_abv"),
    ),
    UntappdSensorDescription(
        key="average_ibu",
        translation_key="average_ibu",
        icon="mdi:leaf",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        requires_cookie=True,
        value_fn=_beer("average_ibu"),
    ),
    UntappdSensorDescription(
        key="unique_breweries",
        translation_key="unique_breweries",
        icon="mdi:factory",
        state_class=SensorStateClass.TOTAL,
        requires_cookie=True,
        value_fn=_beer("unique_breweries"),
    ),
    UntappdSensorDescription(
        key="unique_styles",
        translation_key="unique_styles",
        icon="mdi:shape",
        state_class=SensorStateClass.TOTAL,
        requires_cookie=True,
        value_fn=_beer("unique_styles"),
        attrs_fn=_beer_attrs("unique_substyles"),
    ),
    UntappdSensorDescription(
        key="top_style",
        translation_key="top_style",
        icon="mdi:podium-gold",
        requires_cookie=True,
        value_fn=_beer("top_style"),
        attrs_fn=_beer_attrs("top_styles"),
    ),
    UntappdSensorDescription(
        key="top_brewery",
        translation_key="top_brewery",
        icon="mdi:podium",
        requires_cookie=True,
        value_fn=_beer("top_brewery"),
        attrs_fn=_beer_attrs("top_breweries"),
    ),
    UntappdSensorDescription(
        key="highest_rated",
        translation_key="highest_rated",
        icon="mdi:trophy",
        requires_cookie=True,
        value_fn=_beer("highest_rated"),
        attrs_fn=_beer_attrs("highest_rated_beers"),
    ),
    UntappdSensorDescription(
        key="strongest_beer",
        translation_key="strongest_beer",
        icon="mdi:flash",
        requires_cookie=True,
        value_fn=_beer("strongest_beer"),
        attrs_fn=_beer_attrs("strongest_beer_details"),
    ),
    UntappdSensorDescription(
        key="beers_this_year",
        translation_key="beers_this_year",
        icon="mdi:calendar",
        state_class=SensorStateClass.TOTAL,
        requires_cookie=True,
        value_fn=_beer("beers_this_year"),
    ),
    UntappdSensorDescription(
        key="beers_last_30_days",
        translation_key="beers_last_30_days",
        icon="mdi:calendar-month",
        state_class=SensorStateClass.MEASUREMENT,
        requires_cookie=True,
        value_fn=_beer("beers_last_30_days"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: UntappdConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    descriptions = SENSORS + (BEER_SENSORS if coordinator.cookie else ())
    async_add_entities(UntappdSensor(coordinator, d) for d in descriptions)


class UntappdSensor(UntappdEntity, SensorEntity):
    entity_description: UntappdSensorDescription

    def __init__(self, coordinator: UntappdCoordinator, description: UntappdSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.username.lower()}_{description.key}"
        if description.placeholders:
            self._attr_translation_placeholders = description.placeholders

    @property
    def native_value(self) -> int | float | str | datetime | None:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        fn = self.entity_description.attrs_fn
        return fn(self.coordinator.data) if fn else None
