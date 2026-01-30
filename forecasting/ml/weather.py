# ml/weather.py

import requests
import pandas as pd
from datetime import timedelta
from decouple import config

OPENWEATHER_API_KEY = config("OPENWEATHER_API_KEY")
IST_OFFSET = pd.Timedelta(hours=5, minutes=30)

OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def get_hourly_forecast(lat: float, lon: float, hours: int = 48) -> pd.DataFrame:
    """
    Fetch OpenWeather forecast and return HOURLY data in LST.
    """

    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }

    resp = requests.get(OPENWEATHER_FORECAST_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    records = []

    for entry in data["list"]:
        # OpenWeather gives UTC
        base_time_utc = pd.to_datetime(entry["dt"], unit="s", utc=True)

        # 🔥 Convert immediately to LST
        base_time_lst = base_time_utc + IST_OFFSET

        air_temp = entry["main"]["temp"]
        wind_speed = entry["wind"]["speed"]
        cloud_cover = entry["clouds"]["all"]

        for h in range(3):
            ts_lst = base_time_lst + timedelta(hours=h)
            records.append({
                "timestamp": ts_lst,   # 🔥 LST timestamp
                "air_temp": air_temp,
                "wind_speed": wind_speed,
                "cloud_cover": cloud_cover
            })

    df = pd.DataFrame(records)

    df = (
        df.sort_values("timestamp")
          .drop_duplicates("timestamp")
          .head(hours)
          .reset_index(drop=True)
    )

    return df
