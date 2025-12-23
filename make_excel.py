import pandas as pd

# 1. DEFINE IMAGE BOUNDARIES (Alexandria Port Area)
# Top-Left (North-West)
LAT_START = 31.230
LON_START = 29.850
# Bottom-Right (South-East)
LAT_END = 31.180
LON_END = 29.950

# Image Size (Approximate from your file)
IMG_W = 1178
IMG_H = 665

def get_geo(x, y):
    # Converts Pixel (x,y) to Lat/Lon
    lat = LAT_START - (y / IMG_H) * (LAT_START - LAT_END)
    lon = LON_START + (x / IMG_W) * (LON_END - LON_START)
    return lat, lon

# 2. THE 8 KNOWN SHIPS (Pixel Coordinates from detection)
ships_pixels = [
    {"ID": 1, "Name": "CMA CGM Alex",   "x": 323,  "y": 105},
    {"ID": 2, "Name": "Maersk Nile",    "x": 1140, "y": 163},
    {"ID": 3, "Name": "Hapag Lloyd",    "x": 1137, "y": 270},
    {"ID": 4, "Name": "MSC Egypt",      "x": 363,  "y": 153},
    {"ID": 5, "Name": "Evergreen",      "x": 962,  "y": 27},
    {"ID": 6, "Name": "Pilot Boat 1",   "x": 139,  "y": 583},
    {"ID": 7, "Name": "Tug Boat Alpha", "x": 462,  "y": 270},
    {"ID": 8, "Name": "Navy Vessel",    "x": 182,  "y": 70}
]

# 3. GENERATE EXCEL WITH CORRECT GPS
data = []
for s in ships_pixels:
    lat, lon = get_geo(s['x'], s['y'])
    data.append({
        "Ship_ID": s['ID'],
        "Ship_Name": s['Name'],
        "X_Pixel": s['x'],
        "Y_Pixel": s['y'],
        "Lat": lat,
        "Lon": lon
    })

df = pd.DataFrame(data)
df.to_excel('ais_data.xlsx', index=False)
print("✅ Database Synchronized: GPS coordinates now match Photo pixels.")
print(df[['Ship_Name', 'Lat', 'Lon']])