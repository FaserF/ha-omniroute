"""Test OmniRoute image platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.omniroute.const import (
    DATA_COORDINATOR,
    DEFAULT_MANUFACTURER,
    DEFAULT_MODEL,
    DOMAIN,
)
from custom_components.omniroute.image import (
    DATA_IMAGE_ENTITY,
    OmniRouteLatestGeneratedImage,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_image_setup_entry(hass, mock_config_entry):
    """Test image platform setup."""
    mock_add = MagicMock()
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.0.0"}

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            DATA_COORDINATOR: mock_coord,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    entities = mock_add.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], OmniRouteLatestGeneratedImage)
    assert (
        hass.data[DOMAIN][mock_config_entry.entry_id][DATA_IMAGE_ENTITY] == entities[0]
    )


@pytest.mark.asyncio
async def test_latest_generated_image_entity(hass, mock_config_entry):
    """Test image entity operations."""
    mock_coord = MagicMock()
    mock_coord.data = {"version": "1.0.0"}

    image_entity = OmniRouteLatestGeneratedImage(hass, mock_coord, mock_config_entry)
    assert image_entity.device_info["manufacturer"] == DEFAULT_MANUFACTURER
    assert image_entity.device_info["model"] == DEFAULT_MODEL
    assert (
        image_entity.unique_id == f"{mock_config_entry.entry_id}_latest_generated_image"
    )
    assert image_entity.image_last_updated is None
    assert await image_entity.async_image() is None

    # Test set_image
    image_entity.async_write_ha_state = MagicMock()
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    image_entity.set_image(fake_png)

    assert image_entity.image_last_updated is not None
    assert await image_entity.async_image() == fake_png
    assert image_entity.async_write_ha_state.called
