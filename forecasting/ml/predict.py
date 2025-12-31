import os
import joblib
import pandas as pd
from django.conf import settings
from pathlib import Path
BASE_PATH=Path(__file__).resolve().parent
MODEL_PATH=BASE_PATH/"models"/"RF_artifact.joblib"
print(MODEL_PATH)
# 🔥 Load once at Django startup
_artifact = joblib.load(MODEL_PATH)

MODEL = _artifact["model"]
INPUT_COLS = _artifact["input_columns"]
TARGET_COL = _artifact["target_column"]

def predict_from_dict(input_data: dict):
    """
    input_data → dict with feature_name: value
    """
    df = pd.DataFrame([input_data])

    # enforce column order
    df = df[INPUT_COLS]

    prediction = MODEL.predict(df)[0]

    return float(prediction)
