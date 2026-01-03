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
   
    waiting_logs = PatientLog.query.filter(
        PatientLog.status.in_(["waiting", "assigned"]),
        db.func.date(PatientLog.scan_time) == today
    ).all()

    # --- Aggregate patient data and calculate room load ---
    patients_data = []
    room_loads = {}  # room_no -> total disease time

    for log in waiting_logs:
        p = log.patient

        # Get disease estimated time
        disease = DiseaseDesc.query.get(log.disease_id)
        disease_time = disease.est_time if disease else 0

        # Track total estimated load per room
        if log.room_no:
            room_loads[log.room_no] = room_loads.get(log.room_no, 0) + disease_time

        patients_data.append({
            "patient_id": p.id,
            "is_newly_scanned": (p.id == new_patient.id),
            "age": calculate_age(p.dob),
            "treatment_condition": p.treatment_status,
            "room_no": log.room_no,
            "doctor_id": log.doctor_id,
            "queue_number": log.queue_number,
            "disease_time": disease_time,
            "scan_time": log.scan_time.isoformat()
        })

    # --- Doctor-room info ---
    doctor_rooms = []
    doctor_logs = DoctorLog.query.filter(DoctorLog.log_date == today).all()
    for log in doctor_logs:
        doctor_rooms.append({
            "room_no": log.room_no,
            "doctor_id": log.doctor_id,
            "patients_per_room": log.patients_per_room or 0,
            "total_estimated_time": room_loads.get(log.room_no, 0)
        })   
    prompt = f"""
You are an AI Queue Manager for a cancer hospital. You will assign the new patient and reorder queues based on the rules below.

[QUEUE RULES]

1. **Room Assignment**
   - Only the patient with `"is_newly_scanned": true` can change or receive a new room.
   - Choose the room with the *lowest total estimated disease time* and *shortest queue length*.
   - Existing patients must remain in their current room and doctor.

2. **Queue Prioritization Within Each Room**
   - Patients are prioritized by: 
     a. **Treatment condition** → "In Progress" patients go first.  
     b. **Age** → if two patients have the same treatment status, those aged 60 or older come first.
     c. If treatment condition and age priority are equal,
   the patient with the EARLIER scan_time must be placed first.

   - Patients under 60 with “Completed” status come last.
   - Recalculate queue_number starting from 1 within each room.

3. **Use of Disease Time**
   - Consider each patient's `disease_time` (estimated treatment duration) when calculating total room load.

4. **Output**
   - Return ONLY valid JSON in this exact format:
     ```json
     [
       {{"patient_id": 1001, "room_no": "101A", "doctor_id": 2, "queue_number": 1}},
       {{"patient_id": 1002, "room_no": "101A", "doctor_id": 2, "queue_number": 2}}
     ]
     ```
   - Do not include text or explanation outside the JSON list.

[Patients Data]
{json.dumps(patients_data, indent=2)}

[Available Rooms]
{json.dumps(doctor_rooms, indent=2)}

Return only the JSON list.
"""

    # --- Send to Gemini ---
    response = AI_MODEL.generate_content(prompt)

    try:
        raw_text = response.text.strip().lstrip('`json').rstrip('`')
        ai_result = json.loads(raw_text)

        # --- Apply AI results to DB ---
        for item in ai_result:
            patient_log = PatientLog.query.filter(
                PatientLog.patient_id == item["patient_id"],
                db.func.date(PatientLog.scan_time) == today
            ).order_by(PatientLog.id.desc()).first()

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
            "error": f"Invalid JSON response or DB update issue: {e}",
            "raw_output": getattr(response, "text", "No text available")
        }
