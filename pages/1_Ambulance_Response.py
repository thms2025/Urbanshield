import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
import database as db

st.markdown('<link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">', unsafe_allow_html=True)

# -------- RANDOMIZED INCIDENT DATA --------
now = datetime.now()
incident_id = f"INC-{now.strftime('%Y%m%d')}-{random.randint(1000,9999)}"
eta_minutes = random.randint(7, 20)
eta_time    = (now + timedelta(minutes=eta_minutes)).strftime("%H:%M")

HOSPITALS = [
    {"name": "Apollo Hospitals, Jubilee Hills",       "address": "Plot No. 251, Road No. 78, Jubilee Hills",          "phone": "+91 94405 12783"},
    {"name": "Yashoda Hospitals, Secunderabad",       "address": "Alexander Rd, Beside Mahankali Temple, Secunderabad","phone": "+91 98480 33456"},
    {"name": "CARE Hospitals, Banjara Hills",         "address": "Road No. 1, Banjara Hills, Hyderabad",              "phone": "+91 76600 21100"},
    {"name": "Star Hospitals, Nanakramguda",          "address": "8-2-596/5, Banjara Hills Road No. 10",              "phone": "+91 88977 44321"},
    {"name": "Continental Hospitals, Gachibowli",    "address": "Plot No. 3, Mindspace Road, Gachibowli",            "phone": "+91 91005 67892"},
]

DRIVERS = [
    {"name": "Mohammed Rafiq",    "id": "AMB-HYD-047"},
    {"name": "Suresh Babu K.",    "id": "AMB-HYD-113"},
    {"name": "Pradeep Reddy",     "id": "AMB-HYD-082"},
    {"name": "Arjun Sharma",      "id": "AMB-HYD-029"},
    {"name": "Venkat Narayana",   "id": "AMB-HYD-156"},
]

ROUTES = [
    {"waypoint": "Secunderabad Flyover → Paradise Circle", "incident": "NH-44 & MG Road Jct., Secunderabad"},
    {"waypoint": "Mehdipatnam Flyover → Masab Tank",       "incident": "Tolichowki Signal, Hyderabad"},
    {"waypoint": "Ameerpet X-Roads → SR Nagar",            "incident": "Erragadda Bus Stop Junction"},
    {"waypoint": "Dilsukhnagar → Uppal Ring Road",         "incident": "L.B. Nagar Flyover, Hyderabad"},
    {"waypoint": "Kukatpally Main Rd → KPHB Colony",       "incident": "JNTU-Hitech City Crossing"},
]

INCIDENTS = [
    {"lat": 17.4399, "lon": 78.4983, "location": "NH-44 & MG Road Junction, Secunderabad"},
    {"lat": 17.3850, "lon": 78.4867, "location": "Tolichowki Signal, Hyderabad"},
    {"lat": 17.4374, "lon": 78.4487, "location": "Ameerpet X-Roads, Hyderabad"},
    {"lat": 17.3686, "lon": 78.5532, "location": "L.B. Nagar Flyover, Hyderabad"},
    {"lat": 17.4849, "lon": 78.3981, "location": "JNTU-Hitech City Crossing, Hyderabad"},
]

hosp    = random.choice(HOSPITALS)
driver  = random.choice(DRIVERS)
route   = random.choice(ROUTES)
inc     = random.choice(INCIDENTS)

# -------- HEADER --------
st.markdown("# 🚑 UrbanShield — Ambulance Dispatch Portal")
st.caption("Hospital Response & Traffic Coordination System")
st.divider()

# -------- INCIDENT DETAILS --------
st.subheader("⚠️ Active Incident Alert")
col1, col2, col3 = st.columns(3)
col1.metric("Incident ID", incident_id)
col2.metric("Type", "🚨 Road Accident")
col3.metric("Severity", "🔴 HIGH")

col4, col5 = st.columns(2)
col4.info(f"📍 **Location:** {inc['location']}")
col5.info(f"🛰️ **GPS:** {inc['lat']}°N, {inc['lon']}°E")
st.info(f"🕐 **Detected At:** {now.strftime('%H:%M:%S on %d %B %Y')}")

st.divider()

# -------- AMBULANCE DETAILS --------
st.subheader("🏥 Responding Unit")
col_a, col_b, col_c = st.columns(3)
col_a.success(f"**Hospital:** {hosp['name']}")
col_b.success(f"**Ambulance ID:** {driver['id']}")
col_c.success(f"**Driver:** {driver['name']}")

