"""Test OmniRoute button platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.omniroute.button import (
    OmniRouteFlushCacheButton,
    OmniRouteRefreshButton,
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
    """Test button platform setup."""
    mock_add = MagicMock()
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.0.0"}
    mock_client = MagicMock()

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            DATA_COORDINATOR: mock_coord,
            DATA_CLIENT: mock_client,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    buttons = mock_add.call_args[0][0]
    assert len(buttons) == 2


@pytest.mark.asyncio
async def test_refresh_button_press(mock_config_entry):
    """Test reload models button press."""
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.0.0"}
    mock_coord.async_refresh = AsyncMock()
    mock_client = MagicMock()

    button = OmniRouteRefreshButton(mock_coord, mock_client, mock_config_entry)
    assert button.device_info["manufacturer"] == DEFAULT_MANUFACTURER
    assert button.device_info["model"] == DEFAULT_MODEL
    assert button.unique_id == f"{mock_config_entry.entry_id}_refresh_models"

    await button.async_press()
    assert mock_coord.async_refresh.called


@pytest.mark.asyncio
async def test_flush_cache_button_press(mock_config_entry):
    """Test flush cache button press."""
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.0.0"}
    mock_coord.async_refresh = AsyncMock()
    mock_client = MagicMock()
    mock_client.async_flush_cache = AsyncMock(return_value=True)

    button = OmniRouteFlushCacheButton(mock_coord, mock_client, mock_config_entry)
    assert button.unique_id == f"{mock_config_entry.entry_id}_flush_cache"

    await button.async_press()
    assert mock_client.async_flush_cache.called
    assert mock_coord.async_refresh.called
