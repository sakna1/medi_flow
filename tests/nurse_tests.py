# tests/test_nurse.py

import time
import pytest
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

BASE_URL = "http://127.0.0.1:5000"


# ---------------------------
#  SETUP
# ---------------------------
@pytest.fixture(scope="module")
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

def close_alert_if_present(driver):
    try:
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
    except:
        pass


def login_nurse(driver, username="Anne", password="3456"):
    """Logs in as nurse before running tests."""
    driver.get(f"{BASE_URL}/login")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    ).send_keys(username)

    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[text()='Login']").click()

    WebDriverWait(driver, 10).until(
        EC.url_contains("/nurse/dashboard")
    )


# ---------------------------
#  TEST 2 – Edit Profile Page Loads
# ---------------------------
def test_editprofile_page_loads(driver):
    login_nurse(driver)
    driver.get(f"{BASE_URL}/nurse/editprofile")

    firstname = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "firstname"))
    )

    assert firstname.is_displayed()


# ---------------------------
#  TEST 3 – Get Patient Data (JSON)
# ---------------------------
def test_get_patient_data(driver):
    login_nurse(driver)

    patient_id = 1001  # must exist in DB

    driver.get(f"{BASE_URL}/get_patient_data/{patient_id}")

    body = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Parse JSON safely
    data = json.loads(body.text)

    assert "first_name" in data["patient"]

# ---------------------------
#  TEST 4 – Update Patient (POST JSON via form)
# ---------------------------
def test_update_patient_nurse(driver):
    # 1. Login as nurse
    login_nurse(driver)
    close_alert_if_present(driver)

    # 2. Go to nurse edit page
    driver.get(f"{BASE_URL}/nurse/editprofile")
    close_alert_if_present(driver)

    # 3. Enter patient ID and search - same as doctor example
    driver.find_element(By.ID, "patient_id").send_keys("1001")
    driver.find_element(By.ID, "search-btn").click()
    time.sleep(2)
    close_alert_if_present(driver)

    # 4. Wait for patient's form fields to load
    firstname = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "firstname"))
    )

    # 5. Update fields
    firstname.clear()
    firstname.send_keys("UpdatedFN")

    lastname = driver.find_element(By.ID, "lastname")
    lastname.clear()
    lastname.send_keys("UpdatedLN")

    email = driver.find_element(By.ID, "email")
    email.clear()
    email.send_keys("updated@email.com")

    phone = driver.find_element(By.ID, "phone")
    phone.clear()
    phone.send_keys("0775555555")

    # Optional fields if exist: address, nic, gender, etc.

    # 6. Click save button
    driver.find_element(By.CLASS_NAME, "save-btn").click()
    time.sleep(1)

    # 7. Handle alert popup after update
    close_alert_if_present(driver)

    # 8. Assert page still loaded (basic safety check)
    assert "editprofile" in driver.current_url

# ---------------------------
#  TEST 5 – Get Registered Count (GET JSON)
# ---------------------------
def test_get_registered_count(driver):
    login_nurse(driver)

    driver.get(f"{BASE_URL}/get_registered_count")

    body_text = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    ).text

    data = json.loads(body_text)

    assert "count" in data
    assert isinstance(data["count"], int)