col_d, col_e = st.columns(2)
col_d.info(f"📞 **Contact:** {hosp['phone']}")
col_e.metric("⏱️ Auto-Estimated Arrival", f"{eta_time} (~{eta_minutes} min)")

st.divider()

# -------- ROUTE TRACKER --------
st.subheader("🗺️ Route Corridor")

# Calculate checkpoint times proportionally across the route
t_depart   = now                                            # Origin: ambulance departs NOW
t_enroute  = now + timedelta(minutes=int(eta_minutes * 0.55))  # En-Route: ~55% of journey
t_incident = now + timedelta(minutes=eta_minutes)           # Incident site: full ETA

col_r1, col_r2, col_r3 = st.columns(3)

col_r3.info(
    f"🔵 **Origin**\n\n"
    f"{hosp['name']}\n\n"
    f"🕐 **Departs:** `{t_depart.strftime('%H:%M')}`"
)
col_r2.warning(
    f"🟡 **En Route**\n\n"
    f"{route['waypoint']}\n\n"
    f"🕐 **ETA Here:** `{t_enroute.strftime('%H:%M')}`"
)
col_r1.error(
    f"🔴 **Incident Site**\n\n"
    f"{inc['location']}\n\n"
    f"🕐 **Arrives:** `{t_incident.strftime('%H:%M')}`"
)

st.divider()

# -------- DISPATCH FORM --------
st.subheader("📋 Confirm Dispatch & Notify Traffic Control")

with st.form("ambulance_form"):
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        departure_time = st.time_input("🕐 Departure Time", value=now.replace(second=0, microsecond=0).time())
        driver_note    = st.text_area("📝 Paramedic Notes", placeholder="e.g. 2 paramedics, advanced life support unit")
    with col_f2:
        eta_input = st.time_input("🏁 Expected Arrival Time", value=(now + timedelta(minutes=eta_minutes)).replace(second=0, microsecond=0).time())
        action    = st.radio("Dispatch Decision", ["✅ Accept & Dispatch Ambulance", "❌ Decline (Redirect to alternate)"], index=0)

    submitted = st.form_submit_button("🚑 Confirm & Alert Traffic Control Room", use_container_width=True)

