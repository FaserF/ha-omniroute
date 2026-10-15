"""Binary sensor platform for OmniRoute integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import OmniRouteDataUpdateCoordinator
from .helpers import get_device_info


@dataclass(frozen=True, kw_only=True)
class OmniRouteBinarySensorDescription(BinarySensorEntityDescription):
    """Describes an OmniRoute binary sensor entity."""

    is_on_fn: Callable[[dict[str, Any]], bool]
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


BINARY_SENSORS: tuple[OmniRouteBinarySensorDescription, ...] = (
    OmniRouteBinarySensorDescription(
        key="connected",
        name="Connected",
        translation_key="connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: bool(data.get("reachable", False)),
    ),
    OmniRouteBinarySensorDescription(
        key="healthy",
        name="Healthy",
        translation_key="healthy",
        icon="mdi:heart-pulse",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda data: bool(data.get("healthy", False)),
        attrs_fn=lambda data: {
            "status": data.get("status", "unknown"),
            "active_cascades_count": len(data.get("active_cascades", [])),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OmniRoute binary sensors from config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OmniRouteDataUpdateCoordinator = entry_data[DATA_COORDINATOR]

    entities = [
        OmniRouteBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSORS
    ]
    async_add_entities(entities)


class OmniRouteBinarySensor(
    CoordinatorEntity[OmniRouteDataUpdateCoordinator], BinarySensorEntity
):
    """Representation of an OmniRoute binary sensor."""

    entity_description: OmniRouteBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OmniRouteDataUpdateCoordinator,
        entry: ConfigEntry,
        description: OmniRouteBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        sw_version = None
        if coordinator.data:
            sw_version = coordinator.data.get("version")
        self._attr_device_info = get_device_info(entry, sw_version)

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return False
        return self.entity_description.is_on_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if not self.coordinator.data or not self.entity_description.attrs_fn:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data)
