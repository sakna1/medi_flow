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


def call_gemini_for_queue(new_patient_id): # Renamed argument for clarity
    if AI_MODEL is None:
        return {"error": "AI Model not initialized. Check API Key."}

    today = date.today()
    new_patient = Patient.query.get(new_patient_id)
    disease = DiseaseDesc.query.get(new_patient.disease_id)

    # Collect all currently waiting logs
    waiting_logs = PatientLog.query.filter(PatientLog.status.in_(["Waiting", "Assigned"])).all()

    # --- Start Data Aggregation ---
    patients_data = []
    
    # Aggregate data for all waiting/assigned patients
    for log in waiting_logs:
        p = log.patient
        d = p.disease
        patients_data.append({
            "patient_id": p.id,
            "is_newly_scanned": (p.id == new_patient.id), # Mark the new patient
            "age": calculate_age(p.dob),
            "treatment_condition": p.treatment_status,
            "disease_estimated_time": int(''.join(filter(str.isdigit, str(d.est_time))) or 0),
            "room_no": log.room_no, # AI must NOT change this for existing patients
            "doctor_id": log.doctor_id,
            "queue_number": log.queue_number
        })
        
    # Doctor-room data (Kept the same)
    doctor_rooms = []
    doctor_logs = DoctorLog.query.filter(DoctorLog.log_date == today).all()
    for log in doctor_logs:
        waiting_patients = [p for p in waiting_logs if p.room_no == log.room_no]
        total_time = sum(int(p.patient.disease.est_time or 0) for p in waiting_patients if p.patient.disease)
        doctor_rooms.append({
            "room_no": log.room_no,
            "doctor_id": log.doctor_id,
            "total_estimated_time": total_time # Used for Room Selection
        })
    # --- End Data Aggregation ---

    # New prompt (More specific rules for the AI)
    prompt = f"""
You are an AI Queue Manager. Recalculate queue order and waiting times for ALL patients, including the patient marked 'is_newly_scanned': True.

[YOUR ASSIGNMENT RULES]:
1. **ROOM ASSIGNMENT**: Only the patient marked 'is_newly_scanned' can be assigned a new room. Choose the room with the lowest total estimated time from Available Rooms.
2. **ROOM STABILITY**: DO NOT change the 'room_no' for any patient where 'is_newly_scanned' is False.
3. **QUEUE RE-ORDERING**: For ALL patients (new and existing) within their assigned room, assign a new 'queue_number' (starting at 1) based on priority:
    a. Priority 1: Age >= 60 OR 'treatment_condition' is 'Active' or similar.
    b. Priority 2: All others.
4. **ESTIMATED WAIT TIME**: Calculate a new 'estimated_wait_time' for EVERY patient based on the sum of estimated times of patients ahead of them in their queue.
5. **OUTPUT FORMAT**: Return ONLY a valid, single JSON list.

Patients:
{patients_data}

Available Rooms:
{doctor_rooms}

Return ONLY JSON list with the following structure for ALL patients:
[
  {{
    "patient_id": <int>,
    "room_no": <int>,
    "doctor_id": <int>,
    "queue_number": <int>,
    "estimated_wait_time": <int>
  }},
  ...
]
"""
    response = AI_MODEL.generate_content(prompt)
    try:
        raw_text = response.text.strip().lstrip('`json').rstrip('`')
        ai_result = json.loads(raw_text)
        return ai_result
    except Exception as e:
        return {"error": "Invalid JSON response from Gemini", "raw_output": response.text}
