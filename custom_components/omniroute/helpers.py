"""Helper utilities for OmniRoute integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from .const import CONF_API_URL, DEFAULT_MANUFACTURER, DEFAULT_MODEL, DOMAIN


def get_device_info(entry: ConfigEntry, sw_version: str | None = None) -> DeviceInfo:
    """Return device registry DeviceInfo for OmniRoute entry."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="OmniRoute Gateway",
        manufacturer=DEFAULT_MANUFACTURER,
        model=DEFAULT_MODEL,
        sw_version=sw_version or "0.1.0",
        configuration_url=entry.data.get(CONF_API_URL),
    )
