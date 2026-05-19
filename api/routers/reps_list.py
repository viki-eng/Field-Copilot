"""GET /api/reps — all reps with calculated KPIs for the React frontend."""

import json
from datetime import datetime, timedelta

import pandas as pd
from fastapi import APIRouter

from api.main import get_store

router = APIRouter()

_NAMES = [
    "Arjun Sharma", "Priya Patel", "Rahul Singh", "Sunita Yadav", "Vikram Nair",
    "Anjali Gupta", "Rajesh Kumar", "Meera Joshi", "Amit Verma", "Deepa Reddy",
]


@router.get("/reps")
def get_reps():
    ds = get_store()
    scores = ds.priority_scores
    cutoff = ds.visit_log["visit_date"].max()
    month_start = cutoff - pd.Timedelta(days=30)

    reps_out = []
    for i, (_, rep) in enumerate(ds.reps.iterrows()):
        rid = rep["rep_id"]
        tid = rep["territory_id"]

        # Visit counts
        visits_all = ds.visit_log[ds.visit_log["territory_id"] == tid]
        visits_month = visits_all[visits_all["visit_date"] >= month_start]
        visits_week = visits_all[visits_all["visit_date"] >= cutoff - pd.Timedelta(days=7)]
        total_visits = len(visits_month)
        visits_today = len(visits_all[visits_all["visit_date"] == cutoff])

        # Revenue (POS for territory retailers)
        ter_retailers = ds.retailers[ds.retailers["territory_id"] == tid]["retailer_id"].tolist()
        pos_month = ds.pos[
            (ds.pos["retailer_id"].isin(ter_retailers)) &
            (ds.pos["transaction_date"] >= month_start)
        ]
        mtd_revenue = int(pos_month["sku_price"].sum()) if not pos_month.empty else 0
        avg_order = int(pos_month["sku_price"].mean()) if not pos_month.empty else 0

        # Scores for territory
        ter_scores = scores[scores["territory_id"] == tid]
        avg_score = float(ter_scores["final_priority_score"].mean()) if not ter_scores.empty else 50

        # Trend based on recent vs prior visit activity
        visits_prior = visits_all[
            (visits_all["visit_date"] >= month_start - pd.Timedelta(days=30)) &
            (visits_all["visit_date"] < month_start)
        ]
        trend = "up" if len(visits_month) >= len(visits_prior) else "down"

        conv = min(90, max(40, int(avg_score * 0.8)))

        tehsil_list = []
        try:
            raw = rep["tehsil_list"]
            tehsil_list = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            pass

        name = _NAMES[i % len(_NAMES)]
        initials = "".join(p[0].upper() for p in name.split()[:2])

        reps_out.append({
            "id": rid,
            "name": name,
            "initials": initials,
            "territory": rep["territory_name"],
            "territory_id": tid,
            "district": rep["district"],
            "state": rep["state"],
            "tehsil_count": len(tehsil_list),
            "status": "active" if visits_today > 0 else ("idle" if total_visits > 0 else "offline"),
            "current_location": rep["district"],
            "visits_today": int(visits_today),
            "visits_target": 7,
            "visits_this_month": int(total_visits),
            "conversion_rate": conv / 100,
            "mtd_revenue": mtd_revenue,
            "avg_order_value": avg_order,
            "ai_adoption": min(95, max(30, int(avg_score))),
            "trend": trend,
        })

    return sorted(reps_out, key=lambda x: x["mtd_revenue"], reverse=True)
