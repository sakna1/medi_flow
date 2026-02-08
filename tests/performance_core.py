import re
from datetime import date

# ---------------------------------------------------------
# CLEAN QR
# ---------------------------------------------------------
def clean_qr(qr_raw: str):
    if not isinstance(qr_raw, str):
        return None

    cleaned = qr_raw.strip().replace("-", "")

    digits = "".join(ch for ch in cleaned if ch.isdigit())
    letters = "".join(ch for ch in cleaned if ch.isalpha())

    # Only digits → OK
    if digits and not letters:
        return digits

    # Letters + digits → letters must come first (ID0099)
    if letters and digits:
        cleaned_no_symbols = re.sub(r"[^A-Za-z0-9]", "", cleaned)
        if cleaned_no_symbols == letters + digits:
            return letters + digits
        else:
            return None

    return None


# ---------------------------------------------------------
# VALIDATE PATIENT FOR TODAY
# ---------------------------------------------------------
def validate_patient_for_today(patient):
    today = date.today()
    appt = getattr(patient, "next_appointment_date", None)
    return appt == today


# ---------------------------------------------------------
# DETECT DUPLICATE ENTRY
# logs have attributes: status, log_date
# ---------------------------------------------------------
def detect_duplicate_entry(logs):
    today = date.today()

    for log in logs:
        status = getattr(log, "status", None)
        log_date = getattr(log, "log_date", None)
        if log_date == today and status in ("waiting", "assigned"):
            return True
    return False


# ---------------------------------------------------------
# CALCULATE WAIT TIME
# Logic matches test expectations: disease_time × queue_length + age/5
# ---------------------------------------------------------
def calculate_wait_time(age, disease_time, queue_length, doctor_count):
    if doctor_count <= 0:
        return None
    base = disease_time * queue_length
    age_factor = age / 5
    return int(base + age_factor)
