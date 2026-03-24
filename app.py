import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
import tempfile
import time
import requests
import base64
from twilio.rest import Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
import config
import database as db

# -------- PAGE CONFIG --------
st.set_page_config(page_title="UrbanShield", layout="wide")

# -------- SESSION STATE --------
if "fire_count" not in st.session_state:
    st.session_state.fire_count = 0
    st.session_state.accident_count = 0
    st.session_state.pothole_count = 0
    st.session_state.last_fire_time = 0
    st.session_state.last_accident_time = 0
    st.session_state.last_pothole_time = 0

COOLDOWN = 15  # seconds (increased SMS rate limiting)

# -------- LOAD MODEL --------
model = YOLO("yolov8n.pt")

# -------- DETECTION FUNCTIONS --------
def detect_fire(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (0,150,150), (35,255,255))
    return cv2.countNonZero(mask) > 6000

def detect_pothole(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    dark = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)[1]
    return cv2.countNonZero(edges & dark) > 4000

def detect_accident(results):
    vehicles = []

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]

            if label in ['car','truck','bus']:
                vehicles.append(box.xyxy[0])

    # accident if too many vehicles crowded
    return len(vehicles) >= 4

# -------- UI HEADER & DASHBOARD PLACEHOLDER --------
st.markdown('<link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">', unsafe_allow_html=True)

st.markdown(f"""
<div class="font-sans mb-4">
    <h1 class="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-orange-400 text-center tracking-tight mb-8 mt-4">
        🚦 UrbanShield Smart Monitoring 
    </h1>
</div>
""", unsafe_allow_html=True)

# Create a placeholder to hold the stats AFTER they are updated
dashboard_placeholder = st.empty()

# -------- SIDEBAR: SYSTEM STATUS --------
st.sidebar.markdown("""<div style="background:linear-gradient(135deg,#1e3a5f,#1e40af);padding:14px;border-radius:10px;text-align:center;margin-bottom:12px">
<h2 style="color:white;font-size:1rem;font-weight:800;margin:0">🛰️ UrbanShield System</h2>
<p style="color:#93c5fd;font-size:11px;margin:4px 0 0">Smart City Emergency Network</p>
</div>""", unsafe_allow_html=True)

st.sidebar.markdown("""
| System | Status |
|--------|--------|
| 🤖 AI Engine | 🟢 Online |
| 📧 Email Dispatch | 🟢 Active |
| 📱 SMS Gateway | 🟢 Active |
| 🚑 Ambulance Net | 🟢 Standby |
| 🚦 Traffic Ctrl | 🟢 Linked |
""")
st.sidebar.markdown("---")
st.sidebar.markdown("**📍 Active Camera Feed**")
st.sidebar.info(f"📍 {config.CAMERA_LOCATION}")
st.sidebar.caption(f"GPS: {config.CAMERA_LAT}°N, {config.CAMERA_LON}°E")
st.sidebar.markdown("---")
st.sidebar.markdown("[🚑 Open Ambulance Dispatch Portal](/Ambulance_Response)", unsafe_allow_html=False)

# -------- INPUT MODE TOGGLE --------
mode = st.radio(
    "Select Input Mode:",
    ["📁 Upload Files", "📷 Live Webcam (CCTV)"],
    horizontal=True
)

st.markdown("<hr style='margin-top: 12px; margin-bottom: 12px; border-color: #374151;'>", unsafe_allow_html=True)

# -------- WEBCAM MODE UI --------
if mode == "📷 Live Webcam (CCTV)":
    st.markdown("""<div style="background:linear-gradient(135deg,#7c3aed,#4f46e5);padding:12px;border-radius:10px;text-align:center;margin-bottom:12px"><h2 style="color:white;font-size:1.2rem;font-weight:800;margin:0">📷 Live CCTV Feed — AI Monitoring Active</h2></div>""", unsafe_allow_html=True)
    webcam_tab, video_tab = st.tabs(["📸 Capture Photo", "🎥 Upload Video"])
    with webcam_tab:
        camera_image = st.camera_input("Point camera at the incident scene")
    with video_tab:
        webcam_video = st.file_uploader("Upload a video for CCTV analysis", type=["mp4","avi","mov"])

# -------- UPLOAD MODE UI --------
else:
    gallery_placeholder = st.empty()
    uploaded_files = st.file_uploader(
        "📂 Upload Input Video or Photo",
        type=["jpg","png","jpeg","mp4","avi"],
        accept_multiple_files=True
    )
    st.markdown("<hr style='margin-top: 20px; margin-bottom: 20px; border-color: #374151;'>", unsafe_allow_html=True)
    if uploaded_files:
        with gallery_placeholder.container():
            st.markdown("""<div style="background:linear-gradient(135deg,#059669,#0d9488);padding:10px;border-radius:10px;text-align:center;margin-bottom:12px"><h2 style="color:white;font-size:1.2rem;font-weight:800;margin:0">✅ AI Analysis Gallery</h2></div>""", unsafe_allow_html=True)
            gallery_cols = st.columns(len(uploaded_files))

