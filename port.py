import streamlit as st
from ultralytics import YOLO
import cv2
import numpy as np
import pandas as pd
import pydeck as pdk
from math import radians, cos, sin, asin, sqrt

# ==========================================
# 1. CONFIGURATION & PHYSICS
# ==========================================
st.set_page_config(page_title="Alexandria Port Command", layout="wide")

IMAGE_FILE = 'sat3.tif'
MODEL_PATH = 'best.pt' 

# MAP CALIBRATION (Alexandria Western Harbour)
IMG_W, IMG_H = 1178, 665
LAT_NORTH = 31.202
LAT_SOUTH = 31.168
LON_WEST  = 29.855
LON_EAST  = 29.885

def pixel_to_gps(x, y):
    lat = LAT_NORTH - (y / IMG_H) * (LAT_NORTH - LAT_SOUTH)
    lon = LON_WEST + (x / IMG_W) * (LON_EAST - LON_WEST)
    return lat, lon

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371000 
    return c * r

# ==========================================
# 2. DATA LOADER (TEST MODE)
# ==========================================
@st.cache_resource
def load_model():
    return YOLO(MODEL_PATH)

def load_ais_data():
    try:
        # Load local Excel file
        df = pd.read_excel("ais_data.xlsx")
        # Standardize column names (force lowercase)
        df.columns = df.columns.str.lower()
        return df
    except Exception as e:
        st.error(f"❌ Failed to load 'ais_data.xlsx'. Error: {e}")
        st.stop()

# ==========================================
# 3. THE CORE INTELLIGENCE (Fixed for 4-Channel TIFs)
# ==========================================
def run_surveillance_system(image_path, ais_df, model):
    
    # FORCE 3-CHANNEL IMAGE
    img_cv = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    
    if img_cv.shape[2] == 4:
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGRA2RGB)
    else:
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)

    results = model.predict(img_rgb, conf=0.25)
    
    final_targets = []
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            
            det_lat, det_lon = pixel_to_gps(cx, cy)
            
            # FUSION LOGIC
            status = "DARK SHIP"
            match_name = "UNKNOWN"
            match_id = "N/A"
            min_dist = float('inf')
            
            for index, ship in ais_df.iterrows():
                ais_lat = ship.get('lat') or ship.get('latitude')
                ais_lon = ship.get('lon') or ship.get('longitude')
                ais_name = ship.get('ship_name') or ship.get('name')
                ais_id = ship.get('ship_id') or ship.get('mmsi')

                dist_meters = haversine(det_lon, det_lat, ais_lon, ais_lat)
                
                # TOLERANCE INCREASED TO 1000m TO FIX MISMATCH
                if dist_meters < 1000: 
                    if dist_meters < min_dist:
                        min_dist = dist_meters
                        status = "LEGAL SHIP"
                        match_name = ais_name
                        match_id = ais_id

            if status == "LEGAL SHIP":
                color_map = [0, 255, 0, 200]
                box_color = (0, 255, 0)
            else:
                color_map = [255, 0, 0, 200]
                box_color = (255, 0, 0)

            final_targets.append({
                "id": str(match_id),
                "name": str(match_name),
                "status": status,
                "lat": det_lat,
                "lon": det_lon,
                "color": color_map,
                "bbox": (x1, y1, x2, y2),
                "box_color": box_color
            })
            
    return final_targets, img_rgb

# ==========================================
# 4. DASHBOARD UI
# ==========================================
try:
    model = load_model()
    df_ais = load_ais_data()
    
    if df_ais is not None:
        targets, processed_img = run_surveillance_system(IMAGE_FILE, df_ais, model)
        
        legal_cnt = len([t for t in targets if t['status'] == "LEGAL SHIP"])
        illegal_cnt = len([t for t in targets if t['status'] == "DARK SHIP"])

        st.title("⚓ Alexandria Port Command (AI Test Mode)")
        
        # --- CALIBRATION DEBUG PANEL ---
        st.sidebar.header("🔧 Debug / Calibration")
        st.sidebar.write("If Legal ships show as Dark, verify these coordinates match your Excel:")
        debug_data = []
        for t in targets:
            debug_data.append({
                "Status": t['status'],
                "Lat": round(t['lat'], 4),
                "Lon": round(t['lon'], 4)
            })
        st.sidebar.dataframe(pd.DataFrame(debug_data))
        # -------------------------------

        col1, col2, col3 = st.columns(3)
        col1.metric("Satellite Targets", len(targets))
        col2.metric("✅ Verified Legal", legal_cnt)
        col3.metric("🚨 DARK SHIPS", illegal_cnt, delta_color="inverse")

        tab1, tab2 = st.tabs(["🗺️ Tactical Map", "📷 Computer Vision Feed"])

        with tab1:
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=targets,
                get_position="[lon, lat]",
                get_color="color",
                get_radius=200,
                pickable=True
            )
            st.pydeck_chart(pdk.Deck(
                layers=[layer],
                initial_view_state=pdk.ViewState(
                    latitude=(LAT_NORTH+LAT_SOUTH)/2, 
                    longitude=(LON_WEST+LON_EAST)/2, 
                    zoom=13
                ),
                tooltip={"html": "<b>{status}</b><br/>ID: {id}<br/>Name: {name}"}
            ))

        with tab2:
            annotated_img = processed_img.copy()
            for t in targets:
                x1, y1, x2, y2 = t['bbox']
                cv2.rectangle(annotated_img, (x1, y1), (x2, y2), t['box_color'], 3)
                label = t['status']
                (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
                cv2.rectangle(annotated_img, (x1, y1 - 20), (x1 + w, y1), t['box_color'], -1)
                cv2.putText(annotated_img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            st.image(annotated_img, use_container_width=True)

except Exception as e:
    st.error(f"Detailed Error Log: {e}")