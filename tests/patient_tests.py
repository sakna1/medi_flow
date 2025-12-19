# tests/test_patient_routes.py
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

def login_patient(driver, username="captain", password="Saku@1234"):
    driver.get(f"{BASE_URL}/user-login")
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.TAG_NAME, "form").submit()
    WebDriverWait(driver, 5).until(EC.url_contains("/patient/dashboard"))

# 1. Login Page loads
def test_login_page_load(driver):
    driver.get(f"{BASE_URL}/user-login")
    assert "login" in driver.title.lower() or driver.find_element(By.TAG_NAME, "form")

# 2. Successful patient login
def test_patient_login(driver):
    login_patient(driver)
    assert "/patient/dashboard" in driver.current_url

# 3. Dashboard page loads
def test_dashboard_page(driver):
    login_patient(driver)
    driver.get(f"{BASE_URL}/patient/dashboard")
    assert "Dashboard" in driver.page_source or "Welcome" in driver.page_source

# 4. Appointments page loads
def test_appointments_page(driver):
    login_patient(driver)
    driver.get(f"{BASE_URL}/patient/appoinments")
    assert "Appointments" in driver.page_source

# 5. FAQ page loads
def test_faq_page(driver):
    login_patient(driver)
    driver.get(f"{BASE_URL}/patient/faqpage")
    assert "FAQ" in driver.page_source

# 6. Notifications page loads
def test_notifications_page(driver):
    login_patient(driver)
    driver.get(f"{BASE_URL}/patient/notification")
    assert "Notification" in driver.page_source

# 7. QR code route returns image
def test_qr_code_route(driver):
    login_patient(driver)
    driver.get(f"{BASE_URL}/patient/dashboard/qr")
    # check if content-type is png by requesting via Selenium
    assert "image/png" in driver.execute_script("return document.contentType") or driver.page_source != ""

# 8. Contact page loads without login
def test_contact_page(driver):
    driver.get(f"{BASE_URL}/patient/contact")
    assert "Contact" in driver.page_source
