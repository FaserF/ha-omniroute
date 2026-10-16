"""Test OmniRoute Speech-to-Text (STT) platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResultState,
)

from custom_components.omniroute.const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DEFAULT_MANUFACTURER,
    DEFAULT_MODEL,
    DOMAIN,
)
from custom_components.omniroute.stt import OmniRouteSTTEntity, async_setup_entry


@pytest.mark.asyncio
async def test_stt_setup_entry(hass, mock_config_entry):
    """Test setup of STT platform."""
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
    assert isinstance(entities[0], OmniRouteSTTEntity)


def test_stt_properties_and_device_info(mock_config_entry):
    """Test STT entity properties and device info."""
    mock_client = MagicMock()
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.2.3"}

    entity = OmniRouteSTTEntity(mock_config_entry, mock_client, mock_coord)

    assert "en" in entity.supported_languages
    assert "de" in entity.supported_languages
    assert AudioFormats.WAV in entity.supported_formats
    assert AudioCodecs.PCM in entity.supported_codecs
    assert AudioBitRates.BITRATE_16 in entity.supported_bit_rates
    assert AudioSampleRates.SAMPLERATE_16000 in entity.supported_sample_rates
    assert AudioChannels.CHANNEL_MONO in entity.supported_channels

    dev_info = entity.device_info
    assert dev_info["manufacturer"] == DEFAULT_MANUFACTURER
    assert dev_info["model"] == DEFAULT_MODEL
    assert dev_info["sw_version"] == "1.2.3"


@pytest.mark.asyncio
async def test_stt_process_audio_stream_success(mock_config_entry):
    """Test successful STT audio transcription."""
    mock_client = MagicMock()
    mock_client.async_speech_to_text = AsyncMock(
        return_value="Turn on the living room light"
    )
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.0.0"}

    entity = OmniRouteSTTEntity(mock_config_entry, mock_client, mock_coord)

    async def sample_stream():
        yield b"chunk1"
        yield b"chunk2"

    metadata = SpeechMetadata(
        language="en",
        format=AudioFormats.WAV,
        codec=AudioCodecs.PCM,
        bit_rate=AudioBitRates.BITRATE_16,
        sample_rate=AudioSampleRates.SAMPLERATE_16000,
        channel=AudioChannels.CHANNEL_MONO,
    )

    result = await entity.async_process_audio_stream(metadata, sample_stream())
    assert result.text == "Turn on the living room light"
    assert result.result == SpeechResultState.SUCCESS
    assert mock_client.async_speech_to_text.called


@pytest.mark.asyncio
async def test_stt_process_audio_stream_failure(mock_config_entry):
    """Test failed STT audio transcription handling."""
    mock_client = MagicMock()
    mock_client.async_speech_to_text = AsyncMock(side_effect=RuntimeError("API error"))
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.0.0"}

    entity = OmniRouteSTTEntity(mock_config_entry, mock_client, mock_coord)

    async def sample_stream():
        yield b"dummy audio"

    metadata = SpeechMetadata(
        language="en",
        format=AudioFormats.WAV,
        codec=AudioCodecs.PCM,
        bit_rate=AudioBitRates.BITRATE_16,
        sample_rate=AudioSampleRates.SAMPLERATE_16000,
        channel=AudioChannels.CHANNEL_MONO,
    )

    result = await entity.async_process_audio_stream(metadata, sample_stream())
    assert result.text == ""
    assert result.result == SpeechResultState.ERROR
