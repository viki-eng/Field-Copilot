import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import MinMaxScaler


# =========================================================
# LOAD DATA
# =========================================================

farmers = pd.read_csv("/content/growers.csv")

reps = pd.read_csv("/content/reps_territory.csv")

rets = pd.read_csv("/content/retailers.csv")

wk_inven = pd.read_csv("/content/retailer_inventory_weekly.csv")

ret_pos = pd.read_csv("/content/retailer_pos.csv")

ret_vist_log = pd.read_csv("/content/retailer_visit_log.csv")

whats_camp = pd.read_csv("/content/whatsapp_campaign.csv")

funnel = pd.read_csv("/content/digital_funnel_weekly.csv")

wethr = pd.read_csv("/content/weather_by_district.csv")


# =========================================================
# MASTER ENTITY TABLE
# =========================================================

farmers_table = pd.DataFrame({
    "id": farmers["grower_id"],
    "entity_type": "farmer",
    "district": farmers["district"],
    "territory_id": np.nan
})

retailers_table = pd.DataFrame({
    "id": rets["retailer_id"],
    "entity_type": "retailer",
    "district": rets["district"],
    "territory_id": rets["territory_id"]
})

table = pd.concat(
    [farmers_table, retailers_table],
    ignore_index=True
)


# =========================================================
# WEATHER AGGREGATION
# =========================================================

latest_weather = (
    wethr
    .sort_values("date")
    .groupby("district")
    .tail(7)
)

weather_agg = latest_weather.groupby("district").agg({
    "temp_c": "mean",
    "rain_mm": "mean",
    "humidity": "mean"
}).reset_index()


# =========================================================
# NORMALIZE WEATHER FEATURES
# =========================================================

weather_agg["temp_norm"] = (
    (weather_agg["temp_c"] - weather_agg["temp_c"].min()) /
    (weather_agg["temp_c"].max() - weather_agg["temp_c"].min())
)

weather_agg["rain_norm"] = (
    (weather_agg["rain_mm"] - weather_agg["rain_mm"].min()) /
    (weather_agg["rain_mm"].max() - weather_agg["rain_mm"].min())
)

weather_agg["humidity_norm"] = (
    (weather_agg["humidity"] - weather_agg["humidity"].min()) /
    (weather_agg["humidity"].max() - weather_agg["humidity"].min())
)


# =========================================================
# WEATHER SCORE
# =========================================================

weather_agg["weather_score"] = (
    30 * weather_agg["temp_norm"] +
    40 * weather_agg["rain_norm"] +
    30 * weather_agg["humidity_norm"]
)


# =========================================================
# PEST SCORE
# =========================================================

weather_agg["pest_score"] = (
    (
        0.5 * weather_agg["humidity_norm"] +
        0.5 * weather_agg["rain_norm"]
    ) * 100
)


# =========================================================
# MERGE WEATHER + PEST
# =========================================================

table = table.merge(
    weather_agg[[
        "district",
        "weather_score",
        "pest_score"
    ]],
    on="district",
    how="left"
)


# =========================================================
# INVENTORY SCORE
# =========================================================

latest_inventory = (
    wk_inven
    .sort_values("week_end_date")
    .groupby(["retailer_id", "sku_name"])
    .tail(1)
)

inventory_total = latest_inventory.groupby(
    "retailer_id"
)["sku_qty"].sum().reset_index()

inventory_total["inventory_norm"] = (
    (
        inventory_total["sku_qty"] -
        inventory_total["sku_qty"].min()
    ) /
    (
        inventory_total["sku_qty"].max() -
        inventory_total["sku_qty"].min()
    )
)

# lower inventory = higher urgency
inventory_total["inventory_score"] = (
    (1 - inventory_total["inventory_norm"]) * 100
)

inventory_total.columns = [
    "id",
    "total_inventory",
    "inventory_norm",
    "inventory_score"
]

table = table.merge(
    inventory_total[[
        "id",
        "inventory_score"
    ]],
    on="id",
    how="left"
)

table["inventory_score"] = (
    table["inventory_score"]
    .fillna(0)
)


# =========================================================
# PURCHASE HISTORY SCORE
# =========================================================

sales = ret_pos.groupby("retailer_id").agg({
    "sku_qty": "sum"
}).reset_index()

sales.columns = [
    "id",
    "total_sales"
]

sales["purchase_history_score"] = (
    (
        sales["total_sales"] -
        sales["total_sales"].min()
    ) /
    (
        sales["total_sales"].max() -
        sales["total_sales"].min()
    )
) * 100

table = table.merge(
    sales[[
        "id",
        "purchase_history_score"
    ]],
    on="id",
    how="left"
)

table["purchase_history_score"] = (
    table["purchase_history_score"]
    .fillna(0)
)


# =========================================================
# VISIT SCORE
# =========================================================

visit_counts = (
    ret_vist_log
    .groupby("territory_id")
    .size()
    .reset_index(name="visit_count")
)

