"""Config flow for OmniRoute integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client, selector

from .client import CannotConnect, InvalidAuth, OmniRouteClient, OmniRouteError
from .const import (
    CONF_AI_TASK_MAX_TOKENS,
    CONF_AI_TASK_MODEL,
    CONF_AI_TASK_PROMPT,
    CONF_AI_TASK_TEMPERATURE,
    CONF_API_KEY,
    CONF_API_URL,
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_SCAN_INTERVAL,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DEFAULT_AI_TASK_MAX_TOKENS,
    DEFAULT_AI_TASK_PROMPT,
    DEFAULT_AI_TASK_TEMPERATURE,
    DEFAULT_API_URL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_NAME,
    DEFAULT_PROMPT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DOMAIN,
    LOGGER,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_URL, default=DEFAULT_API_URL): str,
        vol.Optional(CONF_API_KEY): str,
    }
)


class OmniRouteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OmniRoute."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_url = user_input[CONF_API_URL].rstrip("/")
            api_key = user_input.get(CONF_API_KEY)

            await self.async_set_unique_id(api_url.lower())
            self._abort_if_unique_id_configured()

            session = aiohttp_client.async_get_clientsession(self.hass)
            client = OmniRouteClient(session=session, api_url=api_url, api_key=api_key)

            try:
                await client.async_get_models()
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except OmniRouteError as err:
                LOGGER.error("OmniRoute error during setup: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("Unexpected exception during setup: %s", exc)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle reauthorization request."""
        return await self.async_step_user()

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OmniRouteOptionsFlow(config_entry)


class OmniRouteOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for OmniRoute."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Retrieve available models from coordinator if setup
        models: list[str] = []
        if (
            DOMAIN in self.hass.data
            and self.config_entry.entry_id in self.hass.data[DOMAIN]
        ):
            coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id].get(
                "coordinator"
            )
            if coordinator and getattr(coordinator, "models", None):
                models = sorted(set(coordinator.models))
        if not models:
            models = ["default"]

        current_options = self.config_entry.options
        default_chat = current_options.get(CONF_CHAT_MODEL) or models[0]
        default_ai_task = current_options.get(CONF_AI_TASK_MODEL) or models[0]

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_CHAT_MODEL,
                    default=default_chat,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=models,
                        custom_value=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_PROMPT,
                    default=current_options.get(CONF_PROMPT, DEFAULT_PROMPT),
                ): selector.TemplateSelector(),
                vol.Optional(
                    CONF_TEMPERATURE,
                    default=current_options.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=2.0,
                        step=0.05,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(
                    CONF_TOP_P,
                    default=current_options.get(CONF_TOP_P, DEFAULT_TOP_P),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=1.0,
                        step=0.05,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(
                    CONF_MAX_TOKENS,
                    default=current_options.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=16384,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_AI_TASK_MODEL,
                    default=default_ai_task,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=models,
                        custom_value=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_AI_TASK_PROMPT,
                    default=current_options.get(
                        CONF_AI_TASK_PROMPT, DEFAULT_AI_TASK_PROMPT
                    ),
                ): selector.TemplateSelector(),
                vol.Optional(
                    CONF_AI_TASK_TEMPERATURE,
                    default=current_options.get(
                        CONF_AI_TASK_TEMPERATURE, DEFAULT_AI_TASK_TEMPERATURE
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=2.0,
                        step=0.05,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(
                    CONF_AI_TASK_MAX_TOKENS,
                    default=current_options.get(
                        CONF_AI_TASK_MAX_TOKENS, DEFAULT_AI_TASK_MAX_TOKENS
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=16384,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current_options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=15,
                        max=3600,
                        step=5,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
