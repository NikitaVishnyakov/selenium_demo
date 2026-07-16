import os

import pytest

pytestmark = [
    pytest.mark.negative,
    pytest.mark.deadlock,
    pytest.mark.owner("Nikita.Vyshniakov"),
    pytest.mark.case_id("TC-NEG-01"),
    pytest.mark.priority("P0"),
    pytest.mark.skipif(
        not os.environ.get("RUN_DEADLOCK_TEST"),
        reason=(
            "BUG-01 regression: poisons every write for the rest of the container's life. "
            "Skipped unless explicitly opted in via RUN_DEADLOCK_TEST=1 (set by `make test-deadlock`), "
            "so it can never run by accident just from matching -m deadlock or plain collection."
        ),
    ),
]


def test_malformed_patch_does_not_deadlock_subsequent_writes(client_test1, integration_factory):
    """TC-NEG-01 (BUG-01, P0): PATCH /assets with an id that doesn't resolve to an
    asset must return an error response, not lock up every later write for every tenant.

    Isolated test: run via `make test-deadlock`, never inside the main suite - a real
    deadlock leaves the container unusable for every test that runs after it.
    """
    integration = integration_factory(client_test1)

    bad_patch = client_test1.patch("/assets", json={"id": integration["id"], "name": "x"})
    assert bad_patch.status_code >= 400

    followup = integration_factory(client_test1, name="post-malformed-patch-write")
    assert followup["id"]
