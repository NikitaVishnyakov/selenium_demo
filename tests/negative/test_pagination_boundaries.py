import pytest

from tests.helpers import assert_status_in

pytestmark = [pytest.mark.negative, pytest.mark.owner("Nikita.Vyshniakov")]

INVALID_PAGINATION_PARAMS = [
    ({"page": "abc"}, "non-numeric page"),
    ({"page": -1}, "negative page"),
    ({"page": 0}, "page=0 boundary"),
    ({"limit": -1}, "negative limit"),
]


@pytest.mark.case_id("TC-NEG-02..04")
@pytest.mark.priority("P1")
@pytest.mark.parametrize(
    "params, label", INVALID_PAGINATION_PARAMS, ids=[label for _, label in INVALID_PAGINATION_PARAMS]
)
def test_integrations_reject_invalid_pagination(client_test1, integration_factory, params, label):
    """TC-NEG-02/03/04: GET /integrations should reject invalid page/limit with 400, not crash.

    Regression for BUG-07 (widened scope): non-numeric, negative and zero page/limit all
    currently 500 instead of 400. Left red as a regression guard until fixed.

    Requires at least one record to exist first: the negative-limit crash is a slice/bounds
    panic on the actual result set, not on the raw parameter -- on an empty table it silently
    returns 200 null instead of crashing, which would make this case flaky depending on
    whatever state earlier tests left behind.
    """
    integration_factory(client_test1)

    resp = client_test1.get("/integrations", params=params)
    assert_status_in(resp, {400}, f"TC-NEG (integrations, {label})")


@pytest.mark.case_id("TC-NEG-02..04")
@pytest.mark.priority("P1")
@pytest.mark.parametrize(
    "params, label", INVALID_PAGINATION_PARAMS, ids=[label for _, label in INVALID_PAGINATION_PARAMS]
)
def test_assets_reject_invalid_pagination(client_test1, integration_factory, asset_factory, params, label):
    """TC-NEG-02/03/04: GET /assets should reject invalid page/limit with 400, not crash (BUG-07).

    Requires at least one asset to exist first -- same data-dependency as the integrations
    case: with zero assets under integrationId the negative-limit crash doesn't trigger
    (200 []), which would make this case flaky depending on execution order/leftover state.
    """
    integration = integration_factory(client_test1)
    asset_factory(client_test1, integration["id"])

    resp = client_test1.get("/assets", params={"integrationId": integration["id"], **params})
    assert_status_in(resp, {400}, f"TC-NEG (assets, {label})")


@pytest.mark.case_id("TC-NEG-04-control")
@pytest.mark.priority("P1")
def test_integrations_pagination_happy_path(client_test1, integration_factory):
    """TC-NEG-04 control: page=1 (valid boundary) must still work."""
    integration_factory(client_test1)

    resp = client_test1.get("/integrations", params={"page": 1})
    assert_status_in(resp, {200}, "TC-NEG (integrations, page=1 control)")


@pytest.mark.case_id("TC-NEG-05")
@pytest.mark.priority("P2")
def test_integrations_out_of_range_page_returns_empty_list(client_test1):
    """TC-NEG-05: out-of-range page on GET /integrations should return [], not null.

    Regression for BUG-08. GET /assets already returns [] correctly for the equivalent
    case (see test_assets_out_of_range_page_returns_empty_list, a guard test).
    """
    resp = client_test1.get("/integrations", params={"page": 999999})
    assert_status_in(resp, {200}, "TC-NEG-05")
    assert resp.json() == [], f"[TC-NEG-05] BUG-08: expected [], got {resp.json()!r} (out-of-range page returns null)"


@pytest.mark.case_id("TC-NEG-05-guard")
@pytest.mark.priority("P2")
def test_assets_out_of_range_page_returns_empty_list(client_test1, integration_factory):
    """TC-NEG-05 guard: GET /assets already returns [] (not null) for an out-of-range page."""
    integration = integration_factory(client_test1)

    resp = client_test1.get("/assets", params={"integrationId": integration["id"], "page": 999999})
    assert_status_in(resp, {200}, "TC-NEG-05 (assets guard)")
    assert resp.json() == []
