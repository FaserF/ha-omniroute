"""Support for OmniRoute AI Task platform."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import OmniRouteClient
from .const import (
    CONF_AI_TASK_MAX_TOKENS,
    CONF_AI_TASK_MODEL,
    CONF_AI_TASK_PROMPT,
    CONF_AI_TASK_TEMPERATURE,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DEFAULT_AI_TASK_MAX_TOKENS,
    DEFAULT_AI_TASK_MODEL,
    DEFAULT_AI_TASK_PROMPT,
    DEFAULT_AI_TASK_TEMPERATURE,
    DOMAIN,
    LOGGER,
)
from .coordinator import OmniRouteDataUpdateCoordinator
from .helpers import get_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AI Task entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: OmniRouteClient = data[DATA_CLIENT]
    coordinator: OmniRouteDataUpdateCoordinator = data[DATA_COORDINATOR]

    async_add_entities([OmniRouteAITaskEntity(entry, client, coordinator)])


class OmniRouteAITaskEntity(CoordinatorEntity[OmniRouteDataUpdateCoordinator], Entity):
    """OmniRoute AI Task entity for smart home reasoning and generative workflows."""

    _attr_has_entity_name = True
    _attr_name = "Task Engine"

    def __init__(
        self,
        entry: ConfigEntry,
        client: OmniRouteClient,
        coordinator: OmniRouteDataUpdateCoordinator,
    ) -> None:
        """Initialize the AI Task entity."""
        super().__init__(coordinator)
        self.entry = entry
        self.client = client
        self._attr_unique_id = f"{entry.entry_id}_ai_task"
        sw_version = None
        if coordinator.data:
            sw_version = coordinator.data.get("version")
        self._attr_device_info = get_device_info(entry, sw_version)
        self._tasks_executed = 0
        self._last_latency_ms: float | None = None
        self._last_model_used: str | None = None
        self._last_task_timestamp: str | None = None
        self._state = "ready"
        try:
            from homeassistant.components.ai_task import AITaskEntityFeature

            self._attr_supported_features = (
                AITaskEntityFeature.GENERATE_DATA
                | AITaskEntityFeature.GENERATE_IMAGE
                | AITaskEntityFeature.SUPPORT_ATTACHMENTS
            )
        except (ImportError, AttributeError):
            self._attr_supported_features = 7

    @property
    def state(self) -> str | None:
        """Return the state of the entity (timestamp of last execution for ai_task domain)."""
        return self._last_task_timestamp

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        options = self.entry.options
        return {
            "status": self._state,
            "model": options.get(CONF_AI_TASK_MODEL, DEFAULT_AI_TASK_MODEL),
            "temperature": options.get(
                CONF_AI_TASK_TEMPERATURE, DEFAULT_AI_TASK_TEMPERATURE
            ),
            "max_tokens": options.get(
                CONF_AI_TASK_MAX_TOKENS, DEFAULT_AI_TASK_MAX_TOKENS
            ),
            "tasks_executed": self._tasks_executed,
            "last_latency_ms": self._last_latency_ms,
            "last_model_used": self._last_model_used,
            "last_task_timestamp": self._last_task_timestamp,
        }

    async def async_execute_task(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a generative AI task."""
        options = self.entry.options
        chosen_model = model or options.get(CONF_AI_TASK_MODEL, DEFAULT_AI_TASK_MODEL)
        chosen_prompt = system_prompt or options.get(
            CONF_AI_TASK_PROMPT, DEFAULT_AI_TASK_PROMPT
        )
        chosen_temp = (
            temperature
            if temperature is not None
            else options.get(CONF_AI_TASK_TEMPERATURE, DEFAULT_AI_TASK_TEMPERATURE)
        )
        chosen_max_tokens = (
            max_tokens
            if max_tokens is not None
            else options.get(CONF_AI_TASK_MAX_TOKENS, DEFAULT_AI_TASK_MAX_TOKENS)
        )

        messages = [
            {"role": "system", "content": chosen_prompt},
            {"role": "user", "content": prompt},
        ]

        self._state = "executing"
        self.async_write_ha_state()

        start = time.perf_counter()
        try:
            resp = await self.client.async_chat_completion(
                messages=messages,
                model=chosen_model,
                temperature=chosen_temp,
                max_tokens=chosen_max_tokens,
            )
            self._last_latency_ms = round((time.perf_counter() - start) * 1000, 2)
            self._tasks_executed += 1
            self._last_model_used = chosen_model
            self._last_task_timestamp = datetime.now(UTC).isoformat()
            self._state = "ready"
            self.async_write_ha_state()

            choices = resp.get("choices", [])
            content = ""
            if choices and "message" in choices[0]:
                content = choices[0]["message"].get("content", "")

            return {
                "success": True,
                "model": chosen_model,
                "latency_ms": self._last_latency_ms,
                "response": content,
                "usage": resp.get("usage", {}),
            }
        except Exception as err:
            self._state = "error"
            self.async_write_ha_state()
            LOGGER.error("AI Task execution failed: %s", err)
            raise

    async def async_generate_image(
        self,
        prompt: str,
        model: str = "flux-schnell",
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1,
    ) -> list[str]:
        """Generate images matching prompt."""
        return await self.client.async_generate_image(
            prompt=prompt,
            model=model,
            size=size,
            quality=quality,
            n=n,
        )

    async def async_analyze_image(
        self,
        prompt: str,
        image_url: str,
        model: str | None = None,
    ) -> str:
        """Analyze an image using vision model."""
        options = self.entry.options
        chosen_model = model or options.get(CONF_AI_TASK_MODEL, DEFAULT_AI_TASK_MODEL)

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ]

        resp = await self.client.async_chat_completion(
            messages=messages,
            model=chosen_model,
        )
        choices = resp.get("choices", [])
        if choices and "message" in choices[0]:
            return str(choices[0]["message"].get("content", ""))
        return ""

    async def _async_generate_data(self, task: Any, chat_log: Any) -> Any:
        """Handle Home Assistant data generation task (e.g. suggest automation names)."""
        instructions = (
            getattr(task, "instructions", "")
            or "You are an intelligent home assistant. Provide clear, concise answers."
        )
        messages: list[dict[str, Any]] = [{"role": "system", "content": instructions}]

        if hasattr(chat_log, "content") and chat_log.content:
            for item in chat_log.content:
                r = getattr(item, "role", "user")
                c = getattr(item, "content", "")
                if c:
                    messages.append({"role": r, "content": str(c)})
        elif hasattr(chat_log, "messages") and chat_log.messages:
            for m in chat_log.messages:
                if isinstance(m, dict):
                    messages.append(m)

        if len(messages) == 1:
            messages.append({"role": "user", "content": instructions})

        options = self.entry.options
        chosen_model = options.get(CONF_AI_TASK_MODEL, DEFAULT_AI_TASK_MODEL)
        chosen_temp = options.get(CONF_AI_TASK_TEMPERATURE, DEFAULT_AI_TASK_TEMPERATURE)
        chosen_max_tokens = options.get(
            CONF_AI_TASK_MAX_TOKENS, DEFAULT_AI_TASK_MAX_TOKENS
        )

        resp = await self.client.async_chat_completion(
            messages=messages,
            model=chosen_model,
            temperature=chosen_temp,
            max_tokens=chosen_max_tokens,
        )

        choices = resp.get("choices", [])
        content = ""
        if choices and "message" in choices[0]:
            content = str(choices[0]["message"].get("content", ""))

        data_result: Any = content
        if getattr(task, "structure", None):
            import json

            try:
                data_result = json.loads(content)
            except Exception:
                data_result = content

        cid = (
            getattr(chat_log, "conversation_id", None) or f"{self.entry.entry_id}_task"
        )
        try:
            from homeassistant.components.ai_task import GenDataTaskResult

            return GenDataTaskResult(conversation_id=cid, data=data_result)
        except ImportError:
            return {"conversation_id": cid, "data": data_result}

    async def _async_generate_image(self, task: Any) -> Any:
        """Handle Home Assistant image generation task."""
        prompt = getattr(task, "prompt", "") or str(task)
        images = await self.async_generate_image(prompt=prompt)
        url = images[0] if images else ""
        try:
            from homeassistant.components.ai_task import GenImageTaskResult

            return GenImageTaskResult(image_url=url, b64_json=None)
        except ImportError:
            return {"image_url": url, "b64_json": None}
