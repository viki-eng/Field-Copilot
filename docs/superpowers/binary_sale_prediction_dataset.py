"""
BINARY CLASSIFICATION DATASET: Sale Prediction
===============================================
Predicts: 1 = Sale occurred (weekly_sales_qty > 0), 0 = No sale
Features: 56 features including 7 relationship features linking farmer demand to retailer sales
Target: Binary (0/1) with realistic imbalance (~72% sales, 28% no-sales)

Same structure as combined_retailers_farmers_dataset.py but with binary target instead of continuous.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import RobustScaler
import json
import sys
import joblib

# =====================================================
# SETUP
# =====================================================
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
SYNTHETIC_DIR = BASE_DIR / "synthetic"
OUTPUT_DIR = DATA_DIR / "ml_datasets_binary"
OUTPUT_DIR.mkdir(exist_ok=True)

LOG_FILE = OUTPUT_DIR / "binary_dataset_generation_log.txt"

SEASON_START = "2025-10-01"
SEASON_END = "2026-04-30"

def log_message(msg, level="INFO"):
    """Log with UTF-8 support for Windows"""
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass
    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {level}: {msg}"
    print(full_msg)
    with open(LOG_FILE, "a", encoding='utf-8') as f:
        f.write(full_msg + "\n")

# =====================================================
# LOAD DATASETS
# =====================================================
log_message("\n" + "="*70)
log_message("BINARY CLASSIFICATION DATASET GENERATION")
log_message("="*70)
log_message("\nLoading datasets...")

try:
    retailers = pd.read_csv(DATA_DIR / "retailers.csv")
    growers = pd.read_csv(DATA_DIR / "growers.csv")
    visits = pd.read_csv(DATA_DIR / "retailer_visit_log.csv")
    inventory = pd.read_csv(DATA_DIR / "retailer_inventory_weekly.csv")
    pos = pd.read_csv(DATA_DIR / "retailer_pos.csv")
    weather = pd.read_csv(DATA_DIR / "weather_by_district.csv")
    ndvi = pd.read_csv(SYNTHETIC_DIR / "ndvi_weekly.csv")
    pest = pd.read_csv(SYNTHETIC_DIR / "pest_bulletin_weekly.csv")
    whatsapp = pd.read_csv(DATA_DIR / "whatsapp_campaign.csv")
    digital = pd.read_csv(DATA_DIR / "digital_funnel_weekly.csv")
    
    log_message(f"✓ Retailers: {len(retailers)} records")
    log_message(f"✓ Growers/Farmers: {len(growers)} records")
    log_message(f"✓ Visits: {len(visits)} records")
    log_message(f"✓ Inventory: {len(inventory)} records")
    log_message(f"✓ POS (Sales): {len(pos)} records")
    log_message(f"✓ Weather: {len(weather)} records")
    log_message(f"✓ NDVI: {len(ndvi)} records")
    log_message(f"✓ Pest: {len(pest)} records")
    log_message(f"✓ WhatsApp: {len(whatsapp)} records")
    log_message(f"✓ Digital: {len(digital)} records")
except Exception as e:
    log_message(f"ERROR loading datasets: {e}", "ERROR")
    raise

# =====================================================
# DATE CONVERSIONS & WEEK COLUMNS
# =====================================================
log_message("\nConverting dates and creating week columns...")

weather['date'] = pd.to_datetime(weather['date'], format='%Y%m%d')
weather['week'] = weather['date'].dt.to_period('W').dt.start_time

ndvi['week_end_date'] = pd.to_datetime(ndvi['week_end_date'])
ndvi['week'] = ndvi['week_end_date'].dt.to_period('W').dt.start_time

pest['week_end_date'] = pd.to_datetime(pest['week_end_date'])
pest['week'] = pest['week_end_date'].dt.to_period('W').dt.start_time

visits['visit_date'] = pd.to_datetime(visits['visit_date'])
visits['week'] = visits['visit_date'].dt.to_period('W').dt.start_time

inventory['week_end_date'] = pd.to_datetime(inventory['week_end_date'])
inventory['week'] = inventory['week_end_date'].dt.to_period('W').dt.start_time

pos['transaction_date'] = pd.to_datetime(pos['transaction_date'])
pos['week'] = pos['transaction_date'].dt.to_period('W').dt.start_time

whatsapp['message_sent_date'] = pd.to_datetime(whatsapp['message_sent_date'])
whatsapp['week'] = whatsapp['message_sent_date'].dt.to_period('W').dt.start_time

# Filter to season (Oct 2025 - Apr 2026)
season_start = pd.Timestamp(SEASON_START)
season_end = pd.Timestamp(SEASON_END)

visits = visits[(visits['visit_date'] >= season_start) & (visits['visit_date'] <= season_end)]
inventory = inventory[(inventory['week_end_date'] >= season_start) & (inventory['week_end_date'] <= season_end)]
pos = pos[(pos['transaction_date'] >= season_start) & (pos['transaction_date'] <= season_end)]
weather = weather[(weather['date'] >= season_start) & (weather['date'] <= season_end)]
ndvi = ndvi[(ndvi['week_end_date'] >= season_start) & (ndvi['week_end_date'] <= season_end)]
pest = pest[(pest['week_end_date'] >= season_start) & (pest['week_end_date'] <= season_end)]
whatsapp = whatsapp[(whatsapp['message_sent_date'] >= season_start) & (whatsapp['message_sent_date'] <= season_end)]

log_message(f"Season filtered: {SEASON_START} - {SEASON_END}")

# =====================================================
# FARMER DEMAND SIGNALS (Aggregated by District-Week)
# =====================================================
log_message("\n--- FARMER DEMAND SIGNALS (Aggregated by District-Week) ---")

# Aggregate farmer data by tehsil
farmer_agg = growers.groupby('tehsil').agg(
    num_farmers=('grower_id', 'nunique'),
    avg_farm_size_ha=('grower_farm_size', 'mean'),
    farmers_with_offline_campaign=('offline_campaign_attended', 'sum')
).reset_index()

log_message(f"Aggregated farmer data to {len(farmer_agg)} tehsils")

# NDVI aggregation
ndvi_tehsil = ndvi.merge(growers[['grower_id', 'district']].drop_duplicates(), on='district', how='left')
ndvi_agg = ndvi_tehsil.groupby(['district', 'week']).agg(
    district_avg_ndvi=('ndvi_value', 'mean'),
    ndvi_variation=('ndvi_value', 'std'),
    farms_healthy=('ndvi_value', lambda x: (x > 0.6).sum()),
    farms_stressed=('ndvi_value', lambda x: (x < 0.4).sum())
).reset_index()

log_message(f"Computing farmer demand signals from NDVI...")
log_message(f"Farmer NDVI signals: {len(ndvi_agg)} district-week combinations")

# Pest aggregation
pest_severity_map = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
pest['severity_numeric'] = pest['alert_level'].map(pest_severity_map).fillna(1)

pest_agg = pest.groupby(['district', 'week']).agg(
    district_pest_alerts=('pest_name', 'count'),
    unique_pest_types=('pest_name', 'nunique'),
    max_pest_severity=('severity_numeric', 'max'),
    avg_pest_severity=('severity_numeric', 'mean'),
    critical_pest_count=('severity_numeric', lambda x: (x >= 3).sum()),
    max_pest_pressure=('pest_pressure', 'max'),
    avg_pest_pressure=('pest_pressure', 'mean')
).reset_index()

log_message(f"Computing farmer pest pressure signals...")
log_message(f"Farmer pest signals: {len(pest_agg)} district-week combinations")

# Weather aggregation
weather_agg = (
    weather
    .groupby(['district', 'week'])
    .agg(
        district_avg_temp=('temp_c', 'mean'),
        district_total_rainfall=('rain_mm', 'sum'),
        avg_humidity=('humidity', 'mean'),
        extreme_weather=('temp_c', lambda x: ((x > 40) | (x < 5)).sum())
    )
    .reset_index()
)

log_message(f"Computing weather impact on farmer demand...")
log_message(f"Weather signals: {len(weather_agg)} district-week combinations")

# =====================================================
# RETAILER FEATURES
# =====================================================
log_message("\n--- RETAILER OPERATIONAL DATA ---")

# Inventory features
inventory_features = (
    inventory
    .groupby(['retailer_id', 'week'])
    .agg(
        total_inventory_units=('sku_qty', 'sum'),
        out_of_stock_skus=('sku_qty', lambda x: (x == 0).sum()),
        unique_skus_stocked=('sku_id', 'nunique'),
        avg_sku_inventory=('sku_qty', 'mean'),
        max_sku_inventory=('sku_qty', 'max'),
        min_sku_inventory=('sku_qty', 'min')
    )
    .reset_index()
)

log_message(f"Inventory features: {len(inventory_features)} records")

# Sales features
pos['sales_value'] = pos['sku_qty'] * pos['sku_price']

sales_features = (
    pos
    .groupby(['retailer_id', 'week'])
    .agg(
        weekly_sales_qty=('sku_qty', 'sum'),
        weekly_sales_value=('sales_value', 'sum'),
        unique_products_sold=('sku_id', 'nunique'),
        transaction_count=('sku_id', 'count'),
        avg_item_price=('sku_price', 'mean'),
        avg_item_qty=('sku_qty', 'mean')
    )
    .reset_index()
)

sales_features = sales_features.sort_values(['retailer_id', 'week'])

# Add temporal features with lookahead prevention
sales_features['sales_value_prev_week'] = (
    sales_features.groupby('retailer_id')['weekly_sales_value'].shift(1)
)

sales_features['sales_4w_avg'] = (
    sales_features
    .groupby('retailer_id')['weekly_sales_value']
    .transform(lambda x: x.shift(1).rolling(4, min_periods=1).mean())
)

sales_features['sales_growth_4w'] = (
    (sales_features['weekly_sales_value'] - sales_features['sales_4w_avg']) 
    / (sales_features['sales_4w_avg'] + 1)
)

sales_features['sales_volatility_4w'] = (
    sales_features
    .groupby('retailer_id')['weekly_sales_value']
    .transform(lambda x: x.shift(1).rolling(4, min_periods=1).std())
)

sales_features = sales_features.fillna(0)
log_message(f"Sales features: {len(sales_features)} records")

# Visit features
retailer_territory = retailers[['retailer_id', 'territory_id']].copy()
visits_with_retailers = visits.merge(retailer_territory, on='territory_id', how='left')

visit_features = (
    visits_with_retailers
    .groupby(['retailer_id', 'week'])
    .agg(
        visit_count=('rep_id', 'count'),
        unique_reps=('rep_id', 'nunique'),
    )
    .reset_index()
)

visits_sorted = visits_with_retailers.sort_values(['retailer_id', 'visit_date'])
retailer_last_visit = (
    visits_sorted
    .groupby('retailer_id')['visit_date']
    .max()
    .reset_index()
    .rename(columns={'visit_date': 'last_visit_date'})
)

# Create retailer-week base with all weeks
weeks = pd.date_range(start=SEASON_START, end=SEASON_END, freq='W-MON')
retailer_week_base = retailers[['retailer_id', 'territory_id', 'state', 'district', 'tehsil']].merge(
    pd.DataFrame({'week': weeks}),
    how='cross'
)

# Add visit recency
retailer_week_base = retailer_week_base.merge(retailer_last_visit, on='retailer_id', how='left')
retailer_week_base['days_since_last_visit'] = (
    (retailer_week_base['week'] - retailer_week_base['last_visit_date']).dt.days
).fillna(999)

visit_features_full = retailer_week_base[['retailer_id', 'week', 'days_since_last_visit']].copy()
visit_features_full = visit_features_full.merge(visit_features, on=['retailer_id', 'week'], how='left')

log_message(f"Visit features: {len(visit_features_full)} records")

# =====================================================
# LINK RETAILERS TO FARMERS
# =====================================================
log_message("\n--- LINKING RETAILERS TO FARMERS (THE RELATIONSHIP!) ---")

final_df = retailer_week_base[['retailer_id', 'territory_id', 'state', 'district', 'tehsil', 'week']].copy()

# Merge all features
final_df = final_df.merge(inventory_features, on=['retailer_id', 'week'], how='left')
final_df = final_df.merge(sales_features[['retailer_id', 'week', 'weekly_sales_qty', 'weekly_sales_value', 
                                           'sales_4w_avg', 'sales_growth_4w', 'sales_volatility_4w']],
                          on=['retailer_id', 'week'], how='left')
final_df = final_df.merge(visit_features_full[['retailer_id', 'week', 'days_since_last_visit', 'visit_count']],
                          on=['retailer_id', 'week'], how='left')

final_df = final_df.merge(ndvi_agg, on=['district', 'week'], how='left')
final_df = final_df.merge(pest_agg, on=['district', 'week'], how='left')
final_df = final_df.merge(weather_agg, on=['district', 'week'], how='left')
final_df = final_df.merge(farmer_agg, on='tehsil', how='left')

log_message(f"Linked dataset shape: {final_df.shape}")

# =====================================================
# ENGINEER RELATIONSHIP FEATURES
# =====================================================
log_message("\n--- ENGINEERING RELATIONSHIP FEATURES ---")

# 1. Farmer demand for pest inputs
final_df['farmer_pest_demand_signal'] = (
    final_df['max_pest_severity'] * 15 + 
    final_df['district_pest_alerts'] * 2
).clip(0, 100)

# 2. Farmer crop stress
final_df['farmer_crop_stress_signal'] = (
    (1 - final_df['district_avg_ndvi'].clip(0, 1)) * 50
)

# 3. Expected inventory need
final_df['expected_inventory_need'] = (
    final_df['farmer_pest_demand_signal'] * 0.3 +
    final_df['farmer_crop_stress_signal'] * 0.3 +
    (final_df['weekly_sales_value'] / final_df['weekly_sales_value'].max() * 100).fillna(0) * 0.4
).fillna(0)

# 4. Inventory efficiency
final_df['inventory_fulfillment_gap'] = (
    final_df['expected_inventory_need'] - 
    (final_df['total_inventory_units'] / final_df['total_inventory_units'].max() * 100).fillna(0)
).fillna(0)

# 5. WhatsApp engagement
whatsapp_agg = (
    whatsapp
    .groupby('week')
    .agg(
        global_whatsapp_engagement=('opened_status', 'mean'),
        global_whatsapp_click_rate=('clicked_status', 'mean')
    )
    .reset_index()
)
final_df = final_df.merge(whatsapp_agg, on='week', how='left')

# 6. Demand-supply balance
final_df['demand_supply_balance'] = (
    final_df['weekly_sales_value'] / 
    (final_df['expected_inventory_need'].clip(lower=1))
)

# 7. Weather farming urgency
final_df['weather_farming_urgency'] = (
    (final_df['district_total_rainfall'] / 50).clip(0, 1) * 30 +
    (1 - (final_df['district_avg_temp'] - 15) / 25).clip(0, 1) * 20
)

# 8. Farmer-retailer ratio
final_df['farmers_served_proxy'] = final_df['num_farmers']
final_df['farmers_per_retailer_in_tehsil'] = (
    final_df.groupby(['tehsil', 'week'])['retailer_id'].transform('count')
)
final_df['farmer_to_retailer_ratio'] = (
    final_df['farmers_served_proxy'] / 
    final_df['farmers_per_retailer_in_tehsil'].clip(lower=1)
)

log_message("✓ Engineered 7 relationship features")

# =====================================================
# CREATE BINARY TARGET: SALE OR NO SALE
# =====================================================
log_message("\n--- BINARY TARGET: SALE PREDICTION ---")

final_df['target'] = (final_df['weekly_sales_qty'] > 0).astype(int)

log_message(f"Target distribution:")
log_message(f"  Class 1 (Sale): {(final_df['target'] == 1).sum():,} ({(final_df['target'] == 1).mean()*100:.1f}%)")
log_message(f"  Class 0 (No Sale): {(final_df['target'] == 0).sum():,} ({(1-final_df['target'].mean())*100:.1f}%)")

# =====================================================
# DATA QUALITY CHECKS
# =====================================================
log_message("\n--- DATA QUALITY: COMPLETENESS & BALANCE ---")

numeric_cols = final_df.select_dtypes(include=[np.number]).columns
final_df[numeric_cols] = final_df[numeric_cols].fillna(0)

log_message(f"Total rows: {len(final_df)}")
log_message(f"Total columns: {len(final_df.columns)}")
log_message(f"Null values remaining: {final_df[numeric_cols].isnull().sum().sum()}")

# =====================================================
# ADD LAGGED FEATURES
# =====================================================
log_message("\nAdding lagged features...")

final_df = final_df.sort_values(['retailer_id', 'week'])

final_df['visit_count_lag1'] = final_df.groupby('retailer_id')['visit_count'].shift(1)
final_df['sales_value_lag1'] = final_df.groupby('retailer_id')['weekly_sales_value'].shift(1)
final_df['inventory_lag1'] = final_df.groupby('retailer_id')['total_inventory_units'].shift(1)
final_df['farmer_demand_lag1'] = final_df.groupby('retailer_id')['farmer_pest_demand_signal'].shift(1)

lag_features = [col for col in final_df.columns if 'lag' in col]
final_df[lag_features] = final_df[lag_features].fillna(0)

# =====================================================
# FEATURE SCALING
# =====================================================
log_message("\nApplying RobustScaler...")

categorical_features = ['retailer_id', 'territory_id', 'state', 'district', 'tehsil']
numerical_features = [col for col in final_df.columns 
                      if col not in categorical_features + ['week', 'target', 'last_visit_date']]

for col in categorical_features:
    if col in final_df.columns:
        final_df[col] = final_df[col].astype('category')

scaler = RobustScaler()
final_df[numerical_features] = scaler.fit_transform(final_df[numerical_features])

log_message("✓ Applied RobustScaler to numerical features")

# Save scaler
scaler_path = OUTPUT_DIR / "scaler_binary.pkl"
joblib.dump(scaler, scaler_path)
log_message(f"Scaler saved to: {scaler_path}")

# =====================================================
# SAVE DATASET
# =====================================================
log_message("\n--- SAVING OUTPUTS ---")

output_path = OUTPUT_DIR / "binary_sale_prediction_dataset.csv"
final_df.to_csv(output_path, index=False)
log_message(f"✓ Dataset saved: {output_path.name} ({len(final_df):,} rows × {len(final_df.columns)} columns)")
log_message(f"  File size: {output_path.stat().st_size / 1e6:.1f} MB")

# =====================================================
# METADATA
# =====================================================
metadata = {
    'dataset_name': 'Binary Sale Prediction (Retailers + Farmers)',
    'description': 'Predicts whether a retailer-week will have sales or not',
    'target_variable': 'target (binary: 1=sale, 0=no_sale)',
    'target_distribution': final_df['target'].value_counts().to_dict(),
    'total_rows': len(final_df),
    'total_columns': len(final_df.columns),
    'numerical_features': len(numerical_features),
    'categorical_features': len(categorical_features),
    'relationship_features': [
        'farmer_pest_demand_signal',
        'farmer_crop_stress_signal',
        'expected_inventory_need',
        'inventory_fulfillment_gap',
        'demand_supply_balance',
        'weather_farming_urgency',
        'farmer_to_retailer_ratio'
    ],
    'season': f"{SEASON_START} to {SEASON_END}",
    'null_values': int(final_df[numeric_cols].isnull().sum().sum()),
    'sales_rate': float(final_df['target'].mean())
}

metadata_path = OUTPUT_DIR / "binary_dataset_metadata.json"
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2, default=str)
log_message(f"✓ Metadata saved: {metadata_path.name}")

# Feature relationships
feature_relationships = {
    'farmer_pest_demand_signal': 'Links pest pressure to retailer need for stock',
    'farmer_crop_stress_signal': 'Low NDVI indicates need for farmer inputs',
    'expected_inventory_need': 'Weighted combination of farmer demand + sales',
    'inventory_fulfillment_gap': 'How well retailer stock matches expected need',
    'demand_supply_balance': 'Sales efficiency relative to inventory need',
    'weather_farming_urgency': 'Weather conditions driving farmer activity',
    'farmer_to_retailer_ratio': 'Market coverage proxy'
}

relationships_path = OUTPUT_DIR / "feature_relationships.json"
with open(relationships_path, 'w') as f:
    json.dump(feature_relationships, f, indent=2)

# =====================================================
# FINAL SUMMARY
# =====================================================
log_message("\n" + "="*70)
log_message("✅ BINARY CLASSIFICATION DATASET COMPLETE")
log_message("="*70)

log_message(f"\n📊 DATASET SUMMARY:")
log_message(f"  Shape: {len(final_df):,} rows × {len(final_df.columns)} columns")
log_message(f"  Retailers: {final_df['retailer_id'].nunique():,}")
log_message(f"  Weeks: {final_df['week'].nunique()}")
log_message(f"  Features: {len(numerical_features)} numerical + {len(categorical_features)} categorical")

log_message(f"\n🎯 TARGET VARIABLE:")
log_message(f"  Type: Binary (0 = No Sale, 1 = Sale)")
log_message(f"  Class 0: {(final_df['target'] == 0).sum():,} ({(1-final_df['target'].mean())*100:.1f}%)")
log_message(f"  Class 1: {(final_df['target'] == 1).sum():,} ({final_df['target'].mean()*100:.1f}%)")
log_message(f"  Imbalance: REALISTIC (not balanced) - reflects real retail patterns")

log_message(f"\n📂 OUTPUT FILES:")
log_message(f"  • {output_path.name}")
log_message(f"  • {scaler_path.name}")
log_message(f"  • {metadata_path.name}")
log_message(f"  • {relationships_path.name}")

log_message(f"\n✨ Usage (In Kaggle):")
log_message(f"  1. Load {output_path.name}")
log_message(f"  2. Split into train/val/test")
log_message(f"  3. Train classifier: XGBoost, LightGBM, or CatBoost")
log_message(f"  4. Evaluate with: AUC-ROC, F1, Precision-Recall (for imbalanced data)")
log_message(f"  5. Feature importance: SHAP, permutation, or built-in importance")

log_message("="*70)
