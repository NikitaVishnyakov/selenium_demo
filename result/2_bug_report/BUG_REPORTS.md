# Bug Reports — `infralightio/test-integration-api`

Thirteen defects were found during manual exploration (Phase 1) and confirmed with automated
regression tests (Phase 3). Format follows `test_strategy.md` §8. Severity is Critical / High /
Medium / Low / Info. Raw research notes and curl transcripts: `docs/phase1_research.md`.

Reproduction steps assume the service is reachable at `http://localhost:8080` with `test1`/`test123`
(`test2`/`test456` used where a second tenant is needed). Restart the container between reproducing
BUG-01 and BUG-12 and any other write test — both leave the service in a broken/dead state.

---

## BUG-01 — Malformed `PATCH /assets` deadlocks all writes service-wide

**Severity:** Critical (P0)
**Affected endpoint(s):** `PATCH /assets` (trigger), all write endpoints (blast radius)

**Summary:** A single malformed `PATCH /assets` call — an id that doesn't resolve to an asset —
returns a `500`, then silently poisons the service: every subsequent write (POST/PATCH/DELETE),
for every tenant, hangs forever. Reads keep working. Only a container restart recovers it. This is
a service-wide denial-of-service triggerable by any authenticated user with a single bad request.

**Steps to reproduce:**
```
curl -u test1:test123 -X PATCH http://localhost:8080/api/v1/assets \
  -d '{"id":"<an-integration-id, not-an-asset-id>","name":"x"}'
# -> 500 {"error":"internal server error"}

curl -u test1:test123 -X POST http://localhost:8080/api/v1/integrations \
  -d '{"name":"x","type":"y"}'
# -> hangs indefinitely (any tenant, any write endpoint)
```

**Expected result:** The malformed `PATCH` returns a client error (`400`/`404`); the service
remains healthy and all other writes continue to succeed.

**Actual result:** The malformed `PATCH` returns `500`; all subsequent writes across the entire
service hang indefinitely until the container is restarted.

**Linked automated test:** `tests/negative/test_write_deadlock.py::test_malformed_patch_does_not_deadlock_subsequent_writes`
(TC-NEG-01). Isolated behind the `deadlock` pytest marker — run only via `make test-deadlock`, never
interleaved with the main suite; container needs a restart after.

**Fix priority recommendation:** Fix before release — blocking. This is a trivially-triggered,
full-service outage.

---

## BUG-02 — Broken tenant segregation (BOLA, OWASP API1:2023)

**Severity:** Critical (P0)
**Affected endpoint(s):** `GET /integrations`, `GET /integrations/{id}`, `GET /assets/{id}`,
`DELETE /integrations/{id}`, `DELETE /assets/{id}`, `POST /assets`

**Summary:** The service is documented as multi-tenant with required tenant segregation, but tenant
isolation is broken across almost every operation: `GET /integrations` returns all tenants' data
unfiltered; any authenticated tenant can read, delete, or attach data to another tenant's resources
by id. Only `GET /assets?integrationId=` (list) was found to be correctly scoped.

**Steps to reproduce:**
```
# as test1
curl -u test1:test123 -X POST http://localhost:8080/api/v1/integrations -d '{"name":"t1-int","type":"x"}'
# -> {"id":"<id1>", ...}

# as test2 — reads test1's integration directly
curl -u test2:test456 http://localhost:8080/api/v1/integrations/<id1>
# -> 200, returns test1's integration (should be 403/404)

# as test2 — deletes test1's integration
curl -u test2:test456 -X DELETE http://localhost:8080/api/v1/integrations/<id1>
# -> 200 {"message":"integration deleted"}

# as test1 — confirms it's gone
curl -u test1:test123 http://localhost:8080/api/v1/integrations/<id1>
# -> 404 (cross-tenant delete succeeded)

# unfiltered list
curl -u test1:test123 http://localhost:8080/api/v1/integrations
# -> includes test2's integrations too
```

**Expected result:** Every operation scopes to the caller's own tenant; cross-tenant reads/writes/
deletes return `403` or `404`.

**Actual result:** Cross-tenant read, delete, and write-by-reference all succeed; list is
unfiltered across tenants.

**Linked automated test:** `tests/tenant/test_tenant_isolation.py` (TC-TENANT-01..07). 6/7 currently
fail against the live service, confirming the bug; TC-TENANT-07 (list `/assets` scoping, the one
correct path) passes as a guard.

