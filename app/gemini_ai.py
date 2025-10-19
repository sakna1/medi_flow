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

    today = date.today()
    new_patient = Patient.query.get(patient_id)
    disease = DiseaseDesc.query.get(new_patient.disease_id)

    # Collect all currently waiting patients + this new one
    waiting_logs = PatientLog.query.filter(PatientLog.status.in_(["Waiting", "Assigned"])).all()

    patients_data = []
    for log in waiting_logs:
        p = log.patient
        d = p.disease
        patients_data.append({
            "patient_id": p.id,
            "age": calculate_age(p.dob),
            "treatment_condition": p.treatment_status,
            "disease_id": p.disease_id,
            "disease_estimated_time": int(''.join(filter(str.isdigit, str(d.est_time))) or 0),
            "room_no": log.room_no,
            "doctor_id": log.doctor_id,
            "queue_number": log.queue_number
        })

    # Also add the newly scanned patient (if not already in waiting)
    if not any(p["patient_id"] == new_patient.id for p in patients_data):
        patients_data.append({
            "patient_id": new_patient.id,
            "age": calculate_age(new_patient.dob),
            "treatment_condition": new_patient.treatment_status,
            "disease_id": new_patient.disease_id,
            "disease_estimated_time": int(''.join(filter(str.isdigit, str(disease.est_time))) or 0),
            "room_no": None,
            "doctor_id": None,
            "queue_number": None
        })

    # Doctor-room data
    doctor_rooms = []
    doctor_logs = DoctorLog.query.filter(DoctorLog.log_date == today).all()
    for log in doctor_logs:
        waiting_patients = [p for p in waiting_logs if p.room_no == log.room_no]
        total_time = sum(int(p.patient.disease.est_time or 0) for p in waiting_patients if p.patient.disease)
        doctor_rooms.append({
            "room_no": log.room_no,
            "doctor_id": log.doctor_id,
            "queue_length": len(waiting_patients),
            "total_estimated_time": total_time
        })

    # New prompt
    prompt = f"""
You are an AI Queue Manager. Recalculate queue order and waiting times for ALL patients, including a new one.
[RULES]:
1. Reassign the new patient to a room with the lowest total waiting time.
2. Do not change room for existing patients, but reorder within a room based on age >=60 and active treatment condition.
3. Estimate total wait time per patient (based on disease_estimated_time).
4. Return updated queue order for all patients.

Patients:
{patients_data}

Available Rooms:
{doctor_rooms}

Return ONLY JSON list with each patient's details:
[
  {{
    "patient_id": <int>,
    "room_no": <string>,
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
