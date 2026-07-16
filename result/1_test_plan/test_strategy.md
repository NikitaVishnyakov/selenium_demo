# Test Strategy — QA Test API (Phase 2 deliverable)

SUT: `infralightio/test-integration-api`. Built from manual SUT research (bugs, endpoint inventory) and raw design decisions. This is the finalized strategy that Phase 3 automation implements directly — every test case below maps to one pytest test (or a parametrized set).

---

## 1. Scope & test categories

| Category | Covers | Priority |
|---|---|---|
| Auth (authN) | Basic Auth valid/invalid/missing, `WWW-Authenticate` on 401 | High |
| Tenant isolation (authZ / BOLA) | BUG-02 regression: list filtering, direct id access, cross-tenant write/delete | **Critical** |
| Functional/CRUD | Happy path per endpoint | High |
| Contract validation | Response vs `/swagger/doc.json` (schema, codes, headers) | High |
| Negative/boundary | Invalid types, page/limit edges, malformed id/JSON | High |
| Reliability under load | BUG-01 write-deadlock regression, single-test and under load | **Critical** |
| Load (bonus) | Throughput/latency/error-rate at ≥1000 req/min | Medium |

BUG-02 classifies as **BOLA (Broken Object Level Authorization)** — OWASP API1:2023. Use this term in the final report's security section.

## 2. Bug regression priority (Probability × Severity)

| Bug | Priority | Automate |
|---|---|---|
| BUG-01 write-deadlock | **P0** | Required, isolated test |
| BUG-02 tenant isolation | **P0** | Required, 6 sub-cases |
| BUG-03 PUT /integrations route mismatch | P1 | Required |
| BUG-07 pagination → 500 | P1 | Required |
| BUG-04 response code mismatch | P2 | Required, non-blocking |
| BUG-05 id type mismatch | P2 | Caught by contract test |
| BUG-08 null vs [] | P2 | Required, non-blocking |
| BUG-06 no security scheme in spec | P2 | Caught by contract test |
| BUG-09 `PUT /integrations/{id}` silently no-ops | **P1** | Required, functional test (found during Phase 3) |
| BUG-10 `POST /integrations` crashes on empty/missing `name` | **P1** | Required, negative test (found during Phase 3 via schemathesis) |
| BUG-11 `DELETE` on non-existent resource reports fake success | P2 | Required, negative test (found during Phase 3) |
| BUG-12 concurrent `POST /integrations` crashes the whole process | **P0, Critical** | Required, load test (found during Phase 3 via locust) |
| BUG-13 `DELETE /assets/{id}` 204 wrongly declares a body schema | P2 | Caught by contract test (found during Phase 3 via schemathesis) |

Build order in Phase 3: P0 regressions → contract/functional (auto-catches P1/P2) → load.

## 3. Test design techniques applied

- **Equivalence Partitioning + BVA** on `page`/`limit`: {negative, zero, valid, huge, non-numeric}; boundaries `-1, 0, 1, MAX_INT`. `integrationId` required-vs-optional partition on `GET /assets`.
- **Decision table** — auth {valid/invalid/missing} × tenant {owner/other} × resource {exists/not-exists} → systematic case set covering BUG-02 plus standard 401/404.
- **Syntax testing** — malformed id (non-UUID, empty string), injection-style strings in `name`/`description`/`type` — confirm no 500/crash, not a pentest.
- Pairwise and state-transition: not applicable (too few independent params per endpoint; resources have no state machine beyond CRUD).

## 4. Contract validation approach

- **schemathesis** as primary tool — property-based generation from `/swagger/doc.json`, auto-covers boundary/invalid inputs and schema conformance.
- Manual assertions (pydantic/jsonschema) as a supplement where business semantics can't be expressed as pure schema (tenant isolation).
- Known spec/reality gaps (BUG-03, BUG-05, BUG-06) marked `xfail` with a bug reference, not silently ignored.

## 5. Fixtures & configuration

- Config via env vars: `BASE_URL`, `TEST1_USER`/`TEST1_PASS`, `TEST2_USER`/`TEST2_PASS`. No hardcoded values in tests.
- Fixtures:
  - `api_client` — bare `requests.Session`, no auth.
  - `client_test1` / `client_test2`, or a parametrized `tenant_client(params=[...])` to run the same test against both tenants.
  - `created_integration` / `created_asset` — factory fixture with teardown cleanup.
- Given BUG-01 shows service state is fragile: **every test creates its own data**, no shared mutable state or cross-test fixture reuse.

## 6. Test data strategy

- Each test case creates its own integration/asset via POST; never depends on data from another test.
- Teardown does best-effort DELETE wrapped in try/except — logs on failure, never fails the test (service has already shown DELETE itself can hang).
- Tenant-isolation cases require both tenants in the same test: test1 creates → test2 attempts read/write/delete.

## 7. Load test scope (bonus)

- Tool: **locust** (Python-native, integrates into the same repo/CI, no extra runtime like k6).
- Target: ≥1000 req/min (~16.7 rps) sustained, error rate < 2%.
- Scenario **must include writes**, not just GETs — a read-only load test cannot catch BUG-01.
- Metrics: throughput, p95/p99 latency, error rate, whether the deadlock condition was triggered.
- Separate script from the pytest suite, but launched by the same single command (docker-compose/Makefile).

## 8. Bug report format (for the final report)

Per bug: Title, Severity (Critical/High/Medium/Low), Steps to reproduce (curl), Expected vs Actual, Affected endpoint(s), linked automated test (file::name), fix-priority recommendation (§2 table).

## 9. Pytest markers

`smoke`, `functional`, `contract`, `tenant`, `negative`, `load` — registered in `pytest.ini`. Enables `pytest -m "tenant or contract"` for a fast P0/P1 regression pass without the full suite.

