import streamlit as st
import os
import time
from PIL import Image
from datetime import datetime
import pydeck as pdk
import pandas as pd
import psycopg2

# ==========================================
# 1. SETUP
# ==========================================
st.set_page_config(page_title="Alexandria Port Command", page_icon="⚓", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-baseweb="tab-list"] { gap: 8px; }
    div[data-baseweb="tab"] {
        flex-grow: 1; text-align: center; background-color: #1f2937; border-radius: 5px 5px 0px 0px; padding: 10px; font-weight: 600;
    }
    div[aria-selected="true"] { background-color: #ff4b4b !important; color: white !important; }
    div[data-testid="stMetric"] { background-color: #262730; border-radius: 8px; padding: 15px; border-left: 5px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# CONFIG
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FILENAME = 'final_detection.jpg'
IMAGE_PATH = os.path.join(SCRIPT_DIR, IMAGE_FILENAME)
DB_URL = "postgresql://neondb_owner:npg_rGV1neuthUa0@ep-orange-pine-ahlf4955-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# --- ☁️ GITHUB FALLBACK (Edit User/Repo!) ---
GITHUB_USER = "YourUsername"  
REPO_NAME = "YourRepoName"    
GITHUB_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/{IMAGE_FILENAME}"

# --- MAP CALIBRATION (MATCHES MODEL.PY) ---
LAT_NORTH = 31.202
LAT_SOUTH = 31.168
LON_WEST  = 29.855
LON_EAST  = 29.885
LAT_CENTER = (LAT_NORTH + LAT_SOUTH) / 2
LON_CENTER = (LON_WEST + LON_EAST) / 2

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
        if 'latitude' in df.columns: df.rename(columns={'latitude': 'lat'}, inplace=True)
        if 'longitude' in df.columns: df.rename(columns={'longitude': 'lon'}, inplace=True)
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        return df.dropna(subset=['lat', 'lon'])
    except: return pd.DataFrame()

# ==========================================
# 3. UI LAYOUT
# ==========================================
c1, c2 = st.columns([3, 1])
with c1: st.title("⚓ Port Command")
with c2: 
    if st.button("🔄 REFRESH", type="primary", use_container_width=True): st.rerun()

tab1, tab2, tab3 = st.tabs(["🗺️ MAP", "📷 SAT FEED", "📊 DATA"])

# TAB 1: MAP
with tab1:
    st.markdown("### 🛰️ Tactical Situation")
    df_legal = load_data("authorized_ships")
    df_detected = load_data("detected_ships")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Legal (AIS)", len(df_legal))
    m2.metric("Detected", len(df_detected))
    
    # Calculate Dark Ships based on Status
    dark_count = len(df_detected[df_detected['status'] == 'DARK SHIP']) if not df_detected.empty else 0
    
    if dark_count > 0:
        m3.metric("⚠️ Dark Ships", dark_count, delta="ALERT", delta_color="inverse")
    else:
        m3.metric("Status", "SECURE", delta="OK")

    layers = []
    if not df_legal.empty:
        layers.append(pdk.Layer("ScatterplotLayer", data=df_legal, get_position="[lon, lat]", get_color="[0, 255, 0, 200]", get_radius=120, pickable=True))
    
    if not df_detected.empty:
        # Green for Legal Matches, Red for Dark Ships
        # We map colors: 'LEGAL SHIP' -> Green, 'DARK SHIP' -> Red
        df_detected['color'] = df_detected['status'].apply(lambda x: [0, 255, 0, 200] if x == 'LEGAL SHIP' else [255, 0, 0, 200])
        
        layers.append(pdk.Layer("ScatterplotLayer", data=df_detected, get_position="[lon, lat]", get_color="color", get_radius=120, pickable=True))

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v10",
        initial_view_state=pdk.ViewState(latitude=LAT_CENTER, longitude=LON_CENTER, zoom=13.5),
        layers=layers,
        tooltip={"html": "<b>{status}</b><br/>Lat: {lat}<br/>Lon: {lon}"}
    ))

# TAB 2: FEED
with tab2:
    st.markdown("### 📷 Live Analysis")
    if os.path.exists(IMAGE_PATH):
        st.image(Image.open(IMAGE_PATH), use_container_width=True)
    else:
        try: st.image(GITHUB_URL, use_container_width=True)
        except: st.error("❌ No Signal")

# TAB 3: DATA
with tab3:
    st.markdown("### 📂 Intelligence Logs")
    st.caption("🟢 AUTHORIZED VESSELS (AIS)")
    st.dataframe(df_legal, use_container_width=True)
    st.divider()
    st.caption("🔴 DETECTED TARGETS (YOLOv8)")
    st.dataframe(df_detected, use_container_width=True)
