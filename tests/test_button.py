"""Test OmniRoute button platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.omniroute.button import (
    OmniRoutePingButton,
    OmniRouteRefreshButton,
    OmniRouteWebUIButton,
    async_setup_entry,
)
from custom_components.omniroute.const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DEFAULT_MANUFACTURER,
    DEFAULT_MODEL,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_button_setup_entry(hass, mock_config_entry):
    """Test setup of button entities."""
    mock_add = MagicMock()
    mock_coord = MagicMock()
    mock_client = MagicMock()
    mock_coord.data = {"version": "0.1.0"}

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            DATA_COORDINATOR: mock_coord,
            DATA_CLIENT: mock_client,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    buttons = mock_add.call_args[0][0]
    assert len(buttons) == 3


@pytest.mark.asyncio
async def test_web_ui_button(mock_config_entry):
    """Test Web UI button."""
    mock_coord = MagicMock()
    mock_coord.async_refresh = AsyncMock()
    mock_coord.data = {"version": "0.1.0"}
    mock_client = MagicMock()
    mock_client.async_check_health = AsyncMock(return_value={"reachable": True})

    button = OmniRouteWebUIButton(mock_coord, mock_client, mock_config_entry)
    assert button.name == "Web UI"
    assert button.extra_state_attributes == {
        "web_ui_url": "http://omniroute:20128/v1",
    }
    assert button.device_info["manufacturer"] == DEFAULT_MANUFACTURER
    assert button.device_info["model"] == DEFAULT_MODEL
    assert button.device_info["configuration_url"] == "http://omniroute:20128/v1"

    await button.async_press()
    mock_client.async_check_health.assert_called_once()
    mock_coord.async_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_button(mock_config_entry):
    """Test Reload Models button."""
    mock_coord = MagicMock()
    mock_coord.async_refresh = AsyncMock()
    mock_coord.data = {"version": "0.1.0"}
    mock_client = MagicMock()

    button = OmniRouteRefreshButton(mock_coord, mock_client, mock_config_entry)
    assert button.name == "Reload Models"

    await button.async_press()
    mock_coord.async_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_ping_button(mock_config_entry):
    """Test Ping Gateway button."""
    mock_coord = MagicMock()
    mock_coord.async_refresh = AsyncMock()
    mock_coord.data = {"version": "0.1.0"}
    mock_client = MagicMock()
    mock_client.async_check_health = AsyncMock(
        return_value={"reachable": True, "latency_ms": 12.3}
    )

    button = OmniRoutePingButton(mock_coord, mock_client, mock_config_entry)
    assert button.name == "Ping Gateway"

    await button.async_press()
    mock_client.async_check_health.assert_called_once()
    mock_coord.async_refresh.assert_called_once()
