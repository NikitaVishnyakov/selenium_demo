import pytest

from tests.helpers import assert_status_in
from tests.tenant.helpers import assert_not_leaked

pytestmark = [pytest.mark.tenant, pytest.mark.owner("Nikita.Vyshniakov"), pytest.mark.priority("P0")]


@pytest.mark.case_id("TC-TENANT-01")
def test_list_integrations_scoped_to_caller_tenant(client_test1, client_test2, integration_factory):
    """TC-TENANT-01: GET /integrations as test1 must not include test2's records."""
    other = integration_factory(client_test2, name="test2-only-integration")

    resp = client_test1.get("/integrations")
    resp.raise_for_status()

    ids = {item["id"] for item in resp.json()}
    assert_not_leaked(other["id"], ids, "TC-TENANT-01")


@pytest.mark.case_id("TC-TENANT-02")
def test_get_integration_by_id_blocks_other_tenant(client_test1, client_test2, integration_factory):
    """TC-TENANT-02: test2 GET /integrations/{id} on test1's id must be denied."""
    mine = integration_factory(client_test1)

    resp = client_test2.get(f"/integrations/{mine['id']}")

    assert_status_in(resp, {403, 404}, "TC-TENANT-02")


@pytest.mark.case_id("TC-TENANT-03")
def test_get_asset_by_id_blocks_other_tenant(client_test1, client_test2, integration_factory, asset_factory):
    """TC-TENANT-03: test2 GET /assets/{id} on test1's asset must be denied."""
    integration = integration_factory(client_test1)
    mine = asset_factory(client_test1, integration["id"])

    resp = client_test2.get(f"/assets/{mine['id']}")

    assert_status_in(resp, {403, 404}, "TC-TENANT-03")


@pytest.mark.case_id("TC-TENANT-04")
def test_delete_asset_blocks_other_tenant(client_test1, client_test2, integration_factory, asset_factory):
    """TC-TENANT-04: test2 DELETE /assets/{id} on test1's asset must be denied."""
    integration = integration_factory(client_test1)
    mine = asset_factory(client_test1, integration["id"])

    resp = client_test2.delete(f"/assets/{mine['id']}")
    assert_status_in(resp, {403, 404}, "TC-TENANT-04")

    still_there = client_test1.get(f"/assets/{mine['id']}")
    assert_status_in(still_there, {200}, "TC-TENANT-04 (post-check)")


@pytest.mark.case_id("TC-TENANT-05")
def test_delete_integration_blocks_other_tenant(client_test1, client_test2, integration_factory):
    """TC-TENANT-05: test2 DELETE /integrations/{id} on test1's integration must be denied."""
    mine = integration_factory(client_test1)

    resp = client_test2.delete(f"/integrations/{mine['id']}")
    assert_status_in(resp, {403, 404}, "TC-TENANT-05")

    still_there = client_test1.get(f"/integrations/{mine['id']}")
    assert_status_in(still_there, {200}, "TC-TENANT-05 (post-check)")


@pytest.mark.case_id("TC-TENANT-06")
def test_create_asset_under_other_tenant_integration_is_rejected(client_test1, client_test2, integration_factory):
    """TC-TENANT-06: test2 POST /assets with test1's integration_id must be denied."""
    integration = integration_factory(client_test1)

    resp = client_test2.post(
        "/assets",
        json={
            "integration_id": integration["id"],
            "name": "cross-tenant-asset",
            "description": "should be rejected",
        },
    )
    try:
        assert_status_in(resp, {400, 403, 404}, "TC-TENANT-06")
    finally:
        if resp.status_code == 201:
            client_test2.delete(f"/assets/{resp.json()['id']}")


@pytest.mark.smoke
@pytest.mark.case_id("TC-TENANT-07")
def test_list_assets_scoped_to_caller_tenant(client_test1, client_test2, integration_factory, asset_factory):
    """TC-TENANT-07: guard - GET /assets?integrationId= must stay tenant-filtered."""
    integration = integration_factory(client_test1)
    mine = asset_factory(client_test1, integration["id"])

    resp = client_test2.get("/assets", params={"integrationId": integration["id"]})
    resp.raise_for_status()

    ids = {item["id"] for item in resp.json()}
    assert_not_leaked(mine["id"], ids, "TC-TENANT-07")
