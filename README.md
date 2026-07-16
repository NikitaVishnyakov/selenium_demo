# QA Test API — automation

REST API test framework (pytest + requests) for `infralightio/test-integration-api`.
CI[coming soon]. See `docs/TEST_PLAN.md` / `docs/test_strategy.md` for scope.

**Bugs found:** 12 documented in [`docs/BUG_REPORTS.md`](docs/BUG_REPORTS.md) (3 critical, 4 high,
3 medium, 1 low, 1 info) — summary, repro steps, expected/actual, and the automated regression
test for each.

## Setup
- `cp .env.example .env` and adjust if needed (defaults match the pre-populated test1/test2 users)
- `pip install -r requirements.txt`

## Run
- `make up` — start the API container, wait until it's reachable
- `make test` — run the suite (equiv. `pytest -m "not deadlock"`)
- `make test-deadlock` — isolated BUG-01 regression, never run inside the main suite
- `make report` — serve the Allure report
- `make down` — stop the container
- `make all` — up + test + down in one command

## Load testing (bonus, locust)
- `make load-read` — GET-only baseline, safe to run repeatedly; measures sustained throughput/latency against the >=1000 req/min target
- `make load` — mixed read/write; **expected to crash the service** (BUG-12, see `docs/phase1_research.md`) rather than complete cleanly — the crash itself is the finding
- Both run 20 users / 90s by default, override with `LOAD_USERS=`, `LOAD_SPAWN_RATE=`, `LOAD_DURATION=`; results land in `reports/load/`
- Restart the container (`make down && make up`) after `make load` before running anything else — the crash leaves it dead

## Selective runs
- `pytest -m smoke` — only smokes
- `pytest -m "tenant or contract"` — fast P0/P1 regression pass
- `pytest -n auto` — in parallel
