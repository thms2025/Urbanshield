---
title: UrbanShield AI
emoji: 🛡️
colorFrom: blue
colorTo: green
sdk: docker
app_file: app.py
pinned: false
---

# 🛡️ UrbanShield

**Smart City Emergency Response System**

UrbanShield is an AI-powered smart city monitoring dashboard built with Streamlit and YOLOv8. It automatically detects hazards (fires, accidents, potholes) from CCTV feeds or uploaded files, and immediately coordinates emergency response.

### 🌟 Features
- **Real-time AI Detection:** YOLOv8 object detection on live webcam CCTV feeds or uploaded images/videos.
- **Automated Alerts:** Instantly sends SMS alerts (Twilio) and Email alerts with images to relevant authorities (Fire Station, Hospitals, Municipal Office).
- **Ambulance Dispatch Portal:** A dedicated dispatch page for hospitals to accept incidents, estimate arrival times, and calculate route waypoints.
- **Green Corridor Integration:** Auto-generates detailed dispatch summaries and notifies Traffic Control Rooms to clear traffic signals along the ambulance route.
- **Incident History Database:** SQLite backend that logs all detected incidents, alerts sent, and dispatches for auditing and analytics.

### 🚀 Setup & Installation
1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your credentials:
   ```env
   SENDER_EMAIL="your_email@gmail.com"
   SENDER_PASSWORD="your_app_password"
   EMAIL_FIRE_STATION="fire@example.com"
   EMAIL_HOSPITAL="hospital@example.com"
   EMAIL_MUNICIPAL="municipal@example.com"
   EMAIL_TRAFFIC_CTRL="traffic@example.com"
   TWILIO_SID="your_twilio_sid"
   TWILIO_TOKEN="your_twilio_token"
   TWILIO_FROM="+1234567890"
   TWILIO_TO="+0987654321"
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```
