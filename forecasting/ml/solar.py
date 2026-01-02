import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retries = Retry(
    total=2,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
session.mount("https://", HTTPAdapter(max_retries=retries))

def fetch_pvgis(lat, lon):
    url = (
        "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc"
        f"?lat={lat}&lon={lon}"
        "&outputformat=json"
        "&angle=30"
        "&aspect=0"
        "&pvcalculation=1"
        "&peakpower=1"
        "&loss=14"
    )

    response = session.get(url, timeout=8)  # ⏱ timeout is CRUCIAL
    response.raise_for_status()
    return response.json()