**Fix priority recommendation:** Fix before release — blocking. Textbook BOLA; a hard requirement
in the assignment brief ("must ensure tenant segregation") is not met.

---

## BUG-12 — Concurrent `POST /integrations` crashes the entire process

**Severity:** Critical (P0)
**Affected endpoint(s):** `POST /integrations` (confirmed); `POST /assets` likely, same
unsynchronized-map pattern, not separately confirmed

**Summary:** Under ordinary concurrent load (~20 simulated users, mixed reads/writes — well under
the required 1000 req/min), the service died with an unrecoverable Go `fatal error: concurrent map
iteration and map write` in `controller.(*Controller).CreateIntegration`, and the container exited
(code 2). This is a Go runtime `fatal error`, not a panic — Gin's recovery middleware (which
catches the BUG-07/BUG-10 panics and turns them into `500`s) cannot catch it; the whole process
terminates, taking down every in-flight request. Root cause: the integrations store is a plain Go
map, read (list-building in `GET /integrations`) and written (`POST /integrations`) with no
mutex/lock — concurrent access panics by the Go runtime's design. This directly violates the
assignment's "must handle a load of at least 1000 requests per minute" requirement: the service
cannot survive concurrent creates at all, let alone at that throughput.

**Steps to reproduce:**
```
make load       # loadtest/locustfile.py, mixed GET/POST /integrations, ~20 concurrent users
# service crashes within seconds; container exits with code 2
```

**Expected result:** The service handles concurrent creates/reads without crashing, sustaining
≥1000 req/min per the brief.

**Actual result:** The process fatally crashes within seconds of concurrent load; requires a
container restart. Confirmed via full stack trace in the locust run.

**Linked automated test:** `loadtest/locustfile.py` (TC-LOAD-01 baseline, TC-LOAD-02 mixed
read/write — surfaces this crash instead of the originally-scoped BUG-01 recheck).

**Fix priority recommendation:** Fix before release — blocking. More severe than BUG-01: it needs
no malformed input, just ordinary concurrent traffic, and directly fails the explicit load
requirement in the brief.

---

## BUG-03 — Contract mismatch: `PUT /integrations` route

**Severity:** High (P1)
**Affected endpoint(s):** `PUT /integrations`

**Summary:** The OpenAPI spec documents `PUT /integrations` with no path id (id in the request
body). The actual registered route is `PUT /integrations/{id}`. Calling the documented shape
returns `404` — the endpoint is unusable as specified by any client that follows the spec.

**Steps to reproduce:**
```
curl -u test1:test123 -X PUT http://localhost:8080/api/v1/integrations \
  -d '{"id":"<id>","name":"new-name"}'
# -> 404
```

**Expected result:** Matches the documented shape and succeeds (per spec), or the spec documents
the actual `{id}`-in-path route.

**Actual result:** `404` on the documented shape; only the undocumented `/integrations/{id}` route
works.

**Linked automated test:** `tests/contract/test_known_gaps.py::test_put_integration_documented_shape`
(TC-CONTRACT-02, `xfail(strict=True)`).

**Fix priority recommendation:** Fix spec or route before release — any spec-driven client
integration breaks immediately.

---

## BUG-09 — `PUT /integrations/{id}` silently no-ops

**Severity:** High (P1)
**Affected endpoint(s):** `PUT /integrations/{id}`

**Summary:** Calling the actual working route with a body matching the documented
`UpdateIntegrationRequest` schema exactly returns `200` with the integration object, but the
`name` field is unchanged — both in the response and on a follow-up `GET`. No error is surfaced;
the request looks successful but the update never persists. This makes update-by-name unusable
regardless of which route shape is called (distinct from BUG-03, which is about the shape itself).

**Steps to reproduce:**
```
curl -u test1:test123 -X POST http://localhost:8080/api/v1/integrations \
  -d '{"name":"fresh-before","type":"generic"}'
# -> {"id":"<id>","name":"fresh-before",...}

curl -u test1:test123 -X PUT http://localhost:8080/api/v1/integrations/<id> \
  -d '{"id":"<id>","name":"fresh-after"}'
# -> 200 {"id":"<id>","name":"fresh-before",...}   (unchanged, should be "fresh-after")

curl -u test1:test123 http://localhost:8080/api/v1/integrations/<id>
# -> {"id":"<id>","name":"fresh-before",...}       (confirms not persisted)
```

