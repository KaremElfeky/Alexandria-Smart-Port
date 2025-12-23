import streamlit as st
import os
import time
from PIL import Image
from datetime import datetime
import pydeck as pdk
import pandas as pd
import psycopg2

# ==========================================
# 1. SETUP & STYLING
# ==========================================
st.set_page_config(
    page_title="Alexandria Port Command", 
    page_icon="⚓", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    /* BIGGER TABS */
    div[data-baseweb="tab-list"] { gap: 8px; }
    div[data-baseweb="tab"] {
        flex-grow: 1; text-align: center; background-color: #1f2937;
        border-radius: 5px 5px 0px 0px; padding: 10px; font-weight: 600; font-size: 1.1rem;
    }
    div[aria-selected="true"] { background-color: #ff4b4b !important; color: white !important; }
    
    /* METRICS AT TOP */
    div[data-testid="stMetric"] {
        background-color: #262730; border-radius: 8px; padding: 10px;
        border-left: 5px solid #ff4b4b; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    h1 { margin-bottom: 0px; }
    </style>
    """, unsafe_allow_html=True)

# CONFIG
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FILENAME = 'final_detection.jpg'
IMAGE_PATH = os.path.join(SCRIPT_DIR, IMAGE_FILENAME)
DB_URL = "postgresql://neondb_owner:npg_rGV1neuthUa0@ep-orange-pine-ahlf4955-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# --- ☁️ GITHUB SETTINGS ---
GITHUB_USER = "YourUsername" 
REPO_NAME = "YourRepoName"    
GITHUB_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/{IMAGE_FILENAME}"

# --- MAP CALIBRATION (ALEXANDRIA) ---
LAT_CENTER = 31.185
LON_CENTER = 29.870

# ==========================================
# 2. DATA FUNCTIONS
# ==========================================
def get_db_connection():
    try: return psycopg2.connect(DB_URL)
    except: return None

def load_data(table_name):
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        conn.close()
        df.columns = df.columns.str.lower()
        # Fix Column Names
        if 'latitude' in df.columns: df.rename(columns={'latitude': 'lat'}, inplace=True)
        if 'longitude' in df.columns: df.rename(columns={'longitude': 'lon'}, inplace=True)
        # Force Numbers (Critical for Map)
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        return df.dropna(subset=['lat', 'lon'])
    except: return pd.DataFrame()

# ==========================================
# 3. HEADER & METRICS (NOW AT THE TOP)
# ==========================================
c1, c2 = st.columns([3, 1])
with c1: st.title("⚓ Port Command")
with c2: 
    if st.button("🔄 REFRESH SYSTEM", type="primary", use_container_width=True): st.rerun()

st.divider()

# --- LOAD DATA ---
df_legal = load_data("authorized_ships")
df_detected = load_data("detected_ships")

# --- CALCULATE DARK SHIPS ---
# We count how many ships in 'detected_ships' are marked as 'DARK SHIP'
if 'status' in df_detected.columns:
    dark_count = len(df_detected[df_detected['status'] == 'DARK SHIP'])
else:
    # Fallback if column missing
    dark_count = 0 

# --- METRICS ROW (MOVED UP HERE) ---
m1, m2, m3 = st.columns(3)
m1.metric("🟢 Authorized (AIS)", len(df_legal))
m2.metric("🔴 Detected (Sat)", len(df_detected))

if dark_count > 0:
    m3.metric("⚠️ Dark Ships", dark_count, delta="THREAT DETECTED", delta_color="inverse")
else:
    m3.metric("Status", "SECURE", delta="ALL CLEAR")

st.markdown("<br>", unsafe_allow_html=True) # Spacer

# ==========================================
# 4. TABS & MAP
# ==========================================
tab1, tab2, tab3 = st.tabs(["🗺️ TACTICAL MAP", "📷 SAT FEED", "📊 RAW DATA"])

# --- TAB 1: THE MAP ---
with tab1:
    layers = []

    # Layer 1: Green Ships (AIS)
    if not df_legal.empty:
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=df_legal,
            get_position="[lon, lat]",
            get_color="[0, 255, 0, 200]",
            get_radius=120,
            pickable=True,
            radius_min_pixels=5
        ))

    # Layer 2: Red/Green Detected Ships (Sat)
    if not df_detected.empty:
        # Color logic: Green if matched, Red if Dark
        if 'status' in df_detected.columns:
            df_detected['color'] = df_detected['status'].apply(
                lambda x: [0, 255, 0, 200] if x == 'LEGAL SHIP' else [255, 0, 0, 200]
            )
        else:
            df_detected['color'] = [[255, 0, 0, 200]] * len(df_detected)

        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=df_detected,
            get_position="[lon, lat]",
            get_color="color",
            get_radius=120,
            pickable=True,
            radius_min_pixels=5
        ))

    # RENDER MAP (This will show even if layers are empty)
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v10",
        initial_view_state=pdk.ViewState(
            latitude=LAT_CENTER,
            longitude=LON_CENTER,
            zoom=13.5,
            pitch=0
        ),
        layers=layers,
        tooltip={"html": "<b>{status}</b><br/>Lat: {lat}<br/>Lon: {lon}"}
    ))

# --- TAB 2: SAT FEED ---
with tab2:
    if os.path.exists(IMAGE_PATH):
        st.image(Image.open(IMAGE_PATH), use_container_width=True)
    else:
        try: st.image(GITHUB_URL, use_container_width=True)
        except: st.warning("No Satellite Feed Available")

# --- TAB 3: DATA ---
with tab3:
    c_a, c_b = st.columns(2)
    with c_a:
        st.caption("🟢 AUTHORIZED VESSELS (AIS)")
        st.dataframe(df_legal, use_container_width=True)
    with c_b:
        st.caption("🔴 DETECTED TARGETS (SAT)")
        st.dataframe(df_detected, use_container_width=True)
