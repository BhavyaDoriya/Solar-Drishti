import pandas as pd
import numpy as np

def add_features(df):
    # Ensure timestamp is datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["date"]=(pd.to_datetime(df["timestamp"])).dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["day"] = df["timestamp"].dt.day
    df["month"] = df["timestamp"].dt.month

    # Cyclic encodings
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

    df["month_sin"] = np.sin(2 * np.pi * (df["month"] - 1) / 12)
    df["month_cos"] = np.cos(2 * np.pi * (df["month"] - 1) / 12)

    df["day_sin"] = np.sin(2 * np.pi * (df["day"] - 1) / 31)
    df["day_cos"] = np.cos(2 * np.pi * (df["day"] - 1) / 31)

    return df
