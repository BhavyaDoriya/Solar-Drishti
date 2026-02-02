from pathlib import Path
INPUT_COLS=['ghi', 'dni','dhi', 'air_temp', 'wind_speed', 'solar_zenith', "day_sin","day_cos",'hour_sin',"hour_cos","month_sin",'month_cos']
TARGET_COL="specific_energy"
ML_PATH=Path(__file__).parent.parent.resolve()
MODEL_PATH=ML_PATH / "models"/"lgb_model.pkl"
BASE_PATH=Path(__file__).parent.parent.parent.parent.resolve()
DATA_PATH=BASE_PATH/"media"/"pv_weather_hourly.csv"