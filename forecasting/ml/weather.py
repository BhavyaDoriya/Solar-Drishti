import requests
import math
from decouple import config
OWM_API_KEY =config("OPENWEATHER_API_KEY") 

def dew_point(temp_c, humidity):
    a, b = 17.27, 237.7
    alpha = ((a * temp_c) / (b + temp_c)) + math.log(humidity / 100.0)
    return (b * alpha) / (a - alpha)

def fetch_weather(lat, lon):
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric"
    )
    return requests.get(url).json()
def build_preciptype(row):
    types = {
        "preciptype_None": 0,
        "preciptype_freezingrain": 0,
        "preciptype_rain": 0,
        "preciptype_rain,snow": 0,
        "preciptype_snow": 0,
    }

    if row.get("snowdepth", 0) > 0:
        types["preciptype_snow"] = 1
    elif row.get("precip", 0) > 0:
        types["preciptype_rain"] = 1
    else:
        types["preciptype_None"] = 1

    return types
