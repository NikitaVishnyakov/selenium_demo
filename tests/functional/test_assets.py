import uuid

import pytest

from tests.helpers import assert_status_in

pytestmark = [pytest.mark.functional, pytest.mark.owner("Nikita.Vyshniakov"), pytest.mark.priority("P1")]


@pytest.mark.smoke
@pytest.mark.case_id("TC-AST-01")
def test_create_asset(client_test1, integration_factory, asset_factory):
    """TC-AST-01: create happy path (integration_id required)."""
    integration = integration_factory(client_test1)
    asset = asset_factory(client_test1, integration["id"], name="asset-create")

    assert asset["integration_id"] == integration["id"]
    assert asset["name"] == "asset-create"


@pytest.mark.case_id("TC-AST-02")
def test_get_asset_by_id_is_uuid(client_test1, integration_factory, asset_factory):
    """TC-AST-02: get by id happy path — id must be a UUID string (documents BUG-05: spec types id as integer)."""
    integration = integration_factory(client_test1)
    created = asset_factory(client_test1, integration["id"])

    resp = client_test1.get(f"/assets/{created['id']}")
    assert_status_in(resp, {200}, "TC-AST-02")

    asset_id = resp.json()["id"]
    try:
        uuid.UUID(asset_id)
        is_uuid = True
    except (ValueError, TypeError, AttributeError):
        is_uuid = False
    assert is_uuid, f"[TC-AST-02] expected id to be a UUID string, got {asset_id!r}"


@pytest.mark.case_id("TC-AST-03")
def test_update_asset(client_test1, integration_factory, asset_factory):
    """TC-AST-03: update via PATCH /assets (id in body) happy path."""
    integration = integration_factory(client_test1)
    created = asset_factory(client_test1, integration["id"])

    resp = client_test1.patch("/assets", json={"id": created["id"], "name": "asset-updated"})
    assert_status_in(resp, {200}, "TC-AST-03")
    assert resp.json()["name"] == "asset-updated"

    follow_up = client_test1.get(f"/assets/{created['id']}")
    assert follow_up.json()["name"] == "asset-updated"


@pytest.mark.case_id("TC-AST-04")
def test_delete_asset(client_test1, integration_factory, asset_factory):
    """TC-AST-04: delete happy path."""
    integration = integration_factory(client_test1)
    created = asset_factory(client_test1, integration["id"])

    resp = client_test1.delete(f"/assets/{created['id']}")
    assert_status_in(resp, {204}, "TC-AST-04")

    follow_up = client_test1.get(f"/assets/{created['id']}")
    assert_status_in(follow_up, {404}, "TC-AST-04 (post-check)")


@pytest.mark.case_id("TC-AST-05")
def test_list_assets_without_integration_id_rejected(client_test1):
    """TC-AST-05: list without integrationId must be rejected (already-verified guard)."""
    resp = client_test1.get("/assets")
    assert_status_in(resp, {400}, "TC-AST-05")
