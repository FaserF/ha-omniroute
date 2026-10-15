"""Sensors for OmniRoute integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import OmniRouteDataUpdateCoordinator
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class OmniRouteSensorEntityDescription(SensorEntityDescription):
    """Describes an OmniRoute sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]
    extra_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSOR_DESCRIPTIONS: tuple[OmniRouteSensorEntityDescription, ...] = (
    OmniRouteSensorEntityDescription(
        key="status",
        name="Gateway Status",
        icon="mdi:check-network",
        value_fn=lambda data: data.get("status", "unknown"),
    ),
    OmniRouteSensorEntityDescription(
        key="latency_ms",
        name="Gateway Response Time",
        icon="mdi:timer-outline",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("latency_ms"),
    ),
    OmniRouteSensorEntityDescription(
        key="active_cascades",
        name="Active Cascades",
        icon="mdi:transit-connection-variant",
        value_fn=lambda data: len(data.get("active_cascades", [])),
        extra_fn=lambda data: {
            "active_cascades": data.get("active_cascades", []),
            "cascade_status": data.get("cascade_status", {}),
        },
    ),
    OmniRouteSensorEntityDescription(
        key="models_count",
        name="Available Models",
        icon="mdi:robot",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("models_count", 0),
        extra_fn=lambda data: {"models": data.get("models", [])},
    ),
    OmniRouteSensorEntityDescription(
        key="quota_health",
        name="Quota Health",
        icon="mdi:gauge",
        value_fn=lambda data: "optimal" if data.get("reachable") else "offline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OmniRoute sensors from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OmniRouteDataUpdateCoordinator = data["coordinator"]

    entities = [
        OmniRouteSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class OmniRouteSensor(
    CoordinatorEntity[OmniRouteDataUpdateCoordinator], SensorEntity
):
    """Representation of an OmniRoute sensor."""

    entity_description: OmniRouteSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OmniRouteDataUpdateCoordinator,
        entry: ConfigEntry,
        description: OmniRouteSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "OmniRoute Gateway",
            "manufacturer": "FaserF",
            "model": "Hermes AI Gateway",
        }

    @property
    def native_value(self) -> Any:
        """Return native value of the sensor."""
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if not self.coordinator.data or not self.entity_description.extra_fn:
            return None
        return self.entity_description.extra_fn(self.coordinator.data)
