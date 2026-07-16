# Test Plan — QA Test API (Automation Engineer Home Assignment)

SUT: `infralightio/test-integration-api` (Docker), OpenAPI at `/swagger/doc.json`, Basic Auth, multi-tenant.
Assignment brief: `result/0_assignment_brief.md`.

Status legend: ☐ not started · ▶ in progress · ✅ done

---

## Phase 1 — Research the SUT ✅

Goal: understand the actual behavior of the service (not just the spec) before designing tests.

Done:
- Pulled/ran the container, fetched and read the full OpenAPI spec
- Manually exercised every endpoint with both tenants (test1/test2) via curl
- Probed auth (no creds, bad creds), tenant isolation, pagination edge cases, id type handling
- Found and documented 8 bugs (2 critical: global write-deadlock, broken tenant segregation)

Output: a full endpoint inventory + bug list, the source of truth for what Phase 2 needed to cover.

Remaining/optional for this phase:
- ☐ Precise root-cause isolation of BUG-01 trigger shape (nice-to-have, not blocking)

---

## Phase 2 — Test Strategy ✅

Goal: turn Phase 1 findings into a concrete, scoped test plan before writing code.

Research findings were filtered into actionable guidance and finalized into `test_strategy.md` —
that is now the source of truth for Phase 3, including a full test-case matrix (IDs TC-AUTH-*,
TC-TENANT-*, TC-INT-*, TC-AST-*, TC-NEG-*, TC-CONTRACT-*, TC-LOAD-*) ready to convert 1:1 into
pytest tests.

Closed:
- ✅ Test categories & priority — `test_strategy.md` §1
- ✅ Regression cases for each of the 8 confirmed bugs, ranked P0-P2 — `test_strategy.md` §2, §10
- ✅ Contract validation approach: schemathesis + targeted manual assertions — `test_strategy.md` §4
- ✅ Fixture/config design: base client, per-tenant auth fixtures, env-based config — `test_strategy.md` §5
- ✅ Test data strategy: per-test creation/cleanup, no shared mutable state — `test_strategy.md` §6
- ✅ Load test scope (bonus): locust, target 1000 req/min, throughput/p95/p99/error-rate — `test_strategy.md` §7
- ✅ Bug reporting format for the final report — `test_strategy.md` §8
- ✅ Markers/tags for selective runs (smoke, functional, contract, tenant, negative, load) — `test_strategy.md` §9

---

## Phase 3 — Automation ▶

Goal: implement the plan from Phase 2.

Infra prepared, done before writing any actual tests:
- ✅ Project bootstrap: pytest project structure, `requirements.txt`, config via env vars — `src/core/config.py` (`Config.from_env`), `.env.example`
- ✅ Base HTTP client + fixtures (per-tenant auth, cleanup) — `src/api/clients/api_client.py` + `tests/conftest.py` (`client_test1`/`client_test2`/`tenant_client`, `integration_factory`/`asset_factory` with try/except teardown, session-scoped `_wait_for_service` fail-fast fixture)
- ✅ docker-compose: `docker-compose.yml` (api service) + `Makefile` (`make up`/`test`/`report`/`down`/`all` — single-command run). Smoke-verified end-to-end against the live container (create/cross-tenant-read/delete all worked; cross-tenant read reconfirmed BUG-02)
- ✅ Reporting wired: Allure attach-per-test-log hook in `tests/conftest.py`, xdist-safe file logging in `src/core/logger.py`, `make report` target
- ✅ Test directory skeleton by category: `tests/{auth,tenant,functional,negative,contract}/` matching the `pytest.ini` markers and the `test_strategy.md` §10 matrix
- ✅ README: `make up` / `make test` / `make report` documented

