"""Constants for the Weather Underground PWS integration."""

DOMAIN = "wunderground_pws"
PLATFORMS = ["sensor", "weather"]

# Configuration
CONF_STATION_ID = "station_id"
CONF_API_KEY = "api_key"

# Default values
DEFAULT_SCAN_INTERVAL = 300  # 5 minutes

# Wunderground URLs
WU_DASHBOARD_URL = "https://www.wunderground.com/dashboard/pws/{station_id}"
WU_API_URL = (
    "https://api.weather.com/v2/pws/observations/current"
    "?stationId={station_id}&format=json&units=m&apiKey={api_key}&numericPrecision=decimal"
)

# Sensor definitions: (key, name, unit, device_class, state_class, icon)
SENSOR_TYPES = {
    "temp": {
        "name": "Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer",
        "path": ["observation", "metric", "temp"],
    },
    "humidity": {
        "name": "Humidity",
        "unit": "%",
        "device_class": "humidity",
        "state_class": "measurement",
        "icon": "mdi:water-percent",
        "path": ["observation", "humidity"],
    },
    "dewpt": {
        "name": "Dew Point",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer-water",
        "path": ["observation", "metric", "dewpt"],
    },
    "heatIndex": {
        "name": "Heat Index",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer-plus",
        "path": ["observation", "metric", "heatIndex"],
    },
    "windChill": {
        "name": "Wind Chill",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer-minus",
        "path": ["observation", "metric", "windChill"],
    },
    "windSpeed": {
        "name": "Wind Speed",
        "unit": "km/h",
        "device_class": "wind_speed",
        "state_class": "measurement",
        "icon": "mdi:weather-windy",
        "path": ["observation", "metric", "windSpeed"],
    },
    "windGust": {
        "name": "Wind Gust",
        "unit": "km/h",
        "device_class": "wind_speed",
        "state_class": "measurement",
        "icon": "mdi:weather-windy-variant",
        "path": ["observation", "metric", "windGust"],
    },
    "winddir": {
        "name": "Wind Direction",
        "unit": "°",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:compass",
        "path": ["observation", "winddir"],
    },
    "pressure": {
        "name": "Pressure",
        "unit": "hPa",
        "device_class": "pressure",
        "state_class": "measurement",
        "icon": "mdi:gauge",
        "path": ["observation", "metric", "pressure"],
    },
    "precipRate": {
        "name": "Precipitation Rate",
        "unit": "mm/h",
        "device_class": "precipitation_intensity",
        "state_class": "measurement",
        "icon": "mdi:weather-rainy",
        "path": ["observation", "metric", "precipRate"],
    },
    "precipTotal": {
        "name": "Precipitation Today",
        "unit": "mm",
        "device_class": "precipitation",
        "state_class": "total_increasing",
        "icon": "mdi:weather-pouring",
        "path": ["observation", "metric", "precipTotal"],
    },
    "elev": {
        "name": "Elevation",
        "unit": "m",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:elevation-rise",
        "path": ["observation", "metric", "elev"],
    },
    "solarRadiation": {
        "name": "Solar Radiation",
        "unit": "W/m²",
        "device_class": "irradiance",
        "state_class": "measurement",
        "icon": "mdi:solar-power",
        "path": ["observation", "solarRadiation"],
    },
    "uv": {
        "name": "UV Index",
        "unit": "UV index",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:sun-wireless",
        "path": ["observation", "uv"],
    },
}
