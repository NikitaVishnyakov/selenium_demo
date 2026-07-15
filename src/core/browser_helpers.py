from selenium.webdriver.support.ui import WebDriverWait


class BrowserHelpers:
    """Хелперы уровня драйвера/браузера. Подходят и странице, и тесту."""
    driver = None 
    DEFAULT_TIMEOUT = 10

    def get_current_url(self) -> str:
        return self.driver.current_url

    def take_screenshot(self, path: str) -> None:
        self.driver.save_screenshot(path)

    def wait_for_page_loaded(self) -> None:
        WebDriverWait(self.driver, self.DEFAULT_TIMEOUT).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
