# File: app/gemini_ai.py

import google.generativeai as genai
import os
from app import db
from app.models import Patient, DiseaseDesc, DoctorLog, PatientLog
from datetime import datetime, date
import json # Ensure json is imported for parsing

# Configure Gemini Client (Only run this once)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize the model once at the module level (for efficiency)
# Use the new, supported model name 'gemini-2.5-flash'
try:
    AI_MODEL = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    # Handle case where model initialization fails (e.g., bad API key)
    print(f"Failed to initialize Gemini model: {e}")
    AI_MODEL = None


def calculate_age(dob):
    """Calculates age based on date of birth."""
    if not dob:
        return 0
    today = date.today()
    # Subtract 1 if birthday hasn't occurred this year yet
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def call_gemini_for_queue(patient_id):
    if AI_MODEL is None:
        return {"error": "AI Model not initialized. Check API Key."}

    patient = Patient.query.get(patient_id)
    disease = DiseaseDesc.query.get(patient.disease_id)
    today = date.today()

    # Collect doctor-room data
    doctor_rooms = []
    # NOTE: You will need to ensure DoctorLog.log_date is a DATE field for this filter to work correctly
    doctor_logs = DoctorLog.query.filter(DoctorLog.log_date == today).all()
    
    for log in doctor_logs:
        waiting_patients = PatientLog.query.filter_by(room_no=log.room_no, status="Waiting").all()
        # Ensure log.room_no is not None for this filter to be meaningful

        # Calculate total estimated time for patients currently waiting in this room
        total_time = sum(int(p.disease.est_time or 0) for p in waiting_patients if p.disease)
        doctor_rooms.append({
            "room_no": log.room_no,
            "doctor_id": log.doctor_id,
            "queue_length": len(waiting_patients),
            "total_estimated_time": total_time
        })

    # Patient data for AI
    patient_data = {
        "patient_id": patient.id,
        "age": calculate_age(patient.dob), # Using the robust age function
        "treatment_condition": patient.treatment_status,
        "disease_id": patient.disease_id,
        "disease_estimated_time": int(''.join(filter(str.isdigit, str(disease.est_time))) or 0)
    }

    # Prompt for Gemini (kept mostly the same)
    prompt = f"""
You are an AI Queue Manager at a hospital. Your job is to assign this patient to the best room and queue.
[RULES]:
1. Choose the room with the lowest total estimated waiting time.
2. If two rooms have the same total time, choose the one with the shorter queue length.
3. The queue number should be 1 + the current queue length of the assigned room.
4. Within a room, prioritize older patients (age >= 60) or those with active treatment conditions by placing them before others (if applicable, but your primary job is room assignment).

Patient Info:
{patient_data}

Available Rooms (with current waiting stats):
{doctor_rooms}

Return ONLY a valid, single JSON object with the following keys and no other text:
{{
"room_no": <int or string>,
"doctor_id": <int or string>,
"queue_number": <int>,
"estimated_wait_time": <int in minutes>
}}
"""

    response = AI_MODEL.generate_content(prompt)

    # Parse AI JSON safely
    try:
        # Clean up common AI output issues (like markdown formatting)
        raw_text = response.text.strip().lstrip('`json').rstrip('`')
        ai_result = json.loads(raw_text)
        return ai_result

    except Exception:
        # Return an error object if JSON parsing fails, allowing the route to handle it
        return {"error": "Invalid JSON response from Gemini", "raw_output": response.text}

    # NOTE: This function no longer updates the DB. The route handles the DB update.