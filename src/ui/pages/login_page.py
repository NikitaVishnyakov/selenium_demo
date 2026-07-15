from selenium.webdriver.common.by import By
from src.ui.pages.base_page import BasePage

USER_NAME_INPUT = (By.ID, 'user-name')
PASSWORD_INPUT = (By.ID, 'password')
LOGIN_BUTTON = (By.ID, 'login-button')
ERROR_MESSAGE = (By.XPATH, "//h3[@data-test='error']")
ERROR_BUTTON = (By.XPATH, "//h3[@data-test='error-button']")

class LoginPage(BasePage):

    def check(self):
        self.wait_for_element_visible(USER_NAME_INPUT)
        self.wait_for_element_visible(PASSWORD_INPUT)
        self.wait_for_element_visible(LOGIN_BUTTON)

    def login(self, user_name, password):
        self.send_text(USER_NAME_INPUT, user_name)
        self.send_text(PASSWORD_INPUT, password)
        self.wait_for_element_clickable(LOGIN_BUTTON).click()

    def get_error(self):
        return self.wait_for_element_visible(ERROR_MESSAGE).text


