"""Admin backup API contract tests — BACKUP-01/02 (§9, §12, §14, §16).

In-memory only: no database, no object store, no network. The job queue is a
scripted double and the destination is an in-process store, so what these tests
assert is the API's own contract:

* **capability gate** — admin authority alone is not enough; the explicit
  ``can_manage_backups`` capability is required, and a missing one is a 403;
* **confirmation** — a create request without the explicit confirm flag is
  refused, so a stray request cannot start a production dump;
* **queue-only writes** — ``POST`` records queued rows and does no export work;
* **explicit retention ownership** — a policy update routes retention through the
  existing retention setting rather than duplicating the value;
* **honest access control on the invariants** — "turn off encryption" is refused
  with the invariant's own reason instead of being silently ignored;
* **ciphertext-only download** — the download returns exactly the stored bytes
  and is marked ``no-store``;
* **audit + idempotent notification** — every state-changing action is audited
  and a failed verification notifies the requester exactly once.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone

import pytest

from api import v3_backups
from backup.jobs import (
    KIND_DATABASE,
    KIND_OBJECTS,
    STATUS_COMPLETED,
    STATUS_QUEUED,
    VERIFICATION_UNVERIFIED,
    BackupJob,
)
from backup.storage import InMemoryObjectStore
from backup.verification import ArtifactVerification

from tests.unit.api.fakes import (
    backup_admin_user,
    backup_admin_without_capability,
    member_user,
)

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
SET_ID = "aaaaaaaa-1111-2222-3333-444444444444"
DB_JOB_ID = "11111111-1111-1111-1111-111111111111"
OBJ_JOB_ID = "22222222-2222-2222-2222-222222222222"
STORAGE_KEY = "backups/2026/10/01/db.ctbak"
ENVELOPE = b"CTB1-ciphertext-bytes-that-must-round-trip"


def _job(
    job_id: str = DB_JOB_ID,
    *,
    status: str = STATUS_QUEUED,
    kind: str = KIND_DATABASE,
    storage_key: str | None = None,
    verification_status: str = VERIFICATION_UNVERIFIED,
    backup_set_id: str | None = None,
) -> BackupJob:
    return BackupJob(
        id=job_id,
        status=status,
        scope="public+schema+roles",
        requested_by="staff-1",
        requested_at=NOW,
        kind=kind,
        storage_key=storage_key,
        backup_set_id=backup_set_id,
        verification_status=verification_status,
    )


class FakeJobStore:
    """Scripted ``BackupJobStore``: records what the API asked for.

    Deliberately dumb — it stores rows and answers reads. The single-flight,
    claim and stale-lock guarantees are the *database's* (asserted in
    ``tests/unit/backup/test_jobs.py``); here the double only has to be honest
    about what the request path did with them.
    """

    def __init__(self) -> None:
        self.jobs: dict[str, BackupJob] = {}
        self.created: list[dict] = []
        self.verified: list[tuple[str, bool, str | None]] = []
        self._seq = 0

    async def get(self, job_id: str):
        return self.jobs.get(job_id)

    async def list_recent(self, *, limit: int = 50, offset: int = 0):
        rows = sorted(
            self.jobs.values(), key=lambda j: (j.requested_at or NOW), reverse=True
        )
        return rows[offset : offset + limit]

    async def get_active(self, *, kind=None):
        return next(
            (j for j in self.jobs.values() if j.status in (STATUS_QUEUED, "running")),
            None,
        )

    async def create_queued_job(
        self, *, requested_by, scope="public+schema+roles", idempotency_key=None,
        release_commit=None, kind=KIND_DATABASE, backup_set_id=None,
    ):
        if idempotency_key is not None:
            for record in self.created:
                if record["idempotency_key"] == idempotency_key:
                    return self.jobs[record["id"]], False
        self._seq += 1
        job_id = DB_JOB_ID if self._seq == 1 else OBJ_JOB_ID
        job = _job(job_id, kind=kind, backup_set_id=backup_set_id)
        self.jobs[job_id] = job
        self.created.append(
            {"id": job_id, "idempotency_key": idempotency_key, "kind": kind}
        )
        return job, True

    async def attach_backup_set(self, job_id: str, backup_set_id: str):
        job = _job(
            job_id,
            status=self.jobs[job_id].status,
            kind=self.jobs[job_id].kind,
            backup_set_id=backup_set_id,
        )
        self.jobs[job_id] = job
        return job

    async def mark_verified(self, job_id: str, *, verified: bool, error_reason=None):
        current = self.jobs[job_id]
        self.verified.append((job_id, verified, error_reason))
        updated = _job(
            job_id,
            status=current.status,
            kind=current.kind,
            storage_key=current.storage_key,
            verification_status="verified" if verified else "failed",
            backup_set_id=current.backup_set_id,
        )
        self.jobs[job_id] = updated
        return updated

    async def list_by_backup_set(self, backup_set_id: str):
        return [j for j in self.jobs.values() if j.backup_set_id == backup_set_id]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _backup_env(monkeypatch):
    """A configured backup destination (§9): an encryption key and a store."""
    monkeypatch.setenv("CT_BACKUP_ENCRYPTION_KEY", base64.b64encode(b"0" * 32).decode())
    monkeypatch.setenv("CT_BACKUP_KEY_ID", "unit-key-v1")
    monkeypatch.setenv("CT_BACKUP_OBJECT_STORE", "memory")


@pytest.fixture
def job_store() -> FakeJobStore:
    return FakeJobStore()


@pytest.fixture
def backup_app(app, job_store):
    """The composition root with the queue store replaced by the scripted double."""
    app.dependency_overrides[v3_backups._job_store] = lambda: job_store
    return app


@pytest.fixture
def backup_client(backup_app):
    from starlette.testclient import TestClient

    with TestClient(backup_app, raise_server_exceptions=True) as test_client:
        yield test_client


@pytest.fixture
def stored_artifact(backup_app, monkeypatch):
    """Point the API's destination at a store holding one encrypted artifact."""

    class _StaticStore(InMemoryObjectStore):
        async def get_object(self, key: str) -> bytes:
            if key == STORAGE_KEY:
                return ENVELOPE
            return await super().get_object(key)

    store = _StaticStore()
    monkeypatch.setattr(v3_backups, "_object_store", lambda settings: store)
    return store


