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

# Professional Mobile-First CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-baseweb="tab-list"] { gap: 8px; }
    div[data-baseweb="tab"] {
        flex-grow: 1; text-align: center; background-color: #1f2937;
        border-radius: 5px 5px 0px 0px; padding: 10px; font-weight: 600;
    }
    div[aria-selected="true"] { background-color: #ff4b4b !important; color: white !important; }
    div[data-testid="stMetric"] {
        background-color: #262730; border-radius: 8px; padding: 15px;
        border-left: 5px solid #ff4b4b; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CONFIGURATION
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FILENAME = 'final_detection.jpg'
IMAGE_PATH = os.path.join(SCRIPT_DIR, IMAGE_FILENAME)

# --- ☁️ GITHUB SETTINGS (Fill these in!) ---
GITHUB_USER = "YourUsername"  # Replace with your GitHub Username
REPO_NAME = "YourRepoName"    # Replace with your Repo Name
BRANCH = "main"               
GITHUB_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{IMAGE_FILENAME}"

# DATABASE
DB_URL = "postgresql://neondb_owner:npg_rGV1neuthUa0@ep-orange-pine-ahlf4955-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# MAP CENTER (Alexandria)
LAT_CENTER = 31.185 
LON_CENTER = 29.870

# ==========================================
# 3. DATABASE FUNCTIONS
# ==========================================
def get_db_connection():
    try:
        return psycopg2.connect(DB_URL)
    except:
        return None

def load_authorized_ships():
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    
    try:
        df = pd.read_sql("SELECT * FROM authorized_ships", conn)
        conn.close()
        df.columns = df.columns.str.lower()
        if 'latitude' in df.columns: df.rename(columns={'latitude': 'lat'}, inplace=True)
        if 'longitude' in df.columns: df.rename(columns={'longitude': 'lon'}, inplace=True)
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        return df.dropna(subset=['lat', 'lon'])
    except: return pd.DataFrame()

def load_detected_ships():
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    try:
        df = pd.read_sql("SELECT * FROM detected_ships", conn)
        conn.close()
        return df
    except:
        conn.close()
        return pd.DataFrame()

# ==========================================
# 4. HEADER & NAVIGATION
# ==========================================
c1, c2 = st.columns([3, 1])
with c1: st.title("⚓ Port Command")
with c2: 
    if st.button("🔄 REFRESH", type="primary", use_container_width=True): st.rerun()

tab1, tab2, tab3 = st.tabs(["🗺️ MAP", "📷 SAT FEED", "📊 DATA"])

# ==========================================
# 5. TAB 1: LIVE MAP
# ==========================================
with tab1:
    st.markdown("### 🛰️ Tactical Situation")
    df_legal = load_authorized_ships()
    df_detected = load_detected_ships()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Legal (AIS)", len(df_legal))
    m2.metric("Detected", len(df_detected))
    diff = len(df_detected) - len(df_legal)
    
    if diff > 0:
        m3.metric("⚠️ Dark Ships", diff, delta="ALERT", delta_color="inverse")
    else:
        m3.metric("Status", "SECURE", delta="OK")

    layers = []
    
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
            zoom=13,
            pitch=0
        ),
        layers=layers,
        tooltip={"html": "<b>Target</b><br/>Lat: {lat}<br/>Lon: {lon}"}
    ))

# ==========================================
# 6. TAB 2: SATELLITE FEED (Silent Fallback)
# ==========================================
with tab2:
    st.markdown("### 📷 Live Analysis")
    
    # 1. Try Local File first
    if os.path.exists(IMAGE_PATH):
        image = Image.open(IMAGE_PATH)
        st.image(image, use_container_width=True)
        
    # 2. Fallback to GitHub URL (Silent)
    else:
        try:
            st.image(GITHUB_URL, use_container_width=True)
        except:
            st.error("❌ No Signal (Check GitHub Link)")

# ==========================================
# 7. TAB 3: RAW DATA
# ==========================================
with tab3:
    st.markdown("### 📂 Intelligence Logs")
    st.caption("🟢 AUTHORIZED VESSELS (AIS)")
    st.dataframe(load_authorized_ships(), use_container_width=True)
    st.divider()
    st.caption("🔴 DETECTED TARGETS (YOLOv8)")
    st.dataframe(load_detected_ships(), use_container_width=True)
