"""Test OmniRoute binary sensor platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.omniroute.binary_sensor import (
    BINARY_SENSORS,
    OmniRouteBinarySensor,
    async_setup_entry,
)
from custom_components.omniroute.const import (
    DATA_COORDINATOR,
    DEFAULT_MANUFACTURER,
    DEFAULT_MODEL,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_binary_sensor_setup_entry(hass, mock_config_entry):
    """Test setup of binary sensor entities."""
    mock_add = MagicMock()
    mock_coord = MagicMock()
    mock_coord.data = {
        "reachable": True,
        "healthy": True,
        "status": "ok",
        "active_cascades": ["chat-cascade"],
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
    assert len(sensors) == len(BINARY_SENSORS)


def test_binary_sensor_values_and_device_info(mock_config_entry):
    """Test binary sensor state evaluations and attributes."""
    mock_coord = MagicMock()
    mock_coord.data = {
        "reachable": True,
        "healthy": True,
        "status": "ok",
        "active_cascades": ["chat-cascade", "coding-cascade"],
        "version": "1.0.0",
    }

    sensors_by_key = {
        desc.key: OmniRouteBinarySensor(mock_coord, mock_config_entry, desc)
        for desc in BINARY_SENSORS
    }

    assert sensors_by_key["connected"].is_on is True
    assert sensors_by_key["healthy"].is_on is True
    assert sensors_by_key["provider_gemini"].is_on is True
    assert sensors_by_key["provider_anthropic"].is_on is True
    assert sensors_by_key["provider_openai"].is_on is True
    assert sensors_by_key["provider_deepseek"].is_on is True
    assert sensors_by_key["provider_groq"].is_on is True
    attrs = sensors_by_key["healthy"].extra_state_attributes
    assert attrs is not None
    assert attrs["status"] == "ok"
    assert attrs["active_cascades_count"] == 2

    # Check device info
    dev_info = sensors_by_key["connected"].device_info
    assert dev_info["manufacturer"] == DEFAULT_MANUFACTURER
    assert dev_info["model"] == DEFAULT_MODEL
    assert dev_info["configuration_url"] == "http://omniroute:20128"

    # Test offline / degraded state with provider error
    mock_coord.data = {
        "reachable": False,
        "healthy": False,
        "status": "error",
        "active_cascades": [],
        "version": "1.0.0",
        "providers": {
            "google": {"status": "error"},
            "openai": {"status": "ok"},
        },
    }
    assert sensors_by_key["connected"].is_on is False
    assert sensors_by_key["healthy"].is_on is False
    assert sensors_by_key["provider_gemini"].is_on is False
    assert sensors_by_key["provider_openai"].is_on is True


def test_binary_sensor_none_data(mock_config_entry):
    """Test binary sensor handling when coordinator data is None."""
    mock_coord = MagicMock()
    mock_coord.data = None

    sensors_by_key = {
        desc.key: OmniRouteBinarySensor(mock_coord, mock_config_entry, desc)
        for desc in BINARY_SENSORS
    }

    assert sensors_by_key["connected"].is_on is False
    assert sensors_by_key["healthy"].is_on is False
    assert sensors_by_key["healthy"].extra_state_attributes is None
