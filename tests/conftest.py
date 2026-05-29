from src.core.logger import setup_logger

import pytest
import requests

from src.core.config import Config
from src.api.clients.petstore_client import PetstoreClient

#REQUIRED = {"owner", "priority"}

def pytest_collection_modifyitems(config, items):
    missing = []
    for item in items:
        marks = {m.name for m in item.iter_markers()}
        #if not REQUIRED.issubset(marks):
        #    missing.append((item.nodeid, REQUIRED - marks))
    if missing:
        lines = "\n".join(f"  {nid}  missing: {sorted(m)}" for nid, m in missing)
        pytest.exit(f"Tests missing required markers:\n{lines}", returncode=5)


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
def base_url(config) -> str:
    return config.base_url


@pytest.fixture(scope="session", autouse=True)
def _logging():
    setup_logger()


@pytest.fixture(scope="session")
def petstore():
    client = PetstoreClient()
    yield client
    client.close()