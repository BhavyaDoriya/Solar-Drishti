# ml/weather.py
import requests
import pandas as pd
from decouple import config
from timezonefinder import TimezoneFinder  # New library
import pytz

OPENWEATHER_API_KEY = config("OPENWEATHER_API_KEY")
OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Initialize once
tf = TimezoneFinder()

def get_hourly_forecast(lat: float, lon: float, hours: int = 48) -> pd.DataFrame:
    """
    Fetch OpenWeather forecast and return HOURLY data in the LOCATION'S LST.
    """
    # 1. Find the local timezone string (e.g., "America/Chicago")
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if not timezone_str:
        timezone_str = "UTC" # Fallback
    local_tz = pytz.timezone(timezone_str)

    params = {
        "lat": lat, "lon": lon,
        "appid": OPENWEATHER_API_KEY, "units": "metric"
    }

    resp = requests.get(OPENWEATHER_FORECAST_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    records = []
    for entry in data["list"]:
        # 2. Get UTC time
        dt_utc = pd.to_datetime(entry["dt"], unit="s", utc=True)
        
        # 3. Convert to the specific location's time
        dt_local = dt_utc.astimezone(local_tz)
        
        # 4. Remove timezone info so it matches your model's expectation of "Naive LST"
        dt_naive = dt_local.tz_localize(None)

        air_temp = entry["main"]["temp"]
        wind_speed = entry["wind"]["speed"]
        cloud_cover = entry["clouds"]["all"]

        # OpenWeather gives 3-hour steps. We fill the gaps.
        for h in range(3):
            ts_final = dt_naive + pd.Timedelta(hours=h)
            records.append({
                "timestamp": ts_final,
                "air_temp": air_temp,
                "wind_speed": wind_speed,
                "cloud_cover": cloud_cover
            })

    df = pd.DataFrame(records)
    
    # Clean up
    df['timestamp'] = df['timestamp'].dt.floor('h') # Fix the 'H' warning
    df = df.sort_values("timestamp").drop_duplicates("timestamp").head(hours).reset_index(drop=True)

    return df