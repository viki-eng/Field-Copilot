# Syngenta Field Co-pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Groq-powered field operations AI co-pilot that tells each Syngenta rep who to visit today, in what order, and what to recommend at point of visit.

**Architecture:** Synthetic NDVI + pest data enriches a priority scoring engine; a greedy route optimizer sequences visits; Groq llama-3.3-70b generates natural-language next-best-action advice per visit; a FastAPI backend serves all data; Streamlit provides the rep-facing dashboard.

**Tech Stack:** Python 3.10+, FastAPI, Groq SDK, Pandas, NumPy, scikit-learn, SQLite, Streamlit, Uvicorn

---

## File Map

| File | Responsibility |
|------|---------------|
| `src/ndvi_generator.py` | Generate synthetic weekly NDVI by district×crop |
| `src/pest_generator.py` | Generate synthetic weekly pest pressure by district×crop |
| `src/data_loader.py` | Load + cache all datasets (CSVs + synthetic) into memory |
| `src/scoring_engine.py` | Priority score every retailer + farmer (v2, uses NDVI + pest bulletin) |
| `src/route_optimizer.py` | Order visits greedily by tehsil cluster |
| `src/anomaly_detector.py` | Flag demand spikes, stockouts, NDVI crashes, pest outbreaks |
| `src/nba_engine.py` | Build context packet + call Groq + return structured NBA advice |
| `src/outcome_logger.py` | SQLite CRUD for visit outcomes |
| `api/models.py` | All Pydantic request/response schemas |
| `api/main.py` | FastAPI app, lifespan startup, router registration |
| `api/routers/daily_plan.py` | `GET /api/rep/{rep_id}/daily-plan` |
| `api/routers/nba.py` | `GET /api/visit/{entity_id}/nba` |
| `api/routers/alerts.py` | `GET /api/alerts` |
| `api/routers/outcomes.py` | `POST /api/visit/outcome` |
| `api/routers/analytics.py` | `GET /api/analytics/territory/{territory_id}` + `GET /api/entity/{entity_id}` |
| `dashboard/app.py` | Streamlit rep-facing UI |
| `requirements.txt` | All dependencies |
| `synthetic/ndvi_weekly.csv` | Generated output (gitignored, created at startup) |
| `synthetic/pest_bulletin_weekly.csv` | Generated output (gitignored, created at startup) |

---

## Task 1: Environment Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`

- [ ] **Step 1: Write requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
groq==0.11.0
pandas==2.2.3
numpy==1.26.4
scikit-learn==1.5.2
streamlit==1.38.0
python-dotenv==1.0.1
httpx==0.27.2
pydantic==2.9.0
```

- [ ] **Step 2: Write .env.example**

```
GROQ_API_KEY=your_groq_api_key_here
DATA_DIR=./data
SYNTHETIC_DIR=./synthetic
DB_PATH=./outcomes.db
```

- [ ] **Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 4: Create .env from example and add your Groq key**

```bash
cp .env.example .env
# Edit .env and add your actual GROQ_API_KEY from console.groq.com
```

- [ ] **Step 5: Verify Groq key works**

```bash
python3 -c "
from groq import Groq
import os; from dotenv import load_dotenv; load_dotenv()
client = Groq(api_key=os.environ['GROQ_API_KEY'])
r = client.chat.completions.create(model='llama-3.3-70b-versatile',
    messages=[{'role':'user','content':'Say hello in one word'}])
print(r.choices[0].message.content)
"
```

Expected: Prints "Hello" or similar.

- [ ] **Step 6: Create synthetic output directory**

```bash
mkdir -p synthetic
```

---

## Task 2: Synthetic NDVI Generator

**Files:**
- Create: `src/__init__.py` (empty)
- Create: `src/ndvi_generator.py`

- [ ] **Step 1: Create src/__init__.py**

```python
```
(empty file)

- [ ] **Step 2: Write src/ndvi_generator.py**

```python
"""
Generates synthetic weekly NDVI values for each district × crop combination.

NDVI (Normalized Difference Vegetation Index) ranges 0–1.
Higher = denser/healthier vegetation.
Curve follows agronomic growth stages for each crop over the Rabi season.
Modulated by rainfall from real weather data.
3–5 stress events injected per season (simulate drought/disease).
"""

import pandas as pd
import numpy as np
from pathlib import Path


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

# Default curve for any crop not listed
_DEFAULT_CURVE = [
    0.16, 0.20, 0.25, 0.31, 0.38, 0.46, 0.54, 0.61,
    0.66, 0.70, 0.73, 0.75, 0.75, 0.74, 0.71, 0.67,
    0.61, 0.54, 0.46, 0.38, 0.30, 0.24, 0.18, 0.14,
    0.12, 0.10,
]


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
    # Choose 4 districts for stress event injection
    stress_districts = rng.choice(districts, size=min(5, len(districts)), replace=False)

    for district in districts:
        for crop in crops:
            base_curve = np.array(NDVI_CURVES.get(crop, _DEFAULT_CURVE), dtype=float)

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

                # Stress event: one 2-week window per stressed district, crops 3-4
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
    print(f"[NDVI] Generated {len(df)} rows → {output_path}")
    return df


if __name__ == "__main__":
    generate_ndvi(
        weather_path="data/weather_by_district.csv",
        output_path="synthetic/ndvi_weekly.csv",
    )
```

- [ ] **Step 3: Run the generator and verify output**

```bash
python3 src/ndvi_generator.py
```

Expected output: `[NDVI] Generated NNNN rows → synthetic/ndvi_weekly.csv`

```bash
python3 -c "
import pandas as pd
df = pd.read_csv('synthetic/ndvi_weekly.csv')
print(df.shape)
print(df.head())
print('NDVI range:', df['ndvi_value'].min(), '-', df['ndvi_value'].max())
print('Null check:', df.isnull().sum().sum())
"
```

Expected: shape ~ (33 districts × 9 crops × 26 weeks = 7722 rows), ndvi_value between 0.05–0.95, zero nulls.

- [ ] **Step 4: Commit**

```bash
git add src/__init__.py src/ndvi_generator.py synthetic/
git commit -m "feat: add synthetic NDVI weekly generator"
```

---

## Task 3: Synthetic Pest Bulletin Generator

**Files:**
- Create: `src/pest_generator.py`

- [ ] **Step 1: Write src/pest_generator.py**

```python
"""
Generates synthetic weekly pest pressure bulletins per district × crop × pest.

Pest pressure (0–100) is driven by:
- Temperature fit for each pest (species have preferred temp ranges)
- Humidity threshold (fungal pests need high humidity)
- Crop growth-stage vulnerability window
- Random noise
- 2–3 outbreak spikes injected per season per region
"""

import pandas as pd
import numpy as np
from pathlib import Path


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
    print(f"[PEST] Generated {len(df)} rows → {output_path}")
    return df


if __name__ == "__main__":
    generate_pest(
        weather_path="data/weather_by_district.csv",
        output_path="synthetic/pest_bulletin_weekly.csv",
    )
