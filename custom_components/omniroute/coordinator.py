"""DataUpdateCoordinator for OmniRoute."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import CannotConnect, InvalidAuth, OmniRouteClient, OmniRouteError
from .const import DEFAULT_CASCADES, DOMAIN, LOGGER

UPDATE_INTERVAL = timedelta(seconds=60)


class OmniRouteDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching OmniRoute data."""

    def __init__(self, hass: HomeAssistant, client: OmniRouteClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self.models: list[str] = []

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from OmniRoute."""
        try:
            health = await self.client.async_check_health()
            try:
                models = await self.client.async_get_models()
                self.models = models
            except (CannotConnect, OmniRouteError) as err:
                if self.models:
                    LOGGER.debug("Could not refresh models, using cached list: %s", err)
                    models = self.models
                else:
                    raise
            quotas = await self.client.async_get_quotas()

            # Check cascade availability dynamically from server
            server_cascades: list[str] = []
            if hasattr(self.client, "async_get_cascades"):
                try:
                    fetched = await self.client.async_get_cascades()
                    if fetched:
                        server_cascades = fetched
                except Exception as exc:
                    LOGGER.debug("Could not fetch cascades dynamically: %s", exc)

            for c in server_cascades:
                if c not in models:
                    models.append(c)
            self.models = models

            active_cascades = server_cascades if server_cascades else [m for m in models if "cascade" in m]
            cascade_status = {c: True for c in (server_cascades or active_cascades)}

            return {
                "reachable": health.get("reachable", False),
                "status": health.get("status", "unknown"),
                "latency_ms": health.get("latency_ms"),
                "models_count": len(models),
                "models": models,
                "active_cascades": active_cascades,
                "cascade_status": cascade_status,
                "version": str(health.get("version") or "3.8.51"),
                "healthy": (health.get("status") == "ok")
                and health.get("reachable", False),
                "quotas": quotas.get("quotas", {}),
                "providers": quotas.get("providers", {}),
            }
        except (CannotConnect, InvalidAuth, OmniRouteError) as err:
            raise UpdateFailed(f"Error communicating with OmniRoute: {err}") from err
        except Exception as err:
            raise UpdateFailed(
                f"Unexpected error updating OmniRoute data: {err}"
            ) from err
