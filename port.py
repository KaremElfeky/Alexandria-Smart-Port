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
    initial_sidebar_state="collapsed" # Hides sidebar by default on mobile
)

# Professional Mobile-First CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    
    /* Bigger Tabs for easy tapping on phone */
    div[data-baseweb="tab-list"] {
        gap: 8px;
    }
    div[data-baseweb="tab"] {
        flex-grow: 1; /* Tabs stretch to fill screen width */
        text-align: center;
        background-color: #1f2937;
        border-radius: 5px 5px 0px 0px;
        padding: 10px;
        font-weight: 600;
    }
    div[aria-selected="true"] {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    
    /* Metrics Styling */
    div[data-testid="stMetric"] {
        background-color: #262730;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# CONFIG
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(SCRIPT_DIR, 'final_detection.jpg')
DB_URL = "postgresql://neondb_owner:npg_rGV1neuthUa0@ep-orange-pine-ahlf4955-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# MAP CENTER
LAT_CENTER = 31.185
LON_CENTER = 29.870

# ==========================================
# 2. DATABASE FUNCTIONS
# ==========================================
def get_db_connection():
    try:
        return psycopg2.connect(DB_URL)
    except Exception as e:
        st.error(f"❌ DB Connection Error: {e}")
        return None

def load_authorized_ships():
    """🟢 Returns the Legal Ships (AIS)"""
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    
    try:
        df = pd.read_sql("SELECT * FROM authorized_ships", conn)
        conn.close()
        
        # Cleanup
        df.columns = df.columns.str.lower()
        if 'latitude' in df.columns: df.rename(columns={'latitude': 'lat'}, inplace=True)
        if 'longitude' in df.columns: df.rename(columns={'longitude': 'lon'}, inplace=True)
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        return df.dropna(subset=['lat', 'lon'])
    except Exception as e:
        return pd.DataFrame()

def load_detected_ships():
    """🔴 Returns the Detected Ships (Satellite)"""
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    
    try:
        df = pd.read_sql("SELECT * FROM detected_ships", conn)
    except:
        conn.close()
        return pd.DataFrame() 
        
    conn.close()
    return df

# ==========================================
# 3. HEADER & STATUS BAR
# ==========================================
# This row stays visible at the top
c1, c2 = st.columns([3, 1])
with c1:
    st.title("⚓ Port Command")
with c2:
    if st.button("🔄 REFRESH", type="primary", use_container_width=True):
        st.rerun()

# ==========================================
# 4. MAIN NAVIGATION (TABS)
# ==========================================
# Tabs are better than Sidebar for mobile
tab1, tab2, tab3 = st.tabs(["🗺️ MAP", "📷 SAT FEED", "📊 DATA"])

# --- TAB 1: LIVE MAP ---
with tab1:
    st.markdown("### 🛰️ Tactical Situation")
    
    # Load Data
    df_legal = load_authorized_ships()
    df_detected = load_detected_ships()
    
    # Smart Metrics Layout
    m1, m2, m3 = st.columns(3)
    m1.metric("Legal (AIS)", len(df_legal))
    m2.metric("Detected", len(df_detected))
    
    diff = len(df_detected) - len(df_legal)
    if diff > 0:
        m3.metric("⚠️ Dark Ships", diff, delta="ALERT", delta_color="inverse")
    else:
        m3.metric("Status", "SECURE", delta="OK")

    # MAP LAYERS
    layers = []

    # Layer 1: Green (Legal)
    if not df_legal.empty:
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=df_legal,
            get_position="[lon, lat]",
            get_color="[0, 255, 0, 200]",
            get_radius=150,
            pickable=True,
            radius_min_pixels=5
        ))

    # Layer 2: Red (Detected)
    if not df_detected.empty:
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=df_detected,
            get_position="[lon, lat]",
            get_color="[255, 0, 0, 200]", 
            get_radius=150,
            pickable=True,
            radius_min_pixels=5
        ))

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v10",
        initial_view_state=pdk.ViewState(
            latitude=LAT_CENTER,
            longitude=LON_CENTER,
            zoom=12.5,
            pitch=0
        ),
        layers=layers,
        tooltip={"html": "<b>Target Detected</b><br/>Lat: {lat}<br/>Lon: {lon}"}
    ))

# --- TAB 2: SATELLITE FEED ---
with tab2:
    st.markdown("### 📷 Live Analysis")
    
    if os.path.exists(IMAGE_PATH):
        mod_time = os.path.getmtime(IMAGE_PATH)
        ts = datetime.fromtimestamp(mod_time).strftime('%H:%M:%S')
        st.info(f"Last Satellite Pass: {ts}")
        
        image = Image.open(IMAGE_PATH)
        st.image(image, use_container_width=True)
    else:
        st.warning("No Satellite Feed Available. Run 'model.py'.")

# --- TAB 3: RAW DATA ---
with tab3:
    st.markdown("### 📂 Intelligence Logs")
    
    st.caption("🟢 AUTHORIZED VESSELS (AIS)")
    st.dataframe(load_authorized_ships(), use_container_width=True)
    
    st.divider()
    
    st.caption("🔴 DETECTED TARGETS (YOLOv8)")
    st.dataframe(load_detected_ships(), use_container_width=True)
