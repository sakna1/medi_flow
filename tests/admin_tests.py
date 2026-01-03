import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests

BASE_URL = "http://localhost:5000"

ADMIN_USERNAME = "sakna"
ADMIN_PASSWORD = "9090"


# --------------------------------------------------
# Global driver fixture
# --------------------------------------------------
@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()


# --------------------------------------------------
# Helper: LOGIN before running any test
# --------------------------------------------------
def admin_login(driver):
    driver.get(f"{BASE_URL}/login")
    time.sleep(1)

    driver.find_element(By.ID, "username").send_keys(ADMIN_USERNAME)
    driver.find_element(By.ID, "password").send_keys(ADMIN_PASSWORD)
    driver.find_element(By.XPATH, "//button[text()='Login']").click()

    time.sleep(2)
    assert "/admin/dashboard" in driver.current_url
    print("Logged in successfully ✓")


# --------------------------------------------------
# 1. Test: Page loads - /admin/editprofile
# --------------------------------------------------
def test_editprofile_page_load(driver):
    admin_login(driver)
    driver.get(f"{BASE_URL}/admin/editprofile")
    time.sleep(1)

    assert driver.find_element(By.ID, "firstname")
    assert driver.find_element(By.ID, "lastname")
    assert driver.find_element(By.ID, "email")


# --------------------------------------------------
# 2. Update profile valid
# --------------------------------------------------
def test_editprofile_update_valid(driver):
    admin_login(driver)
    driver.get(f"{BASE_URL}/admin/editprofile")
    time.sleep(1)

    driver.find_element(By.ID, "firstname").clear()
    driver.find_element(By.ID, "firstname").send_keys("Saku")

    driver.find_element(By.ID, "lastname").clear()
    driver.find_element(By.ID, "lastname").send_keys("Admin")

    driver.find_element(By.ID, "email").clear()
    driver.find_element(By.ID, "email").send_keys("sakuadmin@example.com")

    driver.find_element(By.ID, "contact").clear()
    driver.find_element(By.ID, "contact").send_keys("0712345678")

    driver.find_element(By.CLASS_NAME, "save-btn").click()
    time.sleep(2)

    assert "editprofile" in driver.current_url


# --------------------------------------------------
# 3. Missing required fields
# --------------------------------------------------
def test_editprofile_missing_fields(driver):
    admin_login(driver)
    driver.get(f"{BASE_URL}/admin/editprofile")
    time.sleep(1)

    driver.find_element(By.ID, "firstname").clear()
    driver.find_element(By.ID, "lastname").clear()

    driver.find_element(By.CLASS_NAME, "save-btn").click()
    time.sleep(2)

    assert "editprofile" in driver.current_url


# --------------------------------------------------
# 4. Invalid email
# --------------------------------------------------
def test_editprofile_invalid_email(driver):
    admin_login(driver)
    driver.get(f"{BASE_URL}/admin/editprofile")
    time.sleep(1)

    driver.find_element(By.ID, "email").clear()
    driver.find_element(By.ID, "email").send_keys("invalid")

    driver.find_element(By.CLASS_NAME, "save-btn").click()
    time.sleep(2)

    assert "editprofile" in driver.current_url

# --------------------------------------------------
# 5. Update user valid
# --------------------------------------------------
def test_update_user_valid_api():
    url = f"{BASE_URL}/update_user/2"
    data = {"firstname": "UpdatedName"}
    response = requests.post(url, json=data)
    assert response.status_code == 200
    assert response.json()["message"] == "User updated successfully"


# --------------------------------------------------
# 6. Update user invalid email
# --------------------------------------------------
def test_update_user_invalid_api():
    url = f"{BASE_URL}/update_user/2"
    data = {"email": "invalidemail"}
    response = requests.post(url, json=data)
    assert response.status_code == 200
