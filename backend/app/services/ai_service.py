import random
# Note: Prices are now fetched from DB, this just predicts class
CLASSES = ["Carrot", "Tomato", "Pumpkin", "Corn", "Red_Chili", "Bell_Pepper", "Cucumber", "Unknown"]

def predict_image():
    # Mock Prediction
    weights = [1] * (len(CLASSES)-1) + [0.1]
    result = random.choices(CLASSES, weights=weights, k=1)[0]
    return result