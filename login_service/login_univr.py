import selenium
from login_service.login_executor import LoginExecutor
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver

class LoginUnivr(LoginExecutor):

    def __init__(self, browser: WebDriver):
        super().__init__(browser)

    def get_login_url(self) -> str:
        return "https://univr.cloud.panopto.eu/Panopto/Pages/Auth/Login.aspx"
    
    def login(self, username: str, password: str) -> bool:
        try:
            userInputLogin = self.browser.find_element(By.ID, 'form_username')
            idPwdLogin = self.browser.find_element(By.ID, 'form_password')
            idSubmitLogin = self.browser.find_element(By.CSS_SELECTOR, '.btn-login')

            userInputLogin.send_keys(username)
            idPwdLogin.send_keys(password)
            idSubmitLogin.click()
        except Exception as e:
            self.logger.error(f"Unespected error during login {e}")
            return False
        return True
    
    def is_login_failed(self) -> bool:
        try:
            self.browser.find_element(By.CLASS_NAME, "alert-danger")
            return True
        except NoSuchElementException as e:
            return False
