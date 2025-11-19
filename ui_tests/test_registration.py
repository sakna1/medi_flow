import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

def test_patient_registration():
    driver = webdriver.Chrome()

    try:
        # 1. Open login page
        driver.get("http://127.0.0.1:5000/login")
        time.sleep(1)

        # 2. Login as test admin/nurse
        driver.find_element(By.ID, "username").send_keys("sakna")
        driver.find_element(By.ID, "password").send_keys("9090")
        driver.find_element(By.XPATH, "//button[text()='Login']").click()
        time.sleep(2)

        # 3. Go to registration page
        driver.get("http://127.0.0.1:5000/admin/register")
        time.sleep(1)

        # 4. Fill Account Information
        Select(driver.find_element(By.ID, "role")).select_by_visible_text("Doctor")
        driver.find_element(By.ID, "username").send_keys("test_patient2")
        driver.find_element(By.ID, "password").send_keys("Test@1234")

        # 5. Fill Personal Information
        driver.find_element(By.ID, "first_name").send_keys("Test2")
        driver.find_element(By.ID, "last_name").send_keys("User")
        Select(driver.find_element(By.ID, "gender")).select_by_visible_text("Male")
        driver.find_element(By.ID, "date_of_birth").send_keys("1990-01-01")
        Select(driver.find_element(By.ID, "marital_status")).select_by_visible_text("Single")
        driver.find_element(By.ID, "nic").send_keys("200012345645")

        # 6. Fill Contact Information
        driver.find_element(By.ID, "phone").send_keys("0712345678")
        driver.find_element(By.ID, "email").send_keys("testpatient4@example.com")
        driver.find_element(By.ID, "address").send_keys("123 Test Street")
        driver.find_element(By.ID, "emergency_contact_name").send_keys("Emergency Person")
        driver.find_element(By.ID, "emergency_contact_phone").send_keys("0771234567")

        # 7. Submit registration (using the form submit)
        driver.find_element(By.TAG_NAME, "form").submit()

        time.sleep(2)
        print("Registration form submitted successfully.")

    finally:
        driver.quit()

if __name__ == "__main__":
    test_patient_registration()
