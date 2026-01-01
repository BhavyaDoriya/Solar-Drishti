import joblib
import pandas as pd
from pathlib import Path
from datetime import datetime

from .weather import fetch_weather, dew_point,build_preciptype
from .solar import fetch_pvgis

# --------------------
# Model loading
# --------------------
BASE_PATH = Path(__file__).resolve().parent
MODEL_PATH = BASE_PATH / "models" / "RF_artifact.joblib"

_artifact = joblib.load(MODEL_PATH)

MODEL = _artifact["model"]
INPUT_COLS = _artifact["input_columns"]
TARGET_COL = _artifact["target_column"]


# --------------------
# Public API (used by views.py)
# --------------------
def predict_daily_energy(system, target_date):
    """
    system      -> SolarSystem model instance
    target_date -> date object (tomorrow / overmorrow)

    returns: daily predicted energy (float)
    """

    df = build_daily_block_features(system, target_date)

    if df.empty:
        raise ValueError("No forecast data available for selected date")

    df = df[INPUT_COLS]

    block_predictions = MODEL.predict(df)

    return float(block_predictions.sum())


# --------------------
# Feature builder
# --------------------
def build_daily_block_features(system, target_date):
    weather = fetch_weather(system.latitude, system.longitude)
    solar = fetch_pvgis(system.latitude, system.longitude)

    rows = []

    # ---- filter weather blocks (3-hour blocks) ----
    for w in weather["list"]:
        w_date = datetime.utcfromtimestamp(w["dt"]).date()

        if w_date != target_date:
            continue

        base = {
            "temp": w["main"]["temp"],
            "humidity": w["main"]["humidity"],
            "windspeed": w["wind"]["speed"],
            "winddir": w["wind"].get("deg", 0),
            "cloudcover": w["clouds"]["all"],
            "visibility": w.get("visibility", 10000) / 1000,
            "sealevelpressure": w["main"]["pressure"],
            "precip": w.get("rain", {}).get("3h", 0),
            "snowdepth": w.get("snow", {}).get("3h", 0),
            "uvindex": 0,
        }

        # --- solar aggregation (average over 3 hours) ---
        solar_blocks = [
            s for s in solar["outputs"]["hourly"]
            if datetime.fromisoformat(s["time"]).date() == target_date
        ]

        if solar_blocks:
            base["solarradiation"] = sum(s["G(i)"] for s in solar_blocks) / len(solar_blocks)
            base["solarenergy"] = sum(s["E_pv"] for s in solar_blocks)
        else:
            base["solarradiation"] = 0
            base["solarenergy"] = 0

        base["dew"] = dew_point(base["temp"], base["humidity"])
        base.update(build_preciptype(base))

        rows.append(base)

    return pd.DataFrame(rows)
