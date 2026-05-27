from src.ui.pages.login_page import LoginPage
from tests.base_test import BaseTest


class TestSmokeLogin(BaseTest):
    """Test successful loging by user"""

    login_page = "https://www.saucedemo.com/"
    valid_user_name = "standard_user"
    valid_user_password = "secret_sauce"
    success_page = "https://www.saucedemo.com/inventory.html"

    def test_smoke_login(self):
        """
            1. Open login page
            2. Fill in username and password and click on login button
        """

        self.logger.info("1. Open login page")
        login_page = LoginPage(self.driver)
        self.wait_for_page_loaded()
        current_url = self.get_current_url()
        assert current_url == self.login_page
        self.logger.info("Login page is opened")

        self.logger.info("2. Fill in username and password")
        login_page.login(self.valid_user_name, self.valid_user_password)
        success_page_after_login = self.get_current_url()
        assert success_page_after_login == self.success_page
        self.logger.info("Successfully logged in")
