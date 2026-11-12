"""Weather Underground PWS API client."""
from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse
from typing import Any

import aiohttp

from .const import WU_API_URL, WU_DASHBOARD_URL

_LOGGER = logging.getLogger(__name__)

# Candidate patterns from the upstream integration. Never hardcode a service key.
API_KEY_PATTERNS = [
    re.compile(r'"apiKey"\s*:\s*"([a-zA-Z0-9]{32})"'),
    re.compile(r'apiKey=([a-zA-Z0-9]{32})'),
    re.compile(r'"SUN_API_KEY"\s*:\s*"([a-zA-Z0-9]{32})"'),
    re.compile(r"TWC_API_KEY\s*=\s*[\"']([a-zA-Z0-9]{32})[\"']"),
    re.compile(r"api\.weather\.com[^\"']*apiKey=([a-zA-Z0-9]{32})"),
    re.compile(r'"key"\s*:\s*"([a-zA-Z0-9]{32})"'),
]
# Limit asset fetching to known dashboard-controlled hosts, not arbitrary HTML URLs.
SCRIPT_HOSTS = {"www.wunderground.com", "wunderground.com", "assets.wunderground.com"}
SCRIPT_SRC = re.compile(r"<script\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)

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
        """Discover and verify a dashboard API key from HTML and JS assets.

        Weather Underground can move the web client's key into its bundled
        JavaScript. No fixed key is shipped or logged by this integration.
        """
        url = WU_DASHBOARD_URL.format(station_id=self.station_id)
        session = await self._get_session()
        try:
            async with session.get(
                url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    raise WundergroundConnectionError(
                        f"Dashboard request failed: HTTP {resp.status}"
                    )
                html = await resp.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise WundergroundConnectionError(f"Dashboard connection error: {err}") from err

        candidates: list[str] = []
        def collect(source: str) -> None:
            for pattern in API_KEY_PATTERNS:
                for match in pattern.finditer(source):
                    key = match.group(1)
                    if key not in candidates:
                        candidates.append(key)

        collect(html)
        # Read a limited number of scripts as browser dashboards typically issue
        # observation requests from JavaScript rather than embedding API URLs in HTML.
        seen: set[str] = set()
        for src in SCRIPT_SRC.findall(html):
            script_url = urljoin(url, src.replace("&amp;", "&"))
            parsed = urlparse(script_url)
            if (parsed.scheme != "https" or parsed.hostname not in SCRIPT_HOSTS
                    or script_url in seen):
                continue
            seen.add(script_url)
            if len(seen) > 20:
                break
            try:
                async with session.get(
                    script_url, headers=HEADERS,
                    timeout=aiohttp.ClientTimeout(total=12),
                    allow_redirects=False,
                ) as resp:
                    if resp.status != 200:
                        continue
                    if int(resp.headers.get("Content-Length", 0)) > 2_000_000:
                        continue
                    script = await resp.content.read(2_000_001)
                    if len(script) > 2_000_000:
                        continue
                    collect(script.decode("utf-8", errors="ignore"))
            except (aiohttp.ClientError, TimeoutError, ValueError):
                continue

        # Validate candidate keys rather than trusting the first regex match.
        previous_key = self.api_key
        try:
            for candidate in candidates:
                self.api_key = candidate
                try:
                    await self.get_observations()
                except (WundergroundAuthError, WundergroundApiError):
                    continue
                _LOGGER.debug("Validated discovered dashboard key for %s", self.station_id)
                return candidate
        finally:
            self.api_key = previous_key

        raise WundergroundAuthError(
            "No working API key found in the dashboard or its scripts. "
            "Enter a valid API key manually."
        )

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
