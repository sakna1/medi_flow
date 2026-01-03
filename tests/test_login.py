import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# (username, password, expected_login_path, expected_redirect_path)
test_users = [
    ("sakna", "9090", "/login", "/admin/dashboard"),      # admin
    ("Anne", "3456", "/login", "/nurse/dashboard"),       # nurse
    ("Ravi", "2345", "/login", "/doctor/dashboard"),      # doctor
    ("captain", "1234", "/user-login", "/patient/dashboard"),  # patient
]

@pytest.mark.parametrize("username,password,login_path,expected_redirect", test_users)
def test_login_for_role(username, password, login_path, expected_redirect):
    driver = webdriver.Chrome()
    base_url = "http://localhost:5000"

    try:
        # Open the correct login page
        driver.get(base_url + login_path)

        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[text()='Login']").click()

        # Wait for redirect
        WebDriverWait(driver, 10).until(
            EC.url_contains(expected_redirect)
        )

        assert expected_redirect in driver.current_url
        print(f"{username} logged in successfully → {driver.current_url}")

    finally:
        driver.quit()
