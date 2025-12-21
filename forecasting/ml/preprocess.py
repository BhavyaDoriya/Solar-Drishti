from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "media" / "data.xlsx"

df = pd.read_excel(DATA_PATH)
df