# -------- TWILIO SMS (auto, from config.py) --------
twilio_sid   = config.TWILIO_SID
twilio_token = config.TWILIO_TOKEN
twilio_from  = config.TWILIO_FROM
twilio_to    = config.TWILIO_TO

def send_twilio_alert(issue_name, location, frame_image):
    if not (twilio_sid and twilio_token and twilio_from and twilio_to):
        return # SMS not configured

    try:
        now = datetime.now()
        msg_body = (
            f"URBANSHIELD ALERT\n"
            f"------------------\n"
            f"Issue    : {issue_name}\n"
            f"Location : {location}\n"
            f"Date     : {now.strftime('%Y-%m-%d')}\n"
            f"Time     : {now.strftime('%H:%M:%S')}\n\n"
            f"Immediate action required."
        )
        client = Client(twilio_sid, twilio_token)
        client.messages.create(body=msg_body, from_=twilio_from, to=twilio_to)
        st.toast(f"SMS Alert Sent for {issue_name}!", icon="📱")
    except Exception as e:
        st.toast(f"Twilio SMS Error: {e}", icon="⚠️")

# -------- EMAIL ALERTS (auto, from config.py) --------
# All credentials are loaded from config.py - nothing is shown on the dashboard
sender_email    = config.SENDER_EMAIL
sender_password = config.SENDER_PASSWORD
email_fire_station = config.EMAIL_FIRE_STATION
email_hospital     = config.EMAIL_HOSPITAL
email_municipal    = config.EMAIL_MUNICIPAL
location_name      = config.CAMERA_LOCATION

def send_email_alert(issue_name, location, frame_image):
    to_email = None
    authority_name = ""
    if issue_name == "Fire":
        to_email = email_fire_station
        authority_name = "Fire Department"
    elif issue_name == "Accident":
        to_email = email_hospital
        authority_name = "Emergency Medical Services"
    elif issue_name == "Pothole":
        to_email = email_municipal
        authority_name = "Municipal Corporation"
        
    if not to_email:
        return
        
    try:
        st.info(f"📧 Dispatching email alert to {authority_name} ({to_email})...")
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = f"URBANSHIELD URGENT ALERT: {issue_name} Detected"
        
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        body = (
            f"Dear {authority_name},\n\n"
            f"This is an automated alert from the UrbanShield Smart Monitoring System.\n\n"
            f"INCIDENT DETAILS:\n"
            f"-----------------\n"
            f"Issue Type : {issue_name}\n"
            f"Location   : {location}\n"
            f"Date       : {date_str}\n"
            f"Time       : {time_str}\n\n"
            f"An image of the detected incident is attached to this email.\n"
            f"Please take the necessary actions immediately.\n\n"
            f"Regards,\n"
            f"UrbanShield AI System"
        )
        msg.attach(MIMEText(body, 'plain'))
        
        success, encoded_image = cv2.imencode('.jpg', frame_image)
        if success:
            image_attachment = MIMEImage(encoded_image.tobytes(), name=f"{issue_name}.jpg")
            msg.attach(image_attachment)
            
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        st.success(f"✅ Email successfully dispatched to {authority_name} ({to_email})!")
        
    except Exception as e:
        st.error(f"❌ Email Error: {e}")

# -------- PROCESS IMAGE --------
def process_image(frame):
    results = model(frame, verbose=False)

    fire = detect_fire(frame)
    accident = detect_accident(results)
    pothole = detect_pothole(frame)

    status = "✅ No Issue"

    current_time = time.time()

    if fire:
        status = "🔥 Fire"
        if current_time - st.session_state.last_fire_time > COOLDOWN:
            st.session_state.fire_count += 1
            st.session_state.last_fire_time = current_time
            send_twilio_alert("Fire", location_name, frame)
            send_email_alert("Fire", location_name, frame)
            inc_id = db.log_incident("Fire", location_name, config.CAMERA_LAT, config.CAMERA_LON, frame)
            db.log_alert(inc_id, "SMS",   config.TWILIO_TO)
            db.log_alert(inc_id, "Email", config.EMAIL_FIRE_STATION)

    elif accident:
        status = "🚨 Accident"
        if current_time - st.session_state.last_accident_time > COOLDOWN:
            st.session_state.accident_count += 1
            st.session_state.last_accident_time = current_time
            send_twilio_alert("Accident", location_name, frame)
            send_email_alert("Accident", location_name, frame)
            inc_id = db.log_incident("Accident", location_name, config.CAMERA_LAT, config.CAMERA_LON, frame)
            db.log_alert(inc_id, "SMS",   config.TWILIO_TO)
            db.log_alert(inc_id, "Email", config.EMAIL_HOSPITAL)

    elif pothole:
        status = "🕳️ Pothole"
        if current_time - st.session_state.last_pothole_time > COOLDOWN:
            st.session_state.pothole_count += 1
            st.session_state.last_pothole_time = current_time
            send_twilio_alert("Pothole", location_name, frame)
            send_email_alert("Pothole", location_name, frame)
            inc_id = db.log_incident("Pothole", location_name, config.CAMERA_LAT, config.CAMERA_LON, frame)
            db.log_alert(inc_id, "SMS",   config.TWILIO_TO)
            db.log_alert(inc_id, "Email", config.EMAIL_MUNICIPAL)

    annotated = results[0].plot()
    annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

    return annotated, status

