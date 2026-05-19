"""
Generates synthetic weekly NDVI values for each district × crop combination.

NDVI (Normalized Difference Vegetation Index) ranges 0–1.
Higher = denser/healthier vegetation.
Curve follows agronomic growth stages for each crop over the Rabi season.
Modulated by rainfall from real weather data.
3–5 stress events injected per season (simulate drought/disease).
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# Rabi 2025-26: 26 weekly snapshots, week ending each Sunday
RABI_WEEKS = pd.date_range("2025-10-12", periods=26, freq="W")

# NDVI curve per crop: 26 values matching the 26-week Rabi season.
# Curve shape: pre-sowing → germination → vegetative → peak → senescence → harvest.
NDVI_CURVES = {
    "wheat": [
        0.18, 0.20, 0.22, 0.25,          # Oct: pre-sow / early germination
        0.30, 0.38, 0.48, 0.58,          # Nov: germination → vegetative
        0.64, 0.70, 0.74, 0.76,          # Dec: vegetative → tillering
        0.78, 0.82, 0.84, 0.85,          # Jan: tillering → jointing
        0.83, 0.80, 0.76, 0.70,          # Feb: flowering → grain fill
        0.62, 0.52, 0.42, 0.34,          # Mar: grain fill → maturity
        0.25, 0.20,                       # Apr: harvest
    ],
    "mustard": [
        0.16, 0.19, 0.23, 0.28,          # Oct
        0.35, 0.44, 0.54, 0.62,          # Nov
        0.68, 0.72, 0.76, 0.79,          # Dec
        0.80, 0.82, 0.80, 0.76,          # Jan: peak at flowering
        0.70, 0.62, 0.52, 0.42,          # Feb: pod formation
        0.34, 0.28, 0.22, 0.18,          # Mar: maturity
        0.15, 0.12,                       # Apr: harvest
    ],
    "chickpea": [
        0.15, 0.18, 0.21, 0.26,          # Oct
        0.32, 0.40, 0.50, 0.58,          # Nov
        0.64, 0.68, 0.71, 0.73,          # Dec
        0.74, 0.75, 0.74, 0.72,          # Jan: peak
        0.68, 0.62, 0.54, 0.46,          # Feb: pod formation
        0.38, 0.30, 0.24, 0.19,          # Mar: maturity
        0.15, 0.12,                       # Apr
    ],
    "barley": [
        0.17, 0.20, 0.24, 0.28,          # Oct
        0.34, 0.42, 0.52, 0.60,          # Nov
        0.66, 0.71, 0.75, 0.78,          # Dec
        0.80, 0.82, 0.80, 0.76,          # Jan
        0.70, 0.62, 0.52, 0.42,          # Feb
        0.34, 0.26, 0.20, 0.16,          # Mar: earlier harvest than wheat
        0.13, 0.11,                       # Apr
    ],
    "potato": [
        0.20, 0.24, 0.30, 0.38,          # Oct: potato sown earlier
        0.48, 0.58, 0.66, 0.72,          # Nov
        0.76, 0.78, 0.80, 0.80,          # Dec: peak
        0.78, 0.74, 0.68, 0.60,          # Jan: tuber bulking
        0.50, 0.40, 0.32, 0.25,          # Feb: maturity
        0.20, 0.16, 0.13, 0.11,          # Mar: harvest
        0.10, 0.10,                       # Apr
    ],
    "lentil": [
        0.15, 0.18, 0.22, 0.27,
        0.33, 0.41, 0.50, 0.57,
        0.62, 0.66, 0.69, 0.71,
        0.72, 0.72, 0.70, 0.67,
        0.62, 0.55, 0.47, 0.39,
        0.31, 0.25, 0.19, 0.15,
        0.13, 0.11,
    ],
    "safflower": [
        0.14, 0.17, 0.21, 0.26,
        0.32, 0.39, 0.47, 0.54,
        0.59, 0.63, 0.67, 0.70,
        0.72, 0.73, 0.72, 0.70,
        0.66, 0.60, 0.52, 0.44,
        0.36, 0.28, 0.22, 0.17,
        0.13, 0.11,
    ],
    "cumin": [
        0.13, 0.16, 0.20, 0.25,
        0.31, 0.38, 0.46, 0.52,
        0.56, 0.59, 0.61, 0.62,
        0.62, 0.61, 0.58, 0.54,
        0.48, 0.40, 0.33, 0.27,
        0.21, 0.16, 0.13, 0.11,
        0.10, 0.10,
    ],
    "maize": [
        0.22, 0.26, 0.31, 0.38,
        0.46, 0.55, 0.63, 0.70,
        0.75, 0.78, 0.79, 0.79,
        0.77, 0.73, 0.67, 0.59,
        0.50, 0.41, 0.33, 0.26,
        0.20, 0.16, 0.13, 0.11,
        0.10, 0.10,
    ],
}



def generate_ndvi(weather_path: str, output_path: str, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic NDVI weekly values and save to output_path.

    Returns the generated DataFrame.
    """
    rng = np.random.default_rng(seed)
    weather = pd.read_csv(weather_path)
    weather["date"] = pd.to_datetime(weather["date"], format="%Y%m%d")

    districts = sorted(weather["district"].unique())
    crops = list(NDVI_CURVES.keys())

    # Aggregate weekly rainfall per district
    weather["week_end"] = weather["date"].dt.to_period("W").apply(lambda p: p.end_time.normalize())
    weekly_rain = (
        weather.groupby(["district", "week_end"])["rain_mm"]
        .mean()
        .reset_index()
    )

    rows = []
    # Choose up to 5 districts for a 2-week NDVI stress event injection
    stress_districts = rng.choice(districts, size=min(5, len(districts)), replace=False)

    for district in districts:
        for crop in crops:
            base_curve = np.array(NDVI_CURVES[crop], dtype=float)

            for i, week_end in enumerate(RABI_WEEKS):
                ndvi = base_curve[i]

                # Rainfall modulation: +0.03 to +0.08 when rain_mm > 5
                rain_row = weekly_rain[
                    (weekly_rain["district"] == district) &
                    (weekly_rain["week_end"].dt.date == week_end.date())
                ]
                if not rain_row.empty:
                    rain = rain_row["rain_mm"].values[0]
                    if rain > 5:
                        ndvi += rng.uniform(0.03, 0.08)
                    elif rain > 2:
                        ndvi += rng.uniform(0.01, 0.03)

                # Gaussian noise
                ndvi += rng.normal(0, 0.015)

                # Stress event: one 2-week NDVI drop window per stressed district
                if district in stress_districts and 10 <= i <= 18:
                    stress_week = int(rng.integers(10, 16))
                    if i in (stress_week, stress_week + 1):
                        ndvi *= rng.uniform(0.75, 0.85)

                ndvi = float(np.clip(ndvi, 0.05, 0.95))
                rows.append({
                    "district": district,
                    "crop": crop,
                    "week_end_date": week_end.date().isoformat(),
                    "ndvi_value": round(ndvi, 4),
                })

    df = pd.DataFrame(rows)

    # Compute ndvi_delta (week-on-week change per district+crop)
    df = df.sort_values(["district", "crop", "week_end_date"]).reset_index(drop=True)
    df["ndvi_delta"] = (
        df.groupby(["district", "crop"])["ndvi_value"]
        .diff()
        .fillna(0)
        .round(4)
    )

    df.to_csv(output_path, index=False)
    logger.info("[NDVI] Generated %d rows → %s", len(df), output_path)
    return df


if __name__ == "__main__":
    generate_ndvi(
        weather_path="data/weather_by_district.csv",
        output_path="synthetic/ndvi_weekly.csv",
    )
