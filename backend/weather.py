import httpx
import asyncio
from datetime import datetime, timedelta

# Cache keyed by (lat, lon) tuple
_weather_cache: dict[tuple, dict] = {}
_cache_times: dict[tuple, datetime] = {}

# Default: Sydney CBD
DEFAULT_LAT = -33.8688
DEFAULT_LON = 151.2093


async def get_sydney_weather(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON) -> dict:
    """Fetch 7-day forecast from Open-Meteo for the given coordinates. No API key required."""
    global _weather_cache, _cache_times

    key = (round(lat, 4), round(lon, 4))
    cached_time = _cache_times.get(key)

    # Cache per location for 1 hour
    if cached_time and (datetime.now() - cached_time).seconds < 3600 and key in _weather_cache:
        return _weather_cache[key]

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min,windspeed_10m_max,weathercode",
        "timezone": "Australia/Sydney",
        "forecast_days": 7
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=5)
            data = response.json()
    except Exception:
        return _weather_cache.get(key, {})

    result = {}
    daily = data.get("daily", {})
    dates = daily.get("time", [])

    weathercode_descriptions = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Icy fog", 51: "Light drizzle", 53: "Moderate drizzle",
        55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Heavy thunderstorm"
    }

    for i, date in enumerate(dates):
        rain = daily.get("precipitation_sum", [0] * 7)[i] or 0
        temp_max = daily.get("temperature_2m_max", [20] * 7)[i] or 20
        temp_min = daily.get("temperature_2m_min", [15] * 7)[i] or 15
        wind = daily.get("windspeed_10m_max", [10] * 7)[i] or 10
        wcode = daily.get("weathercode", [0] * 7)[i] or 0

        if rain > 15 or wcode >= 95 or temp_max > 38:
            weather_risk = "high"
        elif rain > 5 or temp_max > 33:
            weather_risk = "medium"
        else:
            weather_risk = "low"

        result[date] = {
            "condition": weathercode_descriptions.get(wcode, f"Code {wcode}"),
            "rain_mm": round(rain, 1),
            "temp_max": round(temp_max, 1),
            "temp_min": round(temp_min, 1),
            "wind_kmh": round(wind, 1),
            "weather_risk": weather_risk
        }

    _weather_cache[key] = result
    _cache_times[key] = datetime.now()
    return result


def get_weather_for_date(weather_map: dict, date_str: str) -> dict:
    """Get weather for a specific date, return safe defaults if not found."""
    return weather_map.get(date_str, {
        "condition": "Unknown",
        "rain_mm": 0,
        "temp_max": 22,
        "temp_min": 15,
        "wind_kmh": 10,
        "weather_risk": "low"
    })
