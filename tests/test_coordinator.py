"""Test OmniRoute DataUpdateCoordinator."""

from unittest.mock import AsyncMock, MagicMock
import pytest

from custom_components.omniroute.client import CannotConnect
from custom_components.omniroute.coordinator import (
    OmniRouteDataUpdateCoordinator,
    UpdateFailed,
)


@pytest.mark.asyncio
async def test_coordinator_update_success(hass):
    """Test successful coordinator polling cycle."""
    mock_client = MagicMock()
    mock_client.async_check_health = AsyncMock(
        return_value={"status": "ok", "reachable": True, "latency_ms": 12.5}
    )
    mock_client.async_get_models = AsyncMock(
        return_value=["chat-cascade", "coding-cascade", "gpt-4o"]
    )

    coordinator = OmniRouteDataUpdateCoordinator(hass, mock_client)
    await coordinator.async_refresh()

    assert coordinator.data["reachable"] is True
    assert coordinator.data["status"] == "ok"
    assert coordinator.data["latency_ms"] == 12.5
    assert coordinator.data["models_count"] == 3
    assert "chat-cascade" in coordinator.data["active_cascades"]
    assert coordinator.data["cascade_status"]["coding-cascade"] is True
    assert coordinator.data["cascade_status"]["fast-cascade"] is False


@pytest.mark.asyncio
async def test_coordinator_update_failure(hass):
    """Test coordinator update failure handling."""
    mock_client = MagicMock()
    mock_client.async_check_health = AsyncMock(
        side_effect=CannotConnect("Connection refused")
    )

    coordinator = OmniRouteDataUpdateCoordinator(hass, mock_client)
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
