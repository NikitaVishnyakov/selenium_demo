import pytest
import requests

from tests.helpers import assert_status_in

pytestmark = [pytest.mark.contract, pytest.mark.owner("Nikita.Vyshniakov")]


@pytest.mark.case_id("TC-CONTRACT-01a")
@pytest.mark.priority("P2")
@pytest.mark.xfail(reason="BUG-04: POST /integrations returns 201 in practice; spec documents 200", strict=True)
def test_post_integration_status_code_matches_spec(client_test1):
    """TC-CONTRACT-01a: POST /integrations should return the spec's documented 200."""
    resp = client_test1.post("/integrations", json={"name": "contract-check-int", "type": "generic"})
    try:
        assert_status_in(resp, {200}, "TC-CONTRACT-01 (integrations)")
    finally:
        if resp.status_code == 201:
            client_test1.delete(f"/integrations/{resp.json()['id']}")


@pytest.mark.case_id("TC-CONTRACT-01b")
@pytest.mark.priority("P2")
@pytest.mark.xfail(reason="BUG-04: POST /assets returns 201 in practice; spec documents 200", strict=True)
def test_post_asset_status_code_matches_spec(client_test1, integration_factory):
    """TC-CONTRACT-01b: POST /assets should return the spec's documented 200."""
    integration = integration_factory(client_test1)
    resp = client_test1.post(
        "/assets",
        json={"integration_id": integration["id"], "name": "contract-check-asset", "description": "d"},
    )
    try:
        assert_status_in(resp, {200}, "TC-CONTRACT-01 (assets)")
    finally:
        if resp.status_code == 201:
            client_test1.delete(f"/assets/{resp.json()['id']}")


@pytest.mark.case_id("TC-CONTRACT-02")
@pytest.mark.priority("P1")
@pytest.mark.xfail(
    reason="BUG-03: PUT /integrations documented shape (id in body, no path id) returns 404", strict=True
)
def test_put_integration_documented_shape(client_test1, integration_factory):
    """TC-CONTRACT-02: PUT /integrations at the documented shape (no path id) should update per spec."""
    created = integration_factory(client_test1)

    resp = client_test1.put("/integrations", json={"id": created["id"], "name": "contract-shape-update"})
    assert_status_in(resp, {200}, "TC-CONTRACT-02")


@pytest.mark.case_id("TC-CONTRACT-03")
@pytest.mark.priority("P2")
@pytest.mark.xfail(
    reason="BUG-06: spec has no securityDefinitions/security block despite enforcing Basic Auth", strict=True
)
def test_spec_declares_security_scheme(config):
    """TC-CONTRACT-03: spec should document the Basic Auth requirement it actually enforces."""
    raw = requests.get(config.swagger_url, timeout=10).json()
    assert "securityDefinitions" in raw or "security" in raw, (
        "[TC-CONTRACT-03] expected spec to declare a security scheme (BUG-06)"
    )


@pytest.mark.case_id("TC-CONTRACT-04")
@pytest.mark.priority("P2")
@pytest.mark.xfail(
    reason="BUG-13: spec declares a response body schema for DELETE /assets/{id}'s 204, but HTTP 204 "
    "must never carry a body -- the actual response is correctly empty",
    strict=True,
)
def test_delete_asset_204_has_no_body_schema(config):
    """TC-CONTRACT-04: DELETE /assets/{id}'s 204 response should not declare a body schema."""
    raw = requests.get(config.swagger_url, timeout=10).json()
    response_204 = raw["paths"]["/assets/{id}"]["delete"]["responses"]["204"]
    assert "schema" not in response_204, (
        f"[TC-CONTRACT-04] BUG-13: expected no 'schema' key on the 204 response, got {response_204!r}"
    )
