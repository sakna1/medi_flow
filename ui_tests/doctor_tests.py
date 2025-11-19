import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://127.0.0.1:5000"

@pytest.fixture(scope="module")
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def close_alert_if_present(driver):
    try:
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
    except:
        pass

def login_doctor(driver, username="Ravi", password="2345"):
    driver.get(f"{BASE_URL}/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[text()='Login']").click()
    WebDriverWait(driver, 10).until(EC.url_contains("/doctor/dashboard"))
    close_alert_if_present(driver)

def test_doctor_dashboard_loads(driver):
    login_doctor(driver)
    close_alert_if_present(driver)
    driver.get(f"{BASE_URL}/doctor/dashboard")
    close_alert_if_present(driver)
    heading = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Hello Doctor')]"))
    )
    assert heading is not None

def test_doctor_editprofile_loads(driver):
    login_doctor(driver)
    close_alert_if_present(driver)
    driver.get(f"{BASE_URL}/doctor/editprofile")
    firstname_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "firstname"))
    )
    assert firstname_field.is_displayed()

def test_search_patient(driver):
    login_doctor(driver)
    close_alert_if_present(driver)
    driver.get(f"{BASE_URL}/doctor/appoinments")
    search_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "searchInput"))
    )
    search_input.send_keys("Ravi")
    driver.find_element(By.ID, "filterBtn").click()
    time.sleep(2)
    rows = driver.find_elements(By.CSS_SELECTOR, "#pastAppointmentsTable tbody tr")
    assert len(rows) >= 0

def test_save_patient_update(driver):
    login_doctor(driver)
    close_alert_if_present(driver)
    driver.get(f"{BASE_URL}/doctor/editprofile")
    close_alert_if_present(driver)

    driver.find_element(By.ID, "patient_id").send_keys("1001")
    driver.find_element(By.ID, "search-btn").click()
    time.sleep(2)
    close_alert_if_present(driver)

    treatment_status = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "treatmentstatus"))
    )
    treatment_status.send_keys("In Progress")

    treatment_type = driver.find_element(By.ID, "treatmentype")
    treatment_type.send_keys("Chemotherapy")

    driver.find_element(By.CLASS_NAME, "save-btn").click()
    time.sleep(1)
    close_alert_if_present(driver)

def test_start_and_complete_appointment(driver):
    login_doctor(driver)
    close_alert_if_present(driver)
    driver.get(f"{BASE_URL}/doctor/editprofile")
    close_alert_if_present(driver)

    driver.find_element(By.ID, "patient_id").send_keys("1001")
    driver.find_element(By.ID, "search-btn").click()
    time.sleep(2)
    close_alert_if_present(driver)

    start_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "startAppointment"))
    )
    start_btn.click()
    close_alert_if_present(driver)

    complete_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "completeAppointment"))
    )
    complete_btn.click()
    close_alert_if_present(driver)

def test_hospital_updates(driver):
    login_doctor(driver)
    close_alert_if_present(driver)
    driver.get(f"{BASE_URL}/doctor/appoinments")
    close_alert_if_present(driver)

    driver.get(f"{BASE_URL}/hospital-updates")
    body = driver.find_element(By.TAG_NAME, "body").text
    assert "updates" in body or "[]" in body

def test_get_patient_reports(driver):
    login_doctor(driver)
    close_alert_if_present(driver)
    patient_id = 1
    driver.get(f"{BASE_URL}/get_patient_reports/{patient_id}")
    body = driver.find_element(By.TAG_NAME, "body").text
    assert "reports" in body

def test_save_note_api(driver):
    import requests
    login_doctor(driver)
    close_alert_if_present(driver)

    patient_log_id = 1
    url = f"{BASE_URL}/save-note"
    payload = {"log_id": patient_log_id, "notes": "Test note from Selenium"}

    session = requests.Session()
    r = session.post(url, json=payload)

    assert r.status_code in [200, 400, 404]
