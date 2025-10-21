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
    if not new_patient:
        return {"error": f"Patient with ID {new_patient_id} not found."}

    # --- Collect all currently waiting/assigned logs ---
    waiting_logs = PatientLog.query.filter(PatientLog.status.in_(["waiting", "assigned"])).all()

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

    # --- Doctor-room info ---
    doctor_rooms = []
    doctor_logs = DoctorLog.query.filter(DoctorLog.log_date == today).all()
    for log in doctor_logs:
        doctor_rooms.append({
            "room_no": log.room_no,
            "doctor_id": log.doctor_id,
            "patients_per_room": log.patients_per_room or 0
        })

    # --- AI Prompt ---
    prompt = f"""
You are an AI Queue Manager. Your task is to recalculate queue order for ALL patients in the system, including the patient marked "is_newly_scanned": true.

[YOUR RULES]

1. **ROOM ASSIGNMENT**
   - Only the patient with `"is_newly_scanned": true` is allowed to receive a new room assignment.
   - Select an available room from the provided list (prefer the one with the fewest patients if possible).

2. **ROOM STABILITY**
   - Do NOT change the `room_no` or `doctor_id` for any existing patients (`"is_newly_scanned": false`).

3. **QUEUE RE-ORDERING**
   - For ALL patients (both new and existing) within each assigned room:
     - Recalculate their `queue_number` starting from 1.
     - Sort patients by priority:
       a. Patients with `age >= 60` or `"treatment_condition": "Ongoing"` go first.
       b. All others follow afterward.

4. **OUTPUT FORMAT**
   - Return only a valid JSON array of patient objects.
   - Each object should include:  
     `patient_id`, `room_no`, `doctor_id`, and `queue_number`.

5. **STRICT FORMAT RULE**
   - Do not include any explanations, comments, or text outside the JSON list.
   - Example output:
     ```json
     [
       {{"patient_id": 1001, "room_no": "102A", "doctor_id": 4, "queue_number": 1}},
       {{"patient_id": 1002, "room_no": "102A", "doctor_id": 4, "queue_number": 2}}
     ]
     ```

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

    # --- Send to Gemini ---
    response = AI_MODEL.generate_content(prompt)

    try:
        raw_text = response.text.strip().lstrip('`json').rstrip('`')
        ai_result = json.loads(raw_text)

        # --- Apply AI results to DB ---
        for item in ai_result:
            patient_log = PatientLog.query.filter_by(patient_id=item["patient_id"]).first()
            if patient_log:
                patient_log.room_no = item["room_no"]
                patient_log.doctor_id = item["doctor_id"]
                patient_log.queue_number = item["queue_number"]
                patient_log.status = "assigned"

        db.session.commit()

        # --- Update doctor log patient counts ---
        for room in doctor_rooms:
            doctor_id = room["doctor_id"]
            room_no = room["room_no"]

            count = PatientLog.query.filter_by(
                room_no=room_no, doctor_id=doctor_id, status="assigned"
            ).count()

            doctor_log = DoctorLog.query.filter_by(
                doctor_id=doctor_id, room_no=room_no, log_date=today
            ).first()

            if doctor_log:
                doctor_log.patients_per_room = count

        db.session.commit()

        return ai_result

    except Exception as e:
        return {
            "error": f"Invalid JSON response from Gemini or DB update issue: {e}",
            "raw_output": getattr(response, "text", "No text available")
        }
