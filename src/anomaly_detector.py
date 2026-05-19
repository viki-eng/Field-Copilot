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
    tehsil_list: List[str] = None,
) -> List[Alert]:
    """Detect anomalies for a given territory. Returns list of Alert objects."""
    cutoff = pd.Timestamp(as_of_date) if as_of_date else ds.visit_log["visit_date"].max()
    alerts: List[Alert] = []

    # Retailers scoped to rep's tehsils (or territory fallback)
    if tehsil_list:
        ter_retailers = ds.retailers[
            ds.retailers["tehsil"].isin(tehsil_list)
        ]["retailer_id"].tolist()
    else:
        ter_retailers = ds.retailers[
            ds.retailers["territory_id"] == territory_id
        ]["retailer_id"].tolist()
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
    if pd.notna(pest_district) and pest_district > 60:
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
