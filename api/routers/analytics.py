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

    visited_tehsils = ds.visit_log[
        (ds.visit_log["territory_id"] == territory_id) &
        (ds.visit_log["visit_date"] >= ds.visit_log["visit_date"].max() - pd.Timedelta(weeks=weeks))
    ]["visit_tehsil"].unique()

    ter_retailer_df = ds.retailers[ds.retailers["territory_id"] == territory_id]
    unvisited = ter_retailer_df[~ter_retailer_df["tehsil"].isin(visited_tehsils)]["retailer_id"].tolist()
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
