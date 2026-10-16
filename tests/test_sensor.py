"""Test OmniRoute sensor platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.omniroute.const import (
    DATA_COORDINATOR,
    DEFAULT_MANUFACTURER,
    DEFAULT_MODEL,
    DOMAIN,
)
from custom_components.omniroute.sensor import (
    SENSOR_DESCRIPTIONS,
    OmniRouteAutomationSuggestionsSensor,
    OmniRouteSensor,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_sensor_setup_entry(hass, mock_config_entry):
    """Test setup of sensor entities."""
    mock_add = MagicMock()
    mock_coord = MagicMock()
    mock_coord.data = {
        "status": "ok",
        "reachable": True,
        "latency_ms": 15.2,
        "active_cascades": ["chat-cascade", "coding-cascade"],
        "models_count": 12,
        "models": ["chat-cascade", "coding-cascade"],
        "version": "1.0.0",
    }

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            DATA_COORDINATOR: mock_coord,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    sensors = mock_add.call_args[0][0]
    assert len(sensors) == len(SENSOR_DESCRIPTIONS) + 1


def test_automation_suggestions_sensor(mock_config_entry):
    """Test AI automation suggestions sensor."""
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.2.3"}
    sensor = OmniRouteAutomationSuggestionsSensor(mock_coord, mock_config_entry)
    assert sensor.native_value == "No Suggestions"
    assert sensor.extra_state_attributes["entities_processed_count"] == 0

    sensor.async_write_ha_state = MagicMock()
    sensor.set_suggestion(
        description="Turn off lights when away",
        yaml_block="alias: Away lights",
        model="coding-cascade",
        entities_processed_count=15,
    )
    assert sensor.native_value == "Suggestions Available"
    assert sensor.extra_state_attributes["description"] == "Turn off lights when away"
    assert sensor.extra_state_attributes["yaml_block"] == "alias: Away lights"
    assert sensor.extra_state_attributes["model"] == "coding-cascade"
    assert sensor.extra_state_attributes["entities_processed_count"] == 15
    assert sensor.extra_state_attributes["last_update"] is not None


def test_sensor_values_and_device_info(mock_config_entry):
    """Test native values, enabled defaults, device info, and attributes."""
    mock_coord = MagicMock()
    mock_coord.data = {
        "status": "ok",
        "reachable": True,
        "latency_ms": 18.4,
        "active_cascades": ["chat-cascade"],
        "cascade_status": {"chat-cascade": True, "coding-cascade": False},
        "models_count": 5,
        "models": ["chat-cascade"],
        "version": "1.2.3",
        "daily_tokens": 12450,
        "daily_cost": 0.045,
        "quota_reset": "2026-10-17T00:00:00Z",
    }

    sensors_by_key = {
        desc.key: OmniRouteSensor(mock_coord, mock_config_entry, desc)
        for desc in SENSOR_DESCRIPTIONS
    }

    assert sensors_by_key["status"].native_value == "ok"
    assert sensors_by_key["latency_ms"].native_value == 18.4
    assert sensors_by_key["active_cascades"].native_value == 1
    assert "active_cascades" in sensors_by_key["active_cascades"].extra_state_attributes
    assert sensors_by_key["models_count"].native_value == 5
    assert sensors_by_key["quota_health"].native_value == "optimal"
    assert sensors_by_key["daily_tokens"].native_value == 12450
    assert sensors_by_key["daily_cost"].native_value == 0.045
    assert sensors_by_key["quota_reset"].native_value == "2026-10-17T00:00:00Z"

    # Verify enabled defaults: rarely used sensors must be disabled by default
    assert (
        sensors_by_key["status"].entity_description.entity_registry_enabled_default
        is False
    )
    assert (
        sensors_by_key[
            "quota_health"
        ].entity_description.entity_registry_enabled_default
        is False
    )
    assert (
        sensors_by_key["latency_ms"].entity_description.entity_registry_enabled_default
        is True
    )
    assert (
        sensors_by_key[
            "active_cascades"
        ].entity_description.entity_registry_enabled_default
        is True
    )
    assert (
        sensors_by_key[
            "models_count"
        ].entity_description.entity_registry_enabled_default
        is True
    )

    # Check device info conforms to specifications
    dev_info = sensors_by_key["latency_ms"].device_info
    assert dev_info["manufacturer"] == DEFAULT_MANUFACTURER
    assert dev_info["model"] == DEFAULT_MODEL
    assert dev_info["sw_version"] == "1.2.3"
    assert dev_info["configuration_url"] == "http://omniroute:20128"


def test_sensor_none_data(mock_config_entry):
    """Test sensor handling when coordinator data is None."""
    mock_coord = MagicMock()
    mock_coord.data = None

    sensors_by_key = {
        desc.key: OmniRouteSensor(mock_coord, mock_config_entry, desc)
        for desc in SENSOR_DESCRIPTIONS
    }

    assert sensors_by_key["status"].native_value is None
    assert sensors_by_key["status"].extra_state_attributes is None
