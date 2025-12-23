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
    div[data-baseweb="tab-list"] { gap: 8px; }
    div[data-baseweb="tab"] {
        flex-grow: 1; text-align: center; background-color: #1f2937;
        border-radius: 5px 5px 0px 0px; padding: 10px; font-weight: 600; font-size: 1.1rem;
    }
    div[aria-selected="true"] { background-color: #ff4b4b !important; color: white !important; }
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
GITHUB_USER = "YourUsername" 
REPO_NAME = "YourRepoName"    
GITHUB_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/{IMAGE_FILENAME}"
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
        if 'latitude' in df.columns: df.rename(columns={'latitude': 'lat'}, inplace=True)
        if 'longitude' in df.columns: df.rename(columns={'longitude': 'lon'}, inplace=True)
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        return df.dropna(subset=['lat', 'lon'])
    except: return pd.DataFrame()

# ==========================================
# 3. HEADER & METRICS
# ==========================================
c1, c2 = st.columns([3, 1])
with c1: st.title("⚓ Port Command")
with c2: 
    if st.button("🔄 REFRESH SYSTEM", type="primary", use_container_width=True): st.rerun()

st.divider()

# --- LOAD & FILTER DATA ---
df_legal_ais = load_data("authorized_ships") # From AIS Table
df_all_detected = load_data("detected_ships") # From Satellite

# Separate the Good Guys from the Bad Guys
# Logic: If status contains "LEGAL", it's Good. Everything else is Bad.
if not df_all_detected.empty and 'status' in df_all_detected.columns:
    df_green = df_all_detected[df_all_detected['status'].str.contains("LEGAL", case=False, na=False)]
    df_red   = df_all_detected[~df_all_detected['status'].str.contains("LEGAL", case=False, na=False)]
else:
    df_green = pd.DataFrame()
    df_red   = df_all_detected # Assume all bad if no status

# --- METRICS ---
m1, m2, m3 = st.columns(3)
m1.metric("🟢 Authorized (AIS)", len(df_legal_ais))
m2.metric("🔵 Verified Matches", len(df_green)) # Matches found by Sat

if len(df_red) > 0:
    m3.metric("⚠️ Dark Ships", len(df_red), delta="THREAT DETECTED", delta_color="inverse")
else:
    m3.metric("Status", "SECURE", delta="ALL CLEAR")

st.markdown("<br>", unsafe_allow_html=True) 

# ==========================================
# 4. TABS & MAP
# ==========================================
tab1, tab2, tab3 = st.tabs(["🗺️ TACTICAL MAP", "📷 SAT FEED", "📊 RAW DATA"])

with tab1:
    layers = []

    # 1. AIS Data (Hollow Circles or Small Dots)
    if not df_legal_ais.empty:
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=df_legal_ais,
            get_position="[lon, lat]",
            get_color="[0, 255, 0, 100]", # Transparent Green
            get_radius=200,
            pickable=True,
        ))

    # 2. Verified Satellite Matches (Solid Green)
    if not df_green.empty:
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=df_green,
            get_position="[lon, lat]",
            get_color="[0, 255, 0, 255]", # Bright Green
            get_radius=120,
            pickable=True,
        ))

    # 3. DARK SHIPS (Solid Red) - This is the Layer you want!
    if not df_red.empty:
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=df_red,
            get_position="[lon, lat]",
            get_color="[255, 0, 0, 255]", # Bright Red
            get_radius=120,
            pickable=True,
        ))

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v10",
        initial_view_state=pdk.ViewState(
            latitude=LAT_CENTER,
            longitude=LON_CENTER,
            zoom=13.5,
            pitch=0
        ),
        layers=layers,
        tooltip={"html": "<b>STATUS: {status}</b><br/>Lat: {lat}<br/>Lon: {lon}"}
    ))

with tab2:
    if os.path.exists(IMAGE_PATH):
        st.image(Image.open(IMAGE_PATH), use_container_width=True)
    else:
        try: st.image(GITHUB_URL, use_container_width=True)
        except: st.warning("No Satellite Feed Available")

with tab3:
    c_a, c_b = st.columns(2)
    with c_a:
        st.caption("🟢 VERIFIED LEGAL (SAT MATCHED)")
        st.dataframe(df_green, use_container_width=True)
    with c_b:
        st.caption("🔴 DARK SHIPS (UNIDENTIFIED)")
        st.dataframe(df_red, use_container_width=True)