**Expected result:** `200` with `name` updated to `"fresh-after"`, persisted on follow-up `GET`.

**Actual result:** `200` returned, but `name` silently remains unchanged everywhere.

**Linked automated test:** `tests/functional/test_integrations.py::test_update_integration`
(TC-INT-03) — left red as a deliberate regression guard.

**Fix priority recommendation:** Fix before release — a core CRUD operation silently fails with no
error signal, which is worse than an outright failure for API consumers.

---

## BUG-10 — `POST /integrations` crashes on empty/missing `name`

**Severity:** High (P1)
**Affected endpoint(s):** `POST /integrations`

**Summary:** `POST /integrations` returns `500` when `name` is `""` or omitted entirely, regardless
of `type`. `type: null` with a non-empty `name` succeeds fine. `POST /assets` with an empty `name`
does not crash — this is isolated to the integrations create path. Found via schemathesis
property-based fuzzing during contract-test authoring.

**Steps to reproduce:**
```
curl -u test1:test123 -X POST http://localhost:8080/api/v1/integrations -d '{"type":"generic"}'
# -> 500 {"error":"internal server error"}

curl -u test1:test123 -X POST http://localhost:8080/api/v1/integrations \
  -d '{"name":"","type":"generic"}'
# -> 500 {"error":"internal server error"}
```

**Expected result:** `400` with a validation error for missing/empty required field `name`.

**Actual result:** `500 {"error":"internal server error"}`.

**Linked automated test:**
`tests/negative/test_malformed_input.py::test_create_integration_rejects_missing_name` (TC-NEG-09);
also surfaced by the schemathesis sweep in `tests/contract/test_schema_fuzzing.py::test_api_conformance`.

**Fix priority recommendation:** Fix before release — missing input validation causing a 500 on a
core create path.

---

## BUG-07 — No input validation on pagination params → 500

**Severity:** High (P1)
**Affected endpoint(s):** `GET /integrations`, `GET /assets`

**Summary:** Both list endpoints return `500` instead of `400` for out-of-domain `page`/`limit`
values: non-numeric `page`, `page=0`, negative `page`, and negative `limit` (the last only when at
least one record exists for the tenant — on an empty table it returns `200 null` with no crash,
indicating a slice/bounds panic on the actual result set rather than the raw parameter). Scope was
widened from the original non-numeric-only finding via schemathesis fuzzing. `limit=0` does not
crash (`200 []`). Unlike BUG-01, this does not deadlock subsequent writes.

**Steps to reproduce:**
```
curl -u test1:test123 'http://localhost:8080/api/v1/integrations?page=abc'   # -> 500
curl -u test1:test123 'http://localhost:8080/api/v1/integrations?page=0'     # -> 500
curl -u test1:test123 'http://localhost:8080/api/v1/integrations?page=-1'    # -> 500
curl -u test1:test123 'http://localhost:8080/api/v1/assets?integrationId=<id>&limit=-1'  # -> 500 (needs ≥1 existing asset)
```

**Expected result:** `400` with a validation error for out-of-domain pagination params.

**Actual result:** `500 {"error":"internal server error"}`.

**Linked automated test:**
`tests/negative/test_pagination_boundaries.py::test_integrations_reject_invalid_pagination` and
`::test_assets_reject_invalid_pagination` (TC-NEG-02..04); also caught by the schemathesis sweep.

**Fix priority recommendation:** Fix before release — missing input validation causing crashes on
a frequently-used read path.

---

## BUG-11 — `DELETE` on a non-existent resource reports fake success

**Severity:** Medium (P2)
**Affected endpoint(s):** `DELETE /integrations/{id}`, `DELETE /assets/{id}`

**Summary:** Both delete endpoints return their normal success response (`200`/`204`) even when
`{id}` was never created, is a well-formed-but-unknown UUID, or isn't a UUID at all. This is
inconsistent with `GET`, which correctly `404`s for the same non-existent ids. A client cannot
distinguish "deleted" from "never existed" from the response.

