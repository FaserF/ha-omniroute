"""Sensors for OmniRoute integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import OmniRouteDataUpdateCoordinator
from .helpers import get_device_info


@dataclass(frozen=True, kw_only=True)
class OmniRouteSensorEntityDescription(SensorEntityDescription):
    """Describes an OmniRoute sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]
    extra_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSOR_DESCRIPTIONS: tuple[OmniRouteSensorEntityDescription, ...] = (
    OmniRouteSensorEntityDescription(
        key="status",
        name="Gateway Status",
        translation_key="status",
        icon="mdi:check-network",
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("status", "unknown"),
    ),
    OmniRouteSensorEntityDescription(
        key="latency_ms",
        name="Gateway Response Time",
        translation_key="latency_ms",
        icon="mdi:timer-outline",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("latency_ms"),
    ),
    OmniRouteSensorEntityDescription(
        key="active_cascades",
        name="Active Cascades",
        translation_key="active_cascades",
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
        translation_key="models_count",
        icon="mdi:robot",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("models_count", 0),
        extra_fn=lambda data: {"models": data.get("models", [])},
    ),
    OmniRouteSensorEntityDescription(
        key="quota_health",
        name="Quota Health",
        translation_key="quota_health",
        icon="mdi:credit-card-check",
        entity_registry_enabled_default=False,
        value_fn=lambda data: (
            data.get("quotas", {}).get("status", "optimal")
            if isinstance(data.get("quotas"), dict)
            else "optimal"
        ),
        extra_fn=lambda data: {
            "quotas": data.get("quotas", {}),
            "providers": data.get("providers", {}),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OmniRoute sensors from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OmniRouteDataUpdateCoordinator = data[DATA_COORDINATOR]

    entities = [
        OmniRouteSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class OmniRouteSensor(CoordinatorEntity[OmniRouteDataUpdateCoordinator], SensorEntity):
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
        sw_version = None
        if coordinator.data:
            sw_version = coordinator.data.get("version")
        self._attr_device_info = get_device_info(entry, sw_version)

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
