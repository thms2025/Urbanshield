import streamlit as st
import sys, os, base64
import pandas as pd
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db

st.markdown('<link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">', unsafe_allow_html=True)

st.markdown("# 📊 UrbanShield — Incident History")
st.caption("Complete log of all detected incidents, alerts, and ambulance dispatches")
st.divider()

tab1, tab2, tab3 = st.tabs(["🚨 Detected Incidents", "📧 Alerts Sent", "🚑 Ambulance Dispatches"])

# ─────────── TAB 1: INCIDENTS ───────────
with tab1:
    incidents = db.fetch_incidents()
    if not incidents:
        st.info("No incidents recorded yet. Upload an image or use webcam mode to detect hazards.")
    else:
        # Summary metrics
        fires     = sum(1 for r in incidents if r['type'] == 'Fire')
        accidents = sum(1 for r in incidents if r['type'] == 'Accident')
        potholes  = sum(1 for r in incidents if r['type'] == 'Pothole')
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Incidents", len(incidents))
        c2.metric("🔥 Fires",    fires)
        c3.metric("🚨 Accidents", accidents)
        c4.metric("🕳️ Potholes", potholes)
        st.divider()

        # Table view
        df = pd.DataFrame(incidents).drop(columns=['image_b64'], errors='ignore')
        df.rename(columns={
            'incident_id': 'Incident ID', 'type': 'Type',
            'location': 'Location', 'gps_lat': 'Lat',
            'gps_lon': 'Lon', 'severity': 'Severity',
            'detected_at': 'Detected At'
        }, inplace=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("🖼️ Incident Images")
        cols = st.columns(3)
        idx = 0
        for row in incidents:
            if row.get('image_b64'):
                img_bytes = base64.b64decode(row['image_b64'])
                badge = {"Fire":"🔥","Accident":"🚨","Pothole":"🕳️"}.get(row['type'], "⚠️")
                with cols[idx % 3]:
                    st.image(img_bytes, caption=f"{badge} {row['type']} — {row['incident_id']} — {row['detected_at']}", use_container_width=True)
                idx += 1
        if idx == 0:
            st.info("No images stored yet.")

# ─────────── TAB 2: ALERTS ───────────
with tab2:
    alerts = db.fetch_alerts()
    if not alerts:
        st.info("No alerts logged yet.")
    else:
        sms_count   = sum(1 for a in alerts if a['alert_type'] == 'SMS')
        email_count = sum(1 for a in alerts if 'Email' in a['alert_type'])
        a1, a2, a3 = st.columns(3)
        a1.metric("Total Alerts", len(alerts))
        a2.metric("📱 SMS Sent", sms_count)
        a3.metric("📧 Emails Sent", email_count)
        st.divider()

        df_alerts = pd.DataFrame(alerts)
        df_alerts.rename(columns={
            'incident_id': 'Incident ID', 'alert_type': 'Type',
            'recipient': 'Recipient', 'status': 'Status', 'sent_at': 'Sent At'
        }, inplace=True)
        st.dataframe(df_alerts, use_container_width=True, hide_index=True)

# ─────────── TAB 3: DISPATCHES ───────────
with tab3:
    dispatches = db.fetch_dispatches()
    if not dispatches:
        st.info("No ambulance dispatches recorded yet.")
    else:
        st.metric("Total Dispatches", len(dispatches))
        st.divider()

        for d in dispatches:
            with st.expander(f"🚑 {d['incident_id']} — {d['hospital']} — {d['dispatched_at']}"):
                dc1, dc2, dc3 = st.columns(3)
                dc1.info(f"**Ambulance:** {d['ambulance_id']}\n\n**Driver:** {d['driver']}\n\n**Contact:** {d['phone']}")
                dc2.success(f"**Departure:** {d['departure_time']}\n\n**ETA at Scene:** {d['eta_time']}")
                dc3.warning(f"**Route:**\n\n🔵 {d['route_origin']}\n\n🟡 {d['route_waypoint']}\n\n🔴 {d['route_incident']}")
                if d.get('paramedic_notes'):
                    st.caption(f"📝 Notes: {d['paramedic_notes']}")
                st.caption(f"📍 GPS: {d['gps_lat']}°N, {d['gps_lon']}°E")

        # Full table
        st.divider()
        df_d = pd.DataFrame(dispatches).drop(columns=['id'], errors='ignore')
        st.dataframe(df_d, use_container_width=True, hide_index=True)

st.divider()
if st.button("🔄 Refresh Data", use_container_width=True):
    st.rerun()
