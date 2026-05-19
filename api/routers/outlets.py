"""
/api/outlets — retailers + farmers enriched with priority scores, AI recs, coordinates.
Used by the React frontend MapPage and CustomersPage.
"""

import hashlib
import json
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Query

from api.main import get_store

router = APIRouter()

# District → (lat, lng) from district_centroids.csv loaded at import time
_CENTROIDS: dict = {}


def _load_centroids():
    global _CENTROIDS
    if _CENTROIDS:
        return
    try:
        import os
        from pathlib import Path
        p = Path("data/district_centroids.csv")
        if p.exists():
            df = pd.read_csv(p)
            for _, r in df.iterrows():
                _CENTROIDS[r["district"].lower()] = (float(r["centroid_lat"]), float(r["centroid_lon"]))
    except Exception:
        pass


def _coords(district: str, tehsil: str) -> tuple:
    _load_centroids()
    base = _CENTROIDS.get(district.lower(), (20.5937, 78.9629))
    # Deterministic offset per tehsil so it's stable across calls
    h = int(hashlib.md5(tehsil.encode()).hexdigest()[:8], 16)
    dlat = ((h % 1000) - 500) / 5000
    dlng = ((h // 1000 % 1000) - 500) / 5000
    return (round(base[0] + dlat, 5), round(base[1] + dlng, 5))


def _priority_level(score: float) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 45:
        return "MEDIUM"
    return "LOW"


def _pest_risk(pest_score: float) -> str:
    if pest_score >= 70:
        return "HIGH"
    if pest_score >= 40:
        return "MEDIUM"
    return "LOW"


@router.get("/outlets")
def get_outlets(
    type: Optional[str] = Query(None, description="retailer | farmer"),
    rep_id: Optional[str] = Query(None),
    territory_id: Optional[str] = Query(None),
):
    ds = get_store()
    scores = ds.priority_scores

    # Resolve tehsil_list from rep if provided
    tehsil_filter: Optional[List[str]] = None
    if rep_id:
        rep_row = ds.reps[ds.reps["rep_id"] == rep_id]
        if not rep_row.empty:
            raw = rep_row["tehsil_list"].values[0]
            try:
                tehsil_filter = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                tehsil_filter = []
            if not territory_id:
                territory_id = rep_row["territory_id"].values[0]

    cutoff = ds.visit_log["visit_date"].max()
    results = []

    # ── Retailers ────────────────────────────────────────────────────
    if type in (None, "retailer"):
        retailers = ds.retailers.copy()
        if tehsil_filter:
            retailers = retailers[retailers["tehsil"].isin(tehsil_filter)]
        elif territory_id:
            retailers = retailers[retailers["territory_id"] == territory_id]

        latest_inv_week = ds.inventory["week_end_date"].max()
        inv_latest = (
            ds.inventory[ds.inventory["week_end_date"] == latest_inv_week]
            .groupby("retailer_id")["sku_qty"]
            .agg(total_qty="sum", max_qty="max")
            .reset_index()
        )

        latest_pos = (
            ds.pos.sort_values("transaction_date", ascending=False)
            .groupby("retailer_id")
            .first()
            .reset_index()[["retailer_id", "sku_price", "transaction_date"]]
        )

        last_visit_days = (
            ds.visit_log.groupby("territory_id")["visit_date"]
            .max()
            .reset_index()
            .rename(columns={"visit_date": "last_visit"})
        )

        for _, row in retailers.iterrows():
            rid = row["retailer_id"]
            score_row = scores[(scores["id"] == rid) & (scores["entity_type"] == "retailer")]
            ps = float(score_row["final_priority_score"].values[0]) if not score_row.empty else 0.0
            pest_s = float(score_row["pest_score"].values[0]) if not score_row.empty else 0.0

            inv_row = inv_latest[inv_latest["retailer_id"] == rid]
            total_qty = int(inv_row["total_qty"].values[0]) if not inv_row.empty else 0
            inv_pct = min(100, int(total_qty / 3))  # rough %

            pos_row = latest_pos[latest_pos["retailer_id"] == rid]
            last_order = float(pos_row["sku_price"].values[0]) if not pos_row.empty else 0

            lv_row = last_visit_days[last_visit_days["territory_id"] == row["territory_id"]]
            if not lv_row.empty:
                days_ago = (cutoff - lv_row["last_visit"].values[0]).astype("timedelta64[D]").astype(int)
            else:
                days_ago = 99

            lat, lng = _coords(row["district"], row.get("tehsil", row["district"]))

            low_stock_skus = []
            if not inv_row.empty:
                low = ds.inventory[
                    (ds.inventory["retailer_id"] == rid) &
                    (ds.inventory["week_end_date"] == latest_inv_week) &
                    (ds.inventory["sku_qty"] < 10)
                ]["sku_name"].tolist()
                low_stock_skus = low

            ai_rec = (
                f"Restock urgent: {', '.join(low_stock_skus[:2])}. " if low_stock_skus else ""
            ) + f"Pest pressure {pest_s:.0f}/100 in {row['district']} — check fungicide/pesticide range."
            talking_points = []
            if low_stock_skus:
                talking_points.append(f"{low_stock_skus[0]} critically low stock — trigger reorder")
            if pest_s > 60:
                talking_points.append(f"High pest pressure in district — strong demand likely")
            if days_ago > 14:
                talking_points.append(f"Overdue visit — {days_ago} days since last contact")
            talking_points = talking_points or ["Routine check-in and relationship visit"]

            results.append({
                "id": rid,
                "name": f"Retailer {rid.split('_')[1]}",
                "type": "retailer",
                "lat": lat,
                "lng": lng,
                "tehsil": row.get("tehsil", ""),
                "district": row["district"],
                "territory_id": row["territory_id"],
                "priority_score": round(ps, 1),
                "priority_level": _priority_level(ps),
                "last_visit_days_ago": int(days_ago),
                "last_order_value": round(last_order),
                "inventory_pct": inv_pct,
                "crop_stage": None,
                "pest_risk": _pest_risk(pest_s),
                "ai_recommendation": ai_rec,
                "talking_points": talking_points,
            })

    # ── Farmers ──────────────────────────────────────────────────────
    if type in (None, "farmer"):
        farmers = ds.growers.copy()
        if tehsil_filter:
            farmers = farmers[farmers["tehsil"].isin(tehsil_filter)]

        for _, row in farmers.iterrows():
            gid = row["grower_id"]
            score_row = scores[(scores["id"] == gid) & (scores["entity_type"] == "farmer")]
            ps = float(score_row["final_priority_score"].values[0]) if not score_row.empty else 0.0
            pest_s = float(score_row["pest_score"].values[0]) if not score_row.empty else 0.0

            lat, lng = _coords(row["district"], row.get("tehsil", row["district"]))

            crop = row.get("crop", "unknown")
            stage = row.get("current_stage", "unknown")

            ai_rec = f"{crop.title()} at {stage} stage — {('high' if pest_s > 60 else 'moderate')} pest risk. " + (
                "Recommend fungicide/pesticide advisory visit." if pest_s > 60
                else "Routine agronomic advisory recommended."
            )
            talking_points = [
                f"{crop.title()} at {stage} — discuss crop protection needs",
                f"Pest pressure {pest_s:.0f}/100 in district",
            ]

            results.append({
                "id": gid,
                "name": f"Farmer {gid.split('_')[1]}",
                "type": "farmer",
                "lat": lat,
                "lng": lng,
                "tehsil": row.get("tehsil", ""),
                "district": row["district"],
                "territory_id": "",
                "priority_score": round(ps, 1),
                "priority_level": _priority_level(ps),
                "last_visit_days_ago": 30,
                "last_order_value": 0,
                "inventory_pct": 0,
                "crop_stage": stage,
                "pest_risk": _pest_risk(pest_s),
                "ai_recommendation": ai_rec,
                "talking_points": talking_points,
            })

    results.sort(key=lambda x: x["priority_score"], reverse=True)
    return results
