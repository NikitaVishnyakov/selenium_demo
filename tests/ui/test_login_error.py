import pytest

from src.ui.pages.login_page import LoginPage
from tests.base_test import BaseTest

@pytest.mark.owner("nikita")
@pytest.mark.priority("P1")
@pytest.mark.smoke
@pytest.mark.ui
@pytest.mark.case_id("TC-001")
class TestLoginError(BaseTest):
    """Test login by wrong user and check error message"""

    login_page = "https://www.saucedemo.com/"

    @pytest.mark.parametrize(
        "username, password, expected_error",
        [
            ("wrong_user", "wrong_password",
             "Epic sadface: Username and password do not match any user in this service"),
            ("", "secret_sauce",
             "Epic sadface: Username is required"),
            ("standard_user", "",
             "Epic sadface: Password is required"),
            ("locked_out_user", "secret_sauce",
             "Epic sadface: Sorry, this user has been locked out."),
        ],
        ids=["wrong_creds", "empty_username", "empty_password", "locked_out"],
    ) #creads could me moved to test_data.py file e.g. INVALID_CREDS=[(),(),()]

    def test_login_error(self, username, password, expected_error):
        """
            1. Open login page
            2. Fill in username and password and click on login button
            3. Check error message
        """

        self.logger.info("1. Open login page")
        login_page = LoginPage(self.driver)
        self.wait_for_page_loaded()
        current_url = self.get_current_url()
        assert current_url == self.login_page
        self.logger.info("Login page is opened")

        self.logger.info(f"2. Fill in {username=} and {password=}")
        login_page.login(username, password)
        self.logger.info("Login button is clicked")

        self.logger.info("3. Check error message")
        error_message_from_page = login_page.get_error()
        assert error_message_from_page == expected_error
        self.logger.info("Error message is checked!")