```

- [ ] **Step 2: Run and verify**

```bash
python3 src/pest_generator.py
```

```bash
python3 -c "
import pandas as pd
df = pd.read_csv('synthetic/pest_bulletin_weekly.csv')
print(df.shape)
print(df.head())
print('Pressure range:', df['pest_pressure'].min(), '-', df['pest_pressure'].max())
print('Alert levels:', df['alert_level'].value_counts().to_dict())
print('Critical rows:', (df['alert_level']=='critical').sum())
"
```

Expected: ~50k+ rows, pressure 0–100, some "critical" rows (outbreak events), zero nulls.

- [ ] **Step 3: Commit**

```bash
git add src/pest_generator.py synthetic/
git commit -m "feat: add synthetic pest bulletin weekly generator"
```

---

## Task 4: Data Loader

**Files:**
- Create: `src/data_loader.py`

- [ ] **Step 1: Write src/data_loader.py**

```python
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
```

- [ ] **Step 2: Smoke-test the loader**

```bash
python3 -c "
from src.data_loader import load_all
ds = load_all()
print('reps:', len(ds.reps))
print('retailers:', len(ds.retailers))
print('growers:', len(ds.growers))
print('ndvi rows:', len(ds.ndvi))
print('pest rows:', len(ds.pest))
print('All good!')
"
```

Expected: All counts printed without errors. ndvi ~7722 rows, pest ~50k+ rows.

- [ ] **Step 3: Commit**

```bash
git add src/data_loader.py
git commit -m "feat: add centralized data loader with auto-synthetic generation"
```

---

## Task 5: Scoring Engine v2

**Files:**
- Create: `src/scoring_engine.py`

This is an enhanced version of `script.py` that adds NDVI and real pest bulletin signals.

- [ ] **Step 1: Write src/scoring_engine.py**

```python
"""
Priority scoring engine v2.

Scores every retailer and farmer on a 0–100 scale.
Retailers: weather + pest + inventory + purchase history + visit recency + competitive
Farmers: weather + pest + growth stage + NDVI level + NDVI delta
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from src.data_loader import DataStore


GROWTH_SCORE_MAP = {
    "seedling": 35, "vegetative": 55, "tillering": 70,
    "flowering": 95, "fruiting": 85, "pod_formation": 75,
    "maturity": 40, "harvest": 20, "unknown": 30,
}


def _norm(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - mn) / (mx - mn)


def compute_scores(ds: DataStore, as_of_date: str = None) -> pd.DataFrame:
    """
    Compute priority scores for all entities.
    as_of_date: ISO date string (YYYY-MM-DD). Defaults to latest data date.
    Returns DataFrame with columns:
        id, entity_type, district, territory_id,
        weather_score, pest_score, inventory_score, purchase_history_score,
        visit_recency_score, competitive_score,
        ndvi_score, ndvi_delta_score, growth_score,
        raw_priority_score, final_priority_score
    """
    import pandas as pd

    cutoff = pd.Timestamp(as_of_date) if as_of_date else ds.visit_log["visit_date"].max()

    # ── Build master entity table ──────────────────────────────────────
    farmers_tbl = ds.growers[["grower_id", "district", "crop", "current_stage"]].copy()
    farmers_tbl.columns = ["id", "district", "crop", "current_stage"]
    farmers_tbl["entity_type"] = "farmer"
    farmers_tbl["territory_id"] = np.nan

    retailers_tbl = ds.retailers[["retailer_id", "district", "territory_id"]].copy()
    retailers_tbl.columns = ["id", "district", "territory_id"]
    retailers_tbl["entity_type"] = "retailer"
    retailers_tbl["crop"] = np.nan
    retailers_tbl["current_stage"] = np.nan

    table = pd.concat([farmers_tbl, retailers_tbl], ignore_index=True)

    # ── Weather score ─────────────────────────────────────────────────
    recent_weather = (
        ds.weather[ds.weather["date"] <= cutoff]
        .sort_values("date")
        .groupby("district")
        .tail(7)
    )
    weather_agg = recent_weather.groupby("district").agg(
        temp_c=("temp_c", "mean"),
        rain_mm=("rain_mm", "mean"),
        humidity=("humidity", "mean"),
    ).reset_index()
    weather_agg["weather_score"] = (
        30 * _norm(weather_agg["temp_c"]) +
        40 * _norm(weather_agg["rain_mm"]) +
        30 * _norm(weather_agg["humidity"])
    )
    table = table.merge(weather_agg[["district", "weather_score"]], on="district", how="left")
    table["weather_score"] = table["weather_score"].fillna(table["weather_score"].median())

    # ── Pest bulletin score (max pressure across all pests, latest week) ──
    latest_pest_week = ds.pest["week_end_date"].max()
    pest_latest = (
        ds.pest[ds.pest["week_end_date"] == latest_pest_week]
        .groupby(["district", "crop"])["pest_pressure"]
        .max()
        .reset_index()
        .rename(columns={"pest_pressure": "pest_score"})
    )
    # For retailers (no crop): take district max across all crops
    pest_district = (
        pest_latest.groupby("district")["pest_score"].max().reset_index()
    )

    # Merge pest for farmers (by district+crop)
    farmers_mask = table["entity_type"] == "farmer"
    table = table.merge(
        pest_latest.rename(columns={"pest_score": "_pest_crop"}),
        on=["district", "crop"], how="left"
    )
    # Merge pest for retailers (by district only)
    table = table.merge(
        pest_district.rename(columns={"pest_score": "_pest_district"}),
        on="district", how="left"
    )
    table["pest_score"] = np.where(
        farmers_mask,
        table["_pest_crop"].fillna(table["_pest_district"]),
        table["_pest_district"]
    )
    table["pest_score"] = table["pest_score"].fillna(0)
    table.drop(columns=["_pest_crop", "_pest_district"], inplace=True)

    # ── Inventory score (retailers only) ──────────────────────────────
    latest_inv_week = ds.inventory["week_end_date"].max()
    inv_latest = (
        ds.inventory[ds.inventory["week_end_date"] == latest_inv_week]
        .groupby("retailer_id")["sku_qty"]
        .sum()
        .reset_index()
        .rename(columns={"retailer_id": "id", "sku_qty": "total_inv"})
    )
    inv_latest["inventory_score"] = (1 - _norm(inv_latest["total_inv"])) * 100
    table = table.merge(inv_latest[["id", "inventory_score"]], on="id", how="left")
    table["inventory_score"] = table["inventory_score"].fillna(0)

    # ── Purchase history score (retailers only) ────────────────────────
    sales = (
        ds.pos.groupby("retailer_id")["sku_qty"]
        .sum()
        .reset_index()
        .rename(columns={"retailer_id": "id", "sku_qty": "total_sales"})
    )
    sales["purchase_history_score"] = _norm(sales["total_sales"]) * 100
    table = table.merge(sales[["id", "purchase_history_score"]], on="id", how="left")
    table["purchase_history_score"] = table["purchase_history_score"].fillna(0)

    # ── Visit recency score (retailers: penalise recent visits) ────────
    recent_visits = ds.visit_log[
        (ds.visit_log["visit_date"] >= cutoff - pd.Timedelta(days=30)) &
        (ds.visit_log["visit_date"] <= cutoff)
    ]
    recent_count = (
        recent_visits.groupby("territory_id")
        .size()
        .reset_index(name="recent_visit_count")
    )
    recent_count["visit_recency_score"] = (
        1 - _norm(recent_count["recent_visit_count"])
    ) * 100
    table = table.merge(
        recent_count[["territory_id", "visit_recency_score"]],
        on="territory_id", how="left"
    )
    table["visit_recency_score"] = table["visit_recency_score"].fillna(50)

    # ── Competitive score ─────────────────────────────────────────────
    visit_by_ter = (
        ds.visit_log.groupby("territory_id").size().reset_index(name="visits")
    )
    sales_by_ret = (
        ds.pos.groupby("retailer_id")["sku_qty"].sum().reset_index()
        .merge(ds.retailers[["retailer_id", "territory_id"]], on="retailer_id", how="left")
    )
    sales_by_ter = (
        sales_by_ret.groupby("territory_id")["sku_qty"].sum().reset_index(name="sales")
    )
    comp = visit_by_ter.merge(sales_by_ter, on="territory_id", how="left")
    comp["sales"] = comp["sales"].fillna(0)
    comp["spv"] = comp["sales"] / (comp["visits"] + 1)
    threshold = comp["spv"].median()
    comp["competitive_score"] = np.where(comp["spv"] < threshold, 80, 30)
    table = table.merge(
        comp[["territory_id", "competitive_score"]], on="territory_id", how="left"
    )
    table["competitive_score"] = table["competitive_score"].fillna(0)

    # ── NDVI signals (farmers only) ────────────────────────────────────
    latest_ndvi_week = ds.ndvi["week_end_date"].max()
    ndvi_latest = (
        ds.ndvi[ds.ndvi["week_end_date"] == latest_ndvi_week]
        [["district", "crop", "ndvi_value", "ndvi_delta"]]
    )
    table = table.merge(
        ndvi_latest.rename(columns={"ndvi_value": "_ndvi", "ndvi_delta": "_ndvi_delta"}),
        on=["district", "crop"], how="left"
    )
    # ndvi_score: low NDVI = stressed crop = higher urgency (invert)
    table["ndvi_score"] = np.where(
        farmers_mask,
        (1 - table["_ndvi"].fillna(0.5).clip(0, 1)) * 100,
        0
    )
    # ndvi_delta_score: large negative delta = stress event = higher urgency
    table["ndvi_delta_score"] = np.where(
        farmers_mask,
        (-table["_ndvi_delta"].fillna(0)).clip(0, 0.3) / 0.3 * 100,
        0
    )
    table.drop(columns=["_ndvi", "_ndvi_delta"], inplace=True)

    # ── Growth score (farmers only) ────────────────────────────────────
    table["growth_score"] = (
        table["current_stage"].map(GROWTH_SCORE_MAP).fillna(30)
    )
    table.loc[~farmers_mask, "growth_score"] = 0

    # ── Weather × growth bonus ─────────────────────────────────────────
    table["weather_growth_bonus"] = np.where(
        (table["growth_score"] > 80) & (table["pest_score"] > 60), 15, 0
    )

    # ── Raw priority score ─────────────────────────────────────────────
    def _score_row(row):
        if row["entity_type"] == "farmer":
            return (
                0.20 * row["weather_score"] +
                0.25 * row["pest_score"] +
                0.20 * row["growth_score"] +
                0.15 * row["ndvi_score"] +
                0.15 * row["ndvi_delta_score"] +
                0.05 * row["weather_growth_bonus"]
            )
        else:
            return (
                0.20 * row["weather_score"] +
                0.20 * row["pest_score"] +
                0.30 * row["inventory_score"] +
                0.15 * row["purchase_history_score"] +
                0.10 * row["visit_recency_score"] +
                0.05 * row["competitive_score"]
            ) + 12  # entity_bonus for retailers

    table["raw_priority_score"] = table.apply(_score_row, axis=1)

    rng = np.random.default_rng(42)
    table["raw_priority_score"] += rng.normal(0, 1.0, len(table))

    # ── Final normalization 0–100 ──────────────────────────────────────
    scaler = MinMaxScaler(feature_range=(0, 100))
    table["final_priority_score"] = scaler.fit_transform(
        table[["raw_priority_score"]]
    ).flatten().round(2)

    return table.sort_values("final_priority_score", ascending=False).reset_index(drop=True)
```

- [ ] **Step 2: Smoke-test scoring engine**

```bash
python3 -c "
from src.data_loader import load_all
from src.scoring_engine import compute_scores
ds = load_all()
scores = compute_scores(ds)
print(scores.shape)
print(scores[['id','entity_type','district','final_priority_score']].head(10))
print('Score range:', scores['final_priority_score'].min(), '-', scores['final_priority_score'].max())
"
```

Expected: 10000 rows (6000 farmers + 4000 retailers), scores 0–100, top entries have high scores.

- [ ] **Step 3: Commit**

```bash
git add src/scoring_engine.py
git commit -m "feat: scoring engine v2 with NDVI and pest bulletin signals"
```

---

## Task 6: Route Optimizer

**Files:**
- Create: `src/route_optimizer.py`

- [ ] **Step 1: Write src/route_optimizer.py**

```python
"""
Greedy nearest-neighbor route optimizer.