visit_counts["visit_score"] = (
    (
        visit_counts["visit_count"] -
        visit_counts["visit_count"].min()
    ) /
    (
        visit_counts["visit_count"].max() -
        visit_counts["visit_count"].min()
    )
) * 100

table = table.merge(
    visit_counts[[
        "territory_id",
        "visit_score"
    ]],
    on="territory_id",
    how="left"
)

table["visit_score"] = (
    table["visit_score"]
    .fillna(0)
)


# =========================================================
# COMPETITIVE SCORE
# =========================================================

visit_by_territory = (
    ret_vist_log
    .groupby("territory_id")
    .size()
    .reset_index(name="visits")
)

sales_by_retailer = (
    ret_pos
    .groupby("retailer_id")["sku_qty"]
    .sum()
    .reset_index()
)

sales_by_retailer = sales_by_retailer.merge(
    rets[["retailer_id", "territory_id"]],
    on="retailer_id",
    how="left"
)

sales_by_territory = (
    sales_by_retailer
    .groupby("territory_id")["sku_qty"]
    .sum()
    .reset_index(name="sales")
)

comp = visit_by_territory.merge(
    sales_by_territory,
    on="territory_id",
    how="left"
)

comp["sales"] = comp["sales"].fillna(0)

comp["sales_per_visit"] = (
    comp["sales"] / (comp["visits"] + 1)
)

threshold = comp["sales_per_visit"].median()

comp["competitive_score"] = np.where(
    comp["sales_per_visit"] < threshold,
    80,
    30
)

table = table.merge(
    comp[[
        "territory_id",
        "competitive_score"
    ]],
    on="territory_id",
    how="left"
)

table["competitive_score"] = (
    table["competitive_score"]
    .fillna(0)
)


# =========================================================
# GROWTH STAGE EXTRACTION
# =========================================================

def extract_stage(calendar_json):

    try:

        data = json.loads(calendar_json)

        stages = data.get("stages", [])

        if len(stages) > 0:
            return stages[-1]["stage"]

        return "unknown"

    except:
        return "unknown"


farmers["current_stage"] = (
    farmers["grower_crop_calendar"]
    .apply(extract_stage)
)

growth = farmers[[
    "grower_id",
    "current_stage"
]]

growth.columns = [
    "id",
    "current_stage"
]

table = table.merge(
    growth,
    on="id",
    how="left"
)


# =========================================================
# GROWTH SCORE
# =========================================================

growth_map = {
    "seedling": 35,
    "vegetative": 55,
    "tillering": 70,
    "flowering": 95,
    "fruiting": 85,
    "pod_formation": 75,
    "maturity": 40,
    "harvest": 20,
    "unknown": 30
}

table["growth_score"] = (
    table["current_stage"]
    .map(growth_map)
    .fillna(30)
)

# retailers do not have growth stage
table.loc[
    table["entity_type"] == "retailer",
    "growth_score"
] = 0


# =========================================================
# WEATHER + GROWTH BONUS
# =========================================================

table["weather_growth_bonus"] = np.where(
    (
        table["growth_score"] > 80
    ) &
    (
        table["pest_score"] > 70
    ),
    15,
    0
)


# =========================================================
# ENTITY BONUS
# =========================================================

table["entity_bonus"] = np.where(
    table["entity_type"] == "retailer",
    12,
    0
)


# =========================================================
# RAW PRIORITY SCORE
# =========================================================

def calc_raw_score(row):

    if row["entity_type"] == "farmer":

        base = (
            0.30 * row["weather_score"] +
            0.30 * row["pest_score"] +
            0.35 * row["growth_score"] +
            0.05 * row["weather_growth_bonus"]
        )

    else:

        base = (
            0.20 * row["weather_score"] +
            0.20 * row["pest_score"] +
            0.30 * row["inventory_score"] +
            0.15 * row["purchase_history_score"] +
            0.10 * row["visit_score"] +
            0.05 * row["competitive_score"]
        )

    return base + row["entity_bonus"]


table["raw_priority_score"] = (
    table.apply(calc_raw_score, axis=1)
)


# =========================================================
# ADD SMALL RANDOM NOISE
# =========================================================

np.random.seed(42)

table["raw_priority_score"] += np.random.normal(
    0,
    1.5,
    len(table)
)


# =========================================================
# GLOBAL NORMALIZATION
# =========================================================

scaler = MinMaxScaler(feature_range=(0, 100))

table["final_priority_score"] = scaler.fit_transform(
    table[["raw_priority_score"]]
)


# =========================================================
# SORT
# =========================================================

table = table.sort_values(
    "final_priority_score",
    ascending=False
)


# =========================================================
# RESET INDEX
# =========================================================

table = table.reset_index(drop=True)


# =========================================================
# FINAL OUTPUT
# =========================================================

print(table.head())

print("\n")

print(table["final_priority_score"].describe())


# =========================================================
# SAVE
# =========================================================

table.to_csv(
    "/content/priority_score_table.csv",
    index=False
)