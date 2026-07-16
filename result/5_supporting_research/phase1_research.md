# Phase 1 — Research: QA Test API

Service: `infralightio/test-integration-api`, Gin (Go), SQLite/in-memory-like state, port 8080.
OpenAPI (Swagger 2.0) at `/swagger/doc.json`. Auth: HTTP Basic. Base path `/api/v1`.

## Resources & endpoints (as documented)

**Integrations**
- `GET /integrations?page&limit` — list
- `POST /integrations` — create (`name`, `type`)
- `GET /integrations/{id}` — get by id
- `PUT /integrations` — update (spec: id in body) ⚠️ see BUG-03
- `DELETE /integrations/{id}` — delete

**Assets**
- `GET /assets?integrationId&page&limit` — list (integrationId required)
- `POST /assets` — create (`integration_id`, `name`, `description`)
- `GET /assets/{id}` — get by id (spec types `id` as `integer`, actual ids are UUID strings) ⚠️ see BUG-05
- `PATCH /assets` — update (id in body)
- `DELETE /assets/{id}` — delete

Both resources carry `tenant_id`, set server-side from Basic Auth identity — not client-settable on create.

## Confirmed bugs

**BUG-01 (Critical) — Global write deadlock after malformed PATCH /assets**
Sending `PATCH /assets` with an id that doesn't resolve to an asset (e.g. an integration id) returns `500 {"error":"internal server error"}`. After this, **every** write operation (POST/PATCH/DELETE) on the entire service hangs indefinitely for every tenant — reads (GET) keep working. Service-wide DoS from a single bad request; only recovers on container restart.
Repro:
```
curl -u test1:test123 -X PATCH /api/v1/assets -d '{"id":"<non-asset-id>","name":"x"}'   # -> 500
curl -u test1:test123 -X POST /api/v1/integrations -d '{"name":"x","type":"y"}'          # hangs forever
```

**BUG-02 (Critical) — Broken tenant segregation**
- `GET /integrations` returns **all tenants'** integrations, not just the caller's (list is unfiltered).
- `GET /integrations/{id}`, `GET /assets/{id}` let any authenticated tenant read another tenant's resource directly by id.
- `DELETE /assets/{id}` lets any authenticated tenant delete another tenant's asset.
- `DELETE /integrations/{id}` lets any authenticated tenant delete another tenant's integration (test2 deleted test1's integration, `200 {"message":"integration deleted"}`, confirmed gone from test1's view afterward).
- `POST /assets` lets a tenant create an asset under another tenant's `integration_id` (creates fine, tenant_id set to caller — orphaned/cross-tenant linkage).
Only `GET /assets?integrationId=` (list) was correctly tenant-filtered in testing.

**BUG-03 (High) — Contract mismatch: PUT /integrations route**
Swagger documents `PUT /integrations` (no path id, id in body). Actual registered route (confirmed via Gin route table) is `PUT /integrations/{id}`. Calling the documented shape returns `404`; the endpoint is unusable as specified.

**BUG-04 (Medium) — Response code mismatches vs spec**
Spec says `POST /assets` and `POST /integrations` return `200`; actual is `201`. Spec says `DELETE /integrations/{id}` returns `200` — retested post-BUG-01-fix concerns, confirmed actual matches (`200 {"message":"integration deleted"}`). Spec has `DELETE /assets/{id}` at `204` — actual matches.

**BUG-05 (Low) — Schema/type mismatch**
`GET /assets/{id}` path param documented as `type: integer`, but real ids are UUID strings — spec doesn't reflect actual data model.

**BUG-06 (Info) — No security scheme in OpenAPI spec**
Service requires Basic Auth on all `/api/v1/*` routes (confirmed: no creds / bad creds → 401), but the spec has no `securityDefinitions`/`security` block — contract doesn't document auth at all.

