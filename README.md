# Weather Underground External API - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration that automatically discovers your Weather Underground API key and pulls real-time data from your Personal Weather Station (PWS).

---

## Features

- ✅ **Automatic API key discovery** — No need to find or enter your API key manually. The integration scrapes it from the Wunderground dashboard.
- 📊 **15 sensor entities** — Temperature, Humidity, Dew Point, Wind Speed, Wind Gust, Wind Direction, Pressure, Precipitation Rate, Precipitation Total, Heat Index, Wind Chill, Elevation, Solar Radiation, UV Index.
- 🌤️ **Weather entity** — A standard HA weather card entity with current conditions.
- 🔄 **Auto-refresh** — Data updates every 5 minutes.
- 🔑 **Re-auth flow** — If the API key changes, HA will prompt you to refresh it with one click.
- 🌍 **Spanish & English UI**

---

## Installation via HACS

1. In HACS, go to **Integrations → ⋮ → Custom repositories**
2. Add `https://github.com/sebasa/HomeAssistant-Wunderground-API` with category **Dashboard**
3. Search for **Weather Underground API** and install
4. Restart Home Assistant

### Manual Installation

Copy the `custom_components/wunderground_pws` folder into your HA `config/custom_components/` directory, then restart.

---

## Configuration

1. Go to **Settings → Devices & Services → + Add Integration**
2. Search for **Weather Underground API**
3. Enter your station ID (e.g. `IPUNIL11`)
4. The integration will automatically find the API key and validate your station

> **Where do I find my Station ID?**  
> Visit `https://www.wunderground.com/dashboard/pws/YOURSTATION` — the station ID is the part after `/pws/`.

---

## Sensors Created

| Sensor | Unit | Device Class |
|--------|------|-------------|
| Temperature | °C | temperature |
| Humidity | % | humidity |
| Dew Point | °C | temperature |
| Heat Index | °C | temperature |
| Wind Chill | °C | temperature |
| Wind Speed | km/h | wind_speed |
| Wind Gust | km/h | wind_speed |
| Wind Direction | ° | — |
| Pressure | hPa | pressure |
| Precipitation Rate | mm/h | precipitation_intensity |
| Precipitation Today | mm | precipitation |
| Elevation | m | — |
| Solar Radiation | W/m² | irradiance |
| UV Index | UV index | — |

---

## Troubleshooting

**"Could not find API key"**  
The integration scrapes the API key from your Wunderground dashboard page. If this fails:
- Make sure your station ID is correct and public
- Wunderground may have changed their page structure — please open an issue

**Data not updating**  
Check the HA logs for errors from `custom_components.wunderground_pws`. The API key may have expired — go to **Settings → Devices & Services**, find the integration, and click **Re-authenticate**.

---

## License

MIT License
