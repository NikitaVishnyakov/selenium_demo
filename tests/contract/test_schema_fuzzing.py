import pytest
import schemathesis
from schemathesis.core.failures import FailureGroup
from schemathesis.specs.openapi.checks import response_schema_conformance, status_code_conformance

pytestmark = [
    pytest.mark.contract,
    pytest.mark.owner("Nikita.Vyshniakov"),
    pytest.mark.case_id("TC-CONTRACT-FUZZ"),
    pytest.mark.priority("P1"),
]


@pytest.fixture(scope="session")
def api_schema(config):
    return schemathesis.openapi.from_url(config.swagger_url)


# PATCH /assets with an id that doesn't resolve to an asset triggers BUG-01 (global write
# deadlock) -- excluded from the fuzz sweep, regression-tested in isolation by
# tests/negative/test_write_deadlock.py (marker `deadlock`).
#
# IMPORTANT: the exclude must be applied on this LazySchema itself, not on the schema
# returned by the `api_schema` fixture above -- schemathesis's LazySchema.parametrize()
# resolves the fixture then calls schema.clone(filter_set=...), which replaces the
# fixture-level filter_set rather than merging with it. An exclude() only applied inside
# the fixture is silently discarded and the excluded operation still gets fuzzed.
schema = schemathesis.pytest.from_fixture("api_schema").exclude(method="PATCH", path="/assets")

ALL_CHECKS = [schemathesis.checks.not_a_server_error, status_code_conformance, response_schema_conformance]

# (method, path) -> checks to skip for that operation, because they'd only re-report a mismatch
# that's already catalogued and individually regression-tested in test_known_gaps.py. Keeping them
# out of this sweep is what lets its red/green status stay a signal for *new*, previously-unknown
# contract defects instead of permanently re-flagging bugs we already track elsewhere.
KNOWN_GAP_CHECKS = {
    ("POST", "/assets"): {status_code_conformance},  # BUG-04: actual 201, spec documents 200
    ("POST", "/integrations"): {status_code_conformance},  # BUG-04: actual 201, spec documents 200
    ("DELETE", "/assets/{id}"): {response_schema_conformance},  # BUG-13: spec wrongly declares a
    # body schema (`type: string`) for the 204 response; HTTP 204 must never carry a body, and the
    # actual response is correctly empty -- see TC-CONTRACT-04 in test_known_gaps.py.
}


@schema.parametrize()
def test_api_conformance(case, client_test1):
    """Property-based sweep of the full spec: status codes and response bodies must conform to it,
    and no generated input should cause an unhandled 5xx.

    Per-operation known gaps (BUG-04/BUG-13) are skipped here and asserted explicitly/individually
    in test_known_gaps.py instead, so this sweep's failures stay a signal for new defects.
    """
    skip = KNOWN_GAP_CHECKS.get((case.method, case.path), set())
    checks = [check for check in ALL_CHECKS if check not in skip]
    try:
        case.call_and_validate(session=client_test1.session, checks=checks)
    except FailureGroup as exc:
        # schemathesis raises a BaseExceptionGroup here, not an AssertionError, so pytest/allure
        # would otherwise report this as "broken" rather than "failed". Re-raise as a plain
        # AssertionError so a real API defect shows up as a failed test, not a tooling error.
        #
        # pytest's one-line "short test summary info" only shows the first line of the message,
        # so lead with "OPERATION -> STATUS title" (the part that's actually useful at a glance)
        # instead of schemathesis's generic "Schemathesis found N distinct failure" preamble --
        # the full detail (including the curl repro) is still appended below for the full traceback.
        summary = "; ".join(
            f"{getattr(failure, 'operation', None) or f'{case.method} {case.path}'} -> "
            f"{getattr(failure, 'status_code', '?')} {failure.title}"
            for failure in exc.exceptions
        )
        raise AssertionError(f"{summary}\n\n{exc}") from exc
