"""Service registration and handlers for OmniRoute integration."""

from __future__ import annotations

import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError

from .client import OmniRouteClient
from .const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
    SERVICE_EXECUTE_AI_TASK,
    SERVICE_GENERATE_IMAGE,
    SERVICE_REFRESH_MODELS,
)
from .coordinator import OmniRouteDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

EXECUTE_AI_TASK_SCHEMA = vol.Schema(
    {
        vol.Required("prompt"): cv.string,
        vol.Optional("model"): cv.string,
        vol.Optional("temperature"): vol.Coerce(float),
        vol.Optional("max_tokens"): vol.Coerce(int),
        vol.Optional("system_prompt"): cv.string,
    }
)

GENERATE_IMAGE_SCHEMA = vol.Schema(
    {
        vol.Required("prompt"): cv.string,
        vol.Optional("model", default="flux-schnell"): cv.string,
        vol.Optional("size", default="1024x1024"): cv.string,
        vol.Optional("quality", default="standard"): cv.string,
        vol.Optional("n", default=1): vol.Coerce(int),
    }
)

REFRESH_MODELS_SCHEMA = vol.Schema({})


def async_setup_services(hass: HomeAssistant) -> None:
    """Register all OmniRoute services."""

    async def _handle_execute_ai_task(call: ServiceCall) -> ServiceResponse:
        """Execute arbitrary AI task across OmniRoute cascades."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise HomeAssistantError("No OmniRoute config entries configured")

        entry = entries[0]
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        client: OmniRouteClient | None = data.get(DATA_CLIENT)
        if not client:
            raise HomeAssistantError("OmniRoute client is not ready")

        prompt = call.data["prompt"]
        model = call.data.get("model", "coding-cascade")
        temp = call.data.get("temperature", 0.2)
        max_tokens = call.data.get("max_tokens", 2048)
        system_prompt = call.data.get(
            "system_prompt", "You are an AI task specialist for Home Assistant."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        resp = await client.async_chat_completion(
            messages=messages,
            model=model,
            temperature=temp,
            max_tokens=max_tokens,
        )

        choices = resp.get("choices", [])
        content = ""
        if choices and "message" in choices[0]:
            content = choices[0]["message"].get("content", "")

        return {
            "model": model,
            "response": content,
            "usage": resp.get("usage", {}),
        }

    async def _handle_generate_image(call: ServiceCall) -> ServiceResponse:
        """Generate images via OmniRoute."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise HomeAssistantError("No OmniRoute config entries configured")

        entry = entries[0]
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        client: OmniRouteClient | None = data.get(DATA_CLIENT)
        if not client:
            raise HomeAssistantError("OmniRoute client is not ready")

        prompt = call.data["prompt"]
        model = call.data.get("model", "flux-schnell")
        size = call.data.get("size", "1024x1024")
        quality = call.data.get("quality", "standard")
        n = call.data.get("n", 1)

        images = await client.async_generate_image(
            prompt=prompt,
            model=model,
            size=size,
            quality=quality,
            n=n,
        )

        return {
            "prompt": prompt,
            "model": model,
            "images": images,
        }

    async def _handle_refresh_models(call: ServiceCall) -> None:
        """Refresh models and cascades cache."""
        entries = hass.config_entries.async_entries(DOMAIN)
        for entry in entries:
            data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
            coordinator: OmniRouteDataUpdateCoordinator | None = data.get(
                DATA_COORDINATOR
            )
            if coordinator:
                await coordinator.async_refresh()

    if not hass.services.has_service(DOMAIN, SERVICE_EXECUTE_AI_TASK):
        hass.services.async_register(
            DOMAIN,
            SERVICE_EXECUTE_AI_TASK,
            _handle_execute_ai_task,
            schema=EXECUTE_AI_TASK_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_GENERATE_IMAGE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_GENERATE_IMAGE,
            _handle_generate_image,
            schema=GENERATE_IMAGE_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH_MODELS):
        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH_MODELS,
            _handle_refresh_models,
            schema=REFRESH_MODELS_SCHEMA,
        )


def async_unload_services(hass: HomeAssistant) -> None:
    """Unload all OmniRoute services."""
    for service in [
        SERVICE_EXECUTE_AI_TASK,
        SERVICE_GENERATE_IMAGE,
        SERVICE_REFRESH_MODELS,
    ]:
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
