"""Button platform for OmniRoute integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import OmniRouteClient
from .const import CONF_API_URL, DATA_CLIENT, DATA_COORDINATOR, DOMAIN
from .coordinator import OmniRouteDataUpdateCoordinator
from .helpers import get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OmniRoute button entities from a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OmniRouteDataUpdateCoordinator = entry_data[DATA_COORDINATOR]
    client: OmniRouteClient = entry_data[DATA_CLIENT]

    entities: list[ButtonEntity] = [
        OmniRouteRefreshButton(coordinator, client, entry),
    ]

    async_add_entities(entities)


class OmniRouteButton(CoordinatorEntity[OmniRouteDataUpdateCoordinator], ButtonEntity):
    """Base class for OmniRoute buttons."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OmniRouteDataUpdateCoordinator,
        client: OmniRouteClient,
        entry: ConfigEntry,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.client = client
        self.entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        sw_version = None
        if coordinator.data:
            sw_version = coordinator.data.get("version")
        self._attr_device_info = get_device_info(entry, sw_version)


class OmniRouteRefreshButton(OmniRouteButton):
    """Button to force reload models and cascade cache."""

    def __init__(
        self,
        coordinator: OmniRouteDataUpdateCoordinator,
        client: OmniRouteClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize refresh button."""
        super().__init__(
            coordinator,
            client,
            entry,
            ButtonEntityDescription(
                key="refresh_models",
                name="Reload Models",
                icon="mdi:refresh",
                entity_category=EntityCategory.CONFIG,
            ),
        )

    async def async_press(self) -> None:
        """Force refresh data in coordinator."""
        _LOGGER.info("Reloading OmniRoute models cache for %s", self.entry.entry_id)
        await self.coordinator.async_refresh()
