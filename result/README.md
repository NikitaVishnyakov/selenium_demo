# Result — Deliverables Index

This folder collects the final deliverables for the take-home assignment
(`0_assignment_brief.md`) in one place, pulled from `docs/` and `reports/` (which
otherwise stay spread across the repo / are git-ignored as generated output).
**Everything here is a copy** — the source of truth stays in `docs/` and `reports/`.
See "Regenerating this folder" at the bottom for how to refresh it after a new run.

Generated: 2026-07-16, against `infralightio/test-integration-api`, local run.

| # | Folder / file | Assignment requirement it satisfies |
|---|---|---|
| 0 | [`0_assignment_brief.md`](0_assignment_brief.md) | Original brief, for reference |
| 1 | [`1_test_plan/`](1_test_plan) | "Create and automate a test plan for the service" |
| 2 | [`2_bug_report/`](2_bug_report) | "All bugs are found and reported clearly" |
| 3 | [`3_functional_contract_test_report/`](3_functional_contract_test_report) | "Generate a test report" (functional/auth/tenant/contract/negative suite) |
| 4 | [`4_load_test_report/`](4_load_test_report) | "Bonus: load testing" — service must handle ≥1000 req/min |
| 5 | [`5_supporting_research/`](5_supporting_research) | Backing evidence (manual endpoint exploration behind the bug list) |

The single-command automation itself ("Create the automation to run the service, the
test suite and produce the test report") is not duplicated here — it lives at the repo
root as `Makefile` + `docker-compose.yml` (`make all` = up → test → down; `make report`
/ `make load` regenerate what's copied into sections 3–4). See the root `README.md`.

---

## 1 — Test plan (`1_test_plan/`)

- **`test_strategy.md`** — the finalized test plan: test categories & priority, the
  full test-case matrix (`TC-AUTH-*`, `TC-TENANT-*`, `TC-INT-*`, `TC-AST-*`, `TC-NEG-*`,
  `TC-CONTRACT-*`, `TC-LOAD-*`), fixture/config design, contract-validation approach,
  bug-regression mapping. Each row maps 1:1 to an implemented pytest test.
- **`execution_log_TEST_PLAN.md`** — phase-by-phase build log (research → strategy →
  automation) showing the plan was actually carried out, with live-run results and bugs
  found noted inline as they were discovered.

## 2 — Bug report (`2_bug_report/`)

- **`BUG_REPORTS.md`** — 13 documented defects (3 critical, 4 high, 3 medium, 1 low, 1
  info; severity table + one write-up per bug: summary, repro steps, expected vs.
  actual, affected endpoint(s), linked automated regression test, fix-priority
  recommendation). Headline findings: **BUG-01** (malformed `PATCH /assets` deadlocks
  all writes service-wide) and **BUG-02** (broken tenant segregation / BOLA,
  OWASP API1:2023).

## 3 — Functional / contract / auth / tenant / negative test report (`3_functional_contract_test_report/`)

- **`allure_report.html`** — self-contained Allure report (open directly in a browser,
  no server needed) covering the auth, tenant, functional, negative, and
  schemathesis-based contract suites. Regenerate with `make test && make report-static`.

## 4 — Load test report (`4_load_test_report/`, bonus)

Two Locust runs, 20 users / 90s each, against `≥1000 req/min` target:

- **`read_only_baseline/`** — GET-only baseline (safe to repeat). Result: **~302 req/s
  sustained (~18k req/min, 18x target)**, 0.30% error rate, p95 4–7ms / p99 11–16ms.
  Regenerate with `make load-read`.
- **`mixed_read_write_crash/`** — mixed read/write run. Result: **service crashes**
  (BUG-12 — concurrent `POST`/`GET /integrations` triggers a fatal Go runtime error,
  `concurrent map iteration and map write`, container exits). The crash itself is the
  finding, documented in `BUG_REPORTS.md`. Regenerate with `make load` (container needs
  a restart afterward).

## 5 — Supporting research (`5_supporting_research/`)

- **`phase1_research.md`** — raw manual exploration of the SUT that the bug list and
  test plan are built on: full endpoint inventory, curl transcripts, initial bug
  findings. Frozen record, kept for traceability.

---

## Regenerating this folder

There's no dedicated `make result` target (this folder is a point-in-time snapshot for
review, not part of the CI/automation loop). To refresh it after a new run:

```bash
make all                 # up -> test -> down, refreshes reports/allure-results
make report-static       # -> reports/allure-report/index.html
make load-read && make load   # -> reports/load/*.html + *.csv (restart container between them)
```

then re-copy the relevant files from `docs/` and `reports/` into the sections above.
