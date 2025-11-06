# File: app/wait_time_predictor.py
import joblib
import numpy as np
import os
from datetime import datetime

# Load trained model
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "wait_time_model.pkl")

try:
    model = joblib.load(MODEL_PATH)    
except Exception as e:
    model = None
    print(f"⚠️ Failed to load wait time model: {e}")


def predict_wait_time(age, disease_id, queue_length, disease_est_time,
                      treatment_status, available_doctors):
    """
    Predict waiting time using the trained model.
    Automatically computes derived features: queue_per_doctor, weighted_est_time, day_of_week.
    """
    if model is None:
        print("❌ Model not loaded.")
        return None

    # Convert treatment status
    treatment_status = 1 if treatment_status == "Active" else 0

    # Derived features
    queue_per_doctor = queue_length / available_doctors if available_doctors > 0 else queue_length
    weighted_est_time = disease_est_time * (1 + (queue_length / 10))
    scan_hour = datetime.now().hour
    day_of_week = datetime.now().weekday()  # 0 = Monday

    # Prepare feature array in correct order
    features = np.array([[ 
        age,
        disease_id,
        queue_length,
        disease_est_time,
        treatment_status,
        available_doctors,       
        queue_per_doctor,
        weighted_est_time,
        scan_hour,
        day_of_week
    ]])

    try:
        prediction = model.predict(features)[0]
        return round(float(prediction), 2)
    except Exception as e:
        print(f"Prediction error: {e}")
        return None
