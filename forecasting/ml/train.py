import pandas as pd
import pathlib as path

BASE_DIR=path.Path(__file__).resolve().parent.parent.parent
DATA_PATH=BASE_DIR/"media"/"ProcessedData.csv"
df=pd.read_csv(DATA_PATH)
# Checking out data types of each column and dividing them into categorical and numerical columns

print(df.dtypes)
categorical_cols=["preciptype","stations","icon","conditions"]
numeric_cols = [c for c in df.columns if c not in categorical_cols]