Still to build (writing the actual tests now, on top of the prepared infra):
- ✅ Auth tests (TC-AUTH-01..04) — `tests/auth/test_auth.py`. Live run: no-creds/invalid-creds correctly 401'd, valid creds 200, `WWW-Authenticate` present on 401. Shared `assert_status_in` promoted to `tests/helpers.py` (was duplicated in `tests/tenant/helpers.py`); `tests/tenant/helpers.py` now holds only `assert_not_leaked`.
- ✅ Contract tests — `tests/contract/test_schema_fuzzing.py` (schemathesis property-based sweep, all 9 non-deadlock operations, `checks=[not_a_server_error]`) + `tests/contract/test_known_gaps.py` (TC-CONTRACT-01/02/03, xfail(strict=True) regressions for BUG-03/04/06). Live run: 3 xfailed-as-expected known gaps pass; the fuzz sweep genuinely fails on 3 operations (`GET /assets`, `GET /integrations`, `POST /integrations`) — new crash bugs, see BUG-07 (widened) / BUG-10 below. **Gotcha**: excluding an operation from a `LazySchema.parametrize()` sweep must be done via `.exclude()` on the outer `schemathesis.pytest.from_fixture(...)` object itself, not inside the fixture that returns the schema — schemathesis's `get_schema()` clones with a fresh `filter_set`, silently discarding a fixture-level exclude. First attempt got this wrong and let `PATCH /assets` through, which triggered BUG-01 (container had to be restarted) — see `test_schema_fuzzing.py` comment for the concrete explanation. Also: schemathesis raises `FailureGroup` (a `BaseExceptionGroup`, not an `AssertionError`) on a check failure, which Allure reports as **broken** rather than **failed** (`allure_pytest/utils.py::get_status` only maps `AssertionError`/`pytest.fail.Exception` to FAILED, everything else to BROKEN). `test_api_conformance` now catches `FailureGroup` and re-raises `AssertionError(str(exc))` so genuine API defects show up as failed, not broken.
- ✅ Functional tests (TC-INT-01..05, TC-AST-01..05) — `tests/functional/test_integrations.py`, `tests/functional/test_assets.py`. Live run: 9/10 pass; `test_update_integration` (TC-INT-03) fails — new bug found (see BUG-09 below).
- 🐛 **BUG-09 found during functional pass (P1, High)**: `PUT /integrations/{id}` returns `200` with a body matching the documented schema but silently doesn't persist the update (name unchanged on response and follow-up GET). Documented in `test_strategy.md` §2. `TC-INT-03` encodes correct behavior and is left red as a regression guard, same pattern as BUG-01/BUG-02.
- 🐛 **BUG-07 widened + BUG-10 found during contract pass (P1, High), via schemathesis fuzzing**: `page=0` and negative `page`/`limit` also 500 on both list endpoints (BUG-07's scope was previously understood as non-numeric `page` only; the "negative silently accepted" claim under the old BUG-08 was wrong — corrected during this pass). New: `POST /integrations` 500s on empty/missing `name` regardless of `type` (BUG-10); `POST /assets` with empty `name` does not crash, isolated to integrations. Both documented in `test_strategy.md`; `test_api_conformance` in the fuzz sweep is intentionally left red until fixed.
- ✅ TC-NEG-02..09 — `tests/negative/test_pagination_boundaries.py` (TC-NEG-02..05, BUG-07/08) + `tests/negative/test_malformed_input.py` (TC-NEG-06..09, BUG-10/11). Live run (`pytest -m "negative and not deadlock"`, container restarted first): 13 failed (regression guards for BUG-07/08/10/11) / 7 passed (malformed JSON 400, injection strings handled safely, GET-by-non-uuid 404 guards, page=1/out-of-range-assets guards).
- 🐛 **BUG-11 found during this pass (P2, Medium)**: `DELETE /integrations/{id}` and `DELETE /assets/{id}` report success (`200`/`204`) even when the id was never created or isn't a UUID — inconsistent with `GET`, which correctly 404s. Documented in `test_strategy.md`.
- ⚠️ **Process note**: running `pytest -m negative` directly (not via `make test`) also collects `test_write_deadlock.py`, since that test carries both `negative` and `deadlock` markers — this triggered BUG-01 mid-run and required a container restart. Always scope with `-m "negative and not deadlock"` (or use `make test`) when running negative tests ad hoc.
- ⚠️ **Flaky-if-run-out-of-order nuance found**: the BUG-07 negative-`limit` crash only reproduces when at least one matching record already exists (an empty result set short-circuits before the crashing slice/bounds logic) — for assets specifically, a real *asset* must exist under `integrationId`, not just an integration. Both `test_..._reject_invalid_pagination` tests now create the needed data via factories first so the assertion is deterministic regardless of what earlier tests left behind.
- ✅ Load tests (TC-LOAD-01/02, bonus) — `loadtest/locustfile.py` (locust, two `HttpUser` classes), wired into `make load` / `make load-read`.
  - `ReadOnlyUser` / `make load-read`: GET-only baseline, 20 users, 90s. Live run: **10,034 requests, ~302 req/s sustained (~18k req/min, 18x the >=1000 req/min target), 0.30% error rate** (under the <2% target), p50=2ms/p95=4-7ms/p99=11-16ms. Confirms the service comfortably meets the throughput target **for reads**.
  - `ApiUser` / `make load`: mixed read/write, same params. Live run: crashed almost immediately.
- 🐛 **BUG-12 found during this pass (P0, Critical)** — the headline load-test finding: concurrent `POST /integrations` racing a concurrent `GET /integrations` crashes the **entire process** (`fatal error: concurrent map iteration and map write` in `CreateIntegration`, container exit code 2) — an unrecoverable Go runtime error, not a panic Gin's recovery middleware can catch. The service cannot survive concurrent writes at all, let alone at the assignment's required throughput. Documented in `test_strategy.md` with full stack trace and repro.
- ⚠️ **Secondary, lower-confidence observation**: even the read-only baseline run ended with the container exiting `137` (SIGKILL from outside the process, no in-process error logged) shortly after locust's own clean shutdown. Cause not conclusively identified (Docker Desktop resource pressure under ~300 req/s is the leading guess) — flagged for awareness, not asserted as a distinct confirmed bug the way BUG-12 is.
- ✅ Tenant segregation tests (regression for BUG-02) — `tests/tenant/test_tenant_isolation.py`, TC-TENANT-01..07. Live run: 6/7 fail against the current service (confirms BUG-02); TC-TENANT-07 guard passes.
- ✅ Negative/edge case tests — `tests/negative/test_write_deadlock.py` (TC-NEG-01, BUG-01), `test_pagination_boundaries.py` (TC-NEG-02..05), `test_malformed_input.py` (TC-NEG-06..09). BUG-01 test confirmed live (follow-up write times out); isolated via `deadlock` pytest marker, run separately with `make test-deadlock` (`make test` excludes it). Container restarted after the run to clear the poisoned state.
- ✅ Load test script (bonus) — see load test entries above.
- ✅ **Final bug report deliverable** — `BUG_REPORTS.md`, one write-up per bug (BUG-01..13) in the §8 format (Summary, Steps to reproduce, Expected vs Actual, Affected endpoint(s), linked automated test, fix-priority recommendation), plus a severity/priority summary table. Satisfies the "all bugs are found and reported clearly" success criterion.
- ✅ **Contract validation hardened**: `test_schema_fuzzing.py`'s fuzz sweep previously only checked `not_a_server_error` (crash-safety), not actual schema/status-code conformance. Added `status_code_conformance` and `response_schema_conformance` from `schemathesis.specs.openapi.checks` to the sweep. Verified live against the running container before wiring in: the `httputil.HTTPError` schema (`{code, message}`) has no `required` fields, so the actual `{"error": "..."}` error bodies pass it vacuously — no exclusion needed there. A `KNOWN_GAP_CHECKS` dict skips the specific check that would otherwise just re-report an already-catalogued, individually-regression-tested bug on a specific operation (`status_code_conformance` for `POST /assets`/`POST /integrations`, BUG-04's 201-vs-200; `response_schema_conformance` for `DELETE /assets/{id}`, new BUG-13 below) — this keeps the sweep's red/green status a signal for genuinely new defects rather than permanent noise. `GET /assets`/`GET /integrations`/`POST /integrations` stay red for their pre-existing, already-tracked reasons (BUG-07/BUG-10); all other operations now pass more strictly-validated checks than before.
- 🐛 **BUG-13 found during this hardening pass (P2, Low)**: the spec declares a response body schema (`type: string`) for `DELETE /assets/{id}`'s `204` response — HTTP 204 must never carry a body, so this is a spec-authoring defect (runtime behavior is correct; the actual body is empty). Caught by `response_schema_conformance` before being excluded from the broad sweep; regression-tested individually as `TC-CONTRACT-04` (`xfail(strict=True)`) in `test_known_gaps.py`. Documented in `test_strategy.md`/`BUG_REPORTS.md`.

