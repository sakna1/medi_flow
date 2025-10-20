# File: app/gemini_ai.py

import google.generativeai as genai
import os
from app import db
from app.models import Patient, DiseaseDesc, DoctorLog, PatientLog
from datetime import date
import json

# Configure Gemini Client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize Gemini Model
try:
    AI_MODEL = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    print(f"Failed to initialize Gemini model: {e}")
    AI_MODEL = None


def calculate_age(dob):
    """Calculates age based on date of birth."""
    if not dob:
        return 0
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def call_gemini_for_queue(new_patient_id):
    if AI_MODEL is None:
        return {"error": "AI Model not initialized. Check API Key."}

    today = date.today()
    new_patient = Patient.query.get(new_patient_id)

    # Collect all currently waiting logs
    waiting_logs = PatientLog.query.filter(PatientLog.status.in_(["Waiting", "Assigned"])).all()

    # --- Aggregate patient data ---
    patients_data = []
    for log in waiting_logs:
        p = log.patient
        patients_data.append({
            "patient_id": p.id,
            "is_newly_scanned": (p.id == new_patient.id),
            "age": calculate_age(p.dob),
            "treatment_condition": p.treatment_status,
            "room_no": log.room_no,
            "doctor_id": log.doctor_id,
            "queue_number": log.queue_number
        })

    # --- Doctor-room info (basic only) ---
    doctor_rooms = []
    doctor_logs = DoctorLog.query.filter(DoctorLog.log_date == today).all()
    for log in doctor_logs:
        doctor_rooms.append({
            "room_no": log.room_no,
            "doctor_id": log.doctor_id
        })

    # --- AI Prompt (simplified, no estimated times) ---
    prompt = f"""
You are an AI Queue Manager. Recalculate queue order for ALL patients, including the patient marked 'is_newly_scanned': True.

[YOUR RULES]:
1. **ROOM ASSIGNMENT**: Only the patient marked 'is_newly_scanned' can be assigned a new room.
   - Choose any available room from the list below (preferably the one with fewer patients if possible).
2. **ROOM STABILITY**: Do NOT change the 'room_no' for existing patients ('is_newly_scanned': False).
3. **QUEUE RE-ORDERING**: For ALL patients (new and existing) within their assigned room:
   - Assign a new 'queue_number' (starting from 1) based on priority:
     a. Age >= 60 OR 'treatment_condition' == 'Active' → higher priority.
     b. All others come after.
4. **OUTPUT FORMAT**: Return ONLY a valid JSON list.

Patients:
{patients_data}

Available Rooms:
{doctor_rooms}

Return ONLY JSON list in this format:
[
  {{
    "patient_id": <int>,
    "room_no": <int>,
    "doctor_id": <int>,
    "queue_number": <int>
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
