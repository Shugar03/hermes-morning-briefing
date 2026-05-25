"""Weather provider: Open-Meteo API (free, no key)."""

import json
import urllib.request
import urllib.parse
from typing import Optional
from . import WeatherProvider, Weather, WeatherForecast, register


GEO = {"lat": -24.78, "lon": -65.41}  # Salta, Argentina

WMO_CODES: dict[int, tuple[str, str]] = {
    0:  ("Despejado", "sun"),
    1:  ("Mayormente despejado", "sun"),
    2:  ("Parcialmente nublado", "cloud-sun"),
    3:  ("Nublado", "cloud"),
    45: ("Niebla", "fog"),
    48: ("Niebla con escarcha", "fog"),
    51: ("Lluvia ligera", "drizzle"),
    53: ("Lluvia moderada", "drizzle"),
    55: ("Lluvia densa", "drizzle"),
    61: ("Lluvia leve", "rain"),
    63: ("Lluvia moderada", "rain"),
    65: ("Lluvia fuerte", "rain"),
    71: ("Nieve ligera", "snow"),
    73: ("Nieve moderada", "snow"),
    75: ("Nieve intensa", "snow"),
    80: ("Chubascos ligeros", "rain"),
    81: ("Chubascos moderados", "rain"),
    82: ("Chubascos violentos", "rain"),
    95: ("Tormenta", "storm"),
    96: ("Tormenta con granizo leve", "storm"),
    99: ("Tormenta con granizo fuerte", "storm"),
}


class OpenMeteoWeather(WeatherProvider):
    def __init__(self, lat: float = GEO["lat"], lon: float = GEO["lon"],
                 city: str = "Salta"):
        self.lat = lat
        self.lon = lon
        self.city = city

    def is_available(self) -> bool:
        return True  # always — no key needed

    def _fetch(self, url: str) -> dict:
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes-MorningBriefing/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())

    def get_forecast(self) -> WeatherForecast:
        params = urllib.parse.urlencode({
            "latitude": self.lat,
            "longitude": self.lon,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "timezone": "America/Argentina/Salta",
            "forecast_days": 2,
        })
        url = f"https://api.open-meteo.com/v1/forecast?{params}"
        data = self._fetch(url)

        curr = data["current"]
        daily = data["daily"]

        def _parse_day(idx: int) -> Weather:
            code = daily["weather_code"][idx]
            condition = WMO_CODES.get(code, ("Desconocido", "cloud"))[0]
            return Weather(
                temp=curr["temperature_2m"] if idx == 0 else (daily["temperature_2m_max"][idx] + daily["temperature_2m_min"][idx]) / 2,
                condition=condition,
                humidity=curr["relative_humidity_2m"] if idx == 0 else 0,
                wind=curr["wind_speed_10m"] if idx == 0 else 0,
                precip_prob=daily["precipitation_probability_max"][idx] if daily["precipitation_probability_max"][idx] else 0,
            )

        return WeatherForecast(
            today=Weather(
                temp=curr["temperature_2m"],
                condition=WMO_CODES.get(curr["weather_code"], ("Desconocido", "cloud"))[0],
                humidity=curr["relative_humidity_2m"],
                wind=curr["wind_speed_10m"],
                precip_prob=daily["precipitation_probability_max"][0] or 0,
            ),
            tomorrow=Weather(
                temp=(daily["temperature_2m_max"][1] + daily["temperature_2m_min"][1]) / 2,
                condition=WMO_CODES.get(daily["weather_code"][1], ("Desconocido", "cloud"))[0],
                humidity=0,
                wind=0,
                precip_prob=daily["precipitation_probability_max"][1] or 0,
            ),
        )


register(OpenMeteoWeather)
