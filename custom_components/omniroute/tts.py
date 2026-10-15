"""Support for OmniRoute Text-to-Speech (TTS)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.tts import (
    TextToSpeechEntity,
    TtsAudioType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import OmniRouteClient
from .const import (
    CONF_TTS_FORMAT,
    CONF_TTS_MODEL,
    CONF_TTS_SPEED,
    CONF_TTS_VOICE,
    DEFAULT_TTS_FORMAT,
    DEFAULT_TTS_MODEL,
    DEFAULT_TTS_SPEED,
    DEFAULT_TTS_VOICE,
    DOMAIN,
    LOGGER,
    SUPPORTED_TTS_FORMATS,
)
from .coordinator import OmniRouteDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OmniRoute TTS platform from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: OmniRouteClient = data["client"]
    coordinator: OmniRouteDataUpdateCoordinator = data["coordinator"]

    async_add_entities([OmniRouteTTSEntity(entry, client, coordinator)])


class OmniRouteTTSEntity(
    CoordinatorEntity[OmniRouteDataUpdateCoordinator], TextToSpeechEntity
):
    """OmniRoute Text-to-Speech entity."""

    _attr_has_entity_name = True
    _attr_name = "Text-to-Speech"

    def __init__(
        self,
        entry: ConfigEntry,
        client: OmniRouteClient,
        coordinator: OmniRouteDataUpdateCoordinator,
    ) -> None:
        """Initialize TTS entity."""
        super().__init__(coordinator)
        self.entry = entry
        self.client = client
        self._attr_unique_id = f"{entry.entry_id}_tts"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "OmniRoute Gateway",
            "manufacturer": "FaserF",
            "model": "Hermes AI Gateway",
        }

    @property
    def supported_languages(self) -> list[str]:
        """Return supported languages."""
        return ["en", "de", "es", "fr", "it", "nl", "pt", "ru", "zh", "ja"]

    @property
    def default_language(self) -> str:
        """Return default language."""
        return "en"

    @property
    def supported_options(self) -> list[str]:
        """Return supported options."""
        return ["voice", "speed"]

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any] | None = None
    ) -> TtsAudioType:
        """Synthesize text into speech audio bytes."""
        cfg_options = self.entry.options
        model = cfg_options.get(CONF_TTS_MODEL, DEFAULT_TTS_MODEL)
        voice = (options or {}).get("voice") or cfg_options.get(
            CONF_TTS_VOICE, DEFAULT_TTS_VOICE
        )
        speed = float(
            (options or {}).get("speed")
            or cfg_options.get(CONF_TTS_SPEED, DEFAULT_TTS_SPEED)
        )
        response_format = cfg_options.get(CONF_TTS_FORMAT, DEFAULT_TTS_FORMAT)
        if response_format not in SUPPORTED_TTS_FORMATS:
            response_format = "mp3"

        try:
            audio_bytes = await self.client.async_text_to_speech(
                text=message,
                model=model,
                voice=voice,
                response_format=response_format,
                speed=speed,
            )
            return response_format, audio_bytes
        except Exception as err:
            LOGGER.error("OmniRoute TTS synthesis failed: %s", err)
            return None, None