**Steps to reproduce:**
```
curl -u test1:test123 -X DELETE http://localhost:8080/api/v1/integrations/00000000-0000-0000-0000-000000000000
# -> 200 {"message":"integration deleted"}

curl -u test1:test123 -X DELETE http://localhost:8080/api/v1/assets/not-a-uuid
# -> 204

curl -u test1:test123 http://localhost:8080/api/v1/integrations/00000000-0000-0000-0000-000000000000
# -> 404 (GET correctly distinguishes non-existence)
```

**Expected result:** `404` when the target id doesn't exist, consistent with `GET`.

**Actual result:** `200`/`204` reported regardless of whether the resource ever existed.

**Linked automated test:**
`tests/negative/test_malformed_input.py::test_delete_nonexistent_integration_returns_404` and
`::test_delete_nonexistent_asset_returns_404` (TC-NEG-08).

**Fix priority recommendation:** Fix recommended, non-blocking — a correctness/consistency defect,
lower severity than the P0/P1 items.

---

## BUG-04 — Response code mismatches vs spec

**Severity:** Medium (P2)
**Affected endpoint(s):** `POST /assets`, `POST /integrations`

**Summary:** The spec documents `200` for `POST /assets` and `POST /integrations`; the actual
response is `201`. (Other status codes checked — `DELETE /integrations/{id}` at `200`, `DELETE
/assets/{id}` at `204` — match the spec correctly.)

**Steps to reproduce:**
```
curl -i -u test1:test123 -X POST http://localhost:8080/api/v1/integrations -d '{"name":"x","type":"y"}'
# -> HTTP/1.1 201 Created (spec says 200)
```

**Expected result:** `200`, per spec.

**Actual result:** `201`.

**Linked automated test:**
`tests/contract/test_known_gaps.py::test_post_integration_status_code_matches_spec` and
`::test_post_asset_status_code_matches_spec` (TC-CONTRACT-01a/01b, `xfail(strict=True)`).

**Fix priority recommendation:** Fix recommended, non-blocking — `201` is arguably more correct
REST practice than the spec's `200`; recommend updating the spec rather than the behavior.

---

## BUG-08 — Inconsistent empty-result shape (`null` vs `[]`)

**Severity:** Medium (P2)
**Affected endpoint(s):** `GET /integrations`

**Summary:** `GET /integrations` with an out-of-range positive `page` (e.g. `page=99`) returns
JSON `null` instead of an empty array; `GET /assets` returns `[]` correctly for the equivalent
case. Inconsistent empty-collection representation between the two list endpoints.

**Steps to reproduce:**
```
curl -u test1:test123 'http://localhost:8080/api/v1/integrations?page=99'
# -> null

curl -u test1:test123 'http://localhost:8080/api/v1/assets?integrationId=<id>&page=99'
# -> []
```

**Expected result:** `[]` for both endpoints on an out-of-range page.

**Actual result:** `/integrations` returns `null`; `/assets` returns `[]`.

**Linked automated test:**
`tests/negative/test_pagination_boundaries.py::test_integrations_out_of_range_page_returns_empty_list`
(TC-NEG-05).

**Fix priority recommendation:** Fix recommended, non-blocking — a client that doesn't
null-guard before iterating will throw; low severity but easy fix (return `[]` consistently).

---

## BUG-05 — Schema/type mismatch: asset id documented as `integer`

**Severity:** Low (P2)
**Affected endpoint(s):** `GET /assets/{id}`

**Summary:** The spec documents the `GET /assets/{id}` path parameter as `type: integer`, but real
asset ids are UUID strings. The spec doesn't reflect the actual data model.

**Steps to reproduce:**
```
curl -u test1:test123 http://localhost:8080/api/v1/assets/<real-uuid>
# -> 200, works fine with a string id despite spec typing it as integer
```

**Expected result:** Spec's `id` parameter type matches the actual data model (`string`/`uuid`).

**Actual result:** Spec says `integer`; actual ids are UUID strings.

**Linked automated test:** Caught by the schemathesis contract sweep
(`tests/contract/test_schema_fuzzing.py`), which fuzzes against the documented `integer` type.

**Fix priority recommendation:** Fix recommended, non-blocking — spec-accuracy issue only, no
runtime defect.

---

## BUG-13 — `DELETE /assets/{id}`'s 204 response wrongly declares a body schema

**Severity:** Low (P2)
**Affected endpoint(s):** `DELETE /assets/{id}`

