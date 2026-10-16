"""Image platform for OmniRoute integration."""

from __future__ import annotations

from datetime import UTC, datetime

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import OmniRouteDataUpdateCoordinator
from .helpers import get_device_info

DATA_IMAGE_ENTITY = "latest_image_entity"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OmniRoute image entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OmniRouteDataUpdateCoordinator = data[DATA_COORDINATOR]

    entity = OmniRouteLatestGeneratedImage(hass, coordinator, entry)
    data[DATA_IMAGE_ENTITY] = entity
    async_add_entities([entity])


class OmniRouteLatestGeneratedImage(
    CoordinatorEntity[OmniRouteDataUpdateCoordinator], ImageEntity
):
    """Image entity showing the most recently generated AI image."""

    _attr_has_entity_name = True
    _attr_name = "Latest Generated Image"
    _attr_icon = "mdi:image-filter-hdr"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: OmniRouteDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize latest generated image entity."""
        CoordinatorEntity.__init__(self, coordinator)
        ImageEntity.__init__(self, hass)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_latest_generated_image"
        sw_version = coordinator.data.get("version") if coordinator.data else None
        self._attr_device_info = get_device_info(entry, sw_version)
        self._image_bytes: bytes | None = None
        self._image_last_updated: datetime | None = None

    @property
    def image_last_updated(self) -> datetime | None:
        """Return timestamp when image was last updated."""
        return self._image_last_updated

    def set_image(self, image_data: bytes) -> None:
        """Update current image bytes and timestamp."""
        self._image_bytes = image_data
        self._image_last_updated = datetime.now(UTC)
        self.async_write_ha_state()

    async def async_image(self) -> bytes | None:
        """Return bytes of latest generated image."""
        return self._image_bytes