---

## Backlog — polish (done)

- ✅ `smoke` marker distributed: `test_valid_credentials_accepted` (TC-AUTH-03), `test_create_integration` (TC-INT-01), `test_create_asset` (TC-AST-01), `test_list_assets_scoped_to_caller_tenant` (TC-TENANT-07, the one tenant guard that currently passes — deliberately not a currently-failing BUG-02 case, so `pytest -m smoke` stays a meaningful green/red gate rather than permanently red). Live run: 4/4 pass.
- ✅ `owner` marker — `@pytest.mark.owner("Nikita.Vyshniakov")` on every test module's `pytestmark`, registered in `pytest.ini`.
- ✅ `case_id` / `priority` markers — registered in `pytest.ini`, backfilled on every test (case_id per TC-* from `test_strategy.md`; priority P0/P1/P2 hoisted to module level where uniform, e.g. tenant=P0, functional=P1, per-test where mixed, e.g. contract/negative files where priority follows the specific bug's severity).
- ✅ Deadlock test isolation, revised from the original plan: a literal `@pytest.mark.skip` would have broken `make test-deadlock` too (skip always wins over `-m` selection, so the test could never be deliberately run). Used `@pytest.mark.skipif(not os.environ.get("RUN_DEADLOCK_TEST"), ...)` instead — skipped by default even if `-m deadlock` is matched directly, only runs when `make test-deadlock` sets `RUN_DEADLOCK_TEST=1`. Verified live: bare `pytest -m deadlock` → 1 skipped; `make test-deadlock` → actually executes and hits BUG-01 as expected.

## Notes
- Update the checkboxes/sections above directly as each phase progresses — this file is the running plan.
