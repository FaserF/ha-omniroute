"""Sensors for OmniRoute integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
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

from .const import DATA_COORDINATOR, DATA_SUGGESTIONS_SENSOR, DOMAIN
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
    OmniRouteSensorEntityDescription(
        key="daily_tokens",
        name="Daily Tokens Consumed",
        translation_key="daily_tokens",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: (
            data.get("daily_tokens")
            or data.get("analytics", {}).get("total_tokens")
            or data.get("quotas", {}).get("total_tokens", 0)
        ),
        extra_fn=lambda data: data.get("analytics", {}),
    ),
    OmniRouteSensorEntityDescription(
        key="daily_cost",
        name="Daily Estimated Cost",
        translation_key="daily_cost",
        icon="mdi:currency-usd",
        native_unit_of_measurement="USD",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: round(
            float(
                data.get("daily_cost") or data.get("analytics", {}).get("cost_usd", 0.0)
            ),
            4,
        ),
    ),
    OmniRouteSensorEntityDescription(
        key="quota_reset",
        name="Quota Reset Countdown",
        translation_key="quota_reset",
        icon="mdi:clock-fast",
        value_fn=lambda data: str(
            data.get("quota_reset")
            or data.get("quotas", {}).get("next_reset")
            or "Optimal"
        ),
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

    entities: list[SensorEntity] = [
        OmniRouteSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    ]
    sugg_sensor = OmniRouteAutomationSuggestionsSensor(coordinator, entry)
    entities.append(sugg_sensor)
    data[DATA_SUGGESTIONS_SENSOR] = sugg_sensor
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


class OmniRouteAutomationSuggestionsSensor(
    CoordinatorEntity[OmniRouteDataUpdateCoordinator], SensorEntity
):
    """Sensor exposing the latest AI-generated automation suggestions."""

    _attr_has_entity_name = True
    _attr_name = "AI Automation Suggestions"
    _attr_icon = "mdi:robot-happy-outline"

    def __init__(
        self,
        coordinator: OmniRouteDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize suggestions sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_automation_suggestions"
        sw_version = coordinator.data.get("version") if coordinator.data else None
        self._attr_device_info = get_device_info(entry, sw_version)
        self._state = "No Suggestions"
        self._attributes: dict[str, Any] = {
            "description": None,
            "yaml_block": None,
            "last_update": None,
            "entities_processed_count": 0,
            "model": None,
        }

    @property
    def native_value(self) -> str:
        """Return state of sensor."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return suggestions attributes."""
        return self._attributes

    def set_suggestion(
        self,
        description: str,
        yaml_block: str,
        model: str,
        entities_processed_count: int,
    ) -> None:
        """Update suggestion content and state."""
        self._state = "Suggestions Available"
        self._attributes = {
            "description": description,
            "yaml_block": yaml_block,
            "last_update": datetime.now(UTC).isoformat(),
            "entities_processed_count": entities_processed_count,
            "model": model,
        }
        self.async_write_ha_state()