Given a list of entities to visit in a territory (sorted by priority),
reorders them to minimize travel by clustering on tehsil.
Entities in the same tehsil are grouped together; tehsil order is
determined by alphabetical proximity (a simple proxy since we have no
GPS coordinates — tehsil names are used as cluster keys).

Returns the same list reordered with a 'visit_sequence' column.
"""

import pandas as pd


def optimize_route(entities: pd.DataFrame) -> pd.DataFrame:
    """
    Reorder entities for minimal travel using greedy tehsil clustering.

    entities must have columns: id, tehsil (or visit_tehsil), final_priority_score.
    Returns entities with added 'visit_sequence' column (1-indexed).
    """
    if entities.empty:
        return entities

    tehsil_col = "tehsil" if "tehsil" in entities.columns else "visit_tehsil"
    if tehsil_col not in entities.columns:
        entities["visit_sequence"] = range(1, len(entities) + 1)
        return entities

    # Group by tehsil; within each tehsil sort by priority descending
    grouped = (
        entities
        .assign(_tehsil=entities[tehsil_col].fillna("unknown"))
        .sort_values(["_tehsil", "final_priority_score"], ascending=[True, False])
    )

    # Order tehsils: start with the tehsil containing the highest-priority entity
    top_tehsil = (
        entities.loc[entities["final_priority_score"].idxmax(), tehsil_col]
        if tehsil_col in entities.columns else "unknown"
    )
    tehsils = sorted(grouped["_tehsil"].unique())
    if top_tehsil in tehsils:
        tehsils = [top_tehsil] + [t for t in tehsils if t != top_tehsil]

    ordered_ids = []
    for tehsil in tehsils:
        chunk = grouped[grouped["_tehsil"] == tehsil]
        ordered_ids.extend(chunk["id"].tolist())

    id_order = {eid: i + 1 for i, eid in enumerate(ordered_ids)}
    result = entities.copy()
    result["visit_sequence"] = result["id"].map(id_order).fillna(len(entities) + 1).astype(int)
    return result.sort_values("visit_sequence").reset_index(drop=True)
```

- [ ] **Step 2: Test optimizer manually**

```bash
python3 -c "
import pandas as pd
from src.route_optimizer import optimize_route
test = pd.DataFrame({
    'id': ['A','B','C','D','E'],
    'tehsil': ['Patna_T001','Patna_T002','Patna_T001','Patna_T003','Patna_T002'],
    'final_priority_score': [90, 70, 85, 60, 75],
})
result = optimize_route(test)
print(result[['id','tehsil','final_priority_score','visit_sequence']])
"
```

Expected: Entities grouped by tehsil, within each tehsil ordered by priority descending.

- [ ] **Step 3: Commit**

```bash
git add src/route_optimizer.py
git commit -m "feat: greedy nearest-neighbor route optimizer by tehsil"
```

---

## Task 7: Anomaly Detector

**Files:**
- Create: `src/anomaly_detector.py`

- [ ] **Step 1: Write src/anomaly_detector.py**

```python
"""
Anomaly and opportunity detection.

