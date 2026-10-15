"""Test OmniRoute diagnostics support."""

from unittest.mock import MagicMock

import pytest

from custom_components.omniroute.const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
)
from custom_components.omniroute.diagnostics import (
    _to_json_safe,
    async_get_config_entry_diagnostics,
)


@pytest.mark.asyncio
async def test_diagnostics_dump(hass, mock_config_entry):
    """Test diagnostics dump and secret redaction."""
    mock_client = MagicMock()
    mock_client.v1_url = "http://omniroute:20128/v1"
    mock_client.root_url = "http://omniroute:20128"
    mock_client._api_key = "super-secret-key"

    mock_coordinator = MagicMock()
    mock_coordinator.last_update_success = True
    mock_coordinator.models = ["chat-cascade", "coding-cascade"]
    mock_coordinator.data = {
        "reachable": True,
        "healthy": True,
        "status": "ok",
        "latency_ms": 14.5,
        "models_count": 2,
    }

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            DATA_CLIENT: mock_client,
            DATA_COORDINATOR: mock_coordinator,
        }
    }

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert "entry" in diag
    assert "client" in diag
    assert "coordinator" in diag
    assert "devices" in diag
    assert "entities" in diag

    # Verify secret redaction
    assert diag["entry"]["data"]["api_key"] == "**REDACTED**"
    assert diag["client"]["has_api_key"] is True
    assert "super-secret-key" not in str(diag)

    # Verify coordinator data
    assert diag["coordinator"]["last_update_success"] is True
    assert diag["coordinator"]["models_cached_count"] == 2
    assert diag["coordinator"]["data"]["latency_ms"] == 14.5


def test_to_json_safe():
    """Test helper for JSON-safe serialization."""
    assert _to_json_safe(None) is None
    assert _to_json_safe(True) is True
    assert _to_json_safe(42) == 42
    assert _to_json_safe("string") == "string"
    assert _to_json_safe(float("nan")) == "nan"
    assert _to_json_safe(float("inf")) == "inf"
    assert _to_json_safe([1, 2, 3]) == [1, 2, 3]
    assert _to_json_safe({"a": 1}) == {"a": 1}

    class Dummy:
        def __init__(self):
            self.x = 10

    assert _to_json_safe(Dummy()) == {"x": 10}
