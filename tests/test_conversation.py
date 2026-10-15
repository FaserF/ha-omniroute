"""Test OmniRoute conversation agent."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.conversation import ConversationInput

from custom_components.omniroute.const import DOMAIN
from custom_components.omniroute.conversation import (
    OmniRouteConversationEntity,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_conversation_setup_entry(hass, mock_config_entry):
    """Test setting up conversation platform."""
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
    assert isinstance(entities[0], OmniRouteConversationEntity)


@pytest.mark.asyncio
async def test_conversation_process_simple(hass, mock_config_entry):
    """Test simple text conversation response."""
    mock_client = MagicMock()
    mock_client.async_chat_completion = AsyncMock(
        return_value={
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "The living room light is on.",
                    }
                }
            ]
        }
    )
    mock_coord = MagicMock()

    entity = OmniRouteConversationEntity(mock_config_entry, mock_client, mock_coord)
    entity.hass = hass

    assert entity.device_info["manufacturer"] == "OmniRoute"
    assert entity.device_info["model"] == "AI Gateway & Router"

    user_input = ConversationInput(text="Is the living room light on?")
    result = await entity.async_process(user_input)

    assert result.response.speech == "The living room light is on."
    assert result.conversation_id is not None
    assert result.conversation_id in entity.history


@pytest.mark.asyncio
async def test_conversation_process_with_tool_calling(hass, mock_config_entry):
    """Test conversation with tool calling loop."""
    mock_client = MagicMock()
    mock_client.async_chat_completion = AsyncMock(
        side_effect=[
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_123",
                                    "function": {
                                        "name": "HassTurnOn",
                                        "arguments": '{"entity_id": "light.kitchen"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Turned on the kitchen light.",
                        }
                    }
                ]
            },
        ]
    )
    mock_coord = MagicMock()

    entity = OmniRouteConversationEntity(mock_config_entry, mock_client, mock_coord)
    entity.hass = hass

    with patch(
        "homeassistant.helpers.llm.async_get_api", new_callable=AsyncMock
    ) as mock_get_api:
        mock_api = MagicMock()
        mock_api.tools = [
            MagicMock(name="HassTurnOn", description="Turn on light", parameters={})
        ]
        mock_api.async_call_tool = AsyncMock(return_value={"result": "success"})
        mock_get_api.return_value = mock_api

        user_input = ConversationInput(text="Turn on kitchen light")
        result = await entity.async_process(user_input)

        assert result.response.speech == "Turned on the kitchen light."
        assert mock_client.async_chat_completion.call_count == 2
        mock_api.async_call_tool.assert_called_once()
