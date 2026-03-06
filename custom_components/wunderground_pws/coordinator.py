"""DataUpdateCoordinator for Weather Underground PWS."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.helpers.aiohttp_client as ha_aiohttp

from .api import (
    WundergroundApiError,
    WundergroundAuthError,
    WundergroundConnectionError,
    WundergroundPWSClient,
)
from .const import CONF_API_KEY, CONF_STATION_ID, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class WundergroundPWSCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching Weather Underground PWS data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.station_id: str = entry.data[CONF_STATION_ID]
        self.api_key: str = entry.data[CONF_API_KEY]

        session = ha_aiohttp.async_get_clientsession(hass)
        self.client = WundergroundPWSClient(
            station_id=self.station_id,
            api_key=self.api_key,
            session=session,
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.station_id}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Weather Underground API."""
        try:
            return await self.client.get_observations()
        except WundergroundAuthError as err:
            # Signal HA to trigger re-auth flow
            raise ConfigEntryAuthFailed(
                f"Authentication failed for station {self.station_id}: {err}"
            ) from err
        except WundergroundConnectionError as err:
            raise UpdateFailed(
                f"Error communicating with Weather Underground: {err}"
            ) from err
        except WundergroundApiError as err:
            raise UpdateFailed(f"Weather Underground error: {err}") from err