def _actions(world) -> list[str]:
    return [entry.action for entry in world.audit._entries]


# ---------------------------------------------------------------------------
# Authorization — admin authority AND the capability (§9)
# ---------------------------------------------------------------------------


def test_an_admin_without_the_capability_is_refused(backup_client, user_provider) -> None:
    user_provider.set_user(backup_admin_without_capability())

    assert backup_client.get("/api/v3/admin/backups/status").status_code == 403
    assert backup_client.get("/api/v3/admin/backups").status_code == 403
    assert (
        backup_client.post("/api/v3/admin/backups", json={"confirm": True}).status_code
        == 403
    )


def test_an_ordinary_user_never_reaches_the_backup_surface(
    backup_client, user_provider
) -> None:
    user_provider.set_user(member_user("org-a", "user-1", "u@carbontally.test"))

    assert backup_client.get("/api/v3/admin/backups").status_code == 403


# ---------------------------------------------------------------------------
# Status and history — non-secret metadata only
# ---------------------------------------------------------------------------


def test_status_reports_policy_destination_and_counts(
    backup_client, user_provider, job_store
) -> None:
    user_provider.set_user(backup_admin_user())
    job_store.jobs[DB_JOB_ID] = _job(
        status=STATUS_COMPLETED, storage_key=STORAGE_KEY, verification_status="verified"
    )
    job_store.jobs[OBJ_JOB_ID] = _job(
        OBJ_JOB_ID,
        status=STATUS_COMPLETED,
        kind=KIND_OBJECTS,
        storage_key="backups/2026/10/01/objects.ctbak",
    )

    payload = backup_client.get("/api/v3/admin/backups/status").json()["status"]

    assert payload["enabled"] is True
    assert payload["destination"]["provider"] == "memory"
    assert payload["destination"]["encryption_key_configured"] is True
    assert payload["counts"] == {
        "completed": 2,
        "failed": 0,
        "verified": 1,
        "unverified_completed": 1,
    }
    # Nothing was decided about retention yet — and that is what is reported.
    assert payload["retention"] == {"days": None, "explicitly_configured": False}
    assert payload["scheduling"]["automation"].startswith("not implemented")


def test_history_is_bounded_and_never_returns_a_lock_token(
    backup_client, user_provider, job_store
) -> None:
    user_provider.set_user(backup_admin_user())
    job_store.jobs[DB_JOB_ID] = _job(status=STATUS_COMPLETED, storage_key=STORAGE_KEY)

    payload = backup_client.get("/api/v3/admin/backups?limit=9999").json()

    assert payload["limit"] == v3_backups.MAX_PAGE
    assert payload["backups"][0]["id"] == DB_JOB_ID
    assert "lock_token" not in payload["backups"][0]
    assert "locked_at" not in payload["backups"][0]


