# QA Test API — automation

REST API test framework (pytest + requests) for `infralightio/test-integration-api`
(multi-tenant, Basic Auth, OpenAPI spec at `/swagger/doc.json`). Built for the
Automation Engineer take-home assignment — brief: [`result/0_assignment_brief.md`](result/0_assignment_brief.md).

**Bugs found:** 13 documented in [`result/2_bug_report/BUG_REPORTS.md`](result/2_bug_report/BUG_REPORTS.md)
(3 critical, 4 high, 3 medium, 2 low, 1 info) — summary, repro steps, expected/actual, and the
automated regression test for each. Headline findings: **BUG-01** (a malformed `PATCH /assets`
deadlocks all writes service-wide) and **BUG-02** (broken tenant segregation / BOLA, OWASP API1:2023).

## Setup
- `cp .env.example .env` and adjust if needed (defaults match the pre-populated test1/test2 users)
- `pip install -r requirements.txt`

## Run
- `make up` — start the API container, wait until it's reachable
- `make test` — run the suite (equiv. `pytest -m "not deadlock"`)
- `make test-deadlock` — isolated BUG-01 regression, never run inside the main suite
- `make report` — serve the Allure report
- `make report-static` — generate a self-contained `reports/allure-report/index.html` (no server needed)
- `make down` — stop the container
- `make all` — up + test + down in one command

## Load testing (bonus, locust)
- `make load-read` — GET-only baseline, safe to run repeatedly; measures sustained throughput/latency against the >=1000 req/min target
- `make load` — mixed read/write; **expected to crash the service** (BUG-12) rather than complete cleanly — the crash itself is the finding
- Both run 20 users / 90s by default, override with `LOAD_USERS=`, `LOAD_SPAWN_RATE=`, `LOAD_DURATION=`; results land in `reports/load/`
- Restart the container (`make down && make up`) after `make load` before running anything else — the crash leaves it dead

## Selective runs
- `pytest -m smoke` — only smokes
- `pytest -m "tenant or contract"` — fast P0/P1 regression pass
- `pytest -n auto` — in parallel

## Project layout
- `src/core/config.py` — env-based config (`Config.from_env`), no hardcoded values
- `src/api/clients/api_client.py` — base HTTP client
- `tests/conftest.py` — `client_test1`/`client_test2`/`tenant_client` fixtures, `integration_factory`/`asset_factory` (create + try/except teardown), session-scoped fail-fast `_wait_for_service`, Allure per-test log attachment
- `tests/{auth,tenant,functional,negative,contract}/` — one dir per pytest marker/category
- Markers (registered in `pytest.ini`, `--strict-markers` enforced): `smoke`, `auth`, `functional`, `contract`, `tenant`, `negative`, `deadlock`, `load`, `flaky`
- Test data rule: every test creates its own data via the factories; never depends on another test's state (service state is fragile per BUG-01)

## Results (`result/`)

A point-in-time snapshot of the deliverables above, gathered into one labeled folder for review —
useful if you just want the finished artifacts without running anything:

| # | Folder | What's in it |
|---|---|---|
| 0 | [`result/0_assignment_brief.md`](result/0_assignment_brief.md) | Original brief |
| 1 | [`result/1_test_plan/`](result/1_test_plan) | `test_strategy.md` — categories, priorities, full test-case matrix (`TC-AUTH-*`, `TC-TENANT-*`, `TC-INT-*`, `TC-AST-*`, `TC-NEG-*`, `TC-CONTRACT-*`, `TC-LOAD-*`), fixture/config design — plus phase-by-phase `execution_log_TEST_PLAN.md` |
| 2 | [`result/2_bug_report/BUG_REPORTS.md`](result/2_bug_report/BUG_REPORTS.md) | All 13 bugs |
| 3 | [`result/3_functional_contract_test_report/`](result/3_functional_contract_test_report) | `allure_report.html` — self-contained Allure report, open directly in a browser |
| 4 | [`result/4_load_test_report/`](result/4_load_test_report) | `read_only_baseline/` (~302 req/s, 18x the 1000 req/min target) and `mixed_read_write_crash/` (BUG-12 crash evidence) |

`result/` is a static, git-tracked snapshot of the working reports (kept locally, not pushed).
Regenerate it after a new run with `make all && make report-static && make load-read && make load`,
then re-copy the relevant files into `result/`.