Checks four signal types:
1. demand_spike   — retailer+SKU rolling POS > mean + 2σ
2. stockout_risk  — inventory < 10 units AND district pest_pressure > 60
3. ndvi_crash     — week-on-week NDVI delta < -0.15
4. pest_outbreak  — any pest at "critical" alert level in district
5. visit_gap      — entity not visited in > 21 days AND priority > 65
"""

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd

from src.data_loader import DataStore


@dataclass
class Alert:
    alert_type: str          # demand_spike | stockout_risk | ndvi_crash | pest_outbreak | visit_gap
    severity: str            # low | medium | high | critical
    entity_id: str
    district: str
    detail: str
    action: str


def detect_anomalies(
    ds: DataStore,
    territory_id: str,
    as_of_date: str = None,
    priority_scores: pd.DataFrame = None,
) -> List[Alert]:
    """Detect anomalies for a given territory. Returns list of Alert objects."""
    cutoff = pd.Timestamp(as_of_date) if as_of_date else ds.visit_log["visit_date"].max()
    alerts: List[Alert] = []

    # Retailers in this territory
    ter_retailers = ds.retailers[ds.retailers["territory_id"] == territory_id]["retailer_id"].tolist()
    if not ter_retailers:
        return alerts

    # District of this territory (take first retailer's district)
    district = ds.retailers[ds.retailers["territory_id"] == territory_id]["district"].iloc[0]

    # ── 1. Demand spike ───────────────────────────────────────────────
    recent_pos = ds.pos[
        (ds.pos["retailer_id"].isin(ter_retailers)) &
        (ds.pos["transaction_date"] <= cutoff) &
        (ds.pos["transaction_date"] >= cutoff - pd.Timedelta(weeks=4))
    ]
    if not recent_pos.empty:
        weekly_sales = (
            recent_pos.assign(
                week=recent_pos["transaction_date"].dt.to_period("W")
            )
            .groupby(["retailer_id", "sku_name", "week"])["sku_qty"]
            .sum()
            .reset_index()
        )
        stats = (
            weekly_sales.groupby(["retailer_id", "sku_name"])["sku_qty"]
            .agg(["mean", "std"])
            .reset_index()
        )
        latest_week = weekly_sales["week"].max()
        latest = weekly_sales[weekly_sales["week"] == latest_week]
        spike = latest.merge(stats, on=["retailer_id", "sku_name"])
        spike = spike[spike["sku_qty"] > spike["mean"] + 2 * spike["std"].fillna(0)]
        for _, row in spike.iterrows():
            alerts.append(Alert(
                alert_type="demand_spike",
                severity="high",
                entity_id=row["retailer_id"],
                district=district,
                detail=f"{row['sku_name']} sales {row['sku_qty']:.0f} units vs avg {row['mean']:.0f} — likely pest-driven demand",
                action=f"Visit {row['retailer_id']} today; ensure stock of {row['sku_name']}; cross-sell complementary products",
            ))

    # ── 2. Stockout risk ──────────────────────────────────────────────
    latest_inv = ds.inventory[
        (ds.inventory["retailer_id"].isin(ter_retailers)) &
        (ds.inventory["week_end_date"] == ds.inventory["week_end_date"].max())
    ]
    low_stock = latest_inv[latest_inv["sku_qty"] < 10]
    latest_pest_week = ds.pest["week_end_date"].max()
    pest_district = ds.pest[
        (ds.pest["district"] == district) &
        (ds.pest["week_end_date"] == latest_pest_week)
    ]["pest_pressure"].max()
    if pest_district > 60:
        for _, row in low_stock.iterrows():
            alerts.append(Alert(
                alert_type="stockout_risk",
                severity="high" if pest_district > 80 else "medium",
                entity_id=row["retailer_id"],
                district=district,
                detail=f"{row['sku_name']} has only {row['sku_qty']} units; district pest pressure {pest_district:.0f}/100",
                action=f"Trigger reorder for {row['sku_name']} at {row['retailer_id']} immediately",
            ))

    # ── 3. NDVI crash ─────────────────────────────────────────────────
    ndvi_latest = ds.ndvi[
        (ds.ndvi["district"] == district) &
        (ds.ndvi["week_end_date"] == ds.ndvi["week_end_date"].max())
    ]
    crashed = ndvi_latest[ndvi_latest["ndvi_delta"] < -0.15]
    for _, row in crashed.iterrows():
        alerts.append(Alert(
            alert_type="ndvi_crash",
            severity="high",
            entity_id=f"DISTRICT_{district}",
            district=district,
            detail=f"NDVI dropped {row['ndvi_delta']:.2f} this week for {row['crop']} — possible disease or drought stress",
            action="Prioritise all farmer visits in this district; recommend fungicide/irrigation advisory",
        ))

    # ── 4. Pest outbreak ─────────────────────────────────────────────
    critical_pests = ds.pest[
        (ds.pest["district"] == district) &
        (ds.pest["week_end_date"] == ds.pest["week_end_date"].max()) &
        (ds.pest["alert_level"] == "critical")
    ]
    for _, row in critical_pests.iterrows():
        alerts.append(Alert(
            alert_type="pest_outbreak",
            severity="critical",
            entity_id=f"DISTRICT_{district}",
            district=district,
            detail=f"{row['pest_name']} outbreak in {row['crop']} — pressure {row['pest_pressure']:.0f}/100",
            action=f"Mobilise all reps in district; push relevant pesticide to all retailers today",
        ))

    # ── 5. Visit gap ──────────────────────────────────────────────────
    if priority_scores is not None and not priority_scores.empty:
        ter_scores = priority_scores[
            (priority_scores["territory_id"] == territory_id) &
            (priority_scores["final_priority_score"] > 65)
        ]
        last_visit = (
            ds.visit_log[ds.visit_log["territory_id"] == territory_id]
            .groupby("visit_tehsil")["visit_date"]
            .max()
            .reset_index()
            .rename(columns={"visit_date": "last_visit_date"})
        )
        for _, row in ter_scores.iterrows():
            tehsil = row.get("tehsil") or row.get("visit_tehsil", "")
            lv = last_visit[last_visit["visit_tehsil"] == tehsil]["last_visit_date"]
            if lv.empty or (cutoff - lv.values[0]).days > 21:
                alerts.append(Alert(
                    alert_type="visit_gap",
                    severity="medium",
                    entity_id=row["id"],
                    district=district,
                    detail=f"High-priority entity not visited in >21 days (score {row['final_priority_score']:.1f})",
                    action="Include in today's itinerary",
                ))

    return alerts
```

- [ ] **Step 2: Smoke-test anomaly detector**

```bash
python3 -c "
from src.data_loader import load_all
from src.anomaly_detector import detect_anomalies
ds = load_all()
alerts = detect_anomalies(ds, territory_id='TER_0001')
print(f'Found {len(alerts)} alerts for TER_0001')
for a in alerts[:3]:
    print(a)
"
```

Expected: Prints alert count and sample alerts without errors.

- [ ] **Step 3: Commit**

```bash
git add src/anomaly_detector.py
git commit -m "feat: anomaly detector for demand spikes, stockouts, NDVI crashes, outbreaks"
```

---

## Task 8: NBA Engine (Groq)

**Files:**
- Create: `src/nba_engine.py`

- [ ] **Step 1: Write src/nba_engine.py**

```python
"""
Next Best Action engine powered by Groq API.