---

## 10. Test case matrix (Phase 3 backlog)

Each row = one pytest test (or one parametrized family). IDs are stable references for bug reports and PRs.

### AUTH — marker `smoke, auth`
| ID | Case | Expected |
|---|---|---|
| TC-AUTH-01 | No credentials, any endpoint (parametrized) | 401 |
| TC-AUTH-02 | Invalid credentials | 401 |
| TC-AUTH-03 | Valid test1 / test2 | 200 |
| TC-AUTH-04 | `WWW-Authenticate` header present on 401 | header present (documents BUG-06 gap if absent from spec) |

### TENANT — marker `tenant`, **P0**
| ID | Case | Regression for |
|---|---|---|
| TC-TENANT-01 | `GET /integrations` as test1 returns only test1's records | BUG-02 (list) |
| TC-TENANT-02 | test2 `GET /integrations/{id}` on test1's id | BUG-02 (direct read) |
| TC-TENANT-03 | test2 `GET /assets/{id}` on test1's id | BUG-02 (direct read) |
| TC-TENANT-04 | test2 `DELETE /assets/{id}` on test1's asset | BUG-02 (cross-tenant delete) |
| TC-TENANT-05 | test2 `DELETE /integrations/{id}` on test1's integration | BUG-02 (cross-tenant delete) |
| TC-TENANT-06 | test2 `POST /assets` with test1's `integration_id` | BUG-02 (cross-tenant write) |
| TC-TENANT-07 | `GET /assets?integrationId=` correctly tenant-filtered | guard test (already correct — must stay correct) |

### CRUD — Integrations, marker `functional`
| ID | Case |
|---|---|
| TC-INT-01 | Create happy path |
| TC-INT-02 | Get by id happy path |
| TC-INT-03 | Update via actual route `PUT /integrations/{id}` happy path |
| TC-INT-04 | Delete happy path |
| TC-INT-05 | List with pagination happy path |

### CRUD — Assets, marker `functional`
| ID | Case |
|---|---|
| TC-AST-01 | Create happy path (`integration_id` required) |
| TC-AST-02 | Get by id — assert id is a UUID string (documents BUG-05) |
| TC-AST-03 | Update via `PATCH /assets` happy path |
| TC-AST-04 | Delete happy path |
| TC-AST-05 | List without `integrationId` → 400 (already-verified guard) |

### NEGATIVE / BOUNDARY — marker `negative`
| ID | Case | Regression for |
|---|---|---|
| TC-NEG-01 | `PATCH /assets` with id resolving to a non-asset (e.g. integration id) → error handled, subsequent writes still succeed | **BUG-01, P0** — must assert no deadlock, run isolated/last |
| TC-NEG-02 | `page=<non-numeric>` → 400 not 500 | BUG-07 |
| TC-NEG-03 | `page=-1` / `limit=-1` → 400 not 500 (revised: confirmed to 500, not silently accepted as originally assumed) | BUG-07 |
| TC-NEG-04 | Boundary values `page ∈ {0, 1, MAX_INT}` — `page=0` confirmed 500 on both endpoints | BUG-07 |
| TC-NEG-05 | Out-of-range `page` → `[]` not `null` | BUG-08 |
| TC-NEG-06 | Malformed JSON body → 400 | syntax testing |
| TC-NEG-07 | Injection-style strings in `name`/`description`/`type` → no 500, safely handled | syntax testing |
| TC-NEG-09 | `POST /integrations` with empty/missing `name` → 400 not 500 | BUG-10 (found via schemathesis, Phase 3) |
| TC-NEG-08 | Non-UUID id: GET → 404 (correct, guard); DELETE on non-existent/non-UUID id → should 404, actually reports fake success | BUG-11 |

### CONTRACT — marker `contract`
| ID | Case |
|---|---|
| — | schemathesis full-spec property-based run (all endpoints, auto-generated): not-a-server-error, status-code conformance, and response-schema conformance, with per-operation known-gap checks skipped (BUG-04/BUG-13) so red stays a signal for new defects |
| TC-CONTRACT-01 | `POST /assets` / `POST /integrations` return 201 vs spec's 200 | xfail, BUG-04 |
| TC-CONTRACT-02 | `PUT /integrations` at documented (id-in-body) shape → 404 | xfail, BUG-03 |
| TC-CONTRACT-03 | Spec has no `securityDefinitions`/`security` block | documented gap, BUG-06 |
| TC-CONTRACT-04 | `DELETE /assets/{id}`'s 204 response wrongly declares a body schema | xfail, BUG-13 |

### LOAD (bonus) — locust, `loadtest/locustfile.py`
| ID | Case | Result |
|---|---|---|
| TC-LOAD-01 | Sustain ≥1000 req/min; capture throughput, p95/p99, error rate | `make load-read` (GET-only baseline): 302 req/s (~18k/min), 0.30% errors, p95 4-7ms — target met comfortably for reads. `make load` (mixed read/write): service crashes almost immediately, see TC-LOAD-02/BUG-12 |
| TC-LOAD-02 | Explicitly assert whether a global-failure condition manifests under sustained load | Manifests, but not BUG-01 as originally scoped — surfaced **BUG-12** instead (concurrent `POST /integrations` crashes the whole process, unrelated unsynchronized-map bug, more severe than BUG-01 since it needs no malformed input). BUG-01 itself isn't separately re-tested under concurrency: it's server-wide and triggered by a single request, so concurrent load adds no new information over the isolated `tests/negative/test_write_deadlock.py` regression |

---

**Note on TC-NEG-01 / BUG-01:** this test mutates global service state (deadlocks all writes). It must run in its own isolated job/container invocation (not interleaved with the rest of the suite) or as the deliberately-last test with a container restart after — otherwise it poisons every other write-dependent test that runs after it.
