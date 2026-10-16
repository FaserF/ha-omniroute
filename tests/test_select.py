"""Test OmniRoute select platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.omniroute.const import (
    CONF_CHAT_MODEL,
    CONF_TTS_VOICE,
    DATA_COORDINATOR,
    DOMAIN,
)
from custom_components.omniroute.select import (
    OmniRouteActiveCascadeSelect,
    OmniRouteTTSVoiceSelect,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_select_setup_entry(hass, mock_config_entry):
    """Test select platform setup."""
    mock_add = MagicMock()
    mock_coord = MagicMock()
    mock_coord.data = {
        "version": "1.0.0",
        "models": ["chat-cascade", "fast-cascade", "coding-cascade"],
    }

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            DATA_COORDINATOR: mock_coord,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    entities = mock_add.call_args[0][0]
    assert len(entities) == 2


@pytest.mark.asyncio
async def test_active_cascade_select(hass, mock_config_entry):
    """Test active cascade select entity."""
    mock_coord = MagicMock()
    mock_coord.data = {
        "version": "1.0.0",
        "models": ["chat-cascade", "fast-cascade", "coding-cascade"],
    }

    select = OmniRouteActiveCascadeSelect(mock_coord, mock_config_entry)
    select.hass = hass

    assert "chat-cascade" in select.options
    assert "fast-cascade" in select.options
    assert select.current_option == "chat-cascade"

    await select.async_select_option("fast-cascade")
    assert mock_config_entry.options[CONF_CHAT_MODEL] == "fast-cascade"


@pytest.mark.asyncio
async def test_tts_voice_select(hass, mock_config_entry):
    """Test TTS voice select entity."""
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.0.0"}

    select = OmniRouteTTSVoiceSelect(mock_coord, mock_config_entry)
    select.hass = hass

    assert "Charon" in select.options
    assert "Puck" in select.options
    assert select.current_option == "Puck"

    await select.async_select_option("Charon")
    assert mock_config_entry.options[CONF_TTS_VOICE] == "Charon"