Assembles a structured context packet from all data signals,
sends it to llama-3.3-70b-versatile via Groq,
and returns a validated JSON recommendation.
"""

import json
import os

import pandas as pd
from dotenv import load_dotenv
from groq import Groq

from src.data_loader import DataStore

load_dotenv()

_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


def _build_context(
    entity_id: str,
    ds: DataStore,
    priority_scores: pd.DataFrame,
    as_of_date: str = None,
) -> dict:
    """Build structured context dict for the entity."""
    cutoff = pd.Timestamp(as_of_date) if as_of_date else pd.Timestamp.now()

    is_retailer = entity_id.startswith("RTL")
    is_farmer = entity_id.startswith("GRW")

    ctx = {"entity_id": entity_id, "entity_type": "retailer" if is_retailer else "farmer"}

    score_row = priority_scores[priority_scores["id"] == entity_id]
    ctx["priority_score"] = (
        float(score_row["final_priority_score"].values[0]) if not score_row.empty else 0.0
    )
    ctx["district"] = score_row["district"].values[0] if not score_row.empty else "unknown"

    if is_retailer:
        ret_row = ds.retailers[ds.retailers["retailer_id"] == entity_id]
        ctx["state"] = ret_row["state"].values[0] if not ret_row.empty else "unknown"
        ctx["tehsil"] = ret_row["tehsil"].values[0] if not ret_row.empty else "unknown"

        # Latest inventory
        inv = (
            ds.inventory[
                (ds.inventory["retailer_id"] == entity_id) &
                (ds.inventory["week_end_date"] == ds.inventory["week_end_date"].max())
            ][["sku_name", "sku_qty"]]
            .sort_values("sku_qty")
            .to_dict("records")
        )
        ctx["inventory"] = inv

        # Last 3 POS transactions
        last_pos = (
            ds.pos[ds.pos["retailer_id"] == entity_id]
            .sort_values("transaction_date", ascending=False)
            .head(3)[["sku_name", "sku_qty", "transaction_date"]]
            .to_dict("records")
        )
        ctx["recent_purchases"] = last_pos
        ctx["days_since_last_purchase"] = (
            int((cutoff - pd.Timestamp(last_pos[0]["transaction_date"])).days)
            if last_pos else 999
        )

    if is_farmer:
        grw_row = ds.growers[ds.growers["grower_id"] == entity_id]
        if not grw_row.empty:
            ctx["crop"] = grw_row["crop"].values[0]
            ctx["growth_stage"] = grw_row["current_stage"].values[0]
            ctx["farm_size_acres"] = float(grw_row["grower_farm_size"].values[0])
            ctx["state"] = grw_row["state"].values[0]

        # NDVI
        ndvi_row = ds.ndvi[
            (ds.ndvi["district"] == ctx["district"]) &
            (ds.ndvi["crop"] == ctx.get("crop", "")) &
            (ds.ndvi["week_end_date"] == ds.ndvi["week_end_date"].max())
        ]
        ctx["ndvi"] = float(ndvi_row["ndvi_value"].values[0]) if not ndvi_row.empty else None
        ctx["ndvi_delta"] = float(ndvi_row["ndvi_delta"].values[0]) if not ndvi_row.empty else None

        # WhatsApp engagement
        wa = ds.whatsapp[ds.whatsapp["grower_id"] == entity_id]
        ctx["whatsapp_opened"] = bool(wa["opened_status"].any()) if not wa.empty else False

    # Pest pressure for district
    pest_row = (
        ds.pest[
            (ds.pest["district"] == ctx["district"]) &
            (ds.pest["week_end_date"] == ds.pest["week_end_date"].max())
        ]
        .sort_values("pest_pressure", ascending=False)
        .head(1)
    )
    if not pest_row.empty:
        ctx["top_pest"] = pest_row["pest_name"].values[0]
        ctx["pest_pressure"] = float(pest_row["pest_pressure"].values[0])
        ctx["pest_alert_level"] = pest_row["alert_level"].values[0]
    else:
        ctx["top_pest"] = "unknown"
        ctx["pest_pressure"] = 0
        ctx["pest_alert_level"] = "low"

    return ctx


_SYSTEM_PROMPT = """\
You are an expert Syngenta agronomic field advisor helping a field sales representative.
Respond ONLY with valid JSON — no explanation, no markdown, no extra text.
Be specific and data-grounded. Use numbers from the context."""

_USER_TEMPLATE = """\
Entity visit context:
{context_json}

Return exactly this JSON structure:
{{
  "primary_product": "<Syngenta product name>",
  "reason": "<1 sentence, cite specific data from context>",
  "talk_track": "<2 sentences max — what the rep should say to open conversation>",
  "agronomic_advice": "<1 sentence actionable agronomic tip relevant to crop/stage/pest>",
  "promo_mechanic": "<promotional offer or null if none>",
  "whatsapp_followup": <true|false>
}}"""


def get_nba(
    entity_id: str,
    ds: DataStore,
    priority_scores: pd.DataFrame,
    as_of_date: str = None,
) -> dict:
    """
    Get next best action for a visit.
    Returns dict with keys: primary_product, reason, talk_track,
                            agronomic_advice, promo_mechanic, whatsapp_followup.
    Falls back to rule-based response if Groq call fails.
    """
    ctx = _build_context(entity_id, ds, priority_scores, as_of_date)

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _USER_TEMPLATE.format(
                    context_json=json.dumps(ctx, indent=2, default=str)
                )},
            ],
            temperature=0.3,
            max_tokens=400,
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception as exc:
        # Rule-based fallback — always returns something useful
        return {
            "primary_product": "Score 250 EC",
            "reason": f"High pest pressure ({ctx.get('pest_pressure', 0):.0f}/100) in {ctx['district']} district.",
            "talk_track": "Good morning! Given the current pest pressure in your area, we recommend ensuring stock of our fungicide range. Farmers are likely to need it in the next 7–10 days.",
            "agronomic_advice": "Apply fungicide at early disease onset for best efficacy.",
            "promo_mechanic": None,
            "whatsapp_followup": ctx.get("whatsapp_opened", False),
            "_fallback": True,
            "_error": str(exc),
        }
```

- [ ] **Step 2: Test NBA engine (requires GROQ_API_KEY in .env)**

```bash
python3 -c "
from src.data_loader import load_all
from src.scoring_engine import compute_scores
from src.nba_engine import get_nba
import json

ds = load_all()
scores = compute_scores(ds)

# Test with first retailer
retailer_id = 'RTL_00001'
nba = get_nba(retailer_id, ds, scores)
print(json.dumps(nba, indent=2))
"
```

Expected: Valid JSON with primary_product, reason, talk_track, agronomic_advice, promo_mechanic, whatsapp_followup. If fallback fires, `_fallback: true` appears.

- [ ] **Step 3: Commit**

```bash
git add src/nba_engine.py
git commit -m "feat: NBA engine with Groq llama-3.3-70b and rule-based fallback"
```

---

## Task 9: Outcome Logger

**Files:**
- Create: `src/outcome_logger.py`

- [ ] **Step 1: Write src/outcome_logger.py**

```python
"""
SQLite-backed visit outcome logger.
Stores rep visit results and exposes conversion rate queries.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "outcomes.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS visit_outcomes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    rep_id      TEXT NOT NULL,
    entity_id   TEXT NOT NULL,
    visit_date  TEXT NOT NULL,
    outcome     TEXT NOT NULL CHECK(outcome IN ('sale','no_purchase','follow_up')),
    products_sold TEXT,
    qty_sold    INTEGER DEFAULT 0,
    notes       TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);
"""


@contextmanager
def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with _db() as conn:
        conn.executescript(_SCHEMA)


def log_outcome(
    rep_id: str,
    entity_id: str,
    visit_date: str,
    outcome: str,
    products_sold: Optional[List[str]] = None,
    qty_sold: int = 0,
    notes: str = "",
) -> int:
    """Insert a visit outcome. Returns new row id."""
    import json
    with _db() as conn:
        cur = conn.execute(
            """INSERT INTO visit_outcomes
               (rep_id, entity_id, visit_date, outcome, products_sold, qty_sold, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (rep_id, entity_id, visit_date, outcome,
             json.dumps(products_sold or []), qty_sold, notes),
        )
        return cur.lastrowid


def get_conversion_rate(territory_id: str = None, weeks: int = 4) -> dict:
    """Return conversion rate for a territory (or global) over last N weeks."""
    from datetime import timedelta
    cutoff = date.today() - timedelta(weeks=weeks)
    with _db() as conn:
        rows = conn.execute(
            "SELECT outcome, COUNT(*) as cnt FROM visit_outcomes "
            "WHERE visit_date >= ? GROUP BY outcome",
            (cutoff.isoformat(),),
        ).fetchall()
    total = sum(r["cnt"] for r in rows)
    sales = sum(r["cnt"] for r in rows if r["outcome"] == "sale")
    return {
        "total_visits": total,
        "sales": sales,
        "conversion_rate": round(sales / total, 3) if total else 0.0,
        "breakdown": {r["outcome"]: r["cnt"] for r in rows},
    }
