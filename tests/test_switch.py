"""Test OmniRoute switch platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.omniroute.const import (
    CONF_TOKEN_COMPRESSION,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
)
from custom_components.omniroute.switch import (
    OmniRouteTokenCompressionSwitch,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_switch_setup_entry(hass, mock_config_entry):
    """Test switch platform setup."""
    mock_add = MagicMock()
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.0.0"}
    mock_client = MagicMock()
    mock_client.compression_enabled = True

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            DATA_COORDINATOR: mock_coord,
            DATA_CLIENT: mock_client,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    switches = mock_add.call_args[0][0]
    assert len(switches) == 1


@pytest.mark.asyncio
async def test_token_compression_switch_toggle(hass, mock_config_entry):
    """Test token compression switch on/off."""
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.0.0"}
    mock_client = MagicMock()
    mock_client.compression_enabled = True

    switch = OmniRouteTokenCompressionSwitch(mock_coord, mock_config_entry, mock_client)
    switch.hass = hass

    assert switch.is_on is True

    await switch.async_turn_off()
    assert mock_client.compression_enabled is False
    assert mock_config_entry.options[CONF_TOKEN_COMPRESSION] is False

    await switch.async_turn_on()
    assert mock_client.compression_enabled is True
    assert mock_config_entry.options[CONF_TOKEN_COMPRESSION] is True
