# Syngenta Field Operations AI Co-pilot — System Design
**Date:** 2026-05-19  
**Hackathon:** Syngenta IITM Hackathon 2026  
**Season:** Rabi 2025–26 (Oct 2025 – Apr 2026)

---

## 1. Problem Summary

Syngenta field reps plan visits by routine. Agricultural context changes daily — pest outbreaks, weather shifts, competitor activity, crop growth windows. The goal is an AI system that tells each rep: **who to visit today, in what order, and what to say when they get there.**

---

## 2. Architecture: Hybrid Intelligent System (Option C)

Scoring engine + synthetic data enrichment drives prioritization. Groq API (llama-3.3-70b) generates natural-language next-best-action recommendations only at point-of-visit. Separating structured scoring from LLM keeps the system auditable and cost-efficient.

```
Data Layer (CSVs + synthetic NDVI/pest)
    ↓
Scoring Engine v2 (priority_score per entity)
    ↓
Route Optimizer → Anomaly Detector → NBA Engine (Groq)
    ↓
FastAPI Backend (REST)
    ↓
Streamlit Dashboard (rep-facing)
```

---

## 3. Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | FastAPI |
| LLM | Groq API — llama-3.3-70b-versatile |
| Data processing | Pandas, NumPy, scikit-learn |
| Route optimization | Greedy nearest-neighbor (tehsil clusters) |
| Dashboard | Streamlit |
| Outcome storage | SQLite (outcomes.db) |
| Synthetic data | Python generators in src/ |

---

## 4. Project Structure

```
hackathon/
├── data/                        # original CSVs (read-only)
├── synthetic/                   # generated at startup
│   ├── ndvi_weekly.csv
│   └── pest_bulletin_weekly.csv
├── src/
│   ├── data_loader.py
│   ├── scoring_engine.py
│   ├── ndvi_generator.py
│   ├── pest_generator.py
│   ├── route_optimizer.py
│   ├── anomaly_detector.py
│   ├── nba_engine.py
│   └── outcome_logger.py
├── api/
│   ├── main.py
│   ├── models.py
│   └── routers/
│       ├── daily_plan.py
│       ├── nba.py
│       ├── alerts.py
│       ├── outcomes.py
│       └── analytics.py
├── dashboard/
│   └── app.py
├── script.py                    # original scorer (superseded by src/)
└── requirements.txt
```

---

## 5. Synthetic Data Specifications

### 5a. NDVI Weekly (`synthetic/ndvi_weekly.csv`)

**Columns:** `district`, `crop`, `week_end_date`, `ndvi_value`, `ndvi_delta`

**Generation logic:**
- Season: Oct 2025 – Apr 2026 (26 weeks)
- Agronomic NDVI curve per crop:
  - Wheat: sow(0.22) → vegetative(0.58) → tillering(0.72) → flowering(0.83) → grain_fill(0.74) → harvest(0.32)
  - Mustard: sow(0.20) → vegetative(0.52) → flowering(0.78) → pod(0.68) → harvest(0.28)
  - Chickpea: sow(0.18) → vegetative(0.48) → flowering(0.70) → pod(0.62) → harvest(0.25)
  - Potato: sow(0.25) → vegetative(0.65) → tuber(0.72) → maturity(0.55) → harvest(0.30)
- Rainfall modulation: rain_mm > 5 → NDVI += 0.03–0.08
- Gaussian noise: σ = 0.02
- Stress events: 3–5 districts per season get a 15–20% single-week NDVI drop (simulates disease/drought)

### 5b. Pest Bulletin Weekly (`synthetic/pest_bulletin_weekly.csv`)

**Columns:** `district`, `crop`, `pest_name`, `week_end_date`, `pest_pressure` (0–100), `alert_level`

**Crop-pest mapping:**
- Wheat: Yellow Rust (fungal, humidity-driven), Aphids (temp 12–20°C)
- Mustard: Alternaria Blight (humidity + rain), Mustard Aphid (temp 15–22°C)
- Chickpea: Pod Borer (temp 20–28°C, dry), Fusarium Wilt (soil moisture)
- Potato: Late Blight (humidity > 80%, temp 15–20°C), Aphids

**Pressure formula:**
```
base = humidity_score × crop_stage_vulnerability × temp_fit_score
+ random(0, 10) noise
+ outbreak_spike (injected for 2–3 districts per season: +40–60 for 2–3 weeks)
alert_level = "low"(<30) | "medium"(30–60) | "high"(60–80) | "critical"(>80)
```

