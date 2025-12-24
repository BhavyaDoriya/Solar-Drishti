from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "media" / "data.xlsx"

df = pd.read_excel(DATA_PATH)
#checking null values for each column

# print(df.isnull().sum())
# print(df.shape) #13057 rows present


# Null values are present in preciptype,stations and generation columns
# drop null rows that have no station value 
# fill null values in preciptype with "None"

df.fillna({"preciptype": "None"}, inplace=True)
df.dropna(inplace=True)


# print(df.isnull().sum()) #recheck null values      -->No null values present
# print(df.shape)                                    #currently 12485 rows present



# considering maximum power of each station as system size

system_size = df.groupby("stations")["generation"].max()
df["system size"]=df["stations"].map(system_size)

# Converting negative generation values to zero
df["generation"] = df["generation"].clip(lower=0)


# using normalized power=power/system size

df["normalized power"]=df["generation"]/df["system size"]

# exporting processed data to csv file
# df.to_csv(BASE_DIR / "media" / "ProcessedData.csv", index=False)

# final output:predict normalized power using weather data and multiply it with user's system size