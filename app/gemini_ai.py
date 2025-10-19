import google.generativeai as genai
import os
from app import db
from app.models import Patient, DiseaseDesc, DoctorLog, PatientLog
from datetime import datetime, date

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def call_gemini_for_queue(patient_id):
    patient = Patient.query.get(patient_id)
    disease = DiseaseDesc.query.get(patient.disease_id)
    today = date.today()

    # Collect doctor-room data
    doctor_logs = DoctorLog.query.filter_by(log_date=today).all()
    doctor_rooms = []
    for log in doctor_logs:
        waiting_patients = PatientLog.query.filter_by(room_no=log.room_no, status="Waiting").all()
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
        "age": datetime.now().year - patient.dob.year if patient.dob else 0,
        "treatment_condition": patient.treatment_status,
        "disease_id": patient.disease_id,
        "disease_estimated_time": int(disease.est_time or 0)
    }

    # Prompt for Gemini
    prompt = f"""
You are an AI Queue Manager at a hospital.
Your job is to assign this patient to the best room and queue.

Rules:
1. Choose the room with the lowest total estimated time.
2. If two rooms have the same total time, choose the one with the shorter queue.
3. Within a room, prioritize older patients (age >= 60) or those with active treatment conditions.
4. Never move patients between rooms after they are assigned.

Patient Info:
{patient_data}

Available Rooms (with current waiting stats):
{doctor_rooms}

Return a JSON object with:
- room_no
- doctor_id
- queue_number (next available number in that room)
- estimated_wait_time
"""

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    # Parse AI JSON safely
    import json
    try:
        ai_result = json.loads(response.text)
    except Exception:
        ai_result = {"error": "Invalid JSON from Gemini", "raw_output": response.text}

    # Update DB
    if "room_no" in ai_result:
        log = PatientLog.query.filter_by(patient_id=patient.id).order_by(PatientLog.id.desc()).first()
        log.room_no = ai_result.get("room_no")
        log.doctor_id = ai_result.get("doctor_id")
        log.queue_number = ai_result.get("queue_number")
        log.status = "Assigned"
        log.notes = f"AI assigned | Est. wait: {ai_result.get('estimated_wait_time')} mins"
        db.session.commit()

    return ai_result
