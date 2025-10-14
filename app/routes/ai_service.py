import os
import requests
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
load_dotenv()
os.environ['PYTHONHTTPSVERIFY'] = '0'

API_KEY = os.getenv("GEMINI_API_KEY")  
print("✅ GEMINI_API_KEY Loaded:", API_KEY)
 # ← your API key is loaded here

# 🔹 2. Define function that calls Gemini API
def call_gemini_ai(new_patient, rooms):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"

    # Create a prompt for Gemini
    prompt = f"""
    You are an AI assistant helping with hospital queue management.
    Assign the new patient to the most suitable room or doctor.
    Patient info: {new_patient}
    Current room status: {rooms}
    """

    # Make the API call
    response = requests.post(
        url,
        json={
            "contents": [{"parts": [{"text": prompt}]}]
        },
        headers={"Content-Type": "application/json"}
    )

    # Handle the response
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text}

def get_all_rooms_status():
    # Fetch current room data from DB (example static for now)
    return [
        {
            "room_number": "101",
            "patients": [
                {"patient_id": 201, "disease_id": "Blood cancer", "est_time": 20},
                {"patient_id": 202, "disease_id": "Lung cancer", "est_time": 30}
            ]
        },
        {
            "room_number": "102",
            "patients": [
                {"patient_id": 301, "disease_id": "Skin cancer", "est_time": 15}
            ]
        }
    ]
