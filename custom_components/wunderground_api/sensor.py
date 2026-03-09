"""Sensor platform for Weather Underground PWS."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_STATION_ID, DOMAIN, SENSOR_TYPES
from .coordinator import WundergroundPWSCoordinator

_LOGGER = logging.getLogger(__name__)


def _get_value(data: dict, path: list[str]) -> Any:
    """Safely retrieve a nested value from a dict."""
    current = data
    for key in path[1:]:  # skip "observation" prefix
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Weather Underground PWS sensors."""
    coordinator: WundergroundPWSCoordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = entry.data[CONF_STATION_ID]

    async_add_entities([
        WundergroundPWSSensor(coordinator, station_id, key, defn)
        for key, defn in SENSOR_TYPES.items()
    ])


class WundergroundPWSSensor(CoordinatorEntity[WundergroundPWSCoordinator], SensorEntity):
    """A single Weather Underground PWS sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WundergroundPWSCoordinator,
        station_id: str,
        sensor_key: str,
        sensor_def: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._sensor_key = sensor_key
        self._data_path = sensor_def["path"]
        self._station_id = station_id

        self._attr_unique_id = f"{station_id}_{sensor_key}"
        self._attr_name = sensor_def["name"]
        self._attr_native_unit_of_measurement = sensor_def["unit"]
        self._attr_icon = sensor_def["icon"]

        if sensor_def.get("device_class"):
            self._attr_device_class = sensor_def["device_class"]

        if sensor_def.get("state_class"):
            self._attr_state_class = sensor_def["state_class"]

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=f"WU PWS {station_id}",
            manufacturer="Weather Underground",
            model="Personal Weather Station",
            configuration_url=f"https://www.wunderground.com/dashboard/pws/{station_id}",
        )

    @property
    def native_value(self) -> Any:
        """Return the current sensor value."""
        if not self.coordinator.data:
            return None

        # Try metric sub-object first
        metric = self.coordinator.data.get("metric", {}) or {}
        leaf_key = self._data_path[-1]

        if "metric" in self._data_path:
            value = metric.get(leaf_key)
        else:
            value = self.coordinator.data.get(leaf_key)

        if isinstance(value, float):
            return round(value, 2)
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}
        return {
            "station_id": self._station_id,
            "obs_time_utc": self.coordinator.data.get("obsTimeUtc"),
        }
