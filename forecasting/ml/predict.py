# ml/predict.py
import joblib
import pandas as pd
from .weather import get_hourly_forecast
from .solar import compute_solar_features
from .py_files.features import add_features
from .py_files.config import INPUT_COLS, MODEL_PATH

def predict_next_48h(lat: float, lon: float) -> pd.DataFrame:
    # 1. Fetch weather 
    weather_df = get_hourly_forecast(lat, lon, hours=96)

    # 2. Compute solar 
    solar_df = compute_solar_features(weather_df, lat, lon)

    # 🛑 FIX 1: Prevent the "Error: 'timestamp'" Crash
    if weather_df.empty or solar_df.empty:
        raise ValueError("Weather or Solar API returned no data. Please try again.")

    # 3. Merge 
    df = weather_df.merge(solar_df, on="timestamp", how="inner")
    
    if df.empty:
        raise ValueError("Merge result is empty. Check timezone alignment.")

    # 4. Feature Engineering
    df = add_features(df)

    # 5. Predict
    model = joblib.load(MODEL_PATH)
    df["predicted_specific_energy"] = model.predict(df[INPUT_COLS])

    # 6. Daily Aggregation for Energy (Needs all 24 hours to sum correctly)
    df["date"] = df["timestamp"].dt.date
    energy_df = df.groupby("date")["predicted_specific_energy"].sum().reset_index(name="daily_energy")

    # 🛑 FIX 2: UI Factors Aggregation
    # Filter for ONLY hours where the sun is up (GHI > 0)
    daylight_df = df[df["ghi"] > 0]
    
    # Calculate factors that humans understand (Daytime averages and High temps)
    factors_df = daylight_df.groupby("date").agg({
        "ghi": "mean",         # Average radiation *while the sun is shining*
        "air_temp": "mean",    
        "wind_speed": "mean"   # Average wind speed during the day
    }).reset_index()

    # Combine the accurate energy sum with the daytime factors
    daily_df = energy_df.merge(factors_df, on="date", how="left")
    
    # Fallback to 0 if a day mathematically had zero daylight (e.g., polar nights)
    daily_df = daily_df.fillna(0)

    return df, daily_df