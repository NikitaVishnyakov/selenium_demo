import pytest
import requests

from src.core.driver_factory import create_driver
from src.ui.pages.login_page import LoginPage


@pytest.fixture
def driver(config):
    driver = create_driver(browser=config.browser, headless=config.headless, remote_url=config.remote_url)
    yield driver
    driver.quit()


@pytest.fixture(autouse=True)
def _open_base_url(request, driver, base_url):
    if "no_base_url" in request.keywords:
        return
    driver.get(base_url)


@pytest.fixture
def login_page(driver):
    page = LoginPage(driver)
    page.check()
    return page


@pytest.fixture(scope="session", autouse=True)
def _health_check(config):
    try:
        response = requests.get(config.base_url, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        pytest.fail(
            f"Site unreachable {config.base_url}. "
            f"Reason: {e.__class__.__name__}\n"
            f"Hint: Check --env and --locale values"
        )
