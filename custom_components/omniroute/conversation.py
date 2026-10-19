"""Support for OmniRoute conversation agent."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterable
from typing import Any

from homeassistant.components import conversation
from homeassistant.components.conversation import (
    ConversationEntity,
    ConversationEntityFeature,
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import template
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import OmniRouteClient
from .const import (
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DEFAULT_FAST_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_PROMPT,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DOMAIN,
    LOGGER,
    MAX_TOOL_ITERATIONS,
)
from .coordinator import OmniRouteDataUpdateCoordinator
from .helpers import get_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: OmniRouteClient = data[DATA_CLIENT]
    coordinator: OmniRouteDataUpdateCoordinator = data[DATA_COORDINATOR]

    async_add_entities([OmniRouteConversationEntity(entry, client, coordinator)])


class OmniRouteConversationEntity(
    CoordinatorEntity[OmniRouteDataUpdateCoordinator], ConversationEntity
):
    """OmniRoute conversation agent entity."""

    _attr_has_entity_name = True
    _attr_name = "Assist"
    _attr_supported_features = ConversationEntityFeature.CONTROL

    def __init__(
        self,
        entry: ConfigEntry,
        client: OmniRouteClient,
        coordinator: OmniRouteDataUpdateCoordinator,
    ) -> None:
        """Initialize the conversation entity."""
        super().__init__(coordinator)
        self.entry = entry
        self.client = client
        self._attr_unique_id = f"{entry.entry_id}_conversation"
        sw_version = None
        if coordinator.data:
            sw_version = coordinator.data.get("version")
        self._attr_device_info = get_device_info(entry, sw_version)
        self.history: dict[str, list[dict[str, Any]]] = {}

    @property
    def supported_languages(self) -> list[str]:
        """Return supported languages."""
        return ["*"]

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        """Process a conversational input sentence."""
        options = self.entry.options
        chat_model = options.get(CONF_CHAT_MODEL, DEFAULT_FAST_MODEL)
        prompt_raw = options.get(CONF_PROMPT, DEFAULT_PROMPT)
        temperature = options.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE)
        top_p = options.get(CONF_TOP_P, DEFAULT_TOP_P)
        max_tokens = options.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS)

        # Render prompt template
        try:
            prompt_str = template.Template(prompt_raw, self.hass).async_render(
                parse_result=False
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Error rendering prompt template: %s", exc)
            prompt_str = prompt_raw

        # Prepare LLM API and tools if available
        tools: list[dict[str, Any]] | None = None
        llm_api = None
        try:
            from homeassistant.helpers import llm

            llm_context = llm.LLMContext(
                platform=DOMAIN,
                context=user_input.context,
                user_prompt=user_input.text,
                language=user_input.language,
                assistant="conversation",
                device_id=user_input.device_id,
            )
            llm_api = await llm.async_get_api(
                self.hass, llm.LLM_API_ASSIST, llm_context
            )
            if llm_api and getattr(llm_api, "tools", None):
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.parameters,
                        },
                    }
                    for tool in llm_api.tools
                ]
        except Exception as exc:  # noqa: BLE001
            LOGGER.debug("LLM tools could not be loaded: %s", exc)

        conversation_id = user_input.conversation_id or uuid.uuid4().hex
        prior_messages = self.history.get(conversation_id, [])

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": prompt_str},
            *prior_messages,
            {"role": "user", "content": user_input.text},
        ]

        # Conversation completion loop with tool calling
        iterations = 0
        final_text = "I encountered an issue processing your request."

        while iterations < MAX_TOOL_ITERATIONS:
            iterations += 1
            try:
                response = await self.client.async_chat_completion(
                    messages=messages,
                    model=chat_model,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    tools=tools,
                )
            except Exception as err:
                LOGGER.error("Chat completion error: %s", err)
                final_text = f"Error communicating with OmniRoute: {err}"
                break

            choices = response.get("choices", [])
            if not choices or "message" not in choices[0]:
                break

            msg = choices[0]["message"]
            tool_calls = msg.get("tool_calls")

            if not tool_calls or not llm_api:
                final_text = msg.get("content") or ""
                messages.append({"role": "assistant", "content": final_text})
                break

            # Handle tool calls
            messages.append(msg)
            for call in tool_calls:
                call_id = call.get("id", "")
                fn_name = call.get("function", {}).get("name", "")
                fn_args_raw = call.get("function", {}).get("arguments", "{}")
                try:
                    fn_args = json.loads(fn_args_raw)
                except Exception:
                    fn_args = {}

                try:
                    from homeassistant.helpers import llm

                    tool_input = llm.ToolInput(
                        id=call_id,
                        tool_name=fn_name,
                        tool_args=fn_args,
                    )
                    tool_res = await llm_api.async_call_tool(tool_input)
                    tool_content = json.dumps(tool_res)
                except Exception as err:  # noqa: BLE001
                    LOGGER.warning("Tool execution error for %s: %s", fn_name, err)
                    tool_content = json.dumps({"error": str(err)})

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": fn_name,
                        "content": tool_content,
                    }
                )

        # Save conversation history (trim to last 20 messages)
        self.history[conversation_id] = messages[1:][-20:]

        intent_response = conversation.intent.IntentResponse(
            language=user_input.language
        )
        intent_response.async_set_speech(final_text)
        return ConversationResult(
            response=intent_response,
            conversation_id=conversation_id,
        )

    async def async_stream_conversation(self, user_input: ConversationInput) -> AsyncIterable[str]:
        """Process a conversational input sentence and stream the response."""
        options = self.entry.options
        chat_model = options.get(CONF_CHAT_MODEL, DEFAULT_FAST_MODEL)
        prompt_raw = options.get(CONF_PROMPT, DEFAULT_PROMPT)
        temperature = options.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE)
        top_p = options.get(CONF_TOP_P, DEFAULT_TOP_P)
        max_tokens = options.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS)

        try:
            prompt_str = template.Template(prompt_raw, self.hass).async_render(
                parse_result=False
            )
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Error rendering prompt template: %s", exc)
            prompt_str = prompt_raw

        tools: list[dict[str, Any]] | None = None
        llm_api = None
        try:
            from homeassistant.helpers import llm

            llm_context = llm.LLMContext(
                platform=DOMAIN,
                context=user_input.context,
                user_prompt=user_input.text,
                language=user_input.language,
                assistant="conversation",
                device_id=user_input.device_id,
            )
            llm_api = await llm.async_get_api(
                self.hass, llm.LLM_API_ASSIST, llm_context
            )
            if llm_api and getattr(llm_api, "tools", None):
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.parameters,
                        },
                    }
                    for tool in llm_api.tools
                ]
        except Exception as exc:  # noqa: BLE001
            LOGGER.debug("LLM tools could not be loaded: %s", exc)

        conversation_id = user_input.conversation_id or uuid.uuid4().hex
        prior_messages = self.history.get(conversation_id, [])

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": prompt_str},
            *prior_messages,
            {"role": "user", "content": user_input.text},
        ]

        iterations = 0
        final_text = ""

        while iterations < MAX_TOOL_ITERATIONS:
            iterations += 1
            try:
                # We expect the client to support async_chat_completion_stream
                stream = await self.client.async_chat_completion_stream(
                    messages=messages,
                    model=chat_model,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    tools=tools,
                )
            except Exception as err:
                LOGGER.error("Chat completion stream error: %s", err)
                yield f"Error communicating with OmniRoute: {err}"
                return

            tool_calls = []
            msg_content = ""

            async for chunk in stream:
                choices = chunk.get("choices", [])
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                if "content" in delta and delta["content"]:
                    content_chunk = delta["content"]
                    msg_content += content_chunk
                    yield content_chunk
                if "tool_calls" in delta:
                    for t_call in delta["tool_calls"]:
                        idx = t_call.get("index", 0)
                        while len(tool_calls) <= idx:
                            tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                        if "id" in t_call and t_call["id"]:
                            tool_calls[idx]["id"] = t_call["id"]
                        if "function" in t_call:
                            if "name" in t_call["function"] and t_call["function"]["name"]:
                                tool_calls[idx]["function"]["name"] += t_call["function"]["name"]
                            if "arguments" in t_call["function"] and t_call["function"]["arguments"]:
                                tool_calls[idx]["function"]["arguments"] += t_call["function"]["arguments"]

            if not tool_calls or not llm_api:
                if msg_content:
                    final_text = msg_content
                messages.append({"role": "assistant", "content": final_text})
                break

            messages.append({
                "role": "assistant",
                "content": msg_content,
                "tool_calls": tool_calls
            })

            for call in tool_calls:
                call_id = call.get("id", "")
                fn_name = call.get("function", {}).get("name", "")
                fn_args_raw = call.get("function", {}).get("arguments", "{}")
                try:
                    fn_args = json.loads(fn_args_raw)
                except Exception:
                    fn_args = {}

                try:
                    from homeassistant.helpers import llm

                    tool_input = llm.ToolInput(
                        id=call_id,
                        tool_name=fn_name,
                        tool_args=fn_args,
                    )
                    tool_res = await llm_api.async_call_tool(tool_input)
                    tool_content = json.dumps(tool_res)
                except Exception as err:  # noqa: BLE001
                    LOGGER.warning("Tool execution error for %s: %s", fn_name, err)
                    tool_content = json.dumps({"error": str(err)})

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": fn_name,
                        "content": tool_content,
                    }
                )

        self.history[conversation_id] = messages[1:][-20:]