if submitted:
    if "Accept" in action:
        try:
            msg = MIMEMultipart()
            msg['From']    = config.SENDER_EMAIL
            msg['To']      = config.EMAIL_TRAFFIC_CTRL
            msg['Subject'] = f"URGENT: Ambulance En Route — Clear Corridor Required [{incident_id}]"
            body = (
                f"Dear {config.TRAFFIC_CTRL_NAME},\n\n"
                f"This is an automated Priority Alert from the UrbanShield Smart City System.\n\n"
                f"AMBULANCE DISPATCH CONFIRMED:\n"
                f"{'='*45}\n"
                f"Incident ID      : {incident_id}\n"
                f"Incident Type    : Road Accident (High Severity)\n"
                f"Incident Site    : {inc['location']}\n"
                f"GPS Coordinates  : {inc['lat']}°N, {inc['lon']}°E\n"
                f"\nAMBULANCE DETAILS:\n"
                f"{'='*45}\n"
                f"Unit ID          : {driver['id']}\n"
                f"Hospital         : {hosp['name']}\n"
                f"Driver           : {driver['name']}\n"
                f"Contact          : {hosp['phone']}\n"
                f"Departure Time   : {departure_time}\n"
                f"Expected Arrival : {eta_input}\n"
                f"\nROUTE CORRIDOR:\n"
                f"{'='*45}\n"
                f"  Origin         : {hosp['name']} — Departs {t_depart.strftime('%H:%M')}\n"
                f"  En Route       : {route['waypoint']} — ETA {t_enroute.strftime('%H:%M')}\n"
                f"  Incident Site  : {inc['location']} — Arrives {t_incident.strftime('%H:%M')}\n"
                f"\nACTION REQUIRED:\n"
                f"{'='*45}\n"
                f"1. Activate GREEN CORRIDOR along the above route\n"
                f"2. Override all traffic signals to GREEN along route\n"
                f"3. Alert field personnel for manual traffic control\n\n"
                f"Paramedic Notes  : {driver_note if driver_note else 'N/A'}\n"
                f"Date & Time      : {now.strftime('%d %B %Y at %H:%M:%S')}\n\n"
                f"This alert was auto-generated by UrbanShield AI System.\n"
                f"Immediate action is required. Every second counts.\n\n"
                f"Regards,\nUrbanShield Central Command"
            )
            msg.attach(MIMEText(body, 'plain'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
            server.send_message(msg)
            server.quit()

            # ---- Save dispatch to database ----
            db.log_dispatch(
                incident_id   = incident_id,
                hospital      = hosp['name'],
                ambulance_id  = driver['id'],
                driver        = driver['name'],
                phone         = hosp['phone'],
                departure_time= departure_time,
                eta_time      = eta_input,
                route_origin  = hosp['name'],
                route_waypoint= route['waypoint'],
                route_incident= inc['location'],
                gps_lat       = inc['lat'],
                gps_lon       = inc['lon'],
                paramedic_notes = driver_note
            )
            db.log_alert(incident_id, "Email-TrafficCtrl", config.EMAIL_TRAFFIC_CTRL)

            # ---- Send Twilio SMS to traffic control ----
            try:
                from twilio.rest import Client as TwilioClient
                sms_body = (
                    f"URBANSHIELD — AMBULANCE EN ROUTE\n"
                    f"{'='*32}\n"
                    f"Incident : {incident_id}\n"
                    f"Site     : {inc['location']}\n"
                    f"Unit     : {driver['id']} ({driver['name']})\n"
                    f"Hospital : {hosp['name']}\n"
                    f"\nROUTE CORRIDOR:\n"
                    f"  {hosp['name']}\n"
                    f"  Departs : {t_depart.strftime('%H:%M')}\n"
                    f"  → {route['waypoint']}\n"
                    f"  ETA     : {t_enroute.strftime('%H:%M')}\n"
                    f"  → {inc['location']}\n"
                    f"  Arrives : {t_incident.strftime('%H:%M')}\n"
                    f"\nACTION: Activate GREEN CORRIDOR NOW."
                )
                tc = TwilioClient(config.TWILIO_SID, config.TWILIO_TOKEN)
                tc.messages.create(body=sms_body, from_=config.TWILIO_FROM, to=config.TWILIO_TO)
                sms_sent = True
            except Exception as sms_err:
                sms_sent = False
                sms_error = str(sms_err)

            # ---- Visual Dispatch Summary ----
            st.success("✅ Dispatch Confirmed! Email sent to Traffic Control Room.")
            if sms_sent:
                st.success("📱 SMS alert also sent to Traffic Control Room!")
            else:
                st.warning(f"⚠️ SMS could not be sent: {sms_error}")

            st.divider()
            st.subheader("📋 Full Dispatch Summary — Sent to Traffic Control")

            st.markdown(f"""
**🆔 Incident:** `{incident_id}` &nbsp;|&nbsp; **🚨 Type:** Road Accident &nbsp;|&nbsp; **🔴 Severity:** HIGH
""")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🚑 Unit", driver['id'])
            c2.metric("👤 Driver", driver['name'])
            c3.metric("🕐 Departure", str(departure_time))
            c4.metric("🏁 ETA at Scene", str(eta_input))

            st.markdown("#### 🗺️ Full Route Corridor — Notified to Traffic Control")
            r1, r2, r3 = st.columns(3)
            r3.info(f"🔵 **Origin**\n\n{hosp['name']}\n\n🕐 Departs: **{t_depart.strftime('%H:%M')}**")
            r2.warning(f"🟡 **En Route**\n\n{route['waypoint']}\n\n🕐 ETA: **{t_enroute.strftime('%H:%M')}**")
            r1.error(f"🔴 **Incident Site**\n\n{inc['location']}\n\n🕐 Arrives: **{t_incident.strftime('%H:%M')}**")

            st.markdown(f"""
> 📍 **GPS:** `{inc['lat']}°N, {inc['lon']}°E`  
> 📝 **Paramedic Notes:** {driver_note if driver_note else 'N/A'}  
> 🕐 **Alert Generated:** {now.strftime('%d %B %Y at %H:%M:%S')}
""")
            st.info("🚦 Traffic Control has been instructed to activate GREEN CORRIDOR along the full ambulance route.")

        except Exception as e:
            st.error(f"❌ Failed to notify Traffic Control: {e}")
    else:
        st.warning("⚠️ Dispatch Declined. UrbanShield will automatically redirect to the next nearest available hospital.")

