import pandas as pd
import numpy as np
import features
from config import DATA_PATH

def load_and_split_data():
    
    df = pd.read_csv(DATA_PATH)
    df = features.add_features(df)
    df["specific_energy"]=df["energy_mwh"]/df["capacity_mw"]
    unique_dates = df["date"].unique()
    rng = np.random.default_rng(seed=42)
    rng.shuffle(unique_dates)

    n_days = len(unique_dates)

    train_dates = unique_dates[:int(0.7 * n_days)]
    val_dates   = unique_dates[int(0.7 * n_days):int(0.85 * n_days)]
    test_dates  = unique_dates[int(0.85 * n_days):]

    train_df = df[df["date"].isin(train_dates)]
    val_df   = df[df["date"].isin(val_dates)]
    test_df  = df[df["date"].isin(test_dates)]

    return train_df, val_df, test_df
