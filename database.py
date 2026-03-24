import sqlite3
import os
import base64
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "urbanshield.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Incidents table — every detected hazard
    c.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT NOT NULL,
            type        TEXT NOT NULL,
            location    TEXT,
            gps_lat     REAL,
            gps_lon     REAL,
            severity    TEXT DEFAULT 'HIGH',
            detected_at TEXT NOT NULL,
            image_b64   TEXT
        )
    """)

    # Alerts table — every SMS/Email sent
    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT NOT NULL,
            alert_type  TEXT NOT NULL,
            recipient   TEXT,
            status      TEXT DEFAULT 'sent',
            sent_at     TEXT NOT NULL
        )
    """)

    # Dispatches table — ambulance dispatch records
    c.execute("""
        CREATE TABLE IF NOT EXISTS dispatches (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id     TEXT NOT NULL,
            hospital        TEXT,
            ambulance_id    TEXT,
            driver          TEXT,
            phone           TEXT,
            departure_time  TEXT,
            eta_time        TEXT,
            route_origin    TEXT,
            route_waypoint  TEXT,
            route_incident  TEXT,
            gps_lat         REAL,
            gps_lon         REAL,
            paramedic_notes TEXT,
            dispatched_at   TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

# ---- Incident helpers ----
def log_incident(incident_type, location, gps_lat, gps_lon, image_frame=None):
    import cv2, numpy as np
    now = datetime.now()
    incident_id = f"INC-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"
    image_b64 = None
    if image_frame is not None:
        try:
            success, buf = cv2.imencode('.jpg', image_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if success:
                image_b64 = base64.b64encode(buf).decode('utf-8')
        except Exception:
            pass

    conn = get_conn()
    conn.execute("""
        INSERT INTO incidents (incident_id, type, location, gps_lat, gps_lon, detected_at, image_b64)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (incident_id, incident_type, location, gps_lat, gps_lon, now.strftime('%Y-%m-%d %H:%M:%S'), image_b64))
    conn.commit()
    conn.close()
    return incident_id

# ---- Alert helpers ----
def log_alert(incident_id, alert_type, recipient, status="sent"):
    conn = get_conn()
    conn.execute("""
        INSERT INTO alerts (incident_id, alert_type, recipient, status, sent_at)
        VALUES (?, ?, ?, ?, ?)
    """, (incident_id, alert_type, recipient, status, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

# ---- Dispatch helpers ----
def log_dispatch(incident_id, hospital, ambulance_id, driver, phone,
                 departure_time, eta_time, route_origin, route_waypoint,
                 route_incident, gps_lat, gps_lon, paramedic_notes):
    conn = get_conn()
    conn.execute("""
        INSERT INTO dispatches
        (incident_id, hospital, ambulance_id, driver, phone, departure_time, eta_time,
         route_origin, route_waypoint, route_incident, gps_lat, gps_lon, paramedic_notes, dispatched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (incident_id, hospital, ambulance_id, driver, phone,
          str(departure_time), str(eta_time), route_origin, route_waypoint,
          route_incident, gps_lat, gps_lon, paramedic_notes,
          datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

# ---- Fetch helpers ----
def fetch_incidents():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM incidents ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_alerts():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM alerts ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_dispatches():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM dispatches ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_incident_image(incident_id):
    conn = get_conn()
    row = conn.execute("SELECT image_b64 FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()
    conn.close()
    return row['image_b64'] if row else None

# Initialize DB on import
init_db()
