# HomeAssistant-Wunderground-API

A Home Assistant custom integration that automatically discovers your Weather Underground API key and pulls real-time data from any Weather Station

---

## ¿Cómo funciona?

1. Ingresás tu **Station ID** (ej: `IPUNIL11`) en el flujo de configuración
2. La integración accede a `wunderground.com/dashboard/pws/{STATION_ID}` y extrae el API key del código fuente de la página
3. Usa ese key para consultar la API oficial de observaciones cada 5 minutos
4. Se crean automáticamente todas las entidades en Home Assistant

No necesitás buscar ni ingresar el API key manualmente.

---

## Instalación

**Via HACS:**
1. HACS → Integraciones → ⋮ → Repositorios personalizados
2. Agregar la URL del repo con categoría *Integration*
3. Instalar *Weather Underground PWS* → Reiniciar HA

**Manual:**
1. Copiar `custom_components/wunderground_pws/` a `config/custom_components/`
2. Reiniciar Home Assistant

---

## Configuración

1. **Configuración → Dispositivos y servicios → + Agregar integración**
2. Buscar *Weather Underground PWS*
3. Ingresar el Station ID (ej: `IPUNIL11`)

Listo. El API key se descubre solo y se valida la estación automáticamente.

---

## Entidades creadas

| Sensor | Unidad |
|--------|--------|
| Temperature | °C |
| Humidity | % |
| Dew Point | °C |
| Heat Index | °C |
| Wind Chill | °C |
| Wind Speed | km/h |
| Wind Gust | km/h |
| Wind Direction | ° |
| Pressure | hPa |
| Precipitation Rate | mm/h |
| Precipitation Today | mm |
| Solar Radiation | W/m² |
| UV Index | UV index |
| Elevation | m |

Además se crea una entidad **Weather** compatible con la tarjeta de clima estándar de HA.

---

## Troubleshooting

**"No se encontró el API key"** → Verificá que el Station ID sea correcto y que la estación sea pública en Wunderground.

**Los datos dejan de actualizarse** → El API key puede haber cambiado. Ir a *Dispositivos y servicios → Re-autenticar* para refrescarlo con un clic.

---

## Requisitos

- Home Assistant 2023.1+
