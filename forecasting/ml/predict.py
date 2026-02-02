# ml/predict.py

import joblib
import pandas as pd

from .weather import get_hourly_forecast
from .solar import compute_solar_features
from .py_files.features import add_features
from .py_files.config import INPUT_COLS, MODEL_PATH


def predict_next_48h(
    lat: float,
    lon: float
) -> pd.DataFrame:
    """
    Predict hourly and daily solar energy for next 48 hours.
    """

    # 1️⃣ Fetch weather
    weather_df = get_hourly_forecast(lat, lon, hours=48)

    # 2️⃣ Compute solar features
    solar_df = compute_solar_features(weather_df, lat, lon)
    # 3️⃣ Merge (timezone-safe)
    weather_df["timestamp"] = pd.to_datetime(weather_df["timestamp"]).dt.floor("H")
    solar_df["timestamp"] = pd.to_datetime(solar_df["timestamp"]).dt.floor("H")

    df = weather_df.merge(solar_df, on="timestamp", how="inner")


    # 3️⃣ Merge
    # df = weather_df.merge(solar_df, on="timestamp")
    print("weather_df:", weather_df.shape)
    print("solar_df:", solar_df.shape)
    print("merged df:", df.shape)
    print("columns:", df.columns.tolist())

    # 4️⃣ Feature engineering (sin/cos etc.)
    df = add_features(df)

    # 5️⃣ Load trained model
    model = joblib.load(MODEL_PATH)

    # 6️⃣ Predict hourly specific energy
    df["predicted_specific_energy"] = model.predict(df[INPUT_COLS])

    # 7️⃣ Daily aggregation (for UI)
    df["date"] = df["timestamp"].dt.date

    daily_df = (
        df.groupby("date")["predicted_specific_energy"]
        .sum()
        .reset_index(name="daily_energy")
    )

    return df, daily_df