```

- [ ] **Step 2: Test outcome logger**

```bash
python3 -c "
from src.outcome_logger import init_db, log_outcome, get_conversion_rate
init_db()
log_outcome('REP_0001', 'RTL_00001', '2026-04-10', 'sale', ['Score 250 EC'], 40, 'Good visit')
log_outcome('REP_0001', 'RTL_00002', '2026-04-10', 'no_purchase', [], 0, 'Out of budget')
log_outcome('REP_0001', 'GRW_00001', '2026-04-10', 'follow_up', [], 0, 'Wants demo')
print(get_conversion_rate(weeks=52))
"
```

Expected: `{'total_visits': 3, 'sales': 1, 'conversion_rate': 0.333, 'breakdown': {'sale': 1, 'no_purchase': 1, 'follow_up': 1}}`

- [ ] **Step 3: Commit**

```bash
git add src/outcome_logger.py
git commit -m "feat: SQLite outcome logger with conversion rate query"
```

---

## Task 10: FastAPI App + Models

**Files:**
- Create: `api/__init__.py` (empty)
- Create: `api/models.py`
- Create: `api/main.py`
- Create: `api/routers/__init__.py` (empty)

- [ ] **Step 1: Create empty init files**

```bash
touch api/__init__.py api/routers/__init__.py
```

- [ ] **Step 2: Write api/models.py**

```python
from typing import List, Optional
from pydantic import BaseModel


class ItineraryItem(BaseModel):
    rank: int
    visit_sequence: int
    entity_id: str
    entity_type: str
    district: str
    tehsil: Optional[str] = None
    priority_score: float
    reason_codes: List[str]
    top_sku_to_discuss: Optional[str] = None
    visit_type_suggestion: str


class AlertItem(BaseModel):
    alert_type: str
    severity: str
    entity_id: str
    district: str
    detail: str
    action: str


class DailyPlanResponse(BaseModel):
    rep_id: str
    date: str
    territory_id: str
    itinerary: List[ItineraryItem]
    alerts: List[AlertItem]


class NBAResponse(BaseModel):
    entity_id: str
    nba: dict


class OutcomeRequest(BaseModel):
    rep_id: str
    entity_id: str
    date: str
    outcome: str   # sale | no_purchase | follow_up
    products_sold: List[str] = []
    qty_sold: int = 0
    notes: str = ""


class OutcomeResponse(BaseModel):
    success: bool
    outcome_id: int


class AnalyticsResponse(BaseModel):
    territory_id: str
    period_weeks: int
    visit_coverage: float
    conversion_rate: float
    top_skus: List[str]
    high_priority_unvisited: List[str]
```

- [ ] **Step 3: Write api/main.py**

```python
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from src.data_loader import load_all, DataStore
from src.scoring_engine import compute_scores
from src.outcome_logger import init_db

load_dotenv()

# App-wide shared state
_store: DataStore = None
_scores = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _store, _scores
    print("[startup] Loading datasets...")
    _store = load_all()
    print("[startup] Computing priority scores...")
    _scores = compute_scores(_store)
    _store.priority_scores = _scores
    print("[startup] Initialising outcome database...")
    init_db()
    print("[startup] Ready.")
    yield


app = FastAPI(
    title="Syngenta Field Co-pilot API",
    version="1.0.0",
    lifespan=lifespan,
)


def get_store() -> DataStore:
    return _store


from api.routers import daily_plan, nba, alerts, outcomes, analytics

app.include_router(daily_plan.router, prefix="/api")
app.include_router(nba.router,        prefix="/api")
app.include_router(alerts.router,     prefix="/api")
app.include_router(outcomes.router,   prefix="/api")
app.include_router(analytics.router,  prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "entities_scored": len(_scores) if _scores is not None else 0}
```

- [ ] **Step 4: Commit**

```bash
git add api/__init__.py api/routers/__init__.py api/models.py api/main.py
git commit -m "feat: FastAPI app with lifespan data loading and Pydantic models"
```

---

## Task 11: Daily Plan Router

**Files:**
- Create: `api/routers/daily_plan.py`

- [ ] **Step 1: Write api/routers/daily_plan.py**

```python
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, Query

from api.main import get_store
from api.models import DailyPlanResponse, ItineraryItem, AlertItem
from src.route_optimizer import optimize_route
from src.anomaly_detector import detect_anomalies

router = APIRouter()


def _reason_codes(row: pd.Series) -> List[str]:
    codes = []
    if row.get("inventory_score", 0) > 75:
        codes.append("stockout_risk")
    if row.get("pest_score", 0) > 70:
        codes.append("high_pest_district")
    if row.get("ndvi_delta_score", 0) > 60:
        codes.append("ndvi_stress")
    if row.get("visit_recency_score", 0) > 80:
        codes.append("overdue_visit")
    if row.get("growth_score", 0) >= 85:
        codes.append("critical_growth_stage")
    if not codes:
        codes.append("routine_priority")
    return codes


def _top_sku(entity_id: str, ds) -> Optional[str]:
    if not entity_id.startswith("RTL"):
        return None
    inv = ds.inventory[
        (ds.inventory["retailer_id"] == entity_id) &
        (ds.inventory["week_end_date"] == ds.inventory["week_end_date"].max())
    ].sort_values("sku_qty")
    if inv.empty:
        return None
    return inv.iloc[0]["sku_name"]


@router.get("/rep/{rep_id}/daily-plan", response_model=DailyPlanResponse)
def daily_plan(
    rep_id: str,
    date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    max_visits: int = Query(8, ge=1, le=20),
):
    ds = get_store()
    scores = ds.priority_scores

    # Find rep's territory
    rep_row = ds.reps[ds.reps["rep_id"] == rep_id]
    if rep_row.empty:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Rep {rep_id} not found")

    territory_id = rep_row["territory_id"].values[0]

    # Filter scores for this territory (retailers) + district farmers
    district = rep_row["district"].values[0]
    ter_retailers = scores[
        (scores["territory_id"] == territory_id) &
        (scores["entity_type"] == "retailer")
    ]
    ter_farmers = scores[
        (scores["district"] == district) &
        (scores["entity_type"] == "farmer")
    ]
    candidates = pd.concat([ter_retailers, ter_farmers], ignore_index=True)
    candidates = candidates.sort_values("final_priority_score", ascending=False).head(max_visits * 2)

    # Add tehsil column for route optimizer
    retailer_tehsil = ds.retailers[["retailer_id", "tehsil"]].rename(columns={"retailer_id": "id"})
    farmer_tehsil = ds.growers[["grower_id", "tehsil"]].rename(columns={"grower_id": "id"})
    tehsil_map = pd.concat([retailer_tehsil, farmer_tehsil], ignore_index=True)
    candidates = candidates.merge(tehsil_map, on="id", how="left")

    routed = optimize_route(candidates).head(max_visits)

    itinerary = []
    for i, row in routed.iterrows():
        itinerary.append(ItineraryItem(
            rank=int(row["final_priority_score"] > 0) and i + 1 or i + 1,
            visit_sequence=int(row["visit_sequence"]),
            entity_id=row["id"],
            entity_type=row["entity_type"],
            district=row["district"],
            tehsil=row.get("tehsil"),
            priority_score=float(row["final_priority_score"]),
            reason_codes=_reason_codes(row),
            top_sku_to_discuss=_top_sku(row["id"], ds),
            visit_type_suggestion="retailer_meeting" if row["entity_type"] == "retailer" else "grower_meeting",
        ))

    raw_alerts = detect_anomalies(ds, territory_id, as_of_date=date, priority_scores=scores)
    alert_items = [
        AlertItem(
            alert_type=a.alert_type, severity=a.severity, entity_id=a.entity_id,
            district=a.district, detail=a.detail, action=a.action,
        )
        for a in raw_alerts
    ]

    return DailyPlanResponse(
        rep_id=rep_id,
        date=date or str(ds.visit_log["visit_date"].max().date()),
        territory_id=territory_id,
        itinerary=itinerary,
        alerts=alert_items,
    )
```

- [ ] **Step 2: Start server and test endpoint**

```bash
uvicorn api.main:app --reload --port 8000
```

In another terminal:
```bash
curl -s "http://localhost:8000/api/rep/REP_0001/daily-plan?max_visits=5" | python3 -m json.tool | head -60
```

Expected: JSON with `rep_id`, `territory_id`, `itinerary` (5 items with visit_sequence), `alerts`.

- [ ] **Step 3: Commit**

```bash
git add api/routers/daily_plan.py
git commit -m "feat: daily plan router with route optimization and alerts"
```

---

## Task 12: NBA Router

**Files:**
- Create: `api/routers/nba.py`

- [ ] **Step 1: Write api/routers/nba.py**

```python
from typing import Optional
from fastapi import APIRouter, Query

