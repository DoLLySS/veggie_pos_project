import os, requests
BASE_DIR = "dataset"
VEGGIES = ["Carrot", "Tomato", "Pumpkin", "Corn", "Red_Chili", "Bell_Pepper", "Unknown"]
if not os.path.exists(BASE_DIR): os.makedirs(BASE_DIR)
for v in VEGGIES:
    p = os.path.join(BASE_DIR, v)
    os.makedirs(p, exist_ok=True)
    try:
        with open(os.path.join(p, "1.png"), 'wb') as f: f.write(requests.get(f"https://placehold.co/400?text={v}").content)
    except: pass
print("Done")