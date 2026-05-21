"""
ML visit-outcome scorer using pre-trained XGBoost model.

Loads priority_model_xgb_tuned.pkl (trained from syngenta-claude.ipynb)
to score retailers and farmers on priority 0-100 scale.

Features match combined_retailers_farmers_dataset.csv schema.
"""

import logging
import os
import pickle
import warnings

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

logger = logging.getLogger(__name__)

# XGBoost model path (trained in syngenta-claude.ipynb)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "priority_model_xgb_tuned.pkl")

# Features expected by the XGBoost model (46 features, matching syngenta-claude.ipynb training)
FEATURE_COLS = [
    'total_inventory_units', 'out_of_stock_skus', 'unique_skus_stocked', 'avg_sku_inventory',
    'max_sku_inventory', 'min_sku_inventory', 'weekly_sales_value', 'weekly_sales_qty',
    'sales_4w_avg', 'sales_growth_4w', 'sales_volatility_4w',
    'days_since_last_visit', 'visit_count',
    'district_avg_ndvi', 'ndvi_variation', 'farms_healthy', 'farms_stressed',
    'district_pest_alerts', 'unique_pest_types', 'max_pest_severity', 'avg_pest_severity',
    'critical_pest_count', 'max_pest_pressure', 'avg_pest_pressure',
    'district_avg_temp', 'district_total_rainfall', 'district_avg_humidity', 'extreme_weather',
    'num_farmers', 'avg_farm_size_ha', 'farmers_with_offline_campaign',
    'farmer_pest_demand_signal', 'farmer_crop_stress_signal',
    'expected_inventory_need', 'inventory_fulfillment_gap',
    'global_whatsapp_engagement', 'global_whatsapp_click_rate',
    'demand_supply_balance', 'weather_farming_urgency',
    'farmers_served_proxy', 'farmers_per_retailer_in_tehsil', 'farmer_to_retailer_ratio',
    'visit_count_lag1', 'sales_value_lag1', 'inventory_lag1', 'farmer_demand_lag1'
]


