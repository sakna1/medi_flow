import unittest
from tests.performance_core import clean_qr, validate_patient_for_today, detect_duplicate_entry, calculate_wait_time
from datetime import date

class TestPerformanceCore(unittest.TestCase):

    # --------------------------
    # QR CLEANING
    # --------------------------
    def test_clean_qr_valid(self):
        self.assertEqual(clean_qr(" 12345 "), "12345")
        self.assertEqual(clean_qr("ID-0099"), "ID0099")
        self.assertEqual(clean_qr(" !!  888** "), "888")

    def test_clean_qr_invalid(self):
        self.assertIsNone(clean_qr("####"))
        self.assertIsNone(clean_qr("abc"))
        self.assertIsNone(clean_qr("12x3"))

    # --------------------------
    # APPOINTMENT VALIDATION
    # --------------------------
    class DummyPatient:
        def __init__(self, next_appointment_date):
            self.next_appointment_date = next_appointment_date

    def test_validate_patient_for_today(self):
        patient_today = self.DummyPatient(date.today())
        patient_future = self.DummyPatient(date(2050, 1, 1))
        patient_none = self.DummyPatient(None)

        self.assertTrue(validate_patient_for_today(patient_today))
        self.assertFalse(validate_patient_for_today(patient_future))
        self.assertFalse(validate_patient_for_today(patient_none))

    # --------------------------
    # DUPLICATE ENTRY CHECK
    # --------------------------
    class DummyLog:
        def __init__(self, status, log_date):
            self.status = status
            self.log_date = log_date

    def test_detect_duplicate_entry(self):
        today = date.today()
        logs = [
            self.DummyLog("waiting", today),
            self.DummyLog("assigned", today),
            self.DummyLog("completed", today),
        ]
        self.assertTrue(detect_duplicate_entry(logs))

        old_logs = [self.DummyLog("waiting", date(2024, 1, 1))]
        self.assertFalse(detect_duplicate_entry(old_logs))

        empty = []
        self.assertFalse(detect_duplicate_entry(empty))

    # --------------------------
    # WAIT TIME CALCULATION
    # --------------------------
    def test_wait_time(self):
        est = calculate_wait_time(age=50, disease_time=10, queue_length=5, doctor_count=1)
        self.assertEqual(est, 60)  # 10×5 + 50/5 = 60

        est2 = calculate_wait_time(age=30, disease_time=15, queue_length=2, doctor_count=2)
        self.assertEqual(est2, 36)  # 15×2 + 30/5 = 36

if __name__ == "__main__":
    unittest.main()
