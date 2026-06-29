"""
weather.py
-----------
Fetches free, real-time hourly weather forecast data from Open-Meteo
for a given farm location (latitude, longitude).

No API key needed. No cost. No sign-up.

This is the FOUNDATION script — every other part of the farm AI agent
(spray decision, irrigation decision, etc.) will use the data this
script returns.
"""

import requests


def get_forecast(latitude: float, longitude: float, hours: int = 24) -> dict:
    """
    Fetch hourly weather forecast for a specific location.

    Args:
        latitude: Farm's latitude (e.g. 5.4141 for Penang)
        longitude: Farm's longitude (e.g. 100.3288 for Penang)
        hours: How many hours ahead to fetch (default 24)

    Returns:
        A dictionary with hourly lists: time, rain (mm), 
        precipitation_probability (%), temperature (C), 
        relative_humidity (%), wind_speed (km/h)
    """
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "precipitation",
            "wind_speed_10m",
        ],
        "timezone": "Asia/Kuala_Lumpur",
        "forecast_days": 2,  # gives us today + tomorrow, plenty for 24-48h logic
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()  # will raise an error if the request failed
    data = response.json()

    hourly = data["hourly"]

    # Trim to just the next `hours` hours from now
    # Open-Meteo gives us a full list starting from hour 0 of today,
    # so we find "now" and slice from there.
    from datetime import datetime

    now = datetime.now()
    times = hourly["time"]

    # Find the index of the closest hour to "now"
    start_index = 0
    for i, t in enumerate(times):
        hour_time = datetime.fromisoformat(t)
        if hour_time >= now:
            start_index = i
            break

    end_index = start_index + hours

    forecast = {
        "time": times[start_index:end_index],
        "temperature_c": hourly["temperature_2m"][start_index:end_index],
        "humidity_pct": hourly["relative_humidity_2m"][start_index:end_index],
        "rain_chance_pct": hourly["precipitation_probability"][start_index:end_index],
        "rain_mm": hourly["precipitation"][start_index:end_index],
        "wind_speed_kmh": hourly["wind_speed_10m"][start_index:end_index],
    }

    return forecast


def print_forecast_summary(forecast: dict) -> None:
    """Pretty-print the forecast so you can sanity-check the data."""
    print(f"{'Time':<20}{'Temp(C)':<10}{'Humidity%':<12}{'RainChance%':<14}{'RainMM':<10}{'Wind(km/h)':<12}")
    print("-" * 78)
    for i in range(len(forecast["time"])):
        print(
            f"{forecast['time'][i]:<20}"
            f"{forecast['temperature_c'][i]:<10}"
            f"{forecast['humidity_pct'][i]:<12}"
            f"{forecast['rain_chance_pct'][i]:<14}"
            f"{forecast['rain_mm'][i]:<10}"
            f"{forecast['wind_speed_kmh'][i]:<12}"
        )


if __name__ == "__main__":
    # Default coordinates: Penang, Malaysia
    # Replace these with your exact farm coordinates later.
    PENANG_LAT = 5.4141
    PENANG_LON = 100.3288

    print("Fetching weather forecast for Penang, Malaysia...\n")
    forecast = get_forecast(PENANG_LAT, PENANG_LON, hours=24)
    print_forecast_summary(forecast)
