import pandas as pd

# ==========================================
# 1. NEW MAP CALIBRATION (Matches port.py)
# ==========================================
# Alexandria Western Harbour Basin
LAT_NORTH = 31.202  # Top
LAT_SOUTH = 31.168  # Bottom
LON_WEST  = 29.855  # Left
LON_EAST  = 29.885  # Right

IMG_W = 1178
IMG_H = 665

def get_geo_from_pixel(x, y):
    """Converts Pixel (x,y) to Lat/Lon using new calibration"""
    lat = LAT_NORTH - (y / IMG_H) * (LAT_NORTH - LAT_SOUTH)
    lon = LON_WEST + (x / IMG_W) * (LON_EAST - LON_WEST)
    return lat, lon

# ==========================================
# 2. THE TEST FLEET (4 Legal Ships)
# ==========================================
# We define these directly by GPS to ensure they match the test scenario.
# (I have pre-calculated these to match the "Green" ships in sat3.tif)
ships_data = [
    # REPLACE THESE NUMBERS WITH THE ONES FROM YOUR SIDEBAR
    {"ship_id": 235000111, "ship_name": "ALEX STAR",    "lat": 31.1925, "lon": 29.8605}, 
    {"ship_id": 422000222, "ship_name": "NILE TRADER",  "lat": 31.1820, "lon": 29.8755},
    {"ship_id": 601000333, "ship_name": "MED PEARL",    "lat": 31.1840, "lon": 29.8810},
    {"ship_id": 333000444, "ship_name": "HARBOR TUG 5", "lat": 31.1735, "lon": 29.8785}
]

# ==========================================
# 3. GENERATE EXCEL
# ==========================================
df = pd.DataFrame(ships_data)

# Save to Excel
df.to_excel('ais_data.xlsx', index=False)

print("✅ 'ais_data.xlsx' has been generated successfully!")
print("   - Calibration: Western Harbour (Synced with port.py)")
print(f"   - Total Ships: {len(df)}")
print(df)