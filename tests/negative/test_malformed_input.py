import pytest

from tests.helpers import assert_status_in

pytestmark = [pytest.mark.negative, pytest.mark.owner("Nikita.Vyshniakov")]


@pytest.mark.case_id("TC-NEG-06")
@pytest.mark.priority("P1")
def test_malformed_json_body_rejected(client_test1):
    """TC-NEG-06: malformed JSON body on POST /integrations must be rejected with 400."""
    resp = client_test1.post("/integrations", data="{not valid json")
    assert_status_in(resp, {400}, "TC-NEG-06")


INJECTION_PAYLOADS = [
    "'; DROP TABLE integrations; --",
    "<script>alert(1)</script>",
]


@pytest.mark.case_id("TC-NEG-07")
@pytest.mark.priority("P1")
@pytest.mark.parametrize("payload", INJECTION_PAYLOADS, ids=["sql-like", "script-tag"])
def test_injection_style_name_handled_safely(client_test1, payload):
    """TC-NEG-07: injection-style strings in name must not crash the service (syntax testing, not a pentest)."""
    resp = client_test1.post("/integrations", json={"name": payload, "type": "generic"})
    assert_status_in(resp, {201}, "TC-NEG-07")

    try:
        follow_up = client_test1.get("/integrations", params={"page": 1})
        assert_status_in(follow_up, {200}, "TC-NEG-07 (service still healthy)")
    finally:
        client_test1.delete(f"/integrations/{resp.json()['id']}")


@pytest.mark.case_id("TC-NEG-08-guard-integrations")
@pytest.mark.priority("P1")
def test_get_integration_by_non_uuid_id_returns_404(client_test1):
    """TC-NEG-08 guard: GET /integrations/{non-uuid} correctly 404s, not 500."""
    resp = client_test1.get("/integrations/not-a-uuid")
    assert_status_in(resp, {404}, "TC-NEG-08 (integrations get, guard)")


@pytest.mark.case_id("TC-NEG-08-guard-assets")
@pytest.mark.priority("P1")
def test_get_asset_by_non_uuid_id_returns_404(client_test1):
    """TC-NEG-08 guard: GET /assets/{non-uuid} correctly 404s, not 500."""
    resp = client_test1.get("/assets/not-a-uuid")
    assert_status_in(resp, {404}, "TC-NEG-08 (assets get, guard)")


@pytest.mark.case_id("TC-NEG-08")
@pytest.mark.priority("P2")
def test_delete_nonexistent_integration_returns_404(client_test1):
    """TC-NEG-08: DELETE on a well-formed but never-created integration id should 404.

    Regression for BUG-11: currently reports fake success (200) instead of 404, unlike GET
    on the same non-existent id (see test_get_integration_by_non_uuid_id_returns_404).
    """
    resp = client_test1.delete("/integrations/00000000-0000-0000-0000-000000000000")
    assert_status_in(resp, {404}, "TC-NEG-08 (integrations delete)")


@pytest.mark.case_id("TC-NEG-08")
@pytest.mark.priority("P2")
def test_delete_nonexistent_asset_returns_404(client_test1):
    """TC-NEG-08: DELETE on a well-formed but never-created asset id should 404 (BUG-11)."""
    resp = client_test1.delete("/assets/00000000-0000-0000-0000-000000000000")
    assert_status_in(resp, {404}, "TC-NEG-08 (assets delete)")


MISSING_NAME_PAYLOADS = [
    ({"type": "generic"}, "name omitted"),
    ({"name": "", "type": "generic"}, "name empty string"),
]


@pytest.mark.case_id("TC-NEG-09")
@pytest.mark.priority("P1")
@pytest.mark.parametrize("payload, label", MISSING_NAME_PAYLOADS, ids=[label for _, label in MISSING_NAME_PAYLOADS])
def test_create_integration_rejects_missing_name(client_test1, payload, label):
    """TC-NEG-09: POST /integrations with empty/missing name should 400, not crash.

    Regression for BUG-10. POST /assets with an empty name does not crash (isolated to
    integrations) -- not re-tested here, see phase1_research.md.
    """
    resp = client_test1.post("/integrations", json=payload)
    assert_status_in(resp, {400}, f"TC-NEG-09 ({label})")
