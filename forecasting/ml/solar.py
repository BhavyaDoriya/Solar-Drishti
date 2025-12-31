import requests

def fetch_pvgis(lat, lon):
    url = (
        "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc"
        f"?lat={lat}&lon={lon}&outputformat=json"
        "&angle=30&aspect=0&pvcalculation=1&peakpower=1"
        "&loss=14"
    )
    return requests.get(url).json()
