"""
ML visit-outcome scorer inspired by syngenta-deep.ipynb.

Builds a retailer-week feature matrix matching the notebook's
retailer_week_ml_dataset_final.csv schema, trains a LightGBM
binary classifier (predict: will this retailer drive sales this week?),
and returns probability scores 0-100 per retailer.

Feature set mirrors the notebook:
  inventory, sales, visit activity, NDVI, pest pressure
Model: LightGBM with same hyperparameters (n_estimators=1000, LR=0.05)
Target: retailer's latest-week sales > district median (active retailer)
"""

import logging
import warnings

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

logger = logging.getLogger(__name__)

FEATURE_COLS = [
    "total_inventory", "out_of_stock_skus", "unique_skus", "avg_inventory",
    "weekly_sales_qty", "weekly_sales_value", "unique_products_sold",
    "sales_4w_avg", "sales_growth_4w", "sales_volatility_4w",
    "visit_count", "unique_reps", "grower_meetings", "retailer_meetings",
    "avg_ndvi", "ndvi_change",
    "pest_alert_count", "unique_pest_types", "max_pest_severity", "avg_pest_severity",
]


def _build_features(ds) -> pd.DataFrame:
    retailers = ds.retailers[["retailer_id", "territory_id", "state", "district", "tehsil"]].copy()

    # ── Inventory features (latest week) ──────────────────────────────
    inv_week = ds.inventory["week_end_date"].max()
    inv_agg = (
        ds.inventory[ds.inventory["week_end_date"] == inv_week]
        .groupby("retailer_id")
        .agg(
            total_inventory=("sku_qty", "sum"),
            out_of_stock_skus=("sku_qty", lambda x: (x == 0).sum()),
            unique_skus=("sku_qty", "count"),
            avg_inventory=("sku_qty", "mean"),
        )
        .reset_index()
    )

    # ── Sales features (4-week window) ────────────────────────────────
    cutoff = ds.pos["transaction_date"].max()
    pos_4w = ds.pos[ds.pos["transaction_date"] >= cutoff - pd.Timedelta(weeks=4)]
    pos_weekly = (
        pos_4w.assign(week=pos_4w["transaction_date"].dt.to_period("W"))
        .groupby(["retailer_id", "week"])
        .agg(
            wqty=("sku_qty", "sum"),
            wval=("sku_price", "sum"),
            uprods=("sku_name", "nunique"),
        )
        .reset_index()
    )
    sales_stats = (
        pos_weekly.groupby("retailer_id")
        .agg(
            weekly_sales_qty=("wqty", "mean"),
            weekly_sales_value=("wval", "mean"),
            unique_products_sold=("uprods", "mean"),
            sales_4w_avg=("wqty", "mean"),
            sales_volatility_4w=("wqty", "std"),
        )
        .reset_index()
        .fillna(0)
    )
    latest_wk = pos_weekly["week"].max()
    latest_sales = pos_weekly[pos_weekly["week"] == latest_wk][["retailer_id", "wqty"]]
    prior_avg = (
        pos_weekly[pos_weekly["week"] < latest_wk]
        .groupby("retailer_id")["wqty"].mean()
        .reset_index()
        .rename(columns={"wqty": "prior_avg"})
    )
    growth = latest_sales.merge(prior_avg, on="retailer_id", how="left").fillna(0)
    growth["sales_growth_4w"] = np.where(
        growth["prior_avg"] > 0,
        (growth["wqty"] - growth["prior_avg"]) / (growth["prior_avg"] + 1),
        0,
    )
    sales_stats = sales_stats.merge(
        growth[["retailer_id", "sales_growth_4w"]], on="retailer_id", how="left"
    ).fillna(0)

    # ── Visit activity (4 weeks, aggregated by territory) ─────────────
    v_cutoff = ds.visit_log["visit_date"].max()
    visits_4w = ds.visit_log[ds.visit_log["visit_date"] >= v_cutoff - pd.Timedelta(weeks=4)]
    territory_visit = (
        visits_4w.groupby("territory_id")
        .agg(
            visit_count=("visit_date", "count"),
            unique_reps=("rep_id", "nunique"),
            grower_meetings=("visit_type", lambda x: (x == "grower meeting").sum()),
            retailer_meetings=("visit_type", lambda x: (x == "retailer meeting").sum()),
        )
        .reset_index()
    )

    # ── NDVI (latest week, by district) ───────────────────────────────
    ndvi_week = ds.ndvi["week_end_date"].max()
    ndvi_agg = (
        ds.ndvi[ds.ndvi["week_end_date"] == ndvi_week]
        .groupby("district")
        .agg(avg_ndvi=("ndvi_value", "mean"), ndvi_change=("ndvi_delta", "mean"))
        .reset_index()
    )

    # ── Pest pressure (latest week, by district) ──────────────────────
    pest_week = ds.pest["week_end_date"].max()
    pest_agg = (
        ds.pest[ds.pest["week_end_date"] == pest_week]
        .groupby("district")
        .agg(
            pest_alert_count=("alert_level", lambda x: x.isin(["high", "critical"]).sum()),
            unique_pest_types=("pest_name", "nunique"),
            max_pest_severity=("pest_pressure", "max"),
            avg_pest_severity=("pest_pressure", "mean"),
        )
        .reset_index()
    )

    df = retailers.copy()
    df = df.merge(inv_agg, on="retailer_id", how="left")
    df = df.merge(sales_stats, on="retailer_id", how="left")
    df = df.merge(territory_visit, on="territory_id", how="left")
    df = df.merge(ndvi_agg, on="district", how="left")
    df = df.merge(pest_agg, on="district", how="left")
    return df.fillna(0)


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
    Train LightGBM and return ml_visit_score 0–100 per retailer.
    Falls back to zeros on any error.
    """
    try:
        import lightgbm as lgb

        df = _build_features(ds)
        y = _build_target(ds, df)
        X = df[FEATURE_COLS].astype(float)

        X_tr, X_val, y_tr, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42,
            stratify=y if y.sum() > 10 else None,
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = lgb.LGBMClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=7,
                num_leaves=31,
                subsample=0.8,
                colsample_bytree=0.8,
                class_weight="balanced",
                random_state=42,
                verbose=-1,
            )
            model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)],
                      callbacks=[lgb.early_stopping(30, verbose=False),
                                 lgb.log_evaluation(period=-1)])

        proba = model.predict_proba(X)[:, 1]
        auc = roc_auc_score(y_val, model.predict_proba(X_val)[:, 1])
        logger.info("[ML] LightGBM trained — val AUC %.4f | %d retailers scored", auc, len(df))

        return pd.Series(
            (proba * 100).round(2),
            index=df["retailer_id"],
            name="ml_visit_score",
        )

    except Exception as exc:
        logger.warning("[ML] Scoring failed, using zeros: %s", exc)
        return pd.Series(
            np.zeros(len(ds.retailers)),
            index=ds.retailers["retailer_id"],
            name="ml_visit_score",
        )
