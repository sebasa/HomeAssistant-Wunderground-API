"""Weather Underground PWS API client.

Local patch: when automatic dashboard key extraction fails, try a public
website API key published in the MIT-licensed rkuris/wunderground-scraper
project (https://github.com/rkuris/wunderground-scraper/blob/main/src/main.rs).
No guarantee the upstream service will continue accepting the key.
"""
from __future__ import annotations

import logging
import re
from typing import Any

import aiohttp

from .const import WU_API_URL, WU_DASHBOARD_URL

_LOGGER = logging.getLogger(__name__)

# Public web-client key documented in rkuris/wunderground-scraper (Nov 2026).
# This can be revoked/rotated by Weather Underground without notice.
PUBLIC_WEB_API_KEY = "e1f10a1e78da46f5b10a1e78da96f525"

API_KEY_PATTERNS = [
    re.compile(r'"apiKey"\s*:\s*"([a-zA-Z0-9]{32})"'),
    re.compile(r'apiKey=([a-zA-Z0-9]{32})'),
    re.compile(r'"SUN_API_KEY"\s*:\s*"([a-zA-Z0-9]{32})"'),
    re.compile(r'TWC_API_KEY\s*=\s*["\']([a-zA-Z0-9]{32})["\']'),
    re.compile(r'api\.weather\.com[^"\']*apiKey=([a-zA-Z0-9]{32})'),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class WundergroundApiError(Exception):
    """Base class for Weather Underground errors."""


class WundergroundAuthError(WundergroundApiError):
    """The API rejected the key."""


class WundergroundConnectionError(WundergroundApiError):
    """Connection error."""


class WundergroundPWSClient:
    """Client to interact with Weather Underground PWS."""

    def __init__(
        self,
        station_id: str,
        api_key: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self.station_id = station_id.upper()
        self.api_key = api_key
        self._session = session
        self._owns_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def discover_api_key(self) -> str:
        """Try the dashboard's HTML, then a public website key as fallback."""
        url = WU_DASHBOARD_URL.format(station_id=self.station_id)
        session = await self._get_session()
        try:
            async with session.get(
                url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    for pattern in API_KEY_PATTERNS:
                        match = pattern.search(html)
                        if match:
                            _LOGGER.debug(
                                "Found API key in dashboard for station %s",
                                self.station_id,
                            )
                            return match.group(1)
                else:
                    _LOGGER.debug("Dashboard returned HTTP %s", resp.status)
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.debug("Dashboard key lookup failed: %s", err)

        _LOGGER.warning(
            "Dashboard API-key discovery failed for station %s; "
            "trying public web-client API key (not guaranteed to remain valid)",
            self.station_id,
        )
        return PUBLIC_WEB_API_KEY

    async def get_observations(self) -> dict[str, Any]:
        """Return the newest observations for the specified station."""
        if not self.api_key:
            raise WundergroundAuthError("No API key configured")

        url = WU_API_URL.format(station_id=self.station_id, api_key=self.api_key)
        session = await self._get_session()
        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status in (401, 403):
                    raise WundergroundAuthError(
                        f"Weather Underground rejected the API key (HTTP {resp.status})"
                    )
                if resp.status == 404:
                    raise WundergroundApiError(
                        f"Station '{self.station_id}' not found"
                    )
                if resp.status != 200:
                    raise WundergroundConnectionError(
                        f"API request failed: HTTP {resp.status}"
                    )
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise WundergroundConnectionError(
                f"Connection error: {err}"
            ) from err

        if "observations" not in data or not data["observations"]:
            raise WundergroundApiError(
                f"No current observations returned for '{self.station_id}'"
            )
        return data["observations"][0]

    async def validate_station(self) -> bool:
        try:
            await self.get_observations()
            return True
        except WundergroundApiError:
            return False
