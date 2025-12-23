import pandas as pd
import psycopg2

# !!! PASTE YOUR NEON CONNECTION STRING HERE !!!
DB_URL = "postgresql://neondb_owner:npg_rGV1neuthUa0@ep-orange-pine-ahlf4955-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def upload_data():
    try:
        # 1. Read the Local Excel File we made earlier
        df = pd.read_excel('ais_data.xlsx')

        # 2. Connect to Neon
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        # 3. Clear old data (to avoid duplicates)
        cur.execute("TRUNCATE TABLE authorized_ships;")

        # 4. Insert New Data
        for index, row in df.iterrows():
            cur.execute("""
                INSERT INTO authorized_ships (ship_id, ship_name, x_pixel, y_pixel, lat, lon)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (row['Ship_ID'], row['Ship_Name'], row['X_Pixel'], row['Y_Pixel'], row['Lat'], row['Lon']))

        conn.commit()
        cur.close()
        conn.close()
        print("✅ SUCCESS: All 8 ships saved to Neon Database!")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    upload_data()