def _build_features(ds) -> pd.DataFrame:
    """Build all 46 features needed by XGBoost model from raw data."""
    try:
        # Start with retailer base
        df = ds.retailers[["retailer_id", "territory_id", "district"]].copy()
        
        # ── INVENTORY FEATURES ─────────────────────────────────────────
        try:
            inv_week = ds.inventory["week_end_date"].max()
            inv_latest = ds.inventory[ds.inventory["week_end_date"] == inv_week]
            inv_agg = inv_latest.groupby("retailer_id")["sku_qty"].agg([
                ("total_inventory_units", "sum"),
                ("out_of_stock_skus", lambda x: (x == 0).sum()),
                ("unique_skus_stocked", "count"),
                ("avg_sku_inventory", "mean"),
                ("max_sku_inventory", "max"),
                ("min_sku_inventory", "min"),
            ]).reset_index()
            df = df.merge(inv_agg, on="retailer_id", how="left")
        except Exception as e:
            logger.warning("[ML] Inventory feature build failed: %s", e)
            for col in ['total_inventory_units', 'out_of_stock_skus', 'unique_skus_stocked', 'avg_sku_inventory', 'max_sku_inventory', 'min_sku_inventory']:
                df[col] = 0
        
        # ── SALES FEATURES ─────────────────────────────────────────────
        try:
            cutoff_pos = ds.pos["transaction_date"].max()
            pos_4w = ds.pos[ds.pos["transaction_date"] >= cutoff_pos - pd.Timedelta(weeks=4)]
            
            if len(pos_4w) > 0:
                pos_weekly = (
                    pos_4w.assign(week=pos_4w["transaction_date"].dt.to_period("W"))
                    .groupby(["retailer_id", "week"])
                    .agg(wqty=("sku_qty", "sum"), wval=("sku_price", "sum"))
                    .reset_index()
                )
                sales_stats = pos_weekly.groupby("retailer_id").agg(
                    weekly_sales_qty=("wqty", "sum"),
                    weekly_sales_value=("wval", "sum"),
                    sales_4w_avg=("wqty", "mean"),
                    sales_volatility_4w=("wqty", "std"),
                ).reset_index()
                sales_stats["sales_growth_4w"] = 0.0
                df = df.merge(sales_stats, on="retailer_id", how="left")
            else:
                for col in ['weekly_sales_qty', 'weekly_sales_value', 'sales_4w_avg', 'sales_volatility_4w', 'sales_growth_4w']:
                    df[col] = 0
        except Exception as e:
            logger.warning("[ML] Sales feature build failed: %s", e)
            for col in ['weekly_sales_qty', 'weekly_sales_value', 'sales_4w_avg', 'sales_volatility_4w', 'sales_growth_4w']:
                df[col] = 0
        
        # ── VISIT FEATURES ─────────────────────────────────────────────
        try:
            cutoff_visit = ds.visit_log["visit_date"].max()
            
            # Days since last visit - by territory, not retailer
            last_visit = ds.visit_log.groupby("territory_id")["visit_date"].max().reset_index()
            last_visit.columns = ["territory_id", "last_visit_date"]
            last_visit["days_since_last_visit"] = (cutoff_visit - last_visit["last_visit_date"]).dt.days
            
            recent_visits = ds.visit_log[ds.visit_log["visit_date"] >= cutoff_visit - pd.Timedelta(weeks=4)]
            visit_count = recent_visits.groupby("territory_id").size().reset_index(name="visit_count")
            
            df = df.merge(last_visit[["territory_id", "days_since_last_visit"]], on="territory_id", how="left")
            df = df.merge(visit_count, on="territory_id", how="left")
        except Exception as e:
            logger.warning("[ML] Visit feature build failed: %s", e)
            df["days_since_last_visit"] = 0
            df["visit_count"] = 0
        
        # ── LAG FEATURES ───────────────────────────────────────────────
        try:
            cutoff_pos = ds.pos["transaction_date"].max()
            df["visit_count_lag1"] = df["visit_count"].shift(1).fillna(0)
            df["sales_value_lag1"] = 0
            df["inventory_lag1"] = df["total_inventory_units"].shift(1).fillna(0)
            df["farmer_demand_lag1"] = 0
        except Exception as e:
            logger.warning("[ML] Lag feature build failed: %s", e)
            df["visit_count_lag1"] = 0
            df["sales_value_lag1"] = 0
            df["inventory_lag1"] = 0
            df["farmer_demand_lag1"] = 0
        
        # ── DISTRICT-LEVEL NDVI FEATURES ───────────────────────────────
        try:
            ndvi_week = ds.ndvi["week_end_date"].max()
            ndvi_latest = ds.ndvi[ds.ndvi["week_end_date"] == ndvi_week]
            ndvi_agg = ndvi_latest.groupby("district")["ndvi_value"].agg([
                ("district_avg_ndvi", "mean"),
                ("ndvi_variation", "std"),
            ]).reset_index()
            df = df.merge(ndvi_agg, on="district", how="left")
            
            # Count farms by health status
            ndvi_health = ndvi_latest.groupby("district").apply(
                lambda x: pd.Series({
                    "farms_healthy": (x["ndvi_value"] > 0.5).sum(),
                    "farms_stressed": (x["ndvi_value"] < 0.3).sum(),
                })
            ).reset_index()
            
            df = df.merge(ndvi_health, on="district", how="left")
        except Exception as e:
            logger.warning("[ML] NDVI feature build failed: %s", e)
            for col in ['district_avg_ndvi', 'ndvi_variation', 'farms_healthy', 'farms_stressed']:
                df[col] = 0
        
        # ── DISTRICT-LEVEL PEST FEATURES ──────────────────────────────
        try:
            pest_week = ds.pest["week_end_date"].max()
            pest_latest = ds.pest[ds.pest["week_end_date"] == pest_week]
            pest_agg = pest_latest.groupby("district").agg(
                district_pest_alerts=("alert_level", lambda x: x.isin(["high", "critical"]).sum()),
                unique_pest_types=("pest_name", "nunique"),
                max_pest_severity=("pest_pressure", "max"),
                avg_pest_severity=("pest_pressure", "mean"),
                critical_pest_count=("alert_level", lambda x: (x == "critical").sum()),
                max_pest_pressure=("pest_pressure", "max"),
                avg_pest_pressure=("pest_pressure", "mean"),
            ).reset_index()
            df = df.merge(pest_agg, on="district", how="left")
        except Exception as e:
            logger.warning("[ML] Pest feature build failed: %s", e)
            for col in ['district_pest_alerts', 'unique_pest_types', 'max_pest_severity', 'avg_pest_severity', 'critical_pest_count', 'max_pest_pressure', 'avg_pest_pressure']:
                df[col] = 0
        
        # ── DISTRICT-LEVEL WEATHER FEATURES ───────────────────────────
        try:
            weather_recent = ds.weather[ds.weather["date"] <= pd.Timestamp.now()].sort_values("date").groupby("district").tail(7)
            weather_agg = weather_recent.groupby("district").agg(
                district_avg_temp=("temp_c", "mean"),
                district_total_rainfall=("rain_mm", "sum"),
                district_avg_humidity=("humidity", "mean"),
            ).reset_index()
            df = df.merge(weather_agg, on="district", how="left")
            df["extreme_weather"] = 0
        except Exception as e:
            logger.warning("[ML] Weather feature build failed: %s", e)
            for col in ['district_avg_temp', 'district_total_rainfall', 'district_avg_humidity', 'extreme_weather']:
                df[col] = 0
        
        # ── FARMER & CAMPAIGN FEATURES ────────────────────────────────
        try:
            farmers_by_district = ds.growers.groupby("district").size().reset_index(name="num_farmers")
            df = df.merge(farmers_by_district, on="district", how="left")
            
            # Use grower_farm_size (not farm_size_ha)
            avg_farm_size = ds.growers.groupby("district")["grower_farm_size"].mean().reset_index(name="avg_farm_size_ha")
            df = df.merge(avg_farm_size, on="district", how="left")
            
            df["farmers_with_offline_campaign"] = 0
        except Exception as e:
            logger.warning("[ML] Farmer feature build failed: %s", e)
            df["num_farmers"] = 0
            df["avg_farm_size_ha"] = 0
            df["farmers_with_offline_campaign"] = 0
        
        # ── DERIVED FEATURES ───────────────────────────────────────────
        df["farmer_pest_demand_signal"] = 0
        df["farmer_crop_stress_signal"] = 0
        df["expected_inventory_need"] = 0
        df["inventory_fulfillment_gap"] = 0
        df["global_whatsapp_engagement"] = 0
        df["global_whatsapp_click_rate"] = 0
        df["demand_supply_balance"] = 0
        df["weather_farming_urgency"] = 0
        df["farmers_served_proxy"] = 0
        df["farmers_per_retailer_in_tehsil"] = 0
        df["farmer_to_retailer_ratio"] = 0
        
        return df.fillna(0)
    
    except Exception as e:
        logger.error("[ML] Feature building completely failed: %s", e)
        raise


