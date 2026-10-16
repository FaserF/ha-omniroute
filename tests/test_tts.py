"""Test OmniRoute Text-to-Speech (TTS) platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.omniroute.const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DEFAULT_MANUFACTURER,
    DEFAULT_MODEL,
    DOMAIN,
)
from custom_components.omniroute.tts import OmniRouteTTSEntity, async_setup_entry


@pytest.mark.asyncio
async def test_tts_setup_entry(hass, mock_config_entry):
    """Test setup of TTS platform."""
    mock_add = MagicMock()
    mock_client = MagicMock()
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.0.0"}

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            DATA_CLIENT: mock_client,
            DATA_COORDINATOR: mock_coord,
            "client": mock_client,
            "coordinator": mock_coord,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    entities = mock_add.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], OmniRouteTTSEntity)


def test_tts_properties_and_device_info(mock_config_entry):
    """Test TTS entity properties and device info."""
    mock_client = MagicMock()
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.2.3"}

    entity = OmniRouteTTSEntity(mock_config_entry, mock_client, mock_coord)

    assert "en" in entity.supported_languages
    assert "de" in entity.supported_languages
    assert entity.default_language == "en"
    assert "voice" in entity.supported_options
    assert "speed" in entity.supported_options

    dev_info = entity.device_info
    assert dev_info["manufacturer"] == DEFAULT_MANUFACTURER
    assert dev_info["model"] == DEFAULT_MODEL
    assert dev_info["sw_version"] == "1.2.3"


@pytest.mark.asyncio
async def test_tts_get_audio_success(mock_config_entry):
    """Test successful TTS synthesis."""
    mock_client = MagicMock()
    mock_client.async_text_to_speech = AsyncMock(return_value=b"fake_mp3_data")
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.0.0"}

    entity = OmniRouteTTSEntity(mock_config_entry, mock_client, mock_coord)

    fmt, data = await entity.async_get_tts_audio(
        "Hello world", "en", {"voice": "Puck", "speed": 1.0}
    )
    assert fmt == "mp3"
    assert data == b"fake_mp3_data"
    assert mock_client.async_text_to_speech.called


@pytest.mark.asyncio
async def test_tts_get_audio_failure(mock_config_entry):
    """Test failed TTS synthesis handling."""
    mock_client = MagicMock()
    mock_client.async_text_to_speech = AsyncMock(
        side_effect=RuntimeError("Synthesis failed")
    )
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.0.0"}

    entity = OmniRouteTTSEntity(mock_config_entry, mock_client, mock_coord)

    fmt, data = await entity.async_get_tts_audio("Hello world", "en")
    assert fmt is None
    assert data is None
