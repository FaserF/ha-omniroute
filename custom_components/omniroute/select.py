"""Select platform for OmniRoute integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_CHAT_MODEL,
    CONF_TTS_VOICE,
    DATA_COORDINATOR,
    DEFAULT_TTS_VOICE,
    DEFAULT_TTS_VOICES,
    DOMAIN,
)
from .coordinator import OmniRouteDataUpdateCoordinator
from .helpers import get_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OmniRoute select entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OmniRouteDataUpdateCoordinator = data[DATA_COORDINATOR]

    entities: list[SelectEntity] = [
        OmniRouteActiveCascadeSelect(coordinator, entry),
        OmniRouteTTSVoiceSelect(coordinator, entry),
    ]
    async_add_entities(entities)


class OmniRouteActiveCascadeSelect(
    CoordinatorEntity[OmniRouteDataUpdateCoordinator], SelectEntity
):
    """Select entity for active LLM cascade / chat model."""

    _attr_has_entity_name = True
    _attr_name = "Active Cascade"
    _attr_icon = "mdi:routes"

    def __init__(
        self,
        coordinator: OmniRouteDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize active cascade select."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_active_cascade"
        sw_version = coordinator.data.get("version") if coordinator.data else None
        self._attr_device_info = get_device_info(entry, sw_version)

    @property
    def options(self) -> list[str]:
        """Return available cascade / model options dynamically."""
        if self.coordinator.data:
            cascades = self.coordinator.data.get("active_cascades", [])
            if cascades:
                return sorted(cascades)
            models = self.coordinator.data.get("models", [])
            if models:
                return sorted(models)
        return ["default"]

    @property
    def current_option(self) -> str | None:
        """Return currently selected active cascade."""
        current = self.entry.options.get(CONF_CHAT_MODEL)
        if current and current in self.options:
            return current
        return self.options[0] if self.options else None

    async def async_select_option(self, option: str) -> None:
        """Update active cascade in config entry options."""
        new_options = dict(self.entry.options)
        new_options[CONF_CHAT_MODEL] = option
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
        self.async_write_ha_state()


class OmniRouteTTSVoiceSelect(
    CoordinatorEntity[OmniRouteDataUpdateCoordinator], SelectEntity
):
    """Select entity for active TTS voice."""

    _attr_has_entity_name = True
    _attr_name = "TTS Voice"
    _attr_icon = "mdi:account-voice"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: OmniRouteDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize TTS voice select."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_tts_voice"
        sw_version = coordinator.data.get("version") if coordinator.data else None
        self._attr_device_info = get_device_info(entry, sw_version)

    @property
    def options(self) -> list[str]:
        """Return available TTS voices."""
        return list(DEFAULT_TTS_VOICES)

    @property
    def current_option(self) -> str | None:
        """Return current TTS voice."""
        return str(self.entry.options.get(CONF_TTS_VOICE, DEFAULT_TTS_VOICE))

    async def async_select_option(self, option: str) -> None:
        """Update active TTS voice in config entry options."""
        new_options = dict(self.entry.options)
        new_options[CONF_TTS_VOICE] = option
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
        self.async_write_ha_state()