**BUG-07 (Medium) — No input validation on pagination params → 500 (revised, 2026-07-16: scope widened by schemathesis property-based fuzzing)**
`GET /integrations` and `GET /assets` return `500 {"error":"internal server error"}` instead of `400` for out-of-domain `page`/`limit`, confirmed for all of:
- non-numeric `page` (original finding)
- `page=0` (boundary value, both endpoints) — minimal repro: `curl -u test1:test123 '/api/v1/integrations?page=0'`
- negative `page` (e.g. `page=-1`, both endpoints) — supersedes the "silently accepted" claim previously recorded under BUG-08, which was incorrect
- negative `limit` (e.g. `limit=-1`, both endpoints) — **only when at least one record exists for the tenant**; on an empty table `limit=-1` returns `200 null` with no crash. The 500 is a slice/bounds panic on the actual result set, not on the raw parameter.
`limit=0` does not crash (`200 []`). Unlike BUG-01, this does **not** deadlock subsequent writes (verified: POST still works right after) — isolated to the pagination code path.

**BUG-08 (Low) — Inconsistent empty-result shape**
`GET /integrations` with an out-of-range positive `page` (e.g. `page=99`) returns JSON `null` instead of `[]`; `GET /assets` returns `[]` for the equivalent case.

**BUG-10 (High) — `POST /integrations` crashes on empty/missing `name` (found during Phase 3 contract test authoring via schemathesis, 2026-07-16)**
`POST /integrations` returns `500 {"error":"internal server error"}` when `name` is `""` or omitted entirely, regardless of `type`. `type: null` with a non-empty `name` succeeds fine (`type` just ends up `""` in the response) — the crash is specifically triggered by the empty/missing `name`, not `type`. `POST /assets` with an empty `name` does **not** crash (`201`, empty name accepted) — this is isolated to the integrations create path.
Repro:
```
curl -u test1:test123 -X POST /api/v1/integrations -d '{"type":"generic"}'          # -> 500
curl -u test1:test123 -X POST /api/v1/integrations -d '{"name":"","type":"generic"}' # -> 500
curl -u test1:test123 -X POST /api/v1/integrations -d '{"name":"x","type":null}'     # -> 201, fine
```

**BUG-09 (High) — `PUT /integrations/{id}` silently no-ops (found during Phase 3 functional test authoring, 2026-07-16)**
Calling the actual registered route (`PUT /integrations/{id}`, id in path) with a body matching the documented `UpdateIntegrationRequest` schema exactly (`{"id": "<id>", "name": "<new-name>"}`) returns `200` with the integration object, but the `name` is unchanged — both in the response and on a follow-up `GET`. No error is surfaced; the request looks successful but the update never persists. Distinct from BUG-03 (route-shape mismatch): this is on the *working* route, so update-by-name is effectively unusable regardless of which shape is called.
Repro:
```
curl -u test1:test123 -X POST /api/v1/integrations -d '{"name":"fresh-before","type":"generic"}'
# -> {"id":"<id>","name":"fresh-before",...}
curl -u test1:test123 -X PUT /api/v1/integrations/<id> -d '{"id":"<id>","name":"fresh-after"}'
# -> 200 {"id":"<id>","name":"fresh-before",...}   <- unchanged, should be "fresh-after"
curl -u test1:test123 /api/v1/integrations/<id>
# -> {"id":"<id>","name":"fresh-before",...}       <- confirmed not persisted
```

**BUG-11 (Medium) — `DELETE` on a non-existent resource reports fake success (found during Phase 3 negative test authoring, 2026-07-16)**
`DELETE /integrations/{id}` and `DELETE /assets/{id}` return their normal success response (`200 {"message":"integration deleted"}` / `204`) even when `{id}` was never created, is a well-formed-but-unknown UUID, or isn't a UUID at all. Inconsistent with `GET`, which correctly 404s (`{"error":"integration not found"}` / `{"error":"asset not found"}`) for the same non-existent ids. A client cannot distinguish "deleted" from "never existed" from the response.
Repro:
```
curl -u test1:test123 -X DELETE /api/v1/integrations/00000000-0000-0000-0000-000000000000  # -> 200 {"message":"integration deleted"}
curl -u test1:test123 -X DELETE /api/v1/assets/not-a-uuid                                    # -> 204
curl -u test1:test123    /api/v1/integrations/00000000-0000-0000-0000-000000000000          # -> 404 (GET correctly distinguishes)
```

