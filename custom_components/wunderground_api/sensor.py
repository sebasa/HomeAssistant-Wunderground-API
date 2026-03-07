"""Sensor platform for Weather Underground PWS."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
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


def _get_nested(data: dict, path: list[str]) -> Any:
    """Safely retrieve a nested value from a dict using a list of keys."""
    for key in path:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Weather Underground PWS sensors."""
    coordinator: WundergroundPWSCoordinator = hass.data[DOMAIN][entry.entry_id]
    station_id = entry.data[CONF_STATION_ID]

    entities = [
        WundergroundPWSSensor(coordinator, station_id, sensor_key, sensor_def)
        for sensor_key, sensor_def in SENSOR_TYPES.items()
    ]

    async_add_entities(entities)


class WundergroundPWSSensor(CoordinatorEntity[WundergroundPWSCoordinator], SensorEntity):
    """Representation of a Weather Underground PWS sensor."""

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

        if sensor_def["device_class"]:
            self._attr_device_class = sensor_def["device_class"]

        if sensor_def["state_class"]:
            self._attr_state_class = sensor_def["state_class"]

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=f"Weather Underground PWS {station_id}",
            manufacturer="Weather Underground",
            model="Personal Weather Station",
            configuration_url=f"https://www.wunderground.com/dashboard/pws/{station_id}",
        )

    @property
    def native_value(self) -> Any:
        """Return the current sensor value."""
        if self.coordinator.data is None:
            return None

        value = _get_nested(self.coordinator.data, self._data_path[1:])  # skip "observation"

        if value is None:
            # Try from root (non-metric fields like humidity, winddir, uv, solarRadiation)
            root_key = self._data_path[-1]
            value = self.coordinator.data.get(root_key)

        if isinstance(value, float):
            return round(value, 2)
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if self.coordinator.data is None:
            return {}
        return {
            "station_id": self._station_id,
            "obs_time_utc": self.coordinator.data.get("obsTimeUtc"),
            "software_type": self.coordinator.data.get("softwareType"),
        }
