"""
Next Best Action engine powered by Groq API.

Assembles a structured context packet from all data signals,
sends it to llama-3.3-70b-versatile via Groq,
and returns a validated JSON recommendation.
"""

import json
import os

import pandas as pd
from dotenv import load_dotenv
from groq import Groq

from src.data_loader import DataStore

load_dotenv()

_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


def _build_context(
    entity_id: str,
    ds: DataStore,
    priority_scores: pd.DataFrame,
    as_of_date: str = None,
) -> dict:
    """Build structured context dict for the entity."""
    cutoff = pd.Timestamp(as_of_date) if as_of_date else pd.Timestamp.now()

    is_retailer = entity_id.startswith("RTL")
    is_farmer = entity_id.startswith("GRW")

    ctx = {"entity_id": entity_id, "entity_type": "retailer" if is_retailer else "farmer"}

    score_row = priority_scores[priority_scores["id"] == entity_id]
    ctx["priority_score"] = (
        float(score_row["final_priority_score"].values[0]) if not score_row.empty else 0.0
    )
    ctx["district"] = score_row["district"].values[0] if not score_row.empty else "unknown"

    if is_retailer:
        ret_row = ds.retailers[ds.retailers["retailer_id"] == entity_id]
        ctx["state"] = ret_row["state"].values[0] if not ret_row.empty else "unknown"
        ctx["tehsil"] = ret_row["tehsil"].values[0] if not ret_row.empty else "unknown"

        # Latest inventory
        inv = (
            ds.inventory[
                (ds.inventory["retailer_id"] == entity_id) &
                (ds.inventory["week_end_date"] == ds.inventory["week_end_date"].max())
            ][["sku_name", "sku_qty"]]
            .sort_values("sku_qty")
            .to_dict("records")
        )
        ctx["inventory"] = inv

        # Last 3 POS transactions
        last_pos = (
            ds.pos[ds.pos["retailer_id"] == entity_id]
            .sort_values("transaction_date", ascending=False)
            .head(3)[["sku_name", "sku_qty", "transaction_date"]]
            .to_dict("records")
        )
        ctx["recent_purchases"] = last_pos
        ctx["days_since_last_purchase"] = (
            int((cutoff - pd.Timestamp(last_pos[0]["transaction_date"])).days)
            if last_pos else 999
        )

    if is_farmer:
        grw_row = ds.growers[ds.growers["grower_id"] == entity_id]
        if not grw_row.empty:
            ctx["crop"] = grw_row["crop"].values[0]
            ctx["growth_stage"] = grw_row["current_stage"].values[0]
            ctx["farm_size_acres"] = float(grw_row["grower_farm_size"].values[0])
            ctx["state"] = grw_row["state"].values[0]

        # NDVI
        ndvi_row = ds.ndvi[
            (ds.ndvi["district"] == ctx["district"]) &
            (ds.ndvi["crop"] == ctx.get("crop", "")) &
            (ds.ndvi["week_end_date"] == ds.ndvi["week_end_date"].max())
        ]
        ctx["ndvi"] = float(ndvi_row["ndvi_value"].values[0]) if not ndvi_row.empty else None
        ctx["ndvi_delta"] = float(ndvi_row["ndvi_delta"].values[0]) if not ndvi_row.empty else None

        # WhatsApp engagement
        wa = ds.whatsapp[ds.whatsapp["grower_id"] == entity_id]
        ctx["whatsapp_opened"] = bool(wa["opened_status"].any()) if not wa.empty else False

    # Pest pressure for district
    pest_row = (
        ds.pest[
            (ds.pest["district"] == ctx["district"]) &
            (ds.pest["week_end_date"] == ds.pest["week_end_date"].max())
        ]
        .sort_values("pest_pressure", ascending=False)
        .head(1)
    )
    if not pest_row.empty:
        ctx["top_pest"] = pest_row["pest_name"].values[0]
        ctx["pest_pressure"] = float(pest_row["pest_pressure"].values[0])
        ctx["pest_alert_level"] = pest_row["alert_level"].values[0]
    else:
        ctx["top_pest"] = "unknown"
        ctx["pest_pressure"] = 0
        ctx["pest_alert_level"] = "low"

    return ctx


_SYSTEM_PROMPT = """\
You are an expert Syngenta agronomic field advisor helping a field sales representative.
Respond ONLY with valid JSON — no explanation, no markdown, no extra text.
Be specific and data-grounded. Use numbers from the context.

RULES:
1. restock_sku: if any SKU in inventory has qty < 10, set this to that SKU name (lowest qty first). Otherwise null.
2. restock_reason: 1 sentence explaining urgency of restocking (cite qty and pest/demand context). Only if restock_sku is set.
3. upsell_product: a DIFFERENT Syngenta product the rep should cross-sell based on crop stage, pest pressure, or season.
4. upsell_reason: 1 sentence why this upsell fits right now (cite pest pressure or crop stage data).
5. talk_track: 2 sentences — open with restock urgency if applicable, then pitch the upsell.
6. agronomic_advice: 1 actionable tip for the farmer/retailer's specific crop and stage."""

_USER_TEMPLATE = """\
Entity visit context:
{context_json}

Return exactly this JSON structure:
{{
  "restock_sku": "<SKU name with qty < 10, or null>",
  "restock_reason": "<why urgent to restock, or null>",
  "upsell_product": "<cross-sell Syngenta product different from restock_sku>",
  "upsell_reason": "<1 sentence why this upsell fits now>",
  "talk_track": "<2 sentences — restock urgency first if applicable, then upsell pitch>",
  "agronomic_advice": "<1 actionable agronomic tip>",
  "promo_mechanic": "<promotional offer or null>",
  "whatsapp_followup": <true|false>
}}"""


def get_nba(
    entity_id: str,
    ds: DataStore,
    priority_scores: pd.DataFrame,
    as_of_date: str = None,
) -> dict:
    """
    Get next best action for a visit.
    Returns dict with keys: primary_product, reason, talk_track,
                            agronomic_advice, promo_mechanic, whatsapp_followup.
    Falls back to rule-based response if Groq call fails.
    """
    ctx = _build_context(entity_id, ds, priority_scores, as_of_date)

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _USER_TEMPLATE.format(
                    context_json=json.dumps(ctx, indent=2, default=str)
                )},
            ],
            temperature=0.3,
            max_tokens=400,
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception as exc:
        low_stock = next(
            (i["sku_name"] for i in ctx.get("inventory", []) if i.get("sku_qty", 99) < 10),
            None,
        )
        return {
            "restock_sku": low_stock,
            "restock_reason": (
                f"{low_stock} has critically low stock; district pest pressure "
                f"{ctx.get('pest_pressure', 0):.0f}/100 will drive demand." if low_stock else None
            ),
            "upsell_product": "Score 250 EC",
            "upsell_reason": f"High pest pressure ({ctx.get('pest_pressure', 0):.0f}/100) in {ctx['district']} — fungicide demand likely.",
            "talk_track": (
                f"{'Urgent: ' + low_stock + ' is nearly out of stock. ' if low_stock else ''}"
                "Given current pest pressure in your area, ensure your fungicide range is fully stocked — farmers will need it soon."
            ),
            "agronomic_advice": "Apply fungicide at early disease onset for best efficacy.",
            "promo_mechanic": None,
            "whatsapp_followup": ctx.get("whatsapp_opened", False),
            "_fallback": True,
            "_error": str(exc),
        }
