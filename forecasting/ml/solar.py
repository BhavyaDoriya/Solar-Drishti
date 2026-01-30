# ml/solar.py

import pandas as pd
import pvlib

IST_OFFSET = pd.Timedelta(hours=5, minutes=30)


def compute_solar_features(df_weather: pd.DataFrame, lat: float, lon: float) -> pd.DataFrame:
    """
    Input timestamp: LST (tz-aware or naive, handled safely)
    Output timestamp: LST
    pvlib computation: UTC DatetimeIndex ONLY
    """

    # ---------- STEP 1: Force clean DatetimeIndex in LST ----------
    ts = pd.to_datetime(df_weather["timestamp"], errors="raise")

    # If tz-naive → localize as UTC then shift
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize("UTC") + IST_OFFSET

    # If tz-aware but not UTC → convert to UTC then shift
    else:
        ts = ts.dt.tz_convert("UTC") + IST_OFFSET

    # ts is now LST (tz-aware)

    # ---------- STEP 2: Convert LST → UTC for pvlib ----------
    ts_utc = (ts - IST_OFFSET).dt.tz_convert("UTC")

    # 🔥 THIS is what pvlib wants
    times_utc = pd.DatetimeIndex(ts_utc.values, tz="UTC")

    # ---------- STEP 3: pvlib solar physics ----------
    location = pvlib.location.Location(latitude=lat, longitude=lon, tz="UTC")

    solar_position = location.get_solarposition(times_utc)
    clearsky = location.get_clearsky(times_utc, model="ineichen")

    cloud_factor = 1.0 - (df_weather["cloud_cover"].values / 100.0)

    solar_df = pd.DataFrame({
        "timestamp": ts,  # LST for ML + UI
        "ghi": clearsky["ghi"].values * cloud_factor,
        "dni": clearsky["dni"].values * cloud_factor,
        "dhi": clearsky["dhi"].values * cloud_factor,
        "solar_zenith": solar_position["zenith"].values
    })

    return solar_df