# -------- WEBCAM EXECUTION (after process_image is defined) --------
if mode == "📷 Live Webcam (CCTV)":
    # Photo capture
    if camera_image is not None:
        file_bytes = np.asarray(bytearray(camera_image.getvalue()), dtype=np.uint8)
        frame = cv2.imdecode(file_bytes, 1)
        annotated, status = process_image(frame)
        col_cam, col_alert = st.columns([3, 1])
        col_cam.image(annotated, channels="RGB", use_container_width=True, caption="📸 AI-Processed CCTV Frame")
        with col_alert:
            if "Fire" in status: st.error(f"🔥 {status}")
            elif "Accident" in status: st.warning(f"🚨 {status}")
            elif "Pothole" in status: st.info(f"🕳️ {status}")
            else: st.success(f"✅ {status}")

    # Video upload in webcam mode
    if webcam_video is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(webcam_video.read())
        cap = cv2.VideoCapture(tfile.name)
        st.markdown("#### 🎥 Video Analysis")
        vcol, acol = st.columns([3, 1])
        vph = vcol.empty()
        aph = acol.empty()
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            annotated, status = process_image(frame)
            vph.image(annotated, channels="RGB", use_container_width=True)
            if "Fire" in status: aph.error(f"🔥 {status}")
            elif "Accident" in status: aph.warning(f"🚨 {status}")
            elif "Pothole" in status: aph.info(f"🕳️ {status}")
            else: aph.success(f"✅ {status}")
        cap.release()
        st.info("✅ Video analysis complete.")

# -------- MAIN LOGIC (Upload Mode Only) --------
elif mode == "📁 Upload Files" and uploaded_files:
    for i, uploaded_file in enumerate(uploaded_files):
        
        file_type = uploaded_file.type
        current_col = gallery_cols[i]

        # ---------- IMAGE ----------
        if "image" in file_type:

            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, 1)

            annotated, status = process_image(frame)

            with current_col:
                st.image(annotated, caption=uploaded_file.name, use_container_width=True)
                
                # Show color coded alert instead of generic markdown
                if "Fire" in status:
                    st.error(status)
                elif "Accident" in status:
                    st.warning(status)
                elif "Pothole" in status:
                    st.info(status)
                else:
                    st.success(status)

        # ---------- VIDEO ----------
        else:
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfile.write(uploaded_file.read())

            cap = cv2.VideoCapture(tfile.name)

            with current_col:
                video_placeholder = st.empty()
                alert_box = st.empty()

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                annotated, status = process_image(frame)

                video_placeholder.image(annotated, channels="RGB", use_container_width=True)

                if "Fire" in status:
                    alert_box.error(status)
                elif "Accident" in status:
                    alert_box.warning(status)
                elif "Pothole" in status:
                    alert_box.info(status)
                else:
                    alert_box.success(status)

            cap.release()

# -------- UPDATE TOP DASHBOARD METRICS --------
def reset_stats_callback():
    st.session_state.fire_count = 0
    st.session_state.accident_count = 0
    st.session_state.pothole_count = 0

with dashboard_placeholder.container():
    # Use Streamlit's native columns to place the HTML bar on the left and the native button on the far right
    col_bar, col_btn = st.columns([5, 1])
    
    with col_bar:
        st.markdown(f"""<div class="flex flex-row items-center space-x-4 bg-gray-900 border border-gray-800 rounded-xl p-3 shadow-lg font-sans w-full"><div class="flex items-center justify-between space-x-3 bg-gray-800 px-4 py-2 rounded-lg border-l-4 border-red-500 w-1/3"><div class="text-left"><p class="text-gray-400 text-xs font-bold uppercase tracking-wider">Fire</p><p class="text-xl font-black text-white leading-none">{st.session_state.fire_count}</p></div><span class="text-2xl">🔥</span></div><div class="flex items-center justify-between space-x-3 bg-gray-800 px-4 py-2 rounded-lg border-l-4 border-yellow-500 w-1/3"><div class="text-left"><p class="text-gray-400 text-xs font-bold uppercase tracking-wider">Accident</p><p class="text-xl font-black text-white leading-none">{st.session_state.accident_count}</p></div><span class="text-2xl">🚨</span></div><div class="flex items-center justify-between space-x-3 bg-gray-800 px-4 py-2 rounded-lg border-l-4 border-gray-500 w-1/3"><div class="text-left"><p class="text-gray-400 text-xs font-bold uppercase tracking-wider">Pothole</p><p class="text-xl font-black text-white leading-none">{st.session_state.pothole_count}</p></div><span class="text-2xl">🕳️</span></div></div>""", unsafe_allow_html=True)
        
    with col_btn:
        st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
        st.button("🔄 Reset Stats", on_click=reset_stats_callback, use_container_width=True)