# ---------------------------------------------------------------------------
# Create — confirmation, queue-only, idempotency, policy gate (§9, §11)
# ---------------------------------------------------------------------------


def test_create_without_explicit_confirmation_is_refused(
    backup_client, user_provider, job_store
) -> None:
    user_provider.set_user(backup_admin_user())

    response = backup_client.post("/api/v3/admin/backups", json={})

    assert response.status_code == 400
    assert "confirm" in response.json()["error"]["message"]
    assert job_store.created == [], "a refused request must not queue anything"


def test_create_queues_a_database_job_and_its_paired_object_job(
    backup_client, user_provider, job_store, world
) -> None:
    user_provider.set_user(backup_admin_user())

    response = backup_client.post(
        "/api/v3/admin/backups",
        json={"confirm": True},
        headers={"Idempotency-Key": "k-1"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["created"] is True
    assert body["job"]["kind"] == KIND_DATABASE
    assert body["object_job"]["kind"] == KIND_OBJECTS
    assert body["backup_set_id"]
    assert [record["kind"] for record in job_store.created] == [
        KIND_DATABASE,
        KIND_OBJECTS,
    ]
    assert "backup.requested" in _actions(world)


def test_a_replayed_create_resolves_to_the_existing_job(
    backup_client, user_provider, job_store, world
) -> None:
    user_provider.set_user(backup_admin_user())
    headers = {"Idempotency-Key": "k-1"}

    first = backup_client.post(
        "/api/v3/admin/backups", json={"confirm": True}, headers=headers
    )
    second = backup_client.post(
        "/api/v3/admin/backups", json={"confirm": True}, headers=headers
    )

    assert second.status_code == 201
    assert second.json()["created"] is False
    assert second.json()["job"]["id"] == first.json()["job"]["id"]
    assert _actions(world).count("backup.requested") == 1, (
        "a replayed request must not write a second audit entry"
    )


def test_create_is_refused_when_the_policy_disables_backups(
    backup_client, user_provider, job_store
) -> None:
    user_provider.set_user(backup_admin_user())
    assert (
        backup_client.put(
            "/api/v3/admin/backups/policy", json={"enabled": False}
        ).status_code
        == 200
    )

    response = backup_client.post("/api/v3/admin/backups", json={"confirm": True})

    assert response.status_code == 409
    assert job_store.created == []


# ---------------------------------------------------------------------------
# Pair — the consistent restore pair (§14)
# ---------------------------------------------------------------------------


def test_pair_reports_both_halves_of_the_backup_set(
    backup_client, user_provider, job_store
) -> None:
    user_provider.set_user(backup_admin_user())
    job_store.jobs[DB_JOB_ID] = _job(
        status=STATUS_COMPLETED, storage_key=STORAGE_KEY, backup_set_id=SET_ID
    )
    job_store.jobs[OBJ_JOB_ID] = _job(
        OBJ_JOB_ID,
        status=STATUS_COMPLETED,
        kind=KIND_OBJECTS,
        storage_key="backups/2026/10/01/objects.ctbak",
        backup_set_id=SET_ID,
    )

    payload = backup_client.get(f"/api/v3/admin/backups/{DB_JOB_ID}/pair").json()

    assert payload["backup_set_id"] == SET_ID
    assert payload["pair_complete"] is True
    assert payload["database"]["id"] == DB_JOB_ID
    assert payload["objects"]["id"] == OBJ_JOB_ID


# ---------------------------------------------------------------------------
# Verify — the recorded outcome (§12)
# ---------------------------------------------------------------------------


def test_verify_records_a_successful_outcome_and_audits(
    backup_client, user_provider, job_store, world, stored_artifact, monkeypatch
) -> None:
    user_provider.set_user(backup_admin_user())
    job_store.jobs[DB_JOB_ID] = _job(status=STATUS_COMPLETED, storage_key=STORAGE_KEY)

    async def _verified(store, object_key, key, **kwargs):
        return ArtifactVerification(
            object_key=object_key,
            verified=True,
            member_count=4,
            content_checksums_verified=4,
        )

    monkeypatch.setattr(v3_backups, "verify_stored_artifact", _verified)

    response = backup_client.post(f"/api/v3/admin/backups/{DB_JOB_ID}/verify")

    assert response.status_code == 200
    assert response.json()["verification"]["verified"] is True
    assert job_store.verified == [(DB_JOB_ID, True, None)]
    assert "backup.verified" in _actions(world)


def test_a_failed_verification_notifies_the_requester_once(
    backup_client, user_provider, job_store, world, stored_artifact, monkeypatch
) -> None:
    user_provider.set_user(backup_admin_user())
    job_store.jobs[DB_JOB_ID] = _job(status=STATUS_COMPLETED, storage_key=STORAGE_KEY)

    async def _failed(store, object_key, key, **kwargs):
        return ArtifactVerification(
            object_key=object_key,
            verified=False,
            problems=("ciphertext digest differs",),
        )

    monkeypatch.setattr(v3_backups, "verify_stored_artifact", _failed)

    response = backup_client.post(f"/api/v3/admin/backups/{DB_JOB_ID}/verify")

    assert response.status_code == 200
    assert job_store.verified[0][1] is False
    assert "ciphertext digest differs" in (job_store.verified[0][2] or "")

    rows = world.notifications.rows
    assert len(rows) == 1
    assert rows[0]["event_key"] == f"backup:{DB_JOB_ID}:verification_failed"
    assert rows[0]["priority"] == 2


def test_verify_a_queued_job_is_a_conflict(
    backup_client, user_provider, job_store
) -> None:
    user_provider.set_user(backup_admin_user())
    job_store.jobs[DB_JOB_ID] = _job(status=STATUS_QUEUED)

    response = backup_client.post(f"/api/v3/admin/backups/{DB_JOB_ID}/verify")

    assert response.status_code == 409
    assert job_store.verified == []


# ---------------------------------------------------------------------------
# Download — the encrypted artifact, never a public URL (§9)
# ---------------------------------------------------------------------------


def test_download_returns_the_stored_ciphertext_with_no_store(
    backup_client, user_provider, job_store, world, stored_artifact
) -> None:
    user_provider.set_user(backup_admin_user())
    job_store.jobs[DB_JOB_ID] = _job(status=STATUS_COMPLETED, storage_key=STORAGE_KEY)

    response = backup_client.get(f"/api/v3/admin/backups/{DB_JOB_ID}/download")

    assert response.status_code == 200
    assert response.content == ENVELOPE
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-type"] == "application/octet-stream"
    assert (
        f"carbontally-database-{DB_JOB_ID}.tar.gz.enc"
        in response.headers["content-disposition"]
    )
    assert "backup.downloaded" in _actions(world)


def test_download_of_a_job_without_an_artifact_is_a_conflict(
    backup_client, user_provider, job_store, stored_artifact
) -> None:
    user_provider.set_user(backup_admin_user())
    job_store.jobs[DB_JOB_ID] = _job(status=STATUS_QUEUED)

    assert (
        backup_client.get(
            f"/api/v3/admin/backups/{DB_JOB_ID}/download"
        ).status_code
        == 409
    )


# ---------------------------------------------------------------------------
# Policy — one home for retention, no switch for the invariants (§16)
# ---------------------------------------------------------------------------


def test_policy_update_rejects_a_non_configurable_property(
    backup_client, user_provider, world
) -> None:
    user_provider.set_user(backup_admin_user())

    response = backup_client.put(
        "/api/v3/admin/backups/policy", json={"encryption": "off"}
    )

    assert response.status_code == 400
    assert "not configurable" in response.json()["error"]["message"]
    assert _actions(world).count("backup.policy_updated") == 0


def test_policy_update_writes_retention_through_the_retention_setting(
    backup_client, user_provider, world
) -> None:
    user_provider.set_user(backup_admin_user())

    response = backup_client.put(
        "/api/v3/admin/backups/policy",
        json={"enabled": True, "retention_days": 30, "frequency": "weekly"},
    )

    assert response.status_code == 200
    assert response.json()["retention_days"] == 30
    assert world.settings._values["backup_retention_days"] == 30, (
        "retention has exactly one home (the backup_retention_days setting)"
    )
    assert "retention_days" not in world.settings._backup_policy, (
        "the policy row must never duplicate the retention value"
    )
    assert "backup.policy_updated" in _actions(world)


def test_policy_get_lists_the_configurable_and_the_invariant_fields(
    backup_client, user_provider
) -> None:
    user_provider.set_user(backup_admin_user())

    payload = backup_client.get("/api/v3/admin/backups/policy").json()

    assert "retention_days" in payload["configurable_fields"]
    assert "encryption" in payload["not_configurable"]
    assert payload["policy"]["mandatory_invariants"]

