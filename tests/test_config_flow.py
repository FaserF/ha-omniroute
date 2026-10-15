"""Test OmniRoute config flow."""

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.omniroute.client import (
    CannotConnect,
    InvalidAuth,
)
from custom_components.omniroute.config_flow import (
    OmniRouteConfigFlow,
    OmniRouteOptionsFlow,
)
from custom_components.omniroute.const import (
    CONF_API_KEY,
    CONF_API_URL,
    CONF_CHAT_MODEL,
    DEFAULT_API_URL,
)


@pytest.mark.asyncio
async def test_flow_user_init(hass):
    """Test initial user step."""
    flow = OmniRouteConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()
    assert result["type"] == "form"
    assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_flow_user_success(hass):
    """Test successful user configuration."""
    flow = OmniRouteConfigFlow()
    flow.hass = hass

    with patch(
        "custom_components.omniroute.config_flow.OmniRouteClient.async_get_models",
        new_callable=AsyncMock,
        return_value=["chat-cascade", "coding-cascade"],
    ):
        result = await flow.async_step_user(
            {
                CONF_API_URL: DEFAULT_API_URL,
                CONF_API_KEY: "secret-token",
            }
        )
        assert result["type"] == "create_entry"
        assert result["title"] == "OmniRoute"
        assert result["data"][CONF_API_URL] == DEFAULT_API_URL


@pytest.mark.asyncio
async def test_flow_user_invalid_auth(hass):
    """Test authentication error in config flow."""
    flow = OmniRouteConfigFlow()
    flow.hass = hass

    with patch(
        "custom_components.omniroute.config_flow.OmniRouteClient.async_get_models",
        side_effect=InvalidAuth("Invalid key"),
    ):
        result = await flow.async_step_user(
            {
                CONF_API_URL: DEFAULT_API_URL,
                CONF_API_KEY: "bad-token",
            }
        )
        assert result["type"] == "form"
        assert result["errors"]["base"] == "invalid_auth"


@pytest.mark.asyncio
async def test_flow_user_cannot_connect(hass):
    """Test connection error in config flow."""
    flow = OmniRouteConfigFlow()
    flow.hass = hass

    with patch(
        "custom_components.omniroute.config_flow.OmniRouteClient.async_get_models",
        side_effect=CannotConnect("Offline"),
    ):
        result = await flow.async_step_user(
            {
                CONF_API_URL: "http://invalid-host:20128/v1",
            }
        )
        assert result["type"] == "form"
        assert result["errors"]["base"] == "cannot_connect"


@pytest.mark.asyncio
async def test_flow_user_unknown_error(hass):
    """Test unexpected exception in config flow."""
    flow = OmniRouteConfigFlow()
    flow.hass = hass

    with patch(
        "custom_components.omniroute.config_flow.OmniRouteClient.async_get_models",
        side_effect=RuntimeError("Unexpected crash"),
    ):
        result = await flow.async_step_user(
            {
                CONF_API_URL: DEFAULT_API_URL,
            }
        )
        assert result["type"] == "form"
        assert result["errors"]["base"] == "unknown"


@pytest.mark.asyncio
async def test_flow_reauth(hass):
    """Test reauthentication step."""
    flow = OmniRouteConfigFlow()
    flow.hass = hass

    result = await flow.async_step_reauth({})
    assert result["type"] == "form"
    assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_options_flow(hass, mock_config_entry):
    """Test options flow form and save."""
    options_flow = OmniRouteOptionsFlow(mock_config_entry)
    options_flow.hass = hass

    # Form rendering
    result = await options_flow.async_step_init()
    assert result["type"] == "form"
    assert result["step_id"] == "init"

    # Save options
    save_result = await options_flow.async_step_init(
        {
            CONF_CHAT_MODEL: "fast-cascade",
        }
    )
    assert save_result["type"] == "create_entry"
    assert save_result["data"][CONF_CHAT_MODEL] == "fast-cascade"
