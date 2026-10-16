"""Switch platform for OmniRoute integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import OmniRouteClient
from .const import (
    CONF_TOKEN_COMPRESSION,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DEFAULT_TOKEN_COMPRESSION,
    DOMAIN,
)
from .coordinator import OmniRouteDataUpdateCoordinator
from .helpers import get_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OmniRoute switch entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: OmniRouteClient = data[DATA_CLIENT]
    coordinator: OmniRouteDataUpdateCoordinator = data[DATA_COORDINATOR]

    async_add_entities([OmniRouteTokenCompressionSwitch(coordinator, entry, client)])


class OmniRouteTokenCompressionSwitch(
    CoordinatorEntity[OmniRouteDataUpdateCoordinator], SwitchEntity
):
    """Switch entity for prompt token optimization / compression."""

    _attr_has_entity_name = True
    _attr_name = "Token Compression"
    _attr_icon = "mdi:arrow-collapse-horizontal"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: OmniRouteDataUpdateCoordinator,
        entry: ConfigEntry,
        client: OmniRouteClient,
    ) -> None:
        """Initialize token compression switch."""
        super().__init__(coordinator)
        self.entry = entry
        self.client = client
        self._attr_unique_id = f"{entry.entry_id}_token_compression"
        sw_version = coordinator.data.get("version") if coordinator.data else None
        self._attr_device_info = get_device_info(entry, sw_version)
        # Sync initial state from entry options
        initial = entry.options.get(CONF_TOKEN_COMPRESSION, DEFAULT_TOKEN_COMPRESSION)
        self.client.compression_enabled = initial

    @property
    def is_on(self) -> bool:
        """Return whether prompt token compression is enabled."""
        return self.client.compression_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable token compression."""
        self.client.compression_enabled = True
        new_options = dict(self.entry.options)
        new_options[CONF_TOKEN_COMPRESSION] = True
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable token compression."""
        self.client.compression_enabled = False
        new_options = dict(self.entry.options)
        new_options[CONF_TOKEN_COMPRESSION] = False
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
        self.async_write_ha_state()
