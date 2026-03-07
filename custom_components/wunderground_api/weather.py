"""Weather platform for Weather Underground PWS."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.weather import (
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfSpeed, UnitOfTemperature, UnitOfPressure, UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_STATION_ID, DOMAIN
from .coordinator import WundergroundPWSCoordinator

_LOGGER = logging.getLogger(__name__)


def _condition_from_data(data: dict) -> str:
    """Map Wunderground observation data to HA weather condition."""
    precip_rate = data.get("metric", {}).get("precipRate", 0) or 0
    uv = data.get("uv", 0) or 0
    solar = data.get("solarRadiation", 0) or 0
    wind_speed = data.get("metric", {}).get("windSpeed", 0) or 0

    if precip_rate > 5:
        return "pouring"
    if precip_rate > 0:
        return "rainy"
    if wind_speed > 50:
        return "windy"
    if solar > 400:
        return "sunny"
    if solar > 100:
        return "partlycloudy"
    return "cloudy"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Weather Underground PWS weather entity."""
    coordinator: WundergroundPWSCoordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = entry.data[CONF_STATION_ID]

    async_add_entities([WundergroundPWSWeather(coordinator, station_id)])


class WundergroundPWSWeather(CoordinatorEntity[WundergroundPWSCoordinator], WeatherEntity):
    """Weather entity for Weather Underground PWS."""

    _attr_has_entity_name = True
    _attr_name = "Current Weather"
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_precipitation_unit = UnitOfLength.MILLIMETERS

    def __init__(
        self, coordinator: WundergroundPWSCoordinator, station_id: str
    ) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._station_id = station_id
        self._attr_unique_id = f"{station_id}_weather"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=f"Weather Underground PWS {station_id}",
            manufacturer="Weather Underground",
            model="Personal Weather Station",
            configuration_url=f"https://www.wunderground.com/dashboard/pws/{station_id}",
        )

    @property
    def _obs(self) -> dict:
        """Return raw observation data."""
        return self.coordinator.data or {}

    @property
    def _metric(self) -> dict:
        """Return metric sub-object."""
        return self._obs.get("metric", {}) or {}

    @property
    def condition(self) -> str | None:
        """Return the current weather condition."""
        if not self._obs:
            return None
        return _condition_from_data(self._obs)

    @property
    def native_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._metric.get("temp")

    @property
    def humidity(self) -> float | None:
        """Return the current humidity."""
        return self._obs.get("humidity")

    @property
    def native_wind_speed(self) -> float | None:
        """Return the current wind speed."""
        return self._metric.get("windSpeed")

    @property
    def wind_bearing(self) -> float | None:
        """Return the current wind direction."""
        return self._obs.get("winddir")

    @property
    def native_pressure(self) -> float | None:
        """Return the current pressure."""
        return self._metric.get("pressure")

    @property
    def native_dew_point(self) -> float | None:
        """Return the current dew point."""
        return self._metric.get("dewpt")

    @property
    def uv_index(self) -> float | None:
        """Return UV index."""
        return self._obs.get("uv")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        return {
            "station_id": self._station_id,
            "obs_time_utc": self._obs.get("obsTimeUtc"),
            "wind_gust": self._metric.get("windGust"),
            "precip_rate": self._metric.get("precipRate"),
            "precip_total": self._metric.get("precipTotal"),
            "solar_radiation": self._obs.get("solarRadiation"),
            "heat_index": self._metric.get("heatIndex"),
            "wind_chill": self._metric.get("windChill"),
        }
