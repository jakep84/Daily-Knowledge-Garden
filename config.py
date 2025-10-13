from pathlib import Path
import datetime as dt

ROOT = Path(__file__).parent.resolve()
DATA_DIR = ROOT / "data"
IMG_DIRNAME = "images"
PLOTS_DIRNAME = "plots"

RUN_DATE = dt.datetime.utcnow().date()  # daily anchor (UTC)