---

## 6. Scoring Engine v2

### Farmer Priority Score
```
0.20 × weather_score
0.25 × pest_bulletin_score      (replaces weather-derived proxy)
0.20 × growth_score
0.15 × ndvi_score               (NEW: high NDVI = crop healthy, lower urgency)
0.15 × ndvi_delta_score         (NEW: negative delta = stress = higher urgency)
0.05 × weather_growth_bonus
```

### Retailer Priority Score
```
0.20 × weather_score
0.20 × pest_bulletin_score
0.30 × inventory_score
0.15 × purchase_history_score
0.10 × visit_recency_score      (penalise recently visited)
0.05 × competitive_score
```

---

## 7. API Endpoints

### `GET /api/rep/{rep_id}/daily-plan`
Query params: `date`, `max_visits` (default 8)  
Returns: ordered itinerary with priority scores, reason codes, suggested visit type, top SKU to discuss.

### `GET /api/visit/{entity_id}/nba`
Query params: `rep_id`, `date`  
Calls Groq API with structured context. Returns: primary_product, reason, talk_track, agronomic_advice, promo_mechanic, whatsapp_followup flag.

### `GET /api/alerts`
Query params: `territory_id`, `severity` (low/medium/high)  
Returns: demand spikes, stockout risks, NDVI crashes, pest outbreak flags.

### `POST /api/visit/outcome`
Body: rep_id, entity_id, date, outcome (sale/no_purchase/follow_up), products_sold, qty_sold, notes  
Logs to SQLite for outcome learning.

### `GET /api/analytics/territory/{territory_id}`
Query params: `weeks` (default 4)  
Returns: visit coverage %, conversion rate, top SKUs, unvisited high-priority entities.

### `GET /api/entity/{entity_id}`
Returns: full entity profile with all scoring signals, history, NDVI (farmers), inventory (retailers).

---

## 8. Anomaly Detection Rules

| Anomaly Type | Trigger | Action |
|-------------|---------|--------|
| Demand spike | Rolling 4-week POS > mean + 2σ for retailer+SKU | Flag retailer, cross-sell recommendation |
| Stockout risk | Inventory < 10 units AND district pest_pressure > 60 | Urgent visit + reorder push |
| NDVI crash | Week-on-week NDVI delta < -0.15 | Farmer visits prioritised, disease alert |
| Pest outbreak | pest_pressure > 80 (critical) | All retailers + farmers in district boosted |
| Visit gap | Entity not visited in > 21 days AND priority > 70 | Overdue flag in itinerary |

---

## 9. Groq NBA Prompt Template

```
System: You are a Syngenta agronomic field advisor. 
        Respond ONLY with valid JSON. Be specific and concise.

User:
Entity: {entity_type} in {district}, {state}
Crop: {crop} | Stage: {growth_stage}
Pest: {pest_name} pressure {pest_pressure}/100 ({alert_level})
NDVI: {ndvi_value} (weekly change: {ndvi_delta:+.2f})
Inventory low: {low_stock_skus}
Last purchase: {last_sku} on {last_purchase_date} ({days_since} days ago)
WhatsApp opened: {wa_opened}
Campaign product aligned: {campaign_product}

Return JSON:
{
  "primary_product": str,
  "reason": str (1 sentence, data-grounded),
  "talk_track": str (2 sentences max),
  "agronomic_advice": str (1 sentence),
  "promo_mechanic": str or null,
  "whatsapp_followup": bool
}
```

---

## 10. Outcome Learning

Visit outcomes stored in SQLite `outcomes.db`. Weekly batch job:
- Calculates conversion rate per rep × territory × entity_type
- Adjusts `visit_score` weight if high-visit + low-conversion territory detected
- Flags reps for coaching if conversion rate < 40% sustained over 3 weeks

---

## 11. Implementation Order

1. Synthetic data generators (ndvi_generator.py, pest_generator.py)
2. Scoring engine v2 (scoring_engine.py) with NDVI + pest bulletin signals
3. Data loader (data_loader.py)
4. Route optimizer (route_optimizer.py)
5. Anomaly detector (anomaly_detector.py)
6. NBA engine with Groq (nba_engine.py)
7. Outcome logger (outcome_logger.py)
8. FastAPI routers (daily_plan, nba, alerts, outcomes, analytics)
9. Streamlit dashboard
10. Integration testing + demo data prep
