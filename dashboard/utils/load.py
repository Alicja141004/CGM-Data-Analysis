import pandas as pd
import datetime as dt
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED = BASE_DIR / "data" / "processed"

SECTIONS = {
    "meal": "Meal",
    "bolus": "Insulin_bolus",
    "infusion": "Insulin_infusion",
    "glucose": "Glucose_concentration",
    "fingerstick": "Fingerstick_glucose_concentration",
    "priming": "Priming_event",
    "refill": "Refill_event",
    "sensor_inserted": "Sensor_inserted",
    "sensor_stopped": "Sensor_stopped",
    "audio_alerts": "Audio_alerts",
    "vibrate_alerts": "Vibrate_alerts",
}

def read_csv_safe(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
        if "Time" in df.columns:
            df["Time"] = pd.to_datetime(
                df["Time"],
                format="mixed",
                errors="coerce"
            )
            df = df.dropna(subset=["Time"]).sort_values("Time")
        return df
    except Exception as e:
        st.warning(f"Failed to load {path.name}: {e}")
        return None


@st.cache_data(show_spinner="Loading CGM data...")
def load_all() -> dict[str, pd.DataFrame]:
    data = {}
    for key, fname in SECTIONS.items():
        df = read_csv_safe(DATA_PROCESSED / f"{fname}.csv")
        data[key] = df if df is not None else pd.DataFrame()
    return data


@st.cache_data(show_spinner=False)
def load_glucose() -> pd.DataFrame:
    path = DATA_PROCESSED / "Glucose_concentration.csv"
    g = read_csv_safe(path)
    return g if g is not None else pd.DataFrame()


def get_min_max_date(df: pd.DataFrame) -> tuple[dt.date, dt.date]:
    if df.empty or "Time" not in df.columns:
        today = dt.date.today()
        return today, today
    return df["Time"].min().date(), df["Time"].max().date()
