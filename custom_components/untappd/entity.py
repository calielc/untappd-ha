"""Base entity."""

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BASE_URL, DOMAIN
from .coordinator import UntappdCoordinator


class UntappdEntity(CoordinatorEntity[UntappdCoordinator]):
    _attr_has_entity_name = True
    _attr_attribution = "Data from the public Untappd profile page"

    def __init__(self, coordinator: UntappdCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, coordinator.username.lower())},
            name=f"Untappd {coordinator.username}",
            manufacturer="Untappd",
            configuration_url=f"{BASE_URL}/user/{coordinator.username}",
        )
