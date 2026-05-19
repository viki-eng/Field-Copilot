from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, Query, HTTPException

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
    for rank, (_, row) in enumerate(routed.iterrows(), start=1):
        itinerary.append(ItineraryItem(
            rank=rank,
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
