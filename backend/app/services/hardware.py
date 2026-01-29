import random
import time
import threading

class HardwareState:
    def __init__(self):
        self.current_weight = 0.0
        self.is_stable = True
        self.tare_offset = 0.0

state = HardwareState()

# --- Hardware Setup ---
try:
    import RPi.GPIO as GPIO
    from hx711 import HX711
    IS_RASPBERRY_PI = True
    print("✅ Mode: Raspberry Pi (Real Sensor)")
except ImportError:
    IS_RASPBERRY_PI = False
    print("⚠️ Mode: PC Simulation")

def scale_reader():
    if IS_RASPBERRY_PI:
        try:
            hx = HX711(dout_pin=5, pd_sck_pin=6)
            hx.set_scale_ratio(1000) # Calibrate here
            hx.reset()
            state.tare_offset = 0
            while True:
                val = hx.get_weight_mean(5)
                if val < 0.1: 
                    state.current_weight = 0.0
                    state.is_stable = True
                else:
                    diff = abs(val - state.current_weight)
                    state.is_stable = diff < 0.1
                    state.current_weight = float(val)
                time.sleep(0.1)
        except: pass
    else:
        # Simulation
        state.tare_offset = 0.5 # Auto Tare
        raw = 0.5
        target = 0.5
        while True:
            if random.random() < 0.05: target = random.choice([0.5, 1.5, 3.0, 0.0])
            diff = (target - raw) * 0.1
            raw += diff + random.uniform(-0.02, 0.02)
            state.is_stable = abs(diff) < 0.02
            state.current_weight = max(0, round(raw - state.tare_offset, 2))
            time.sleep(0.1)

threading.Thread(target=scale_reader, daemon=True).start()

def get_weight_data():
    return {"weight": state.current_weight, "is_stable": state.is_stable}