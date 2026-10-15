"""The OmniRoute integration."""

from __future__ import annotations

from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import aiohttp_client

from .client import OmniRouteClient
from .const import (
    CONF_API_KEY,
    CONF_API_URL,
    DOMAIN,
    PLATFORMS,
    SERVICE_EXECUTE_AI_TASK,
    SERVICE_GENERATE_IMAGE,
)
from .coordinator import OmniRouteDataUpdateCoordinator

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


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up OmniRoute integration services."""
    hass.data.setdefault(DOMAIN, {})

    async def async_handle_execute_ai_task(call: ServiceCall) -> dict[str, Any]:
        """Execute arbitrary AI task across OmniRoute cascades."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise ValueError("No OmniRoute config entries configured")

        entry = entries[0]
        data = hass.data[DOMAIN].get(entry.entry_id, {})
        client: OmniRouteClient | None = data.get("client")
        if not client:
            raise ValueError("OmniRoute client is not ready")

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

    async def async_handle_generate_image(call: ServiceCall) -> dict[str, Any]:
        """Generate images via OmniRoute."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise ValueError("No OmniRoute config entries configured")

        entry = entries[0]
        data = hass.data[DOMAIN].get(entry.entry_id, {})
        client: OmniRouteClient | None = data.get("client")
        if not client:
            raise ValueError("OmniRoute client is not ready")

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

    if not hass.services.has_service(DOMAIN, SERVICE_EXECUTE_AI_TASK):
        hass.services.async_register(
            DOMAIN,
            SERVICE_EXECUTE_AI_TASK,
            async_handle_execute_ai_task,
            schema=EXECUTE_AI_TASK_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_GENERATE_IMAGE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_GENERATE_IMAGE,
            async_handle_generate_image,
            schema=GENERATE_IMAGE_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OmniRoute from a config entry."""
    session = aiohttp_client.async_get_clientsession(hass)
    api_url = entry.data[CONF_API_URL]
    api_key = entry.data.get(CONF_API_KEY)

    client = OmniRouteClient(session=session, api_url=api_url, api_key=api_key)
    coordinator = OmniRouteDataUpdateCoordinator(hass, client)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
