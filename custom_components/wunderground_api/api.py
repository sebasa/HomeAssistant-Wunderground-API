"""Weather Underground PWS API client."""
from __future__ import annotations

import logging
import re
from typing import Any

import aiohttp

from .const import WU_API_URL, WU_DASHBOARD_URL

_LOGGER = logging.getLogger(__name__)

# Patterns to find the API key in the Wunderground dashboard page source
API_KEY_PATTERNS = [
    re.compile(r'"apiKey"\s*:\s*"([a-zA-Z0-9]{32})"'),
    re.compile(r'apiKey=([a-zA-Z0-9]{32})'),
    re.compile(r'"SUN_API_KEY"\s*:\s*"([a-zA-Z0-9]{32})"'),
    re.compile(r'TWC_API_KEY\s*=\s*["\']([a-zA-Z0-9]{32})["\']'),
    re.compile(r'api\.weather\.com[^"\']*apiKey=([a-zA-Z0-9]{32})'),
    re.compile(r'"key"\s*:\s*"([a-zA-Z0-9]{32})"'),
    re.compile(r'["\']([a-zA-Z0-9]{32})["\']'),  # Fallback: any 32-char alphanumeric string
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
    """Base exception for Wunderground API errors."""


class WundergroundAuthError(WundergroundApiError):
    """Authentication error (bad API key)."""


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
        """Initialize the client."""
        self.station_id = station_id.upper()
        self.api_key = api_key
        self._session = session
        self._owns_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session if we own it."""
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def discover_api_key(self) -> str:
        """
        Scrape the Wunderground dashboard page to extract the API key.
        Returns the API key string.
        """
        url = WU_DASHBOARD_URL.format(station_id=self.station_id)
        session = await self._get_session()

        _LOGGER.debug("Fetching Wunderground dashboard: %s", url)

        try:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    raise WundergroundConnectionError(
                        f"Failed to fetch dashboard page: HTTP {resp.status}"
                    )
                html = await resp.text()
        except aiohttp.ClientError as err:
            raise WundergroundConnectionError(f"Connection error: {err}") from err

        # Try each pattern to find the API key
        for pattern in API_KEY_PATTERNS[:-1]:  # Skip fallback pattern first
            match = pattern.search(html)
            if match:
                api_key = match.group(1)
                _LOGGER.info(
                    "Found Wunderground API key for station %s (pattern: %s)",
                    self.station_id,
                    pattern.pattern[:30],
                )
                return api_key

        # Try fallback: look for API calls in the HTML that contain the key
        api_call_pattern = re.compile(
            r'api\.weather\.com[^\s"\']*apiKey=([a-zA-Z0-9]{32})', re.IGNORECASE
        )
        match = api_call_pattern.search(html)
        if match:
            return match.group(1)

        # Last resort: find any 32-char alphanumeric token near API-related keywords
        context_pattern = re.compile(
            r'(?:apiKey|API_KEY|api_key)[^a-zA-Z0-9]*([a-zA-Z0-9]{32})', re.IGNORECASE
        )
        match = context_pattern.search(html)
        if match:
            return match.group(1)

        _LOGGER.debug("Page source length: %d characters", len(html))
        raise WundergroundAuthError(
            f"Could not find API key in Wunderground dashboard for station '{self.station_id}'. "
            "The page structure may have changed. Please report this issue."
        )

    async def get_observations(self) -> dict[str, Any]:
        """
        Fetch current observations for the station.
        Returns parsed JSON data.
        """
        if not self.api_key:
            raise WundergroundAuthError("No API key set. Call discover_api_key() first.")

        url = WU_API_URL.format(station_id=self.station_id, api_key=self.api_key)
        session = await self._get_session()

        _LOGGER.debug("Fetching observations for station %s", self.station_id)

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 401:
                    raise WundergroundAuthError("Invalid API key")
                if resp.status == 404:
                    raise WundergroundApiError(
                        f"Station '{self.station_id}' not found"
                    )
                if resp.status != 200:
                    raise WundergroundConnectionError(
                        f"API request failed: HTTP {resp.status}"
                    )
                data = await resp.json()
        except aiohttp.ClientError as err:
            raise WundergroundConnectionError(f"Connection error: {err}") from err

        if "observations" not in data or not data["observations"]:
            raise WundergroundApiError(
                f"No observations returned for station '{self.station_id}'"
            )

        return data["observations"][0]

    async def validate_station(self) -> bool:
        """Validate that the station ID exists and is accessible."""
        try:
            await self.get_observations()
            return True
        except WundergroundApiError:
            return False
