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
    table = table.merge(
        pest_latest.rename(columns={"pest_score": "_pest_crop"}),
        on=["district", "crop"], how="left"
    )
    # Merge pest for retailers (by district only)
    table = table.merge(
        pest_district.rename(columns={"pest_score": "_pest_district"}),
        on="district", how="left"
    )
    farmers_mask = table["entity_type"] == "farmer"
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
        .drop_duplicates(["district", "crop"])
    )
    table = table.merge(
        ndvi_latest.rename(columns={"ndvi_value": "_ndvi", "ndvi_delta": "_ndvi_delta"}),
        on=["district", "crop"], how="left"
    )
    farmers_mask = table["entity_type"] == "farmer"
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
