import pytest
import requests

from src.core.config import Config
from src.core.driver_factory import create_driver


def pytest_addoption(parser):
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        choices=["chrome", "firefox"],
        help="browser to use"
    )
    parser.addoption(
        "--headless",
        action="store_true",
        help="headless mode - without browser rendering"
    )
    parser.addoption(
        "--remote-url",
        action="store",
        default=None,
        help="remote url to use from CI/CD"
    )
    parser.addoption(
        "--env",
        action="store",
        default="local",
        choices=["local", "staging", "prod"],
        help="Target environment (key from URLS registry)",
    )


@pytest.fixture(scope="session")
def config(request):
    browser = request.config.getoption("browser")
    headless = request.config.getoption("headless")
    remote_url = request.config.getoption("remote_url")
    env = request.config.getoption("env")
    return Config(browser=browser, headless=headless, remote_url=remote_url, env=env)


@pytest.fixture
def driver(config):
    driver = create_driver(browser=config.browser, headless=config.headless, remote_url=config.remote_url)
    yield driver
    driver.quit()

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
