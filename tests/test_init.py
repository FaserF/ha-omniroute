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
    SERVICE_ANALYZE_CAMERA,
    SERVICE_EXECUTE_AI_TASK,
    SERVICE_FLUSH_CACHE,
    SERVICE_GENERATE_EMBEDDING,
    SERVICE_GENERATE_IMAGE,
    SERVICE_REFRESH_MODELS,
    SERVICE_SUGGEST_AUTOMATIONS,
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

    # Test analyze_camera
    mock_camera_image = MagicMock()
    mock_camera_image.content = b"TEST_IMAGE_BYTES"
    with patch(
        "homeassistant.components.camera.async_get_image",
        new_callable=AsyncMock,
        return_value=mock_camera_image,
    ):
        mock_client.async_analyze_camera_image = AsyncMock(
            return_value={
                "response": "Front door snapshot",
                "model": "coding-cascade",
                "latency_ms": 120.0,
                "usage": {},
            }
        )
        camera_handler = registered_handlers[SERVICE_ANALYZE_CAMERA]
        call_mock.data = {
            "camera_entity_id": "camera.front_door",
            "prompt": "Check for packages",
        }
        cam_result = await camera_handler(call_mock)
        assert cam_result["response"] == "Front door snapshot"

    # Test generate_embedding
    mock_client.async_generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
    embed_handler = registered_handlers[SERVICE_GENERATE_EMBEDDING]
    call_mock.data = {"text": "Solar panel battery state"}
    embed_result = await embed_handler(call_mock)
    assert embed_result["embedding"] == [0.1, 0.2, 0.3]
    assert embed_result["dimensions"] == 3

    # Test flush_cache
    mock_client.async_flush_cache = AsyncMock(return_value=True)
    mock_coord = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]
    mock_coord.async_refresh = AsyncMock()
    flush_handler = registered_handlers[SERVICE_FLUSH_CACHE]
    await flush_handler(call_mock)
    assert mock_client.async_flush_cache.called
    assert mock_coord.async_refresh.called

    # Test refresh_models
    refresh_handler = registered_handlers[SERVICE_REFRESH_MODELS]
    await refresh_handler(call_mock)
    assert mock_coord.async_refresh.call_count >= 2

    # Test suggest_automations
    mock_client.async_chat_completion = AsyncMock(
        return_value={
            "choices": [
                {
                    "message": {
                        "content": "Turn on porch light when motion detected.\n\n```yaml\nalias: Motion Porch Light\ntrigger:\n  - platform: state\n    entity_id: binary_sensor.motion\n```"
                    }
                }
            ],
            "usage": {},
        }
    )
    suggest_handler = registered_handlers[SERVICE_SUGGEST_AUTOMATIONS]
    call_mock.data = {"domains": ["light", "binary_sensor"], "entity_limit": 10}
    sugg_res = await suggest_handler(call_mock)
    assert "alias: Motion Porch Light" in sugg_res["yaml_block"]
    assert "Turn on porch light" in sugg_res["description"]
