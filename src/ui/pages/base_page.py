from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.core.browser_helpers import BrowserHelpers

Locator = tuple[str, str]
Timeout = 10

class BasePage(BrowserHelpers):
    def __init__(self, driver: WebDriver, timeout: int = Timeout):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.check()

    def check(self):
        assert "Swag Labs" in self.driver.title

    def wait_for_element_visible(self, locator: Locator) -> WebElement:
        return self.wait.until(EC.visibility_of_element_located(locator))

    def wait_for_element_clickable(self, locator: Locator)-> WebElement:
        return self.wait.until(EC.element_to_be_clickable(locator))

    def is_element_present(self, locator: Locator) -> bool:
        return len(self.driver.find_elements(*locator)) > 0

    def click(self, locator: Locator) -> None:
        self.wait_for_element_clickable(locator).click()

    def send_text(self, locator: Locator, text: str) -> None:
        self.wait_for_element_visible(locator).send_keys(text)

    def get_element_text(self, locator: Locator) -> str:
        return self.wait_for_element_visible(locator).text
