import os
from dotenv import load_dotenv

# Load variables from .env if running locally
load_dotenv()

# --- Email ---
# Pulls from HF Space Secrets in production, or .env locally
SENDER_EMAIL    = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")

# Authority Routing (Email)
EMAIL_FIRE_STATION = os.getenv("EMAIL_FIRE_STATION", "")
EMAIL_HOSPITAL     = os.getenv("EMAIL_HOSPITAL", "")
EMAIL_MUNICIPAL    = os.getenv("EMAIL_MUNICIPAL", "")
EMAIL_TRAFFIC_CTRL = os.getenv("EMAIL_TRAFFIC_CTRL", "")

# --- Twilio SMS ---
TWILIO_SID   = os.getenv("TWILIO_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "")
TWILIO_FROM  = os.getenv("TWILIO_FROM", "")
TWILIO_TO    = os.getenv("TWILIO_TO", "")

# --- Location & Demo Data (Safe to be public) ---
CAMERA_LOCATION = "NH-44 & MG Road Junction, Secunderabad, Hyderabad"
CAMERA_LAT      = 17.4399
CAMERA_LON      = 78.4983

HOSPITAL_NAME    = "Apollo Hospitals, Jubilee Hills"
HOSPITAL_ADDRESS = "Plot No. 251, Road No. 78, Jubilee Hills, Hyderabad"
AMBULANCE_ID     = "AMB-HYD-047"
AMBULANCE_DRIVER = "Mohammed Rafiq"
AMBULANCE_PHONE  = "+91 94405 12783"

TRAFFIC_CTRL_NAME    = "Hyderabad City Traffic Police Control Room"
TRAFFIC_CTRL_ADDRESS = "Traffic Control Room, Goshamahal, Hyderabad"
