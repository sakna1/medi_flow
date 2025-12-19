import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# ---------------------------------------
# DRIVER SETUP FIXTURE
# ---------------------------------------
@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

# ---------------------------------------
# LOGIN ROLE TEST DATA
# ---------------------------------------
test_users = [
    ("sakna", "9090", "/login", "/admin/dashboard"),         # admin
    ("Anne", "3456", "/login", "/nurse/dashboard"),          # nurse
    ("Ravi", "2345", "/login", "/doctor/dashboard"),         # doctor
    ("captain", "1234", "/user-login", "/patient/dashboard") # patient
]

# ---------------------------------------
# TEST 1: LOGIN BY ROLE
# ---------------------------------------
@pytest.mark.parametrize("username,password,login_path,expected_redirect", test_users)
def test_login_for_role(driver, username, password, login_path, expected_redirect):
    base_url = "http://localhost:5000"

    # Open login page
    driver.get(base_url + login_path)

    # Enter credentials
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)

    # Click login
    driver.find_element(By.XPATH, "//button[text()='Login']").click()

    # Wait for redirect
    WebDriverWait(driver, 10).until(
        EC.url_contains(expected_redirect)
    )

    assert expected_redirect in driver.current_url
    print(f"[OK] {username} logged in → {driver.current_url}")

# ---------------------------------------
# TEST 2: PATIENT REGISTRATION (Admin)
# ---------------------------------------
def test_registration(driver):
    # STEP 1: Login as admin
    driver.get("http://127.0.0.1:5000/login")
    time.sleep(1)

    driver.find_element(By.ID, "username").send_keys("sakna")
    driver.find_element(By.ID, "password").send_keys("9090")
    driver.find_element(By.XPATH, "//button[text()='Login']").click()
    time.sleep(2)

    # STEP 2: Open registration page
    driver.get("http://127.0.0.1:5000/admin/register")
    time.sleep(1)

    # STEP 3: Account Information
    Select(driver.find_element(By.ID, "role")).select_by_visible_text("Doctor")
    driver.find_element(By.ID, "username").send_keys("test_patient3")
    driver.find_element(By.ID, "password").send_keys("Test@1234")

    # STEP 4: Personal Information
    driver.find_element(By.ID, "first_name").send_keys("Test3")
    driver.find_element(By.ID, "last_name").send_keys("User")
    Select(driver.find_element(By.ID, "gender")).select_by_visible_text("Male")
    driver.find_element(By.ID, "date_of_birth").send_keys("1990-01-01")
    Select(driver.find_element(By.ID, "marital_status")).select_by_visible_text("Single")
    driver.find_element(By.ID, "nic").send_keys("200012333645")

    # STEP 5: Contact Information
    driver.find_element(By.ID, "phone").send_keys("0712345678")
    driver.find_element(By.ID, "email").send_keys("testpatient5@example.com")
    driver.find_element(By.ID, "address").send_keys("123 Test Street")
    driver.find_element(By.ID, "emergency_contact_name").send_keys("Emergency Person")
    driver.find_element(By.ID, "emergency_contact_phone").send_keys("0771234567")

    # STEP 6: Submit form
    driver.find_element(By.TAG_NAME, "form").submit()

    time.sleep(2)
    print("[OK] Patient registration submitted successfully!")

# ---------------------------------------
# MAIN RUN (optional if running without pytest)
# ---------------------------------------
if __name__ == "__main__":
    pytest.main(["-v"])
