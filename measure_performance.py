import time
from tests.performance_core import clean_qr, detect_duplicate_entry, calculate_wait_time, validate_patient_for_today
from datetime import date

# Dummy data for testing
class DummyPatient:
    def __init__(self, next_appointment_date):
        self.next_appointment_date = next_appointment_date

class DummyLog:
    def __init__(self, status, log_date):
        self.status = status
        self.log_date = log_date

# -------------------------
# Utility to measure time
# -------------------------
def measure(func, *args, runs=20, **kwargs):
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()
        times.append(end - start)
    return min(times), max(times), sum(times)/len(times)

# -------------------------
# QR Scan → AI Queue Assignment
# -------------------------
def qr_scan_simulation():
    qr = "ID-1234"
    patient = DummyPatient(date.today())
    logs = [DummyLog("waiting", date.today())]
    
    cleaned = clean_qr(qr)
    validate_patient_for_today(patient)
    detect_duplicate_entry(logs)
    calculate_wait_time(age=50, disease_time=10, queue_length=5, doctor_count=1)

# -------------------------
# Dashboard Refresh
# -------------------------
def dashboard_refresh_simulation():
    # Simulate reading logs + calculating wait times for all patients
    logs = [DummyLog("waiting", date.today()) for _ in range(10)]
    for log in logs:
        detect_duplicate_entry([log])
        calculate_wait_time(age=50, disease_time=10, queue_length=5, doctor_count=1)

# -------------------------
# Notification Retrieval
# -------------------------
def notification_retrieval_simulation():
    # Simulate retrieving 5 notifications
    for _ in range(5):
        time.sleep(0.01)  # small delay to simulate network/db fetch

# -------------------------
# Run measurements
# -------------------------
if __name__ == "__main__":
    runs = 20

    qr_min, qr_max, qr_avg = measure(qr_scan_simulation, runs=runs)
    dash_min, dash_max, dash_avg = measure(dashboard_refresh_simulation, runs=runs)
    notif_min, notif_max, notif_avg = measure(notification_retrieval_simulation, runs=runs)

    print("Operation\tMinimum (s)\tMaximum (s)\tAverage (s)")
    print(f"QR Scan → AI Queue Assignment\t{qr_min:.4f}\t{qr_max:.4f}\t{qr_avg:.4f}")
    print(f"Dashboard Refresh\t{dash_min:.4f}\t{dash_max:.4f}\t{dash_avg:.4f}")
    print(f"Notification Retrieval\t{notif_min:.4f}\t{notif_max:.4f}\t{notif_avg:.4f}")
