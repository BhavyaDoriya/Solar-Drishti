import requests
import pandas as pd
import pvlib
from timezonefinder import TimezoneFinder

# Initialize TimezoneFinder once
tf = TimezoneFinder()

def compute_solar_features(df_weather: pd.DataFrame, lat: float, lon: float) -> pd.DataFrame:
    """
    Fetches 3-day solar forecast from Open-Meteo and calculates Solar Zenith locally.
    Returns GHI, DNI, DHI, and solar_zenith aligned with df_weather.
    """
    
    # 1. Get the Timezone String (e.g., "America/Chicago")
    timezone_str = tf.timezone_at(lng=lon, lat=lat)
    if not timezone_str:
        timezone_str = "UTC"

    # 2. Open-Meteo API Call (ONLY for radiation, NO zenith to avoid 400 error)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "shortwave_radiation,direct_normal_irradiance,diffuse_radiation",
        "forecast_days": 5,
        "timezone": timezone_str
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()['hourly']
    except Exception as e:
        print(f"Error fetching solar forecast: {e}")
        return pd.DataFrame()

    # 3. Create DataFrame
    # Convert API time strings to datetime objects
    forecast_df = pd.DataFrame({
        "timestamp": pd.to_datetime(data['time']),
        "ghi": data['shortwave_radiation'],
        "dni": data['direct_normal_irradiance'],
        "dhi": data['diffuse_radiation']
    })

    # 4. Filter to match your Weather Data (Tomorrow/Overmorrow)
    # Ensure both are 'naive' and floored to hour for perfect merging
    df_weather['timestamp'] = pd.to_datetime(df_weather['timestamp']).dt.tz_localize(None).dt.floor('h')
    forecast_df['timestamp'] = forecast_df['timestamp'].dt.tz_localize(None).dt.floor('h')

    # Merge first to get only the rows we need
    final_df = pd.merge(df_weather[['timestamp']], forecast_df, on="timestamp", how="inner")

    # 5. Calculate Solar Zenith LOCALLY (The Fix)
    # We use the final timestamps and the location to calculate the sun's angle
    # This keeps your ML model happy without relying on the API
    location = pvlib.location.Location(latitude=lat, longitude=lon, tz=timezone_str)
    
    # pvlib needs the timestamps to be localized to the specific timezone to calculate zenith correctly
    times_for_zenith = pd.DatetimeIndex(final_df['timestamp']).tz_localize(timezone_str)
    
    # Calculate position
    solar_position = location.get_solarposition(times_for_zenith)
    
    # Assign zenith to the dataframe
    final_df['solar_zenith'] = solar_position['zenith'].values

    return final_df