"""
Central data loader. Loads all CSVs and synthetic files once at startup.
Returns a typed DataStore dataclass used throughout the application.
Generates synthetic files if they don't exist yet.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
SYNTHETIC_DIR = Path(os.getenv("SYNTHETIC_DIR", "synthetic"))


@dataclass
class DataStore:
    reps: pd.DataFrame
    retailers: pd.DataFrame
    growers: pd.DataFrame
    inventory: pd.DataFrame
    pos: pd.DataFrame
    visit_log: pd.DataFrame
    whatsapp: pd.DataFrame
    funnel: pd.DataFrame
    weather: pd.DataFrame
    ndvi: pd.DataFrame
    pest: pd.DataFrame
    priority_scores: pd.DataFrame  # filled after scoring


def _ensure_synthetic():
    """Generate synthetic files if missing."""
    SYNTHETIC_DIR.mkdir(exist_ok=True)
    ndvi_path = SYNTHETIC_DIR / "ndvi_weekly.csv"
    pest_path = SYNTHETIC_DIR / "pest_bulletin_weekly.csv"
    if not ndvi_path.exists():
        from src.ndvi_generator import generate_ndvi
        generate_ndvi(str(DATA_DIR / "weather_by_district.csv"), str(ndvi_path))
    if not pest_path.exists():
        from src.pest_generator import generate_pest
        generate_pest(str(DATA_DIR / "weather_by_district.csv"), str(pest_path))


def load_all() -> DataStore:
    """Load every dataset into memory. Call once at app startup."""
    _ensure_synthetic()

    reps = pd.read_csv(DATA_DIR / "reps_territory.csv")
    retailers = pd.read_csv(DATA_DIR / "retailers.csv")
    growers = pd.read_csv(DATA_DIR / "growers.csv")

    # Parse crop from JSON calendar
    def _crop(cal):
        try:
            return json.loads(cal)["crop"]
        except Exception:
            return "unknown"

    growers["crop"] = growers["grower_crop_calendar"].apply(_crop)

    # Parse growth stages
    def _stage(cal):
        try:
            stages = json.loads(cal).get("stages", [])
            return stages[-1]["stage"] if stages else "unknown"
        except Exception:
            return "unknown"

    growers["current_stage"] = growers["grower_crop_calendar"].apply(_stage)

    inventory = pd.read_csv(DATA_DIR / "retailer_inventory_weekly.csv")
    inventory["week_end_date"] = pd.to_datetime(inventory["week_end_date"])

    pos = pd.read_csv(DATA_DIR / "retailer_pos.csv")
    pos["transaction_date"] = pd.to_datetime(pos["transaction_date"])

    visit_log = pd.read_csv(DATA_DIR / "retailer_visit_log.csv")
    visit_log["visit_date"] = pd.to_datetime(visit_log["visit_date"])

    whatsapp = pd.read_csv(DATA_DIR / "whatsapp_campaign.csv")
    funnel = pd.read_csv(DATA_DIR / "digital_funnel_weekly.csv")

    weather = pd.read_csv(DATA_DIR / "weather_by_district.csv")
    weather["date"] = pd.to_datetime(weather["date"], format="%Y%m%d")

    ndvi = pd.read_csv(SYNTHETIC_DIR / "ndvi_weekly.csv")
    ndvi["week_end_date"] = pd.to_datetime(ndvi["week_end_date"])

    pest = pd.read_csv(SYNTHETIC_DIR / "pest_bulletin_weekly.csv")
    pest["week_end_date"] = pd.to_datetime(pest["week_end_date"])

    return DataStore(
        reps=reps,
        retailers=retailers,
        growers=growers,
        inventory=inventory,
        pos=pos,
        visit_log=visit_log,
        whatsapp=whatsapp,
        funnel=funnel,
        weather=weather,
        ndvi=ndvi,
        pest=pest,
        priority_scores=pd.DataFrame(),
    )
