"""Test OmniRoute AI Task platform."""

from unittest.mock import AsyncMock, MagicMock
import pytest

from custom_components.omniroute.ai_task import (
    OmniRouteAITaskEntity,
    async_setup_entry,
)
from custom_components.omniroute.const import DOMAIN


@pytest.mark.asyncio
async def test_ai_task_setup_entry(hass, mock_config_entry):
    """Test setting up ai_task platform."""
    mock_add = MagicMock()
    mock_client = MagicMock()
    mock_coord = MagicMock()

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "client": mock_client,
            "coordinator": mock_coord,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    entities = mock_add.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], OmniRouteAITaskEntity)


@pytest.mark.asyncio
async def test_ai_task_execution(hass, mock_config_entry):
    """Test executing generative AI task."""
    mock_client = MagicMock()
    mock_client.async_chat_completion = AsyncMock(
        return_value={
            "choices": [{"message": {"content": "Reasoning complete."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
    )
    mock_coord = MagicMock()

    entity = OmniRouteAITaskEntity(mock_config_entry, mock_client, mock_coord)
    entity.hass = hass

    result = await entity.async_execute_task(
        prompt="Synthesize power consumption trends",
        model="coding-cascade",
    )

    assert result["success"] is True
    assert result["response"] == "Reasoning complete."
    assert result["model"] == "coding-cascade"
    assert entity.state == "ready"

    attrs = entity.extra_state_attributes
    assert attrs["tasks_executed"] == 1
    assert attrs["last_model_used"] == "coding-cascade"
    assert attrs["last_latency_ms"] is not None


@pytest.mark.asyncio
async def test_ai_task_generate_image(mock_config_entry):
    """Test generating image via AI task entity."""
    mock_client = MagicMock()
    mock_client.async_generate_image = AsyncMock(return_value=["http://image.url/1.png"])
    mock_coord = MagicMock()

    entity = OmniRouteAITaskEntity(mock_config_entry, mock_client, mock_coord)
    urls = await entity.async_generate_image("Sunset over mountain cabin")
    assert urls == ["http://image.url/1.png"]


@pytest.mark.asyncio
async def test_ai_task_analyze_image(mock_config_entry):
    """Test multimodal vision analysis."""
    mock_client = MagicMock()
    mock_client.async_chat_completion = AsyncMock(
        return_value={
            "choices": [{"message": {"content": "The image shows a front door delivery package."}}]
        }
    )
    mock_coord = MagicMock()

    entity = OmniRouteAITaskEntity(mock_config_entry, mock_client, mock_coord)
    desc = await entity.async_analyze_image(
        prompt="What is in the porch camera?",
        image_url="http://camera.local/snapshot.jpg",
    )
    assert desc == "The image shows a front door delivery package."
