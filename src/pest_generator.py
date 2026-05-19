"""
Generates synthetic weekly pest pressure bulletins per district × crop × pest.

Pest pressure (0–100) is driven by:
- Temperature fit for each pest (species have preferred temp ranges)
- Humidity threshold (fungal pests need high humidity)
- Crop growth-stage vulnerability window
- Random noise
- 2–3 outbreak spikes injected per season per region
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

RABI_WEEKS = pd.date_range("2025-10-12", periods=26, freq="W")

# Crop → list of (pest_name, pest_type, temp_min, temp_max, humidity_threshold,
#                  vulnerability_weeks_start, vulnerability_weeks_end)
# vulnerability_weeks: 0-indexed week numbers when the crop is most susceptible
PEST_MAP = {
    "wheat": [
        ("Yellow Rust",    "fungal",  8,  18, 75, 12, 20),  # Jan-Feb (tillering-flowering)
        ("Wheat Aphid",    "insect",  10, 22, 50,  8, 16),  # Dec-Jan (vegetative-tillering)
        ("Powdery Mildew", "fungal",  15, 22, 70, 14, 20),  # Feb (flowering)
    ],
    "mustard": [
        ("Alternaria Blight", "fungal",  18, 28, 78, 12, 20),  # Jan-Feb (flowering)
        ("Mustard Aphid",     "insect",  12, 22, 50,  8, 18),  # Dec-Feb
        ("White Rust",        "fungal",  10, 18, 80,  6, 16),  # Nov-Dec (vegetative)
    ],
    "chickpea": [
        ("Pod Borer",        "insect",  20, 30, 40, 14, 22),  # Feb-Mar (pod formation)
        ("Fusarium Wilt",    "fungal",  22, 28, 65,  6, 18),  # Nov-Jan (vegetative)
        ("Ascochyta Blight", "fungal",  15, 22, 80,  8, 16),  # Dec (vegetative)
    ],
    "barley": [
        ("Barley Yellow Dwarf", "insect",  10, 20, 55, 10, 18),
        ("Net Blotch",          "fungal",  12, 20, 75, 12, 20),
    ],
    "potato": [
        ("Late Blight",  "fungal",  12, 20, 85, 6, 18),   # Nov-Jan (vegetative-tuber)
        ("Potato Aphid", "insect",  15, 25, 50, 4, 16),   # Oct-Jan
        ("Early Blight", "fungal",  20, 30, 70, 10, 20),  # Dec-Feb
    ],
    "lentil": [
        ("Stemphylium Blight", "fungal",  18, 26, 75, 10, 20),
        ("Pod Borer",          "insect",  20, 28, 40, 14, 22),
    ],
    "safflower": [
        ("Alternaria Leaf Spot", "fungal",  20, 28, 70, 12, 20),
        ("Aphids",               "insect",  15, 25, 50,  8, 18),
    ],
    "cumin": [
        ("Blight",  "fungal",  15, 22, 80, 10, 18),
        ("Aphids",  "insect",  12, 22, 50,  8, 16),
    ],
    "maize": [
        ("Fall Armyworm", "insect",  20, 30, 50,  6, 18),
        ("Leaf Blight",   "fungal",  22, 30, 75, 10, 18),
    ],
}

ALERT_LEVELS = [(30, "low"), (60, "medium"), (80, "high"), (101, "critical")]


def _alert_level(pressure: float) -> str:
    for threshold, label in ALERT_LEVELS:
        if pressure < threshold:
            return label
    return "critical"


def _temp_fit(temp: float, t_min: float, t_max: float) -> float:
    """Score 0–1: how well current temp fits pest's preferred range."""
    if temp < t_min or temp > t_max:
        gap = min(abs(temp - t_min), abs(temp - t_max))
        return max(0.0, 1.0 - gap / 10.0)
    return 1.0


def _humidity_fit(humidity: float, threshold: float) -> float:
    """Score 0–1: humidity vs threshold (sigmoid-like)."""
    if humidity >= threshold:
        return min(1.0, (humidity - threshold) / 20.0 + 0.6)
    return max(0.0, (humidity - (threshold - 20)) / 20.0 * 0.5)


def generate_pest(weather_path: str, output_path: str, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic pest bulletin and save to output_path."""
    rng = np.random.default_rng(seed)
    weather = pd.read_csv(weather_path)
    weather["date"] = pd.to_datetime(weather["date"], format="%Y%m%d")

    # Weekly weather aggregates per district
    weather["week_end"] = weather["date"].dt.to_period("W").apply(lambda p: p.end_time.normalize())
    weekly = (
        weather.groupby(["district", "week_end"])
        .agg(temp_c=("temp_c", "mean"), humidity=("humidity", "mean"), rain_mm=("rain_mm", "mean"))
        .reset_index()
    )

    districts = sorted(weather["district"].unique())

    # Outbreak schedule: randomly pick (district, crop_index, week_start) triples
    num_outbreaks = max(3, len(districts) // 5)
    outbreak_districts = rng.choice(districts, size=num_outbreaks, replace=True)
    outbreak_crops = [rng.choice(list(PEST_MAP.keys())) for _ in range(num_outbreaks)]
    outbreak_starts = rng.integers(8, 18, size=num_outbreaks)

    rows = []
    for district in districts:
        dist_weather = weekly[weekly["district"] == district].copy()
        dist_weather = dist_weather.sort_values("week_end").reset_index(drop=True)

        for crop, pests in PEST_MAP.items():
            for pest_name, pest_type, t_min, t_max, hum_thresh, vuln_start, vuln_end in pests:
                for i, week_end in enumerate(RABI_WEEKS):
                    # Get weather for this week
                    match = dist_weather[dist_weather["week_end"].dt.date == week_end.date()]
                    if match.empty:
                        temp, humidity = 18.0, 65.0
                    else:
                        temp = match["temp_c"].values[0]
                        humidity = match["humidity"].values[0]

                    tf = _temp_fit(temp, t_min, t_max)
                    hf = _humidity_fit(humidity, hum_thresh)

                    # Vulnerability window multiplier
                    vuln = 1.2 if vuln_start <= i <= vuln_end else 0.6

                    base_pressure = tf * hf * vuln * 80.0
                    noise = rng.normal(0, 5)
                    pressure = base_pressure + noise

                    # Inject outbreak spike
                    for od, oc, os_ in zip(outbreak_districts, outbreak_crops, outbreak_starts):
                        if od == district and oc == crop and os_ <= i <= os_ + 2:
                            pressure += rng.uniform(30, 55)

                    pressure = float(np.clip(pressure, 0, 100))
                    rows.append({
                        "district": district,
                        "crop": crop,
                        "pest_name": pest_name,
                        "week_end_date": week_end.date().isoformat(),
                        "pest_pressure": round(pressure, 2),
                        "alert_level": _alert_level(pressure),
                    })

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info("[PEST] Generated %d rows → %s", len(df), output_path)
    return df


if __name__ == "__main__":
    generate_pest(
        weather_path="data/weather_by_district.csv",
        output_path="synthetic/pest_bulletin_weekly.csv",
    )
