import cv2
import numpy as np

# ==========================================
# 1. SETUP
# ==========================================
IMAGE_PATH = 'sat3.tif'
OUTPUT_PATH = 'sat3_analysis_result.jpg'

def analyze_satellite_image(image_path):
    print(f"🛰️ INITIALIZING SATELLITE ANALYSIS FOR: {image_path}")
    
    # Load Image
    img = cv2.imread(image_path)
    if img is None:
        print("❌ Error: Image not found.")
        return

    # Convert to HSV (Hue, Saturation, Value)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # ==========================================
    # 2. DEFINING COLOR MASKS
    # ==========================================
    
    # RANGE FOR GREEN (Legal Ships)
    lower_green = np.array([40, 50, 50])
    upper_green = np.array([80, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)

    # RANGE FOR RED (Dark Ships)
    # Red is at the start (0-10) AND end (170-180) of the color spectrum
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])
    
    # --- FIX IS HERE ---
    # We create two separate masks for the red ranges and combine them
    mask_red_part1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask_red_part2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = mask_red_part1 + mask_red_part2

    # ==========================================
    # 3. DETECTION ENGINE
    # ==========================================
    
    # -- FIND GREEN SHIPS --
    contours_g, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    green_count = 0
    
    for cnt in contours_g:
        if cv2.contourArea(cnt) > 50: # Filter small noise
            green_count += 1
            x, y, w, h = cv2.boundingRect(cnt)
            # Draw Confirmation Box
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(img, "LEGAL", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # -- FIND RED SHIPS --
    contours_r, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    red_count = 0
    
    for cnt in contours_r:
        if cv2.contourArea(cnt) > 50:
            red_count += 1
            x, y, w, h = cv2.boundingRect(cnt)
            # Draw Alert Box
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(img, "DARK SHIP", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # ==========================================
    # 4. INTELLIGENCE REPORT
    # ==========================================
    print("\n--------------------------------------")
    print("⚓ SENSOR FUSION REPORT")
    print("--------------------------------------")
    print(f"Total Targets Detected: {green_count + red_count}")
    print(f"✅ Legal Vessels (Green): {green_count}")
    print(f"🚨 Dark Ships (Red):      {red_count}")
    print("--------------------------------------")
    
    if green_count == 8 and red_count == 2:
        print("✅ SYSTEM VERIFIED: Matches expected Intelligence (8 Legal, 2 Dark).")
    else:
        print(f"⚠️ SYSTEM ALERT: Found {green_count} Green and {red_count} Red. Adjust lighting/thresholds if incorrect.")

    # Save the analyzed photo
    cv2.imwrite(OUTPUT_PATH, img)
    print(f"\nVisual proof saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    analyze_satellite_image(IMAGE_PATH)