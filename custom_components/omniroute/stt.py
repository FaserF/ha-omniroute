"""Support for OmniRoute Speech-to-Text (STT)."""

from __future__ import annotations

from collections.abc import AsyncIterable

from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
    SpeechToTextEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import OmniRouteClient
from .const import (
    CONF_STT_LANGUAGE,
    CONF_STT_MODEL,
    DEFAULT_STT_LANGUAGE,
    DEFAULT_STT_MODEL,
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
    """Set up OmniRoute STT platform from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: OmniRouteClient = data["client"]
    coordinator: OmniRouteDataUpdateCoordinator = data["coordinator"]

    async_add_entities([OmniRouteSTTEntity(entry, client, coordinator)])


class OmniRouteSTTEntity(
    CoordinatorEntity[OmniRouteDataUpdateCoordinator], SpeechToTextEntity
):
    """OmniRoute Speech-to-Text entity."""

    _attr_has_entity_name = True
    _attr_name = "Speech-to-Text"

    def __init__(
        self,
        entry: ConfigEntry,
        client: OmniRouteClient,
        coordinator: OmniRouteDataUpdateCoordinator,
    ) -> None:
        """Initialize STT entity."""
        super().__init__(coordinator)
        self.entry = entry
        self.client = client
        self._attr_unique_id = f"{entry.entry_id}_stt"
        sw_version = None
        if coordinator.data:
            sw_version = coordinator.data.get("version")
        self._attr_device_info = get_device_info(entry, sw_version)

    @property
    def supported_languages(self) -> list[str]:
        """Return supported languages."""
        return ["en", "de", "es", "fr", "it", "nl", "pt", "ru", "zh", "ja"]

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return supported audio formats."""
        return [AudioFormats.WAV, AudioFormats.OGG]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return supported audio codecs."""
        return [AudioCodecs.PCM, AudioCodecs.OPUS]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return supported bit rates."""
        return [AudioBitRates.BITRATE_16, AudioBitRates.BITRATE_32]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return supported sample rates."""
        return [
            AudioSampleRates.SAMPLERATE_8000,
            AudioSampleRates.SAMPLERATE_16000,
            AudioSampleRates.SAMPLERATE_44100,
            AudioSampleRates.SAMPLERATE_48000,
        ]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return supported channels."""
        return [AudioChannels.CHANNEL_MONO, AudioChannels.CHANNEL_STEREO]

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Process audio stream and return transcription."""
        audio_chunks = []
        async for chunk in stream:
            audio_chunks.append(chunk)
        audio_data = b"".join(audio_chunks)

        if not audio_data:
            return SpeechResult("", SpeechResultState.ERROR)

        # Ensure raw PCM streams are properly wrapped in a WAV container with RIFF header
        if not audio_data.startswith(b"RIFF"):
            try:
                import io
                import wave

                channels = int(
                    getattr(metadata.channel, "value", metadata.channel)
                    if hasattr(metadata, "channel")
                    else 1
                )
                sampwidth = int(getattr(metadata.bit_rate, "value", metadata.bit_rate)) // 8
                framerate = int(getattr(metadata.sample_rate, "value", metadata.sample_rate))

                wav_buf = io.BytesIO()
                with wave.open(wav_buf, "wb") as wav_file:
                    wav_file.setnchannels(channels)
                    wav_file.setsampwidth(sampwidth)
                    wav_file.setframerate(framerate)
                    wav_file.writeframes(audio_data)
                audio_data = wav_buf.getvalue()
            except Exception as enc_err:
                LOGGER.warning("Could not wrap audio into WAV container: %s", enc_err)

        options = self.entry.options
        model = options.get(CONF_STT_MODEL, DEFAULT_STT_MODEL)
        language = options.get(CONF_STT_LANGUAGE, DEFAULT_STT_LANGUAGE)

        try:
            text = await self.client.async_speech_to_text(
                audio_data=audio_data,
                model=model,
                language=language if language != "auto" else None,
            )
            return SpeechResult(text, SpeechResultState.SUCCESS)
        except Exception as err:
            LOGGER.error("OmniRoute STT transcription failed: %s", err)
            return SpeechResult("", SpeechResultState.ERROR)
