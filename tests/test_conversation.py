"""Test OmniRoute conversation agent."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.conversation import ConversationInput
from homeassistant.helpers import llm

from custom_components.omniroute.const import DOMAIN
from custom_components.omniroute.conversation import (
    OmniRouteConversationEntity,
    async_setup_entry,
)


@pytest.fixture
def omniroute_conversation_entity(mock_config_entry):
    """Fixture for OmniRoute conversation entity."""
    mock_client = MagicMock()
    mock_coord = MagicMock()
    return OmniRouteConversationEntity(mock_config_entry, mock_client, mock_coord)


def test_supported_languages(omniroute_conversation_entity):
    """Verify that the conversation agent supports all languages."""
    assert omniroute_conversation_entity.supported_languages == "*"


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
        tool = MagicMock()
        tool.name = "HassTurnOn"
        tool.description = "Turn on light"
        tool.parameters = object()
        mock_api.tools = [tool]
        mock_api.api_prompt = (
            "Use these tools to control exposed Home Assistant devices."
        )
        mock_api.custom_serializer = MagicMock()
        mock_api.async_call_tool = AsyncMock(
            return_value=llm.ToolResult(data={"result": "success"})
        )
        mock_get_api.return_value = mock_api

        with patch(
            "probatio.to_openapi",
            return_value={"type": "object", "properties": {}},
        ) as mock_to_openapi:
            user_input = ConversationInput(text="Turn on kitchen light")
            result = await entity.async_process(user_input)

        assert result.response.speech == "Turned on the kitchen light."
        assert mock_client.async_chat_completion.call_count == 2
        sent_messages = mock_client.async_chat_completion.await_args_list[0].kwargs[
            "messages"
        ]
        assert mock_api.api_prompt in sent_messages[0]["content"]
        assert (
            mock_client.async_chat_completion.await_args_list[0].kwargs["tools"]
            is not None
        )
        tool_message = next(
            message
            for message in entity.history[result.conversation_id]
            if message.get("role") == "tool"
        )
        assert tool_message["role"] == "tool"
        assert json.loads(tool_message["content"]) == {"result": "success"}
        json.dumps(mock_client.async_chat_completion.await_args_list[0].kwargs["tools"])
        mock_to_openapi.assert_called_once_with(
            tool.parameters,
            custom_serializer=mock_api.custom_serializer,
            openapi_version="3.1.0",
        )
        llm_context = mock_get_api.await_args.args[2]
        assert llm_context.platform == "omniroute"
        assert llm_context.assistant == "conversation"
        assert llm_context.language == user_input.language
        assert llm_context.device_id == user_input.device_id
        assert llm_context.agent_id == user_input.agent_id
        mock_api.async_call_tool.assert_called_once()
