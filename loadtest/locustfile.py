import os
import random
import uuid

from locust import HttpUser, between, task

TENANTS = [
    (os.environ.get("TEST1_USER", "test1"), os.environ.get("TEST1_PASS", "test123")),
    (os.environ.get("TEST2_USER", "test2"), os.environ.get("TEST2_PASS", "test456")),
]


class ReadOnlyUser(HttpUser):
    """Read-only baseline load (TC-LOAD-01): GET /integrations and GET /assets only.

    Use this class (`make load-read`) to measure sustained throughput/latency against the
    assignment's >=1000 req/min target without tripping BUG-12: the integrations/assets stores
    are plain unsynchronized Go maps, and any concurrent GET (map iteration) racing a concurrent
    write (map insert) crashes the whole process with an unrecoverable `fatal error: concurrent
    map iteration and map write` (see docs/phase1_research.md). Concurrent reads alone are safe
    in Go -- only a read racing a write (or two writes) triggers it -- so this scenario isolates
    "can the service sustain read throughput" from "does the service survive concurrent writes".
    """

    wait_time = between(0.02, 0.1)

    def on_start(self):
        self.client.auth = random.choice(TENANTS)
        resp = self.client.post(
            "/integrations",
            json={"name": f"load-seed-{uuid.uuid4().hex[:8]}", "type": "generic"},
            name="/integrations [POST] (seed, one-off)",
        )
        self.integration_id = resp.json()["id"] if resp.status_code == 201 else None

    @task(2)
    def list_integrations(self):
        self.client.get("/integrations", name="/integrations [GET]")

    @task(2)
    def list_assets(self):
        if self.integration_id:
            self.client.get("/assets", params={"integrationId": self.integration_id}, name="/assets [GET]")


class ApiUser(HttpUser):
    """Mixed read/write load against /integrations and /assets (TC-LOAD-01/02).

    This scenario is *expected* to crash the service almost immediately -- that crash is
    itself the load-testing finding, see BUG-12 in docs/phase1_research.md: ordinary concurrent
    traffic (not malformed input) kills the whole process via an unsynchronized map access in
    the integrations store, well below the assignment's >=1000 req/min target. Run via
    `make load` to reproduce; use `make load-read` for a crash-free read-throughput baseline.

    Deliberately never sends PATCH /assets with an id that doesn't resolve to an asset --
    that exact shape is BUG-01 (global write deadlock, see docs/phase1_research.md): a single
    such request hangs every subsequent write for every tenant. BUG-01's effect under
    concurrency isn't separately re-tested (TC-LOAD-02 covers BUG-12 instead, which surfaces
    first): the deadlock is server-wide and triggered by one request, so concurrent load adds
    no new information over the isolated regression test in tests/negative/test_write_deadlock.py
    (TC-NEG-01, marker `deadlock`).
    """

    wait_time = between(0.05, 0.25)

    def on_start(self):
        self.client.auth = random.choice(TENANTS)
        self.integration_ids: list[str] = []
        self.asset_ids: list[str] = []
        self._create_integration()

    def _create_integration(self):
        resp = self.client.post(
            "/integrations",
            json={"name": f"load-{uuid.uuid4().hex[:8]}", "type": "generic"},
            name="/integrations [POST]",
        )
        if resp.status_code == 201:
            self.integration_ids.append(resp.json()["id"])

    def _create_asset(self):
        if not self.integration_ids:
            return
        integration_id = random.choice(self.integration_ids)
        resp = self.client.post(
            "/assets",
            json={
                "integration_id": integration_id,
                "name": f"load-asset-{uuid.uuid4().hex[:8]}",
                "description": "locust load test",
            },
            name="/assets [POST]",
        )
        if resp.status_code == 201:
            self.asset_ids.append(resp.json()["id"])

    @task(10)
    def list_integrations(self):
        self.client.get("/integrations", name="/integrations [GET]")

    @task(10)
    def list_assets(self):
        if not self.integration_ids:
            return
        integration_id = random.choice(self.integration_ids)
        self.client.get("/assets", params={"integrationId": integration_id}, name="/assets [GET]")

    @task(3)
    def create_integration(self):
        self._create_integration()

    @task(3)
    def create_asset(self):
        self._create_asset()

    @task(2)
    def update_asset(self):
        if not self.asset_ids:
            return
        asset_id = random.choice(self.asset_ids)
        self.client.patch(
            "/assets",
            json={"id": asset_id, "name": f"load-updated-{uuid.uuid4().hex[:8]}"},
            name="/assets [PATCH]",
        )

    @task(1)
    def delete_asset(self):
        if not self.asset_ids:
            return
        asset_id = self.asset_ids.pop()
        self.client.delete(f"/assets/{asset_id}", name="/assets/[id] [DELETE]")