from api.main import get_store
from api.models import NBAResponse
from src.nba_engine import get_nba

router = APIRouter()


@router.get("/visit/{entity_id}/nba", response_model=NBAResponse)
def next_best_action(
    entity_id: str,
    rep_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
):
    ds = get_store()
    nba = get_nba(entity_id, ds, ds.priority_scores, as_of_date=date)
    return NBAResponse(entity_id=entity_id, nba=nba)
```

- [ ] **Step 2: Test NBA endpoint**

```bash
curl -s "http://localhost:8000/api/visit/RTL_00001/nba?rep_id=REP_0001" | python3 -m json.tool
```

Expected: JSON with `entity_id` and `nba` dict containing primary_product, reason, talk_track, agronomic_advice, promo_mechanic, whatsapp_followup.

- [ ] **Step 3: Commit**

```bash
git add api/routers/nba.py
git commit -m "feat: NBA router calling Groq for point-of-visit recommendations"
```

---

## Task 13: Alerts Router

**Files:**
- Create: `api/routers/alerts.py`

- [ ] **Step 1: Write api/routers/alerts.py**

```python
from typing import List, Optional
from fastapi import APIRouter, Query

from api.main import get_store
from api.models import AlertItem
from src.anomaly_detector import detect_anomalies

router = APIRouter()


@router.get("/alerts", response_model=List[AlertItem])
def get_alerts(
    territory_id: str = Query(..., description="Territory ID e.g. TER_0001"),
    severity: Optional[str] = Query(None, description="Filter: low|medium|high|critical"),
    date: Optional[str] = Query(None),
):
    ds = get_store()
    raw = detect_anomalies(ds, territory_id, as_of_date=date, priority_scores=ds.priority_scores)

    SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    if severity:
        min_level = SEVERITY_ORDER.get(severity, 0)
        raw = [a for a in raw if SEVERITY_ORDER.get(a.severity, 0) >= min_level]

    raw.sort(key=lambda a: SEVERITY_ORDER.get(a.severity, 0), reverse=True)

    return [
        AlertItem(
            alert_type=a.alert_type, severity=a.severity, entity_id=a.entity_id,
            district=a.district, detail=a.detail, action=a.action,
        )
        for a in raw
    ]
```

- [ ] **Step 2: Test alerts endpoint**

```bash
curl -s "http://localhost:8000/api/alerts?territory_id=TER_0001&severity=medium" | python3 -m json.tool
```

Expected: JSON array of alert objects sorted by severity descending.

- [ ] **Step 3: Commit**

```bash
git add api/routers/alerts.py
git commit -m "feat: alerts router with severity filtering"
```

---

## Task 14: Outcomes + Analytics Routers

**Files:**
- Create: `api/routers/outcomes.py`
- Create: `api/routers/analytics.py`

- [ ] **Step 1: Write api/routers/outcomes.py**

```python
from fastapi import APIRouter

from api.models import OutcomeRequest, OutcomeResponse
from src.outcome_logger import log_outcome

router = APIRouter()


@router.post("/visit/outcome", response_model=OutcomeResponse)
def record_outcome(req: OutcomeRequest):
    outcome_id = log_outcome(
        rep_id=req.rep_id,
        entity_id=req.entity_id,
        visit_date=req.date,
        outcome=req.outcome,
        products_sold=req.products_sold,
        qty_sold=req.qty_sold,
        notes=req.notes,
    )
    return OutcomeResponse(success=True, outcome_id=outcome_id)
```

- [ ] **Step 2: Write api/routers/analytics.py**

```python
from typing import Optional
import pandas as pd
from fastapi import APIRouter, Query

from api.main import get_store
from api.models import AnalyticsResponse
from src.outcome_logger import get_conversion_rate

router = APIRouter()


@router.get("/analytics/territory/{territory_id}", response_model=AnalyticsResponse)
def territory_analytics(
    territory_id: str,
    weeks: int = Query(4, ge=1, le=52),
):
    ds = get_store()
    scores = ds.priority_scores

    ter_retailers = ds.retailers[ds.retailers["territory_id"] == territory_id]["retailer_id"].tolist()
    total = len(ter_retailers)

    visited = ds.visit_log[
        (ds.visit_log["territory_id"] == territory_id) &
        (ds.visit_log["visit_date"] >= ds.visit_log["visit_date"].max() - pd.Timedelta(weeks=weeks))
    ]["visit_tehsil"].nunique()

    all_tehsils = ds.retailers[ds.retailers["territory_id"] == territory_id]["tehsil"].nunique()
    coverage = round(visited / all_tehsils, 3) if all_tehsils else 0.0

    top_skus = (
        ds.pos[ds.pos["retailer_id"].isin(ter_retailers)]
        .groupby("sku_name")["sku_qty"].sum()
        .sort_values(ascending=False)
        .head(3)
        .index.tolist()
    )

    high_priority = scores[
        (scores["territory_id"] == territory_id) &
        (scores["final_priority_score"] > 70)
    ]["id"].tolist()

    visited_ids = ds.visit_log[
        (ds.visit_log["territory_id"] == territory_id) &
        (ds.visit_log["visit_date"] >= ds.visit_log["visit_date"].max() - pd.Timedelta(weeks=weeks))
    ]["visit_tehsil"].unique()

    ter_retailer_df = ds.retailers[ds.retailers["territory_id"] == territory_id]
    unvisited = ter_retailer_df[~ter_retailer_df["tehsil"].isin(visited_ids)]["retailer_id"].tolist()
    unvisited_hp = [r for r in unvisited if r in high_priority][:5]

    conv = get_conversion_rate(territory_id=territory_id, weeks=weeks)

    return AnalyticsResponse(
        territory_id=territory_id,
        period_weeks=weeks,
        visit_coverage=coverage,
        conversion_rate=conv["conversion_rate"],
        top_skus=top_skus,
        high_priority_unvisited=unvisited_hp,
    )


@router.get("/entity/{entity_id}")
def entity_profile(entity_id: str):
    ds = get_store()
    scores = ds.priority_scores

    score_row = scores[scores["id"] == entity_id].to_dict("records")
    profile = score_row[0] if score_row else {}

    if entity_id.startswith("RTL"):
        inv = ds.inventory[
            (ds.inventory["retailer_id"] == entity_id) &
            (ds.inventory["week_end_date"] == ds.inventory["week_end_date"].max())
        ][["sku_name", "sku_qty"]].to_dict("records")
        recent_pos = (
            ds.pos[ds.pos["retailer_id"] == entity_id]
            .sort_values("transaction_date", ascending=False)
            .head(10)[["sku_name", "sku_qty", "transaction_date"]]
            .to_dict("records")
        )
        profile["inventory"] = inv
        profile["recent_transactions"] = recent_pos

    if entity_id.startswith("GRW"):
        grw = ds.growers[ds.growers["grower_id"] == entity_id].to_dict("records")
        wa = ds.whatsapp[ds.whatsapp["grower_id"] == entity_id].to_dict("records")
        profile["grower_details"] = grw[0] if grw else {}
        profile["whatsapp_messages"] = wa

    return profile
```

- [ ] **Step 3: Test both endpoints**

```bash
# Log an outcome
curl -s -X POST "http://localhost:8000/api/visit/outcome" \
  -H "Content-Type: application/json" \
  -d '{"rep_id":"REP_0001","entity_id":"RTL_00001","date":"2026-04-10","outcome":"sale","products_sold":["Score 250 EC"],"qty_sold":30,"notes":""}' \
  | python3 -m json.tool

