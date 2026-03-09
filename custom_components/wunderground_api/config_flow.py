"""Config flow for Weather Underground PWS integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
import homeassistant.helpers.aiohttp_client as ha_aiohttp

from .api import (
    WundergroundApiError,
    WundergroundAuthError,
    WundergroundConnectionError,
    WundergroundPWSClient,
)
from .const import CONF_API_KEY, CONF_STATION_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STATION_ID): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate user input: scrape API key and test connection."""
    session = ha_aiohttp.async_get_clientsession(hass)
    station_id = data[CONF_STATION_ID].strip().upper()

    client = WundergroundPWSClient(station_id=station_id, session=session)

    api_key = await client.discover_api_key()
    client.api_key = api_key

    observation = await client.get_observations()
    neighborhood = observation.get("neighborhood", "")

    return {
        "api_key": api_key,
        "station_id": station_id,
        "title": f"WU PWS: {station_id}" + (f" ({neighborhood})" if neighborhood else ""),
    }


class WundergroundPWSConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Weather Underground PWS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except WundergroundAuthError:
                errors["base"] = "api_key_not_found"
            except WundergroundConnectionError:
                errors["base"] = "cannot_connect"
            except WundergroundApiError as err:
                _LOGGER.error("Wunderground API error: %s", err)
                errors["base"] = "unknown"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during config flow")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info["station_id"])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_STATION_ID: info["station_id"],
                        CONF_API_KEY: info["api_key"],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Re-scrape a fresh API key."""
        errors: dict[str, str] = {}
        reauth_entry: ConfigEntry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        if user_input is not None:
            try:
                info = await validate_input(
                    self.hass, {CONF_STATION_ID: reauth_entry.data[CONF_STATION_ID]}
                )
            except WundergroundAuthError:
                errors["base"] = "api_key_not_found"
            except WundergroundConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(
                    reauth_entry,
                    data={**reauth_entry.data, CONF_API_KEY: info["api_key"]},
                )
                await self.hass.config_entries.async_reload(reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({}),
            errors=errors,
        )