**Summary:** The spec declares `"204": {"schema": {"type": "string"}}` for this operation's success
response. HTTP `204 No Content` must never carry a response body by definition, so declaring any
schema for it is a spec-authoring error. The runtime behavior is already correct — the actual
response body is empty, as it must be — only the spec is wrong. Found via schemathesis's
`response_schema_conformance` check, added to the contract fuzz sweep during Phase 3 hardening; it
flagged the correctly-empty body as a "JSON deserialization error" against the wrongly-declared
string schema. `DELETE /integrations/{id}`'s `200` response has no `schema` key at all and is
unaffected — this is isolated to the assets delete path.

**Steps to reproduce:**
```
curl -s http://localhost:8080/swagger/doc.json | jq '.paths["/assets/{id}"].delete.responses."204"'
# -> {"description":"asset deleted","schema":{"type":"string"}}   (should have no "schema" key)
```

**Expected result:** The spec's `204` response for `DELETE /assets/{id}` declares no body schema.

**Actual result:** Spec declares `{"schema":{"type":"string"}}` for a status code that must never
carry a body.

**Linked automated test:**
`tests/contract/test_known_gaps.py::test_delete_asset_204_has_no_body_schema` (TC-CONTRACT-04,
`xfail(strict=True)`); also caught by the schemathesis contract sweep in
`tests/contract/test_schema_fuzzing.py` prior to this specific-operation exclusion being added.

**Fix priority recommendation:** Fix recommended, non-blocking — spec-accuracy issue only, no
runtime defect; a client-generated SDK expecting a string body on `204` would be the only one
affected.

---

## BUG-06 — No security scheme declared in OpenAPI spec

**Severity:** Info
**Affected endpoint(s):** All `/api/v1/*` routes

**Summary:** The service requires HTTP Basic Auth on every `/api/v1/*` route (confirmed: missing
or bad credentials return `401`), but the OpenAPI spec has no `securityDefinitions`/`security`
block — the contract doesn't document authentication at all.

**Steps to reproduce:**
```
curl http://localhost:8080/swagger/doc.json | jq '.securityDefinitions, .security'
# -> null / absent

curl http://localhost:8080/api/v1/integrations
# -> 401 (auth is enforced despite not being documented)
```

**Expected result:** Spec declares a `securityDefinitions`/`security` block describing Basic Auth.

**Actual result:** No security scheme present in the spec.

**Linked automated test:**
`tests/contract/test_known_gaps.py::test_spec_declares_security_scheme` (TC-CONTRACT-03,
`xfail(strict=True)`).

**Fix priority recommendation:** Fix recommended, non-blocking — documentation-only gap; doesn't
affect runtime behavior but hurts spec-driven client/SDK generation.

---

## Summary table

| Bug | Severity | Priority | Automated |
|---|---|---|---|
| BUG-01 write-deadlock | Critical | P0 | ✅ `test_write_deadlock.py` (isolated marker) |
| BUG-02 tenant isolation | Critical | P0 | ✅ `test_tenant_isolation.py` (6 cases) |
| BUG-12 concurrent create crash | Critical | P0 | ✅ `loadtest/locustfile.py` |
| BUG-03 PUT route mismatch | High | P1 | ✅ `test_known_gaps.py` (xfail) |
| BUG-09 PUT silently no-ops | High | P1 | ✅ `test_integrations.py` |
| BUG-10 POST /integrations crash on empty name | High | P1 | ✅ `test_malformed_input.py` + schemathesis |
| BUG-07 pagination → 500 | High | P1 | ✅ `test_pagination_boundaries.py` + schemathesis |
| BUG-11 DELETE fake success | Medium | P2 | ✅ `test_malformed_input.py` |
| BUG-04 response code mismatch | Medium | P2 | ✅ `test_known_gaps.py` (xfail) |
| BUG-08 null vs [] | Medium | P2 | ✅ `test_pagination_boundaries.py` |
| BUG-05 id type mismatch | Low | P2 | ✅ schemathesis sweep |
| BUG-13 204 wrongly declares body schema | Low | P2 | ✅ `test_known_gaps.py` (xfail) + schemathesis sweep |
| BUG-06 no security scheme in spec | Info | P2 | ✅ `test_known_gaps.py` (xfail) |