# Territory analytics
curl -s "http://localhost:8000/api/analytics/territory/TER_0001?weeks=4" | python3 -m json.tool

# Entity profile
curl -s "http://localhost:8000/api/entity/RTL_00001" | python3 -m json.tool
```

Expected: All three return valid JSON without errors.

- [ ] **Step 4: Commit**

```bash
git add api/routers/outcomes.py api/routers/analytics.py
git commit -m "feat: outcomes and analytics routers"
```

---

## Task 15: Streamlit Dashboard

**Files:**
- Create: `dashboard/app.py`

- [ ] **Step 1: Write dashboard/app.py**

```python
"""
Streamlit rep-facing dashboard.
Run: streamlit run dashboard/app.py
Requires the FastAPI backend running at localhost:8000.
"""

import httpx
import streamlit as st
import pandas as pd

API_BASE = "http://localhost:8000/api"

st.set_page_config(page_title="Syngenta Field Co-pilot", page_icon="🌾", layout="wide")
st.title("🌾 Syngenta Field Co-pilot")

# ── Sidebar: Rep selector ──────────────────────────────────────────
st.sidebar.header("Field Rep")

rep_id = st.sidebar.text_input("Rep ID", value="REP_0001")
visit_date = st.sidebar.date_input("Date")
max_visits = st.sidebar.slider("Max visits today", 3, 15, 8)

if st.sidebar.button("Load My Plan", type="primary"):
    st.session_state["plan_loaded"] = True

tabs = st.tabs(["📋 Daily Plan", "🎯 Next Best Action", "🚨 Alerts", "📊 Analytics"])

# ── Tab 1: Daily Plan ──────────────────────────────────────────────
with tabs[0]:
    if st.session_state.get("plan_loaded"):
        with st.spinner("Building your optimised visit plan..."):
            r = httpx.get(
                f"{API_BASE}/rep/{rep_id}/daily-plan",
                params={"date": str(visit_date), "max_visits": max_visits},
                timeout=60,
            )
        if r.status_code == 200:
            plan = r.json()
            st.success(f"Territory: **{plan['territory_id']}** | Date: {plan['date']}")

            rows = []
            for item in plan["itinerary"]:
                rows.append({
                    "Stop": item["visit_sequence"],
                    "Entity ID": item["entity_id"],
                    "Type": item["entity_type"],
                    "District": item["district"],
                    "Tehsil": item.get("tehsil", ""),
                    "Priority Score": f"{item['priority_score']:.1f}",
                    "Top SKU": item.get("top_sku_to_discuss", ""),
                    "Signals": ", ".join(item["reason_codes"]),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

            if plan["alerts"]:
                st.warning(f"⚠️ {len(plan['alerts'])} alerts for this territory — see Alerts tab")
        else:
            st.error(f"API error: {r.status_code} — {r.text[:200]}")
    else:
        st.info("Select your Rep ID and date in the sidebar, then click **Load My Plan**.")

# ── Tab 2: Next Best Action ────────────────────────────────────────
with tabs[1]:
    st.subheader("Get AI Recommendation for a Visit")
    entity_id = st.text_input("Entity ID (RTL_XXXXX or GRW_XXXXX)", value="RTL_00001")
    if st.button("Get Recommendation", type="primary"):
        with st.spinner("Asking Groq AI..."):
            r = httpx.get(
                f"{API_BASE}/visit/{entity_id}/nba",
                params={"rep_id": rep_id, "date": str(visit_date)},
                timeout=30,
            )
        if r.status_code == 200:
            nba = r.json()["nba"]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Recommended Product", nba.get("primary_product", "—"))
                st.info(f"**Why:** {nba.get('reason', '')}")
                st.success(f"**Talk Track:** {nba.get('talk_track', '')}")
            with col2:
                st.info(f"**Agronomic Advice:** {nba.get('agronomic_advice', '')}")
                if nba.get("promo_mechanic"):
                    st.warning(f"**Promo:** {nba['promo_mechanic']}")
                st.write(f"WhatsApp follow-up: {'✅' if nba.get('whatsapp_followup') else '❌'}")
            if nba.get("_fallback"):
                st.caption("⚠️ Fallback response (Groq unavailable)")
        else:
            st.error(f"API error: {r.status_code}")

# ── Tab 3: Alerts ─────────────────────────────────────────────────
with tabs[2]:
    st.subheader("Territory Alerts")
    territory_id_alert = st.text_input("Territory ID", value="TER_0001")
    severity_filter = st.selectbox("Min Severity", ["low", "medium", "high", "critical"])
    if st.button("Load Alerts"):
        r = httpx.get(
            f"{API_BASE}/alerts",
            params={"territory_id": territory_id_alert, "severity": severity_filter},
            timeout=30,
        )
        if r.status_code == 200:
            alerts = r.json()
            if alerts:
                severity_colors = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                for a in alerts:
                    icon = severity_colors.get(a["severity"], "⚪")
                    with st.expander(f"{icon} [{a['alert_type'].upper()}] {a['entity_id']}"):
                        st.write(f"**Detail:** {a['detail']}")
                        st.write(f"**Action:** {a['action']}")
            else:
                st.success("No alerts for this territory at this severity level.")
        else:
            st.error(f"API error: {r.status_code}")

# ── Tab 4: Analytics ──────────────────────────────────────────────
with tabs[3]:
    st.subheader("Territory Performance")
    territory_id_analytics = st.text_input("Territory ID ", value="TER_0001")
    weeks = st.slider("Weeks", 1, 12, 4)
    if st.button("Load Analytics"):
        r = httpx.get(
            f"{API_BASE}/analytics/territory/{territory_id_analytics}",
            params={"weeks": weeks},
            timeout=30,
        )
        if r.status_code == 200:
            a = r.json()
            col1, col2, col3 = st.columns(3)
            col1.metric("Visit Coverage", f"{a['visit_coverage']*100:.1f}%")
            col2.metric("Conversion Rate", f"{a['conversion_rate']*100:.1f}%")
            col3.metric("Period", f"Last {a['period_weeks']} weeks")

            st.write("**Top SKUs:**", ", ".join(a["top_skus"]) or "None")
            if a["high_priority_unvisited"]:
                st.warning(
                    f"**High-priority unvisited:** {', '.join(a['high_priority_unvisited'])}"
                )
        else:
            st.error(f"API error: {r.status_code}")
```

- [ ] **Step 2: Start the dashboard (backend must be running)**

In terminal 1:
```bash
uvicorn api.main:app --reload --port 8000
```

In terminal 2:
```bash
streamlit run dashboard/app.py
```

Open browser at `http://localhost:8501`. Enter `REP_0001`, click **Load My Plan**. Verify:
- Daily plan tab shows 8 stops with sequences
- Next Best Action tab returns product recommendation
- Alerts tab shows any alerts for TER_0001
- Analytics tab shows coverage metrics

- [ ] **Step 3: Commit**

```bash
git add dashboard/app.py
git commit -m "feat: Streamlit rep dashboard with daily plan, NBA, alerts, analytics tabs"
```

---

## Self-Review

**Spec coverage check:**

| Requirement | Task |
|-------------|------|
| Synthetic NDVI | Task 2 |
| Synthetic pest bulletin | Task 3 |
| Dynamic visit prioritization | Task 5, 11 |
| Route sequencing | Task 6, 11 |
| Next best action at point of visit | Task 8, 12 |
| Anomaly + opportunity detection | Task 7, 13 |
| Outcome logging | Task 9, 14 |
| FastAPI backend | Tasks 10–14 |
| Groq NBA engine | Task 8 |
| Streamlit dashboard | Task 15 |
| NDVI delta signal in scoring | Task 5 |
| Pest bulletin replaces weather proxy | Task 5 |
| Visit recency signal | Task 5 |
| Territory analytics | Task 14 |
| Entity profile endpoint | Task 14 |

All requirements covered. No placeholders, no TODOs. All code blocks are complete.
