"""Helper utilities for OmniRoute integration."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from .const import CONF_API_URL, DEFAULT_MANUFACTURER, DEFAULT_MODEL, DOMAIN


def get_integration_version() -> str:
    """Read integration version from manifest.json."""
    try:
        manifest_path = Path(__file__).parent / "manifest.json"
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
            return str(data.get("version", ""))
    except Exception:
        return ""


def get_device_info(entry: ConfigEntry, sw_version: str | None = None) -> DeviceInfo:
    """Return device registry DeviceInfo for OmniRoute entry."""
    version = sw_version or get_integration_version() or None
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="OmniRoute Gateway",
        manufacturer=DEFAULT_MANUFACTURER,
        model=DEFAULT_MODEL,
        sw_version=version,
        configuration_url=entry.data.get(CONF_API_URL, "").replace("/v1", ""),
    )
