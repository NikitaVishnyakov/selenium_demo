from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions


def create_driver(browser: str, headless: bool=False, remote_url: str | None = None) -> WebDriver:
    if browser == 'chrome':
        options = _build_chrome_options(headless)
        if remote_url:
            return webdriver.Remote(command_executor=remote_url, options=options)
        return webdriver.Chrome(options=options)

    elif browser == 'firefox':
        options = _build_firefox_options(headless)
        if remote_url:
            return webdriver.Remote(command_executor=remote_url, options=options)
        return webdriver.Firefox(options=options)

    else:
        raise ValueError(f'Unknown browser type: {browser}')

def _build_chrome_options(headless: bool) -> ChromeOptions:
    options = ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    return options

def _build_firefox_options(headless: bool) -> FirefoxOptions:
    options = FirefoxOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--width=1920')
    options.add_argument('--height=1080')
    return options