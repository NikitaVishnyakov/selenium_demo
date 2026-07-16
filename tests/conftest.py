from src.core.logger import setup_logger
from src.core.config import Config
from src.api.clients.api_client import ApiClient

import allure
import logging
import time

import pytest
import requests


@pytest.fixture(scope="session", autouse=True)
def _logging():
    setup_logger()


@pytest.fixture(autouse=True)
def _attach_log_to_allure(caplog):
    caplog.set_level(logging.INFO)
    yield
    if caplog.text:
        allure.attach(caplog.text, name="log", attachment_type=allure.attachment_type.TEXT)


@pytest.fixture(scope="session")
def config() -> Config:
    return Config.from_env()


@pytest.fixture(scope="session", autouse=True)
def _wait_for_service(config):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            if requests.get(config.swagger_url, timeout=2).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    pytest.exit(f"API not reachable at {config.swagger_url} after 30s", returncode=1)


@pytest.fixture(scope="session")
def client_test1(config) -> ApiClient:
    tenant = config.tenants["test1"]
    client = ApiClient(config.base_url, tenant.username, tenant.password)
    yield client
    client.close()


@pytest.fixture(scope="session")
def client_test2(config) -> ApiClient:
    tenant = config.tenants["test2"]
    client = ApiClient(config.base_url, tenant.username, tenant.password)
    yield client
    client.close()


@pytest.fixture(params=["test1", "test2"])
def tenant_client(request, client_test1, client_test2) -> ApiClient:
    return {"test1": client_test1, "test2": client_test2}[request.param]


@pytest.fixture
def integration_factory():
    created: list[tuple[ApiClient, str]] = []

    def _make(client: ApiClient, **overrides) -> dict:
        payload = {"name": "test-integration", "type": "generic", **overrides}
        resp = client.post("/integrations", json=payload)
        resp.raise_for_status()
        data = resp.json()
        created.append((client, data["id"]))
        return data

    yield _make

    log = logging.getLogger("cleanup")
    for client, integration_id in created:
        try:
            client.delete(f"/integrations/{integration_id}")
        except Exception as exc:
            log.warning("cleanup failed for integration %s: %s", integration_id, exc)


@pytest.fixture
def asset_factory():
    created: list[tuple[ApiClient, str]] = []

    def _make(client: ApiClient, integration_id: str, **overrides) -> dict:
        payload = {
            "integration_id": integration_id,
            "name": "test-asset",
            "description": "created by tests",
            **overrides,
        }
        resp = client.post("/assets", json=payload)
        resp.raise_for_status()
        data = resp.json()
        created.append((client, data["id"]))
        return data

    yield _make

    log = logging.getLogger("cleanup")
    for client, asset_id in created:
        try:
            client.delete(f"/assets/{asset_id}")
        except Exception as exc:
            log.warning("cleanup failed for asset %s: %s", asset_id, exc)