**BUG-12 (Critical) — Concurrent `POST /integrations` crashes the entire process (found during Phase 3 load testing via locust, 2026-07-16)**
Under ordinary concurrent load (~20 simulated users, mixed reads/writes, well under the ~1000 req/min target), the service died with an unrecoverable Go `fatal error: concurrent map iteration and map write` inside `controller.(*Controller).CreateIntegration` (`/app/controller/integrations.go:35`) and the container exited (exit code 2). This is a `fatal error`, not a panic — Gin's recovery middleware (which handles BUG-07/BUG-10's panics and turns them into `500`s) **cannot catch it**; the whole process terminates immediately, taking down every in-flight request and requiring a container restart. Root cause: the integrations store is a plain Go `map` read (iterated, e.g. by `GET /integrations`'s list-building) and written (`POST /integrations`'s insert) without a mutex/lock — concurrent access panics by design in the Go runtime rather than silently corrupting memory. This directly contradicts the assignment's explicit requirement that "the service must handle a load of at least 1000 requests per minute": it cannot survive concurrent creates at all, let alone at that throughput. The assets store likely has the same unsynchronized-map pattern (same codebase, same author) but this was only confirmed for integrations in this run — flagged as a likely, unconfirmed risk for `POST /assets` too.
Repro: run any concurrent mix of `GET /integrations` and `POST /integrations` (e.g. `make load`, see `loadtest/locustfile.py`) — a handful of concurrent users is enough to hit the race window within seconds.

**BUG-13 (Low) — Spec declares a response body schema for a 204 No Content (found during Phase 3 contract-test hardening via schemathesis, 2026-07-16)**
The spec's `DELETE /assets/{id}` operation declares `"204": {"schema": {"type": "string"}}`. HTTP `204 No Content` must never carry a response body by definition, so declaring any schema for it is a spec-authoring error — confirmed via schemathesis's `response_schema_conformance` check, which flags the actual (correctly empty) body as a "JSON deserialization error" against the wrongly-declared string schema. The runtime behavior is correct (body is empty, as it must be); only the spec is wrong. `DELETE /integrations/{id}`'s `200` response has no `schema` key at all and is unaffected.
Repro:
```
curl -s http://localhost:8080/swagger/doc.json | jq '.paths["/assets/{id}"].delete.responses."204"'
# -> {"description":"asset deleted","schema":{"type":"string"}}   <- should have no "schema" key
```

## Verified as working correctly
- `GET /assets` without required `integrationId` → `400 {"error":"integrationId is required"}` — correct.
- `GET /assets?integrationId=<non-existent>` → `200 []` — correct, no crash.
- No creds / bad creds on any `/api/v1/*` route → `401` — correct.
- Malformed JSON body on `POST /integrations` → `400` with a parser error message — correct.
- `GET /integrations/{id}` / `GET /assets/{id}` with a non-UUID or unknown id → `404` — correct (contrast with BUG-11 on `DELETE`).
- Injection-style strings (`'; DROP TABLE...`, `<script>...`) in `name`/`type` on create → stored/escaped safely, `201`, no crash, service stays healthy afterward — correct.
- `limit=0` on either list endpoint → `200 []`, no crash — correct (contrast with `page=0`, BUG-07).
- A `500` from bad pagination params does not cascade into the global write-deadlock (only the specific PATCH /assets malformed-id path does, per BUG-01).

## Remaining for Phase 2/3
- Rate limit / load behavior at 1000 req/min (bonus, needs a load tool — Phase 3)
- Full schemathesis-driven fuzz of all params/bodies against the spec
- Precise root-cause isolation of BUG-01 trigger condition (which malformed id shapes trigger it vs. don't) — enough is confirmed to write a regression test; deeper root-cause is optional
