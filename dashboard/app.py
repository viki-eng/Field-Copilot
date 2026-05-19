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

# ── Sidebar: Rep selector ──────────────────────────────────────────
st.sidebar.header("Field Rep")

rep_id = st.sidebar.text_input("Rep ID", value="REP_0001")
visit_date = st.sidebar.date_input("Date")
max_visits = st.sidebar.slider("Max visits today", 3, 15, 8)

if st.sidebar.button("Load My Plan", type="primary"):
    st.session_state["plan_loaded"] = True

tabs = st.tabs(["📋 Daily Plan", "🎯 Next Best Action", "🚨 Alerts", "📊 Analytics"])

# ── Tab 1: Daily Plan ──────────────────────────────────────────────
with tabs[0]:
    if st.session_state.get("plan_loaded"):
        with st.spinner("Building your optimised visit plan..."):
            r = httpx.get(
                f"{API_BASE}/rep/{rep_id}/daily-plan",
                params={"date": str(visit_date), "max_visits": max_visits},
                timeout=60,
            )
        if r.status_code == 200:
            plan = r.json()
            st.success(f"Territory: **{plan['territory_id']}** | Date: {plan['date']}")

            rows = []
            for item in plan["itinerary"]:
                rows.append({
                    "Stop": item["visit_sequence"],
                    "Entity ID": item["entity_id"],
                    "Type": item["entity_type"],
                    "District": item["district"],
                    "Tehsil": item.get("tehsil", ""),
                    "Priority Score": f"{item['priority_score']:.1f}",
                    "Top SKU": item.get("top_sku_to_discuss", ""),
                    "Signals": ", ".join(item["reason_codes"]),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

            if plan["alerts"]:
                st.warning(f"⚠️ {len(plan['alerts'])} alerts for this territory — see Alerts tab")
        else:
            st.error(f"API error: {r.status_code} — {r.text[:200]}")
    else:
        st.info("Select your Rep ID and date in the sidebar, then click **Load My Plan**.")

# ── Tab 2: Next Best Action ────────────────────────────────────────
with tabs[1]:
    st.subheader("Get AI Recommendation for a Visit")
    entity_id = st.text_input("Entity ID (RTL_XXXXX or GRW_XXXXX)", value="RTL_00001")
    if st.button("Get Recommendation", type="primary"):
        with st.spinner("Asking Groq AI..."):
            r = httpx.get(
                f"{API_BASE}/visit/{entity_id}/nba",
                params={"rep_id": rep_id, "date": str(visit_date)},
                timeout=30,
            )
        if r.status_code == 200:
            nba = r.json()["nba"]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Recommended Product", nba.get("primary_product", "—"))
                st.info(f"**Why:** {nba.get('reason', '')}")
                st.success(f"**Talk Track:** {nba.get('talk_track', '')}")
            with col2:
                st.info(f"**Agronomic Advice:** {nba.get('agronomic_advice', '')}")
                if nba.get("promo_mechanic"):
                    st.warning(f"**Promo:** {nba['promo_mechanic']}")
                st.write(f"WhatsApp follow-up: {'✅' if nba.get('whatsapp_followup') else '❌'}")
            if nba.get("_fallback"):
                st.caption("⚠️ Fallback response (Groq unavailable)")
        else:
            st.error(f"API error: {r.status_code}")

# ── Tab 3: Alerts ─────────────────────────────────────────────────
with tabs[2]:
    st.subheader("Territory Alerts")
    territory_id_alert = st.text_input("Territory ID", value="TER_0001")
    severity_filter = st.selectbox("Min Severity", ["low", "medium", "high", "critical"])
    if st.button("Load Alerts"):
        r = httpx.get(
            f"{API_BASE}/alerts",
            params={"territory_id": territory_id_alert, "severity": severity_filter},
            timeout=30,
        )
        if r.status_code == 200:
            alerts = r.json()
            if alerts:
                severity_colors = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                for a in alerts:
                    icon = severity_colors.get(a["severity"], "⚪")
                    with st.expander(f"{icon} [{a['alert_type'].upper()}] {a['entity_id']}"):
                        st.write(f"**Detail:** {a['detail']}")
                        st.write(f"**Action:** {a['action']}")
            else:
                st.success("No alerts for this territory at this severity level.")
        else:
            st.error(f"API error: {r.status_code}")

# ── Tab 4: Analytics ──────────────────────────────────────────────
with tabs[3]:
    st.subheader("Territory Performance")
    territory_id_analytics = st.text_input("Territory ID ", value="TER_0001")
    weeks = st.slider("Weeks", 1, 12, 4)
    if st.button("Load Analytics"):
        r = httpx.get(
            f"{API_BASE}/analytics/territory/{territory_id_analytics}",
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
                st.warning(
                    f"**High-priority unvisited:** {', '.join(a['high_priority_unvisited'])}"
                )
        else:
            st.error(f"API error: {r.status_code}")