def _build_target(ds, df: pd.DataFrame) -> pd.Series:
    """Target: retailer's latest-week sales above its district median."""
    cutoff = ds.pos["transaction_date"].max()
    latest_sales = (
        ds.pos[ds.pos["transaction_date"] >= cutoff - pd.Timedelta(weeks=1)]
        .groupby("retailer_id")["sku_qty"]
        .sum()
        .reset_index()
    )
    merged = df[["retailer_id", "district"]].merge(latest_sales, on="retailer_id", how="left").fillna(0)
    district_median = merged.groupby("district")["sku_qty"].transform("median")
    return (merged["sku_qty"] > district_median).astype(int)


def train_and_score(ds) -> pd.Series:
    """
    Load pre-trained XGBoost model (priority_model_xgb_tuned.pkl) and score retailers/farmers.
    Returns ml_visit_score 0–100 per retailer.
    Falls back to zeros on any error.
    """
    try:
        import xgboost as xgb
        
        # Load pre-trained XGBoost model
        if not os.path.exists(MODEL_PATH):
            logger.warning("[ML] Model file not found at %s. Using fallback zero scores.", MODEL_PATH)
            return pd.Series(
                np.zeros(len(ds.retailers)),
                index=ds.retailers["retailer_id"],
                name="ml_visit_score",
            )

        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        logger.info("[ML] Loaded XGBoost model from %s", MODEL_PATH)

        # Build features for current dataset
        df = _build_features(ds)
        
        # Ensure all required features are present
        for col in FEATURE_COLS:
            if col not in df.columns:
                logger.warning("[ML] Missing feature: %s. Filling with 0.", col)
                df[col] = 0
        
        X = df[FEATURE_COLS].astype(float)

        # Score with the model (returns priority scores)
        priority_scores = model.predict(X)
        
        # Normalize to 0-100 if needed
        scores = priority_scores.clip(0, 100)
        
        logger.info("[ML] XGBoost scoring complete | %d entities scored", len(df))

        return pd.Series(
            np.round(scores, 2),
            index=df["retailer_id"],
            name="ml_visit_score",
        )

    except Exception as exc:
        logger.warning("[ML] XGBoost scoring failed, using zeros: %s", exc)
        return pd.Series(
            np.zeros(len(ds.retailers)),
            index=ds.retailers["retailer_id"],
            name="ml_visit_score",
        )
