import pytest

from tests.helpers import assert_status_in

pytestmark = [pytest.mark.functional, pytest.mark.owner("Nikita.Vyshniakov"), pytest.mark.priority("P1")]


@pytest.mark.smoke
@pytest.mark.case_id("TC-INT-01")
def test_create_integration(client_test1, integration_factory):
    """TC-INT-01: create happy path."""
    integration = integration_factory(client_test1, name="int-create", type="generic")

    assert integration["name"] == "int-create"
    assert integration["type"] == "generic"
    assert integration["id"]


@pytest.mark.case_id("TC-INT-02")
def test_get_integration_by_id(client_test1, integration_factory):
    """TC-INT-02: get by id happy path."""
    created = integration_factory(client_test1)

    resp = client_test1.get(f"/integrations/{created['id']}")
    assert_status_in(resp, {200}, "TC-INT-02")
    assert resp.json()["id"] == created["id"]


@pytest.mark.case_id("TC-INT-03")
def test_update_integration(client_test1, integration_factory):
    """TC-INT-03: update via actual route PUT /integrations/{id} (BUG-03: spec documents id-in-body, no path id).

    Regression for BUG-09: even on the working route with a body matching the documented
    UpdateIntegrationRequest schema, the update currently returns 200 but does not persist —
    this assertion encodes the *correct* expected behavior and is expected to fail until fixed.
    """
    created = integration_factory(client_test1)

    resp = client_test1.put(f"/integrations/{created['id']}", json={"id": created["id"], "name": "int-updated"})
    assert_status_in(resp, {200}, "TC-INT-03")
    assert resp.json()["name"] == "int-updated", (
        f"[TC-INT-03] BUG-09: expected updated name 'int-updated', got {resp.json()['name']!r} "
        f"(update did not persist)"
    )

    follow_up = client_test1.get(f"/integrations/{created['id']}")
    assert follow_up.json()["name"] == "int-updated", "[TC-INT-03] BUG-09: update not persisted on follow-up GET"


@pytest.mark.case_id("TC-INT-04")
def test_delete_integration(client_test1, integration_factory):
    """TC-INT-04: delete happy path."""
    created = integration_factory(client_test1)

    resp = client_test1.delete(f"/integrations/{created['id']}")
    assert_status_in(resp, {200}, "TC-INT-04")

    follow_up = client_test1.get(f"/integrations/{created['id']}")
    assert_status_in(follow_up, {404}, "TC-INT-04 (post-check)")


@pytest.mark.case_id("TC-INT-05")
def test_list_integrations_pagination(client_test1, integration_factory):
    """TC-INT-05: list with pagination happy path."""
    for i in range(3):
        integration_factory(client_test1, name=f"int-page-{i}")

    resp = client_test1.get("/integrations", params={"page": 1, "limit": 2})
    assert_status_in(resp, {200}, "TC-INT-05")

    items = resp.json()
    assert len(items) <= 2, f"[TC-INT-05] expected at most 2 items for limit=2, got {len(items)}"
