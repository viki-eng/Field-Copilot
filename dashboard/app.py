"""
Streamlit rep-facing dashboard.
Run: streamlit run dashboard/app.py
Requires the FastAPI backend running at localhost:8000.
"""

import httpx
import streamlit as st
import pandas as pd

API_BASE = "http://localhost:8000/api"

st.set_page_config(page_title="Syngenta Field Co-pilot", page_icon="🌾", layout="wide")
st.title("🌾 Syngenta Field Co-pilot")

# ── Sidebar ────────────────────────────────────────────────────────
st.sidebar.header("Field Rep")
rep_id = st.sidebar.text_input("Rep ID", value="REP_0001")
visit_date = st.sidebar.date_input("Date")
max_visits = st.sidebar.slider("Max visits today", 3, 15, 8)


def _load_profile(rid: str):
    try:
        r = httpx.get(f"{API_BASE}/rep/{rid}/profile", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


if st.sidebar.button("Load My Plan", type="primary") or st.session_state.get("rep_id") != rep_id:
    profile = _load_profile(rep_id)
    if profile:
        st.session_state["profile"] = profile
        st.session_state["rep_id"] = rep_id
        st.session_state["plan_loaded"] = True
        st.session_state["plan_data"] = None  # invalidate cache
    else:
        st.session_state["plan_loaded"] = False
        st.sidebar.error(f"Rep {rep_id} not found")

profile = st.session_state.get("profile", {})
territory_id = profile.get("territory_id", "")
tehsil_list = profile.get("tehsil_list", [])

if profile:
    st.sidebar.success(
        f"**Territory:** {territory_id}  \n"
        f"**District:** {profile.get('district', '')}  \n"
        f"**Tehsils covered:** {len(tehsil_list)}"
    )

tabs = st.tabs(["📋 Daily Plan & AI Advice", "🚨 Alerts", "📊 Analytics"])

# ── Tab 1: Daily Plan with inline AI ──────────────────────────────
with tabs[0]:
    if not st.session_state.get("plan_loaded"):
        st.info("Enter your Rep ID in the sidebar and click **Load My Plan**.")
    else:
        # Load plan (cache in session so alerts tab reuse doesn't re-fetch)
        if not st.session_state.get("plan_data"):
            with st.spinner("Building visit plan and fetching AI recommendations for each stop..."):
                r = httpx.get(
                    f"{API_BASE}/rep/{rep_id}/daily-plan",
                    params={"date": str(visit_date), "max_visits": max_visits},
                    timeout=120,
                )
            if r.status_code != 200:
                st.error(f"API error {r.status_code}: {r.text[:200]}")
                st.stop()
            st.session_state["plan_data"] = r.json()

        plan = st.session_state["plan_data"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Territory", plan["territory_id"])
        c2.metric("Date", plan["date"])
        c3.metric("Stops planned", len(plan["itinerary"]))

        if plan["alerts"]:
            st.warning(f"⚠️ {len(plan['alerts'])} territory alerts — see Alerts tab")

        st.divider()

        severity_icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}

        for item in plan["itinerary"]:
            etype_icon = "🏪" if item["entity_type"] == "retailer" else "🌾"
            header = (
                f"{item['visit_sequence']}. {etype_icon} **{item['entity_id']}** "
                f"— {item.get('tehsil', item['district'])} "
                f"| Score: **{item['priority_score']:.1f}** "
                f"| Signals: `{'`, `'.join(item['reason_codes'])}`"
            )
            with st.expander(header, expanded=True):
                left, right = st.columns([1, 1])

                with left:
                    st.markdown("**Visit details**")
                    st.write(f"- **Type:** {item['visit_type_suggestion'].replace('_', ' ').title()}")
                    if item.get("top_sku_to_discuss"):
                        st.write(f"- **Low stock SKU:** {item['top_sku_to_discuss']}")
                    st.write(f"- **District:** {item['district']}")

                with right:
                    st.markdown("**🤖 AI Recommendation**")

                    # Restock priority (highest urgency)
                    if item.get("ai_restock_sku"):
                        st.error(f"🔴 **Restock Priority:** {item['ai_restock_sku']}")
                        if item.get("ai_restock_reason"):
                            st.caption(f"Why: {item['ai_restock_reason']}")
                    else:
                        st.success("✅ Stock levels adequate")

                    # Upsell opportunity
                    if item.get("ai_upsell_product"):
                        st.info(f"💡 **Upsell Opportunity:** {item['ai_upsell_product']}")
                        if item.get("ai_upsell_reason"):
                            st.caption(f"Why: {item['ai_upsell_reason']}")

                    if item.get("ai_talk_track"):
                        st.markdown(f"💬 **Talk Track:** {item['ai_talk_track']}")
                    if item.get("ai_agronomic_advice"):
                        st.success(f"🌱 **Agronomic Advice:** {item['ai_agronomic_advice']}")
                    if item.get("ai_promo"):
                        st.warning(f"🎁 **Promo:** {item['ai_promo']}")
                    wa = "✅ Send WhatsApp follow-up" if item.get("ai_whatsapp_followup") else "❌ No WhatsApp needed"
                    st.write(wa)

        if tehsil_list:
            with st.expander(f"📍 Territory tehsils ({len(tehsil_list)})"):
                st.write(", ".join(tehsil_list))

# ── Tab 2: Alerts ─────────────────────────────────────────────────
with tabs[1]:
    st.subheader("Territory Alerts")
    alert_territory = st.text_input("Territory ID", value=territory_id or "TER_0001")
    severity_filter = st.selectbox("Min Severity", ["low", "medium", "high", "critical"])
    if st.button("Load Alerts"):
        r = httpx.get(
            f"{API_BASE}/alerts",
            params={"territory_id": alert_territory, "rep_id": rep_id, "severity": severity_filter},
            timeout=30,
        )
        if r.status_code == 200:
            alerts_data = r.json()
            if alerts_data:
                for a in alerts_data:
                    icon = severity_icons.get(a["severity"], "⚪")
                    with st.expander(f"{icon} [{a['alert_type'].upper()}] {a['entity_id']}"):
                        st.write(f"**Detail:** {a['detail']}")
                        st.write(f"**Action:** {a['action']}")
            else:
                st.success("No alerts at this severity level.")
        else:
            st.error(f"API error: {r.status_code}")

# ── Tab 3: Analytics ──────────────────────────────────────────────
with tabs[2]:
    st.subheader("Territory Performance")
    analytics_territory = st.text_input("Territory ID ", value=territory_id or "TER_0001")
    weeks = st.slider("Weeks", 1, 12, 4)
    if st.button("Load Analytics"):
        r = httpx.get(
            f"{API_BASE}/analytics/territory/{analytics_territory}",
            params={"weeks": weeks},
            timeout=30,
        )
        if r.status_code == 200:
            a = r.json()
            col1, col2, col3 = st.columns(3)
            col1.metric("Visit Coverage", f"{a['visit_coverage']*100:.1f}%")
            col2.metric("Conversion Rate", f"{a['conversion_rate']*100:.1f}%")
            col3.metric("Period", f"Last {a['period_weeks']} weeks")
            st.write("**Top SKUs:**", ", ".join(a["top_skus"]) or "None")
            if a["high_priority_unvisited"]:
                st.warning(f"**High-priority unvisited:** {', '.join(a['high_priority_unvisited'])}")
        else:
            st.error(f"API error: {r.status_code}")
