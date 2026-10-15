"""Test OmniRoute setup and unload lifecycles."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.omniroute import (
    async_reload_entry,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.omniroute.const import (
    DOMAIN,
    SERVICE_EXECUTE_AI_TASK,
    SERVICE_GENERATE_IMAGE,
)


@pytest.mark.asyncio
async def test_async_setup(hass):
    """Test setting up integration and services."""
    assert await async_setup(hass, {}) is True
    assert hass.services.async_register.call_count >= 2


@pytest.mark.asyncio
async def test_async_setup_and_unload_entry(hass, mock_config_entry):
    """Test setting up and unloading config entry."""
    with patch(
        "custom_components.omniroute.OmniRouteDataUpdateCoordinator.async_config_entry_first_refresh",
        new_callable=AsyncMock,
    ):
        result = await async_setup_entry(hass, mock_config_entry)
        assert result is True
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        assert hass.config_entries.async_forward_entry_setups.called

        unload_result = await async_unload_entry(hass, mock_config_entry)
        assert unload_result is True
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_async_reload_entry(hass, mock_config_entry):
    """Test reloading config entry."""
    await async_reload_entry(hass, mock_config_entry)
    hass.config_entries.async_reload.assert_called_once_with(mock_config_entry.entry_id)


@pytest.mark.asyncio
async def test_services_execution(hass, mock_config_entry):
    """Test execute_ai_task and generate_image service handlers."""
    registered_handlers = {}

    def mock_register(domain, service, handler, **kwargs):
        registered_handlers[service] = handler

    hass.services.async_register.side_effect = mock_register

    await async_setup(hass, {})

    mock_client = MagicMock()
    mock_client.async_chat_completion = AsyncMock(
        return_value={
            "choices": [{"message": {"content": "Task result"}}],
            "usage": {"total_tokens": 42},
        }
    )
    mock_client.async_generate_image = AsyncMock(return_value=["http://image.url"])

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "client": mock_client,
            "coordinator": MagicMock(),
        }
    }
    hass.config_entries.async_entries.return_value = [mock_config_entry]

    # Test execute_ai_task
    execute_handler = registered_handlers[SERVICE_EXECUTE_AI_TASK]
    call_mock = MagicMock()
    call_mock.data = {"prompt": "Analyze solar stats", "model": "coding-cascade"}
    result = await execute_handler(call_mock)
    assert result["response"] == "Task result"
    assert result["model"] == "coding-cascade"

    # Test generate_image
    image_handler = registered_handlers[SERVICE_GENERATE_IMAGE]
    call_mock.data = {"prompt": "A modern smart home", "model": "flux-schnell"}
    img_result = await image_handler(call_mock)
    assert img_result["images"] == ["http://image.url"]
