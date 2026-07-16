import pytest
import requests

from tests.helpers import assert_status_in

pytestmark = [pytest.mark.auth, pytest.mark.owner("Nikita.Vyshniakov"), pytest.mark.priority("P1")]

ENDPOINTS = [
    ("GET", "/integrations", None),
    ("GET", "/assets", None),
    ("POST", "/integrations", {"name": "auth-test", "type": "generic"}),
]


@pytest.fixture
def anonymous_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
    yield session
    session.close()


@pytest.mark.case_id("TC-AUTH-01")
@pytest.mark.parametrize("method, path, payload", ENDPOINTS, ids=[f"{m}_{p}" for m, p, _ in ENDPOINTS])
def test_no_credentials_rejected(config, anonymous_session, method, path, payload):
    """TC-AUTH-01: no credentials on any endpoint must be rejected."""
    resp = anonymous_session.request(method, f"{config.base_url}{path}", json=payload, timeout=10)
    assert_status_in(resp, {401}, "TC-AUTH-01")


@pytest.mark.case_id("TC-AUTH-02")
def test_invalid_credentials_rejected(config):
    """TC-AUTH-02: wrong password for a known user must be rejected."""
    session = requests.Session()
    session.auth = (config.tenants["test1"].username, "wrong-password")
    resp = session.get(f"{config.base_url}/integrations", timeout=10)
    assert_status_in(resp, {401}, "TC-AUTH-02")


@pytest.mark.smoke
@pytest.mark.case_id("TC-AUTH-03")
def test_valid_credentials_accepted(client_test1, client_test2):
    """TC-AUTH-03: valid test1/test2 credentials must be accepted."""
    resp1 = client_test1.get("/integrations")
    assert_status_in(resp1, {200}, "TC-AUTH-03 (test1)")

    resp2 = client_test2.get("/integrations")
    assert_status_in(resp2, {200}, "TC-AUTH-03 (test2)")


@pytest.mark.case_id("TC-AUTH-04")
def test_www_authenticate_header_on_401(config):
    """TC-AUTH-04: 401 responses should carry a WWW-Authenticate header (documents auth-spec gap if absent)."""
    resp = requests.get(f"{config.base_url}/integrations", timeout=10)
    assert_status_in(resp, {401}, "TC-AUTH-04")
    assert "WWW-Authenticate" in resp.headers, (
        f"[TC-AUTH-04] expected WWW-Authenticate header on 401 response, got headers: {dict(resp.headers)}"
    )
