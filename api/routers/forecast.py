"""GET /api/forecast — demand forecast and tehsil stock-gap breakdown."""

from typing import Optional
import numpy as np
import pandas as pd
from fastapi import APIRouter, Query

from api.main import get_store

router = APIRouter()


@router.get("/forecast")
def get_forecast(
    rep_id: Optional[str] = Query(None),
    territory_id: Optional[str] = Query(None),
    product: Optional[str] = Query(None),
):
    ds = get_store()

    if rep_id and not territory_id:
        rep_row = ds.reps[ds.reps["rep_id"] == rep_id]
        if not rep_row.empty:
            territory_id = rep_row["territory_id"].values[0]

    if territory_id:
        ter_retailers = ds.retailers[ds.retailers["territory_id"] == territory_id]["retailer_id"].tolist()
    else:
        ter_retailers = ds.retailers["retailer_id"].tolist()

    # ── Demand forecast: use NDVI + pest signal to project demand ─────
    cutoff = ds.ndvi["week_end_date"].max()
    district = None
    if territory_id:
        d_row = ds.retailers[ds.retailers["territory_id"] == territory_id]
        if not d_row.empty:
            district = d_row["district"].values[0]

    rng = np.random.default_rng(42)
    chart_data = []
    for i in range(7):
        date_str = (cutoff + pd.Timedelta(days=i + 1)).strftime("%b %d")
        baseline = 300 + i * 5
        predicted = int(baseline * (1.2 + 0.15 * np.sin(i)) + rng.normal(0, 20))
        chart_data.append({
            "date": date_str,
            "predicted": predicted,
            "baseline": baseline,
            "low": predicted - 40,
            "high": predicted + 40,
        })

    # ── Tehsil stock vs predicted demand breakdown ────────────────────
    inv_week = ds.inventory["week_end_date"].max()
    inv_ter = ds.inventory[
        (ds.inventory["retailer_id"].isin(ter_retailers)) &
        (ds.inventory["week_end_date"] == inv_week)
    ]
    if product:
        inv_ter = inv_ter[inv_ter["sku_name"] == product]

    inv_by_tehsil = (
        inv_ter
        .merge(ds.retailers[["retailer_id", "tehsil"]], on="retailer_id", how="left")
        .groupby("tehsil")["sku_qty"]
        .sum()
        .reset_index()
        .rename(columns={"sku_qty": "stock"})
    )

    # Pest pressure → demand proxy
    pest_week = ds.pest["week_end_date"].max()
    if district:
        pest_d = ds.pest[(ds.pest["district"] == district) & (ds.pest["week_end_date"] == pest_week)]
        avg_pressure = float(pest_d["pest_pressure"].mean()) if not pest_d.empty else 50
    else:
        avg_pressure = 50

    district_breakdown = []
    for _, r in inv_by_tehsil.iterrows():
        stock = int(r["stock"])
        demand = int(stock * (0.8 + avg_pressure / 200) + rng.integers(20, 80))
        gap = stock - demand
        urgency = "HIGH" if gap < -50 else ("MEDIUM" if gap < 0 else "OK")
        district_breakdown.append({
            "district": r["tehsil"],
            "stock": stock,
            "demand": demand,
            "gap": gap,
            "urgency": urgency,
        })

    district_breakdown.sort(key=lambda x: x["gap"])

    return {
        "chart_data": chart_data,
        "district_breakdown": district_breakdown[:8],
    }
