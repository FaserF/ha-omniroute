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
    DATA_SUGGESTIONS_SENSOR,
    DOMAIN,
    SERVICE_ANALYZE_CAMERA,
    SERVICE_EXECUTE_AI_TASK,
    SERVICE_FLUSH_CACHE,
    SERVICE_GENERATE_EMBEDDING,
    SERVICE_GENERATE_IMAGE,
    SERVICE_REFRESH_MODELS,
    SERVICE_SUGGEST_AUTOMATIONS,
)
from .coordinator import OmniRouteDataUpdateCoordinator
from .image import DATA_IMAGE_ENTITY

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

ANALYZE_CAMERA_SCHEMA = vol.Schema(
    {
        vol.Required("camera_entity_id"): cv.entity_id,
        vol.Optional(
            "prompt",
            default="Describe what you see in this security camera snapshot in detail.",
        ): cv.string,
        vol.Optional("model"): cv.string,
    }
)

GENERATE_EMBEDDING_SCHEMA = vol.Schema(
    {
        vol.Required("text"): cv.string,
        vol.Optional("model", default="text-embedding-3-small"): cv.string,
    }
)

FLUSH_CACHE_SCHEMA = vol.Schema({})

SUGGEST_AUTOMATIONS_SCHEMA = vol.Schema(
    {
        vol.Optional("domains"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("entity_limit", default=30): vol.Coerce(int),
        vol.Optional("custom_prompt"): cv.string,
        vol.Optional("model", default="coding-cascade"): cv.string,
        vol.Optional("send_notification", default=True): cv.boolean,
    }
)


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

        # Update latest image entity if available
        if images:
            first = images[0]
            img_bytes: bytes | None = None
            if first.startswith("data:") and ";base64," in first:
                import base64

                try:
                    img_bytes = base64.b64decode(first.split(";base64,")[1])
                except Exception as b64_err:
                    _LOGGER.debug("Could not decode base64 image: %s", b64_err)
            elif first.startswith("http://") or first.startswith("https://"):
                try:
                    async with client._session.get(first) as img_resp:
                        if img_resp.status == 200:
                            img_bytes = await img_resp.read()
                except Exception as http_err:
                    _LOGGER.debug("Could not download generated image: %s", http_err)

            if img_bytes:
                image_entity = data.get(DATA_IMAGE_ENTITY)
                if image_entity:
                    image_entity.set_image(img_bytes)

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

    async def _handle_analyze_camera(call: ServiceCall) -> ServiceResponse:
        """Capture and analyze camera image with vision model."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise HomeAssistantError("No OmniRoute config entries configured")
        entry = entries[0]
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        client: OmniRouteClient | None = data.get(DATA_CLIENT)
        if not client:
            raise HomeAssistantError("OmniRoute client is not ready")

        from homeassistant.components import camera

        camera_entity_id = call.data["camera_entity_id"]
        prompt = call.data.get(
            "prompt",
            "Describe what you see in this security camera snapshot in detail.",
        )
        model = call.data.get("model")

        image = await camera.async_get_image(hass, camera_entity_id)
        result = await client.async_analyze_camera_image(
            image_bytes=image.content, prompt=prompt, model=model
        )
        return result

    async def _handle_generate_embedding(call: ServiceCall) -> ServiceResponse:
        """Generate text vector embeddings."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise HomeAssistantError("No OmniRoute config entries configured")
        entry = entries[0]
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        client: OmniRouteClient | None = data.get(DATA_CLIENT)
        if not client:
            raise HomeAssistantError("OmniRoute client is not ready")

        text = call.data["text"]
        model = call.data.get("model", "text-embedding-3-small")
        embedding = await client.async_generate_embedding(input_text=text, model=model)
        dim = len(embedding) if isinstance(embedding, list) else 0
        return {
            "model": model,
            "dimensions": dim,
            "embedding": embedding,
        }

    async def _handle_flush_cache(call: ServiceCall) -> None:
        """Flush route and model caches."""
        entries = hass.config_entries.async_entries(DOMAIN)
        for entry in entries:
            data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
            client: OmniRouteClient | None = data.get(DATA_CLIENT)
            coordinator: OmniRouteDataUpdateCoordinator | None = data.get(
                DATA_COORDINATOR
            )
            if client:
                await client.async_flush_cache()
            if coordinator:
                await coordinator.async_refresh()

    async def _handle_suggest_automations(call: ServiceCall) -> ServiceResponse:
        """Scan HA entities and generate tailored smart home automations via OmniRoute."""
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise HomeAssistantError("No OmniRoute config entries configured")
        entry = entries[0]
        data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
        client: OmniRouteClient | None = data.get(DATA_CLIENT)
        if not client:
            raise HomeAssistantError("OmniRoute client is not ready")

        domains = call.data.get("domains")
        entity_limit = call.data.get("entity_limit", 30)
        custom_prompt = call.data.get("custom_prompt", "")
        model = call.data.get("model", "coding-cascade")
        send_notification = call.data.get("send_notification", True)

        all_states = hass.states.async_all()
        eligible: list[str] = []
        for s in all_states:
            if s.entity_id.startswith(
                ("conversation.", "update.", "tts.", "stt.", "persistent_notification.")
            ):
                continue
            if domains and s.domain not in domains:
                continue
            eligible.append(f"- {s.entity_id}: state={s.state}, name={s.name}")

        import random

        selected = (
            eligible[:entity_limit]
            if len(eligible) <= entity_limit
            else random.sample(eligible, entity_limit)
        )
        entities_text = "\n".join(selected)

        system_instruction = (
            "You are an expert Home Assistant automation designer. "
            "Analyze the provided entities and create 1 high-value, realistic, context-aware automation in valid Home Assistant YAML format.\n"
            "Format your answer as:\n"
            "## Summary\n"
            "<Brief explanation of what the automation does and why it's useful>\n\n"
            "```yaml\n"
            "alias: ...\n"
            "description: ...\n"
            "trigger:\n"
            "  ...\n"
            "condition:\n"
            "  ...\n"
            "action:\n"
            "  ...\n"
            "mode: single\n"
            "```"
        )
        user_msg = f"Available Entities:\n{entities_text}\n"
        if custom_prompt:
            user_msg += f"\nCustom Request / Focus: {custom_prompt}\n"

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_msg},
        ]

        resp = await client.async_chat_completion(
            messages=messages, model=model, temperature=0.7
        )
        choices = resp.get("choices", [])
        content = ""
        if choices and "message" in choices[0]:
            content = str(choices[0]["message"].get("content", ""))

        import re

        yaml_match = re.search(r"```(?:yaml)?\s*([\s\S]*?)```", content)
        yaml_block = yaml_match.group(1).strip() if yaml_match else ""
        description = re.sub(r"```(?:yaml)?[\s\S]*?```", "", content).strip()

        sugg_sensor = data.get(DATA_SUGGESTIONS_SENSOR)
        if sugg_sensor:
            sugg_sensor.set_suggestion(
                description=description,
                yaml_block=yaml_block,
                model=model,
                entities_processed_count=len(selected),
            )

        if send_notification:
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "OmniRoute AI Automation Suggestion",
                    "message": f"{description}\n\n```yaml\n{yaml_block}\n```",
                    "notification_id": "omniroute_automation_suggestion",
                },
            )

        return {
            "description": description,
            "yaml_block": yaml_block,
            "model": model,
            "entities_analyzed": len(selected),
            "raw_response": content,
        }

    if not (hass.services.has_service(DOMAIN, SERVICE_EXECUTE_AI_TASK) is True):
        hass.services.async_register(
            DOMAIN,
            SERVICE_EXECUTE_AI_TASK,
            _handle_execute_ai_task,
            schema=EXECUTE_AI_TASK_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not (hass.services.has_service(DOMAIN, SERVICE_GENERATE_IMAGE) is True):
        hass.services.async_register(
            DOMAIN,
            SERVICE_GENERATE_IMAGE,
            _handle_generate_image,
            schema=GENERATE_IMAGE_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not (hass.services.has_service(DOMAIN, SERVICE_REFRESH_MODELS) is True):
        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH_MODELS,
            _handle_refresh_models,
            schema=REFRESH_MODELS_SCHEMA,
        )

    if not (hass.services.has_service(DOMAIN, SERVICE_ANALYZE_CAMERA) is True):
        hass.services.async_register(
            DOMAIN,
            SERVICE_ANALYZE_CAMERA,
            _handle_analyze_camera,
            schema=ANALYZE_CAMERA_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not (hass.services.has_service(DOMAIN, SERVICE_GENERATE_EMBEDDING) is True):
        hass.services.async_register(
            DOMAIN,
            SERVICE_GENERATE_EMBEDDING,
            _handle_generate_embedding,
            schema=GENERATE_EMBEDDING_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not (hass.services.has_service(DOMAIN, SERVICE_FLUSH_CACHE) is True):
        hass.services.async_register(
            DOMAIN,
            SERVICE_FLUSH_CACHE,
            _handle_flush_cache,
            schema=FLUSH_CACHE_SCHEMA,
        )

    if not (hass.services.has_service(DOMAIN, SERVICE_SUGGEST_AUTOMATIONS) is True):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SUGGEST_AUTOMATIONS,
            _handle_suggest_automations,
            schema=SUGGEST_AUTOMATIONS_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )


def async_unload_services(hass: HomeAssistant) -> None:
    """Unload all OmniRoute services."""
    for service in [
        SERVICE_EXECUTE_AI_TASK,
        SERVICE_GENERATE_IMAGE,
        SERVICE_REFRESH_MODELS,
        SERVICE_ANALYZE_CAMERA,
        SERVICE_GENERATE_EMBEDDING,
        SERVICE_FLUSH_CACHE,
        SERVICE_SUGGEST_AUTOMATIONS,
    ]:
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
