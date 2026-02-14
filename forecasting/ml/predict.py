# ml/predict.py
import joblib
import pandas as pd
from .weather import get_hourly_forecast
from .solar import compute_solar_features
from .py_files.features import add_features
from .py_files.config import INPUT_COLS, MODEL_PATH

def predict_next_48h(lat: float, lon: float) -> pd.DataFrame:
    # 1. Fetch weather (Correct LST for Tulsa/Location)
    weather_df = get_hourly_forecast(lat, lon, hours=96)

    # 2. Compute solar (Correct LST for Tulsa/Location)
    solar_df = compute_solar_features(weather_df, lat, lon)

    # 3. Merge (They are already aligned now)
    df = weather_df.merge(solar_df, on="timestamp", how="inner")

    # Debugging prints
    print(f"Merged Shape: {df.shape}")
    
    if df.empty:
        raise ValueError("Merge result is empty. Check timezone alignment.")

    # 4. Feature Engineering
    df = add_features(df)

    # 5. Predict
    model = joblib.load(MODEL_PATH)
    df["predicted_specific_energy"] = model.predict(df[INPUT_COLS])

    # 6. Daily Aggregation
    df["date"] = df["timestamp"].dt.date
    daily_df = df.groupby("date")["predicted_specific_energy"].sum().reset_index(name="daily_energy")

    return df, daily_df