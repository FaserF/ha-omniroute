"""Test OmniRoute sensor platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.omniroute.const import DOMAIN
from custom_components.omniroute.sensor import (
    SENSOR_DESCRIPTIONS,
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
    }

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "coordinator": mock_coord,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    sensors = mock_add.call_args[0][0]
    assert len(sensors) == len(SENSOR_DESCRIPTIONS)


def test_sensor_values(mock_config_entry):
    """Test native values and attributes for sensors."""
    mock_coord = MagicMock()
    mock_coord.data = {
        "status": "ok",
        "reachable": True,
        "latency_ms": 18.4,
        "active_cascades": ["chat-cascade"],
        "cascade_status": {"chat-cascade": True, "coding-cascade": False},
        "models_count": 5,
        "models": ["chat-cascade"],
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
