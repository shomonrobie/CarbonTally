"""Unit tests for :mod:`backup.jobs` — the durable job model (BACKUP-01 §10/§11).

No database and no live service is involved: a *scripted* asyncpg double stands
in for the connection, so the guarantees are asserted where they actually live —
on the statement the store issues and the row it persists:

* **single-flight** — the insert's ``ON CONFLICT DO NOTHING`` must stay bare, so
  *either* unique index (the active-slot index and the idempotency key) resolves
  a duplicate request to the existing job instead of raising;
* **claim** — ``FOR UPDATE SKIP LOCKED``, the ``attempt_count`` guard and the
  stale-lock reclaim are one statement, and the attempt is consumed *at claim
  time* (a crash after the claim still costs an attempt);
* **bounded transitions** — the terminal updates are guarded on
  ``status = 'running'`` (or the deletable set), so a duplicated worker cannot
  overwrite a terminal row;
* **ciphertext-only** — only key *identity*, byte count and checksums are ever
  persisted; no plaintext, no archive body, no key material;
* **failure absorption** — :func:`run_claimed_job` records an export failure on
  the row instead of propagating, while an impossible transition still raises.
"""
from __future__ import annotations

import json
import pathlib
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

import pytest

from backup.artifact import BACKUP_FORMAT_VERSION, EXPORTER_VERSION
from backup.errors import BackupExportError, BackupJobConflictError, BackupJobError
from backup.jobs import (
    ACTIVE_STATUSES,
    ALLOWED_SCOPES,
    ALL_STATUSES,
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_STALE_LOCK_SECONDS,
    KIND_DATABASE,
    MAX_ERROR_REASON_LENGTH,
    SCOPE_FULL,
    STATUS_COMPLETED,
    STATUS_DELETED,
    STATUS_EXPIRED,
    STATUS_FAILED,
    STATUS_QUEUED,
    STATUS_RUNNING,
    VERIFICATION_UNVERIFIED,
    BackupJob,
    BackupJobStore,
    _COLUMNS,
    _affected_rows,
    _row_to_job,
    run_claimed_job,
    run_next_job,
    sanitise_reason,
)
from backup.service import BackupRecord

# ---------------------------------------------------------------------------
# Fixtures and the scripted connection double
# ---------------------------------------------------------------------------
JOB_ID = "11111111-2222-3333-4444-555555555555"
OTHER_JOB_ID = "99999999-8888-7777-6666-555555555555"
#: The acting staff user. ``requested_by``/``deleted_by`` are ``UUID`` columns
#: referencing ``public.users``, so the fixture uses a real UUID string.
REQUESTER = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
LATER = NOW + timedelta(hours=1)

ARCHIVE_SHA256 = "a" * 64
CIPHERTEXT_SHA256 = "b" * 64

#: Stands in for key material: it must never reach a persisted parameter.
KEY_MATERIAL_CANARY = "do-not-persist-this-256-bit-key-material"

RECORD = BackupRecord(
    backup_id="3f2b1c0d9e",
    object_key="backups/3f2b1c0d9e.ctbak",
    created_at="2026-10-01T12:00:00Z",
    format_version=BACKUP_FORMAT_VERSION,
    exporter_version=EXPORTER_VERSION,
    archive_sha256=ARCHIVE_SHA256,
    ciphertext_sha256=CIPHERTEXT_SHA256,
    size_bytes=4096,
    table_count=4,
    total_rows=2,
    key_id="unit-key-v1",
    compression="gzip",
)


def _row(**overrides: Any) -> dict[str, Any]:
    """A ``backup_jobs`` row as asyncpg would return it (migration defaults)."""
    row: dict[str, Any] = {
        "id": JOB_ID,
        "status": STATUS_QUEUED,
        "scope": SCOPE_FULL,
        "requested_by": REQUESTER,
        "requested_at": NOW,
        "started_at": None,
        "finished_at": None,
        "attempt_count": 0,
        "lock_token": None,
        "locked_at": None,
        "storage_key": None,
        "storage_bucket": None,
        "artifact_bytes": None,
        "checksum_sha256": None,
        "key_version": None,
        "manifest": None,
        "release_commit": None,
        "error_reason": None,
        "expires_at": None,
        "deleted_at": None,
        "deleted_by": None,
        "idempotency_key": None,
        # BACKUP-02 (§14/§12) — the paired-artifact and verification columns that
        # migration 20261027000000 adds. A row returned by asyncpg always carries
        # them, so the double must too (their defaults are the migration's).
        "kind": KIND_DATABASE,
        "backup_set_id": None,
        "object_count": None,
        "object_bytes": None,
        "verification_status": VERIFICATION_UNVERIFIED,
        "verification_checked_at": None,
        "verification_error": None,
    }
    row.update(overrides)
    return row


class FakeConnection:
    """Scripted asyncpg double: one queued result per awaited call.

    Each ``*_results`` list is a FIFO; exhausting it yields the empty result for
    that method (``None`` / ``[]`` / ``"UPDATE 0"``), which is exactly the shape
    most tests want for their final assertion.
    """

    def __init__(self) -> None:
        self.fetchrow_results: list[Any] = []
        self.fetch_results: list[Any] = []
        self.execute_results: list[Any] = []
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def _record(self, query: str, args: tuple[Any, ...]) -> None:
        self.calls.append((query, args))

    @property
    def flat_queries(self) -> list[str]:
        """Whitespace-collapsed statements, for readable containment checks."""
        return [" ".join(query.split()) for query, _ in self.calls]

    @property
    def flat_query(self) -> str:
        """The (single) statement under test, whitespace-collapsed."""
        assert len(self.calls) == 1, f"expected one statement, got {len(self.calls)}"
        return self.flat_queries[0]

    @property
    def args(self) -> tuple[Any, ...]:
        """The parameters of the (single) statement under test."""
        assert len(self.calls) == 1, f"expected one statement, got {len(self.calls)}"
        return self.calls[0][1]

    async def fetchrow(self, query: str, *args: Any) -> Any:
        self._record(query, args)
        return self.fetchrow_results.pop(0) if self.fetchrow_results else None

    async def fetch(self, query: str, *args: Any) -> list[Any]:
        self._record(query, args)
        return self.fetch_results.pop(0) if self.fetch_results else []

    async def execute(self, query: str, *args: Any) -> str:
        self._record(query, args)
        return self.execute_results.pop(0) if self.execute_results else "UPDATE 0"


def _factory(connection: FakeConnection) -> Any:
    async def create() -> FakeConnection:
        return connection

    return create


def _store(connection: FakeConnection) -> BackupJobStore:
    return BackupJobStore(connection_factory=_factory(connection))


def _running_row(**overrides: Any) -> dict[str, Any]:
    """The ``backup_jobs`` row a successful ``claim_next`` returns."""
    base: dict[str, Any] = {
        "status": STATUS_RUNNING,
        "attempt_count": 1,
        "lock_token": "worker-1",
        "locked_at": NOW,
        "started_at": NOW,
    }
    base.update(overrides)
    return _row(**base)


def _running_job(**overrides: Any) -> BackupJob:
    """A claimed job, as ``claim_next`` hands it to a worker."""
    return _row_to_job(_running_row(**overrides))


class StubService:
    """Minimal ``BackupService`` stand-in: records the call, completes or raises."""

    def __init__(
        self,
        *,
        record: Optional[BackupRecord] = None,
        error: Optional[BaseException] = None,
    ) -> None:
        self._record = record
        self._error = error
        self.calls: list[dict[str, Any]] = []

    async def create_backup(
        self, *, requested_by: Optional[str] = None, reason: Optional[str] = None
    ) -> BackupRecord:
        self.calls.append({"requested_by": requested_by, "reason": reason})
        if self._error is not None:
            raise self._error
        assert self._record is not None, "StubService needs a record to return"
        return self._record


# ---------------------------------------------------------------------------
# Vocabulary and row mapping
# ---------------------------------------------------------------------------
class TestVocabulary:
    def test_status_vocabulary_mirrors_the_migration_check_constraint(self) -> None:
        assert ALL_STATUSES == (
            STATUS_QUEUED,
            STATUS_RUNNING,
            STATUS_COMPLETED,
            STATUS_FAILED,
            STATUS_EXPIRED,
            STATUS_DELETED,
        )
        assert ALLOWED_SCOPES == (SCOPE_FULL,)

    def test_only_queued_and_running_occupy_the_single_flight_slot(self) -> None:
        assert ACTIVE_STATUSES == (STATUS_QUEUED, STATUS_RUNNING)

    @pytest.mark.parametrize(
        ("status", "active", "terminal"),
        [
            (STATUS_QUEUED, True, False),
            (STATUS_RUNNING, True, False),
            (STATUS_COMPLETED, False, True),
            (STATUS_EXPIRED, False, True),
            (STATUS_DELETED, False, True),
            # A failed job is neither active (the slot is free) nor terminal
            # (it may be re-queued until the attempt budget is spent).
            (STATUS_FAILED, False, False),
        ],
    )
    def test_status_classification(self, status: str, active: bool, terminal: bool) -> None:
        job = _row_to_job(_row(status=status))
        assert job.is_active is active
        assert job.is_terminal is terminal


class TestRowMapping:
    def test_uuid_columns_are_normalised_to_strings(self) -> None:
        deleter = UUID("ffffffff-0000-1111-2222-333333333333")
        job = _row_to_job(
            _row(id=UUID(JOB_ID), requested_by=UUID(REQUESTER), deleted_by=deleter)
        )

        assert job.id == JOB_ID
        assert job.requested_by == REQUESTER
        assert job.deleted_by == str(deleter)
        assert all(isinstance(value, str) for value in (job.id, job.requested_by, job.deleted_by))

    def test_jsonb_manifest_round_trips(self) -> None:
        job = _row_to_job(_row(manifest='{"backup_id": "3f2b1c0d9e"}'))
        assert job.manifest == {"backup_id": "3f2b1c0d9e"}

    def test_a_corrupt_manifest_degrades_to_none_rather_than_raising(self) -> None:
        assert _row_to_job(_row(manifest="not json")).manifest is None

    def test_as_dict_renders_datetimes_as_utc_iso8601(self) -> None:
        payload = _row_to_job(_row(requested_at=NOW, finished_at=NOW)).as_dict()
        assert payload["requested_at"] == "2026-10-01T12:00:00Z"
        assert payload["finished_at"] == "2026-10-01T12:00:00Z"
        assert payload["started_at"] is None

    def test_as_dict_never_exposes_worker_lock_state(self) -> None:
        payload = _running_job().as_dict()
        assert "lock_token" not in payload
        assert "locked_at" not in payload
        assert payload["attempt_count"] == 1


# ---------------------------------------------------------------------------
# Enqueue — the ratified single-flight guard (§11)
# ---------------------------------------------------------------------------
class TestCreateQueuedJob:
    async def test_a_fresh_request_creates_one_queued_row(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row())
        store = _store(conn)

        job, created = await store.create_queued_job(
            requested_by=REQUESTER, idempotency_key="key-1", release_commit="abc123"
        )

        assert created is True
        assert job.id == JOB_ID
        assert job.status == STATUS_QUEUED
        assert job.scope == SCOPE_FULL
        assert conn.args == (
            STATUS_QUEUED,
            SCOPE_FULL,
            REQUESTER,
            "key-1",
            "abc123",
            KIND_DATABASE,
            None,
        )
        assert "INSERT INTO public.backup_jobs" in conn.flat_query
        assert "RETURNING" in conn.flat_query

    async def test_the_conflict_clause_is_bare_so_either_index_resolves_it(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row())
        store = _store(conn)

        await store.create_queued_job(requested_by=REQUESTER, idempotency_key="key-1")

        insert = conn.flat_queries[0]
        assert "ON CONFLICT DO NOTHING" in insert
        assert "ON CONFLICT (" not in insert, (
            "a conflict *target* would leave the other unique index (the "
            "single-flight slot) free to raise a unique violation instead of "
            "resolving the request to the job that already holds the slot"
        )

    async def test_a_duplicate_request_returns_the_job_holding_the_slot(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(None)  # INSERT ... ON CONFLICT DO NOTHING
        conn.fetchrow_results.append(
            _row(status=STATUS_RUNNING, attempt_count=1, lock_token="worker-1")
        )
        store = _store(conn)

        job, created = await store.create_queued_job(requested_by=REQUESTER)

        assert created is False
        assert job.id == JOB_ID
        assert job.status == STATUS_RUNNING
        assert len(conn.calls) == 2
        assert "WHERE status = ANY($1::text[])" in conn.flat_queries[-1]
        assert conn.calls[-1][1] == (list(ACTIVE_STATUSES), KIND_DATABASE)
        assert "ORDER BY requested_at ASC LIMIT 1" in conn.flat_queries[-1]

    async def test_the_idempotency_key_wins_over_whatever_is_running(self) -> None:
        """A retried request must resolve to *its* job, not to the current one."""
        conn = FakeConnection()
        conn.fetchrow_results.append(None)
        conn.fetchrow_results.append(
            _row(status=STATUS_COMPLETED, idempotency_key="key-1", finished_at=NOW)
        )
        store = _store(conn)

        job, created = await store.create_queued_job(
            requested_by=REQUESTER, idempotency_key="key-1"
        )

        assert created is False
        assert job.status == STATUS_COMPLETED
        assert job.idempotency_key == "key-1"
        assert "WHERE idempotency_key = $1 LIMIT 1" in conn.flat_queries[1]
        assert conn.calls[1][1] == ("key-1",)
        assert len(conn.calls) == 2, (
            "a key match must not fall through to the active-slot lookup"
        )

    async def test_a_conflict_with_no_resolvable_row_fails_closed(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.extend([None, None])  # insert and slot lookup both empty
        store = _store(conn)

        with pytest.raises(BackupJobError):
            await store.create_queued_job(requested_by=REQUESTER)

    async def test_a_scope_outside_the_vocabulary_is_refused_before_any_sql(self) -> None:
        conn = FakeConnection()
        store = _store(conn)

        with pytest.raises(BackupJobError) as excinfo:
            await store.create_queued_job(requested_by=REQUESTER, scope="everything")

        assert "everything" in str(excinfo.value)
        assert conn.calls == [], "an invalid scope must never reach the database"


class TestGetActive:
    async def test_a_free_slot_is_reported_as_none(self) -> None:
        conn = FakeConnection()
        store = _store(conn)

        assert await store.get_active() is None
        assert conn.args == (list(ACTIVE_STATUSES),)

    async def test_the_running_job_is_returned(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row(status=STATUS_RUNNING, lock_token="worker-1"))
        store = _store(conn)

        job = await store.get_active()

        assert job is not None
        assert job.status == STATUS_RUNNING
        assert job.is_active is True


# ---------------------------------------------------------------------------
# Claim — one statement solves locking, retry bounding and crash recovery (§11)
# ---------------------------------------------------------------------------
class TestClaimNext:
    async def test_an_empty_queue_yields_none(self) -> None:
        conn = FakeConnection()
        store = _store(conn)

        assert await store.claim_next(lock_token="worker-1", now=NOW) is None
        assert "FOR UPDATE SKIP LOCKED" in conn.flat_query

    async def test_the_claim_is_atomic_and_skips_locked_rows(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_running_row(lock_token="worker-1"))
        store = _store(conn)

        job = await store.claim_next(lock_token="worker-1", now=NOW)

        assert job is not None
        assert job.status == STATUS_RUNNING
        assert job.lock_token == "worker-1"
        assert "FOR UPDATE SKIP LOCKED" in conn.flat_query
        assert "LIMIT 1" in conn.flat_query

    async def test_the_claim_consumes_an_attempt_and_clears_the_last_error(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_running_row(attempt_count=2))
        store = _store(conn)

        await store.claim_next(lock_token="worker-1", now=NOW)

        statement = conn.flat_query
        assert "attempt_count = attempt_count + 1" in statement, (
            "the attempt is consumed at claim time, so a crash *after* the claim "
            "still counts and the retry loop terminates"
        )
        assert "error_reason = NULL" in statement
        assert "started_at = COALESCE(started_at, $3)" in statement

    async def test_retries_are_bounded_by_an_attempt_ceiling(self) -> None:
        conn = FakeConnection()
        store = _store(conn)

        await store.claim_next(lock_token="worker-1", now=NOW)

        assert conn.args[0] == DEFAULT_MAX_ATTEMPTS
        assert "attempt_count < $1" in conn.flat_query

    async def test_a_dead_workers_lock_is_reclaimable(self) -> None:
        conn = FakeConnection()
        store = _store(conn)

        await store.claim_next(lock_token="worker-2", now=NOW)

        statement = conn.flat_query
        assert "locked_at IS NOT NULL" in statement
        assert "locked_at < $3::timestamptz - make_interval(secs => $8)" in statement
        assert conn.args[7] == DEFAULT_STALE_LOCK_SECONDS

    async def test_the_candidate_order_is_fifo(self) -> None:
        conn = FakeConnection()
        store = _store(conn)

        await store.claim_next(lock_token="worker-1", now=NOW)

        assert "ORDER BY requested_at ASC" in conn.flat_query

    async def test_the_claim_parameters_are_in_addressable_order(self) -> None:
        conn = FakeConnection()
        store = _store(conn)

        await store.claim_next(
            lock_token="worker-7", max_attempts=5, stale_after_seconds=90, now=NOW
        )

        assert conn.args == (
            5,  # $1  attempt ceiling
            STATUS_RUNNING,  # $2  new status
            NOW,  # $3  claimed-at timestamp
            "worker-7",  # $4  lock token
            STATUS_QUEUED,  # $5  always runnable
            STATUS_FAILED,  # $6  retryable only while attempts remain
            STATUS_RUNNING,  # $7  stale-lock candidates
            90,  # $8  stale-lock age
        )


class TestReleaseStale:
    async def test_a_stale_lock_is_requeued_and_counted(self) -> None:
        conn = FakeConnection()
        conn.execute_results.append("UPDATE 2")
        store = _store(conn)

        assert await store.release_stale(stale_after_seconds=60, now=NOW) == 2

        statement = conn.flat_query
        assert "SET status = $1, lock_token = NULL, locked_at = NULL" in statement
        assert "WHERE status = $2" in statement
        assert "locked_at < $3::timestamptz - make_interval(secs => $4)" in statement
        assert conn.args == (STATUS_QUEUED, STATUS_RUNNING, NOW, 60)

    async def test_release_never_touches_an_unlocked_row(self) -> None:
        conn = FakeConnection()
        store = _store(conn)

        await store.release_stale(now=NOW)

        assert "locked_at IS NOT NULL" in conn.flat_query

    async def test_release_does_not_reset_the_attempt_counter(self) -> None:
        conn = FakeConnection()
        store = _store(conn)

        await store.release_stale(now=NOW)

        assert "attempt_count" not in conn.flat_query, (
            "the attempt was already consumed at claim time; resetting it here "
            "would let a permanently poisoned job loop forever"
        )

    async def test_nothing_to_release_is_not_an_error(self) -> None:
        conn = FakeConnection()  # the default command tag is "UPDATE 0"
        store = _store(conn)

        assert await store.release_stale(now=NOW) == 0


# ---------------------------------------------------------------------------
# Terminal transitions — guarded so a duplicated worker cannot overwrite the row
# ---------------------------------------------------------------------------
class TestMarkCompleted:
    async def test_completion_records_only_ciphertext_metadata(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(
            _row(
                status=STATUS_COMPLETED,
                finished_at=NOW,
                storage_key=RECORD.object_key,
                storage_bucket="ct-backups",
                artifact_bytes=RECORD.size_bytes,
                checksum_sha256=RECORD.ciphertext_sha256,
                key_version=RECORD.key_id,
                manifest="{}",
            )
        )
        store = _store(conn)

        job = await store.mark_completed(
            JOB_ID,
            record=RECORD,
            manifest_extra={"job_id": JOB_ID, "scope": SCOPE_FULL},
            storage_bucket="ct-backups",
            retention_days=30,
            now=NOW,
        )

        assert job.status == STATUS_COMPLETED
        assert job.storage_key == RECORD.object_key
        assert job.artifact_bytes == RECORD.size_bytes

        assert conn.args[0] == JOB_ID
        assert conn.args[1] == STATUS_COMPLETED
        assert conn.args[2] == NOW
        assert conn.args[3] == RECORD.object_key
        assert conn.args[4] == "ct-backups"
        assert conn.args[5] == RECORD.size_bytes
        assert conn.args[6] == RECORD.ciphertext_sha256, "the *ciphertext* digest is stored"
        assert conn.args[7] == RECORD.key_id, "the key identifier, never the key"
        assert conn.args[9] == 30
        assert conn.args[10] == STATUS_RUNNING
        assert "WHERE id = $1 AND status = $11" in conn.flat_query

    async def test_the_manifest_merges_the_record_with_the_job_metadata(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row(status=STATUS_COMPLETED, manifest="{}"))
        store = _store(conn)

        await store.mark_completed(
            JOB_ID,
            record=RECORD,
            manifest_extra={"job_id": JOB_ID, "scope": SCOPE_FULL},
            now=NOW,
        )

        manifest = json.loads(conn.args[8])
        assert manifest["backup_id"] == RECORD.backup_id
        assert manifest["object_key"] == RECORD.object_key
        assert manifest["ciphertext_sha256"] == RECORD.ciphertext_sha256
        assert manifest["job_id"] == JOB_ID
        assert manifest["scope"] == SCOPE_FULL

    async def test_the_manifest_is_merged_into_any_existing_jsonb(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row(status=STATUS_COMPLETED, manifest="{}"))
        store = _store(conn)

        await store.mark_completed(JOB_ID, record=RECORD, now=NOW)

        assert "COALESCE(manifest, '{}'::jsonb) || $9::jsonb" in conn.flat_query

    async def test_no_key_material_is_ever_persisted(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row(status=STATUS_COMPLETED, manifest="{}"))
        store = _store(conn)

        await store.mark_completed(JOB_ID, record=RECORD, now=NOW)

        persisted = json.dumps([str(arg) for arg in conn.args])
        assert KEY_MATERIAL_CANARY not in persisted
        assert KEY_MATERIAL_CANARY not in conn.flat_query

    async def test_a_missing_retention_setting_means_no_expiry(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row(status=STATUS_COMPLETED, manifest="{}"))
        store = _store(conn)

        await store.mark_completed(JOB_ID, record=RECORD, now=NOW)

        assert conn.args[9] is None, (
            "'retention not configured' must be stored as no expiry, not as a "
            "silently invented default"
        )
        assert "WHEN $10::integer IS NULL THEN NULL" in conn.flat_query

    async def test_completing_a_job_that_is_not_running_is_a_conflict(self) -> None:
        conn = FakeConnection()  # the guarded UPDATE matches no row
        store = _store(conn)

        with pytest.raises(BackupJobConflictError) as excinfo:
            await store.mark_completed(JOB_ID, record=RECORD, now=NOW)

        assert JOB_ID in str(excinfo.value)
        assert excinfo.value.http_status == 409


class TestMarkFailed:
    async def test_failure_closes_the_job_and_clears_the_lock(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(
            _row(status=STATUS_FAILED, finished_at=NOW, error_reason="BackupExportError: boom")
        )
        store = _store(conn)

        job = await store.mark_failed(JOB_ID, error_reason="BackupExportError: boom", now=NOW)

        assert job.status == STATUS_FAILED
        assert job.error_reason == "BackupExportError: boom"
        assert conn.args == (JOB_ID, STATUS_FAILED, NOW, "BackupExportError: boom", STATUS_RUNNING)
        assert "lock_token = NULL, locked_at = NULL" in conn.flat_query
        assert "error_reason = $4" in conn.flat_query
        assert "WHERE id = $1 AND status = $5" in conn.flat_query

    async def test_an_overlong_reason_is_truncated_at_the_store(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row(status=STATUS_FAILED))
        store = _store(conn)

        await store.mark_failed(JOB_ID, error_reason="x" * 500, now=NOW)

        assert len(conn.args[3]) == MAX_ERROR_REASON_LENGTH

    async def test_failing_a_job_that_is_not_running_is_a_conflict(self) -> None:
        conn = FakeConnection()
        store = _store(conn)

        with pytest.raises(BackupJobConflictError):
            await store.mark_failed(JOB_ID, error_reason="late", now=NOW)


class TestMarkExpired:
    async def test_expiry_is_metadata_only_and_counted(self) -> None:
        conn = FakeConnection()
        conn.execute_results.append("UPDATE 1")
        store = _store(conn)

        assert await store.mark_expired(now=NOW) == 1

        statement = conn.flat_query
        assert "SET status = $1, lock_token = NULL, locked_at = NULL" in statement
        assert "WHERE status = $2" in statement
        assert "expires_at IS NOT NULL" in statement
        assert "expires_at <= $3" in statement
        assert conn.args == (STATUS_EXPIRED, STATUS_COMPLETED, NOW)

    async def test_expiry_leaves_the_artifact_alone(self) -> None:
        conn = FakeConnection()
        store = _store(conn)

        await store.mark_expired(now=NOW)

        statement = conn.flat_query
        assert "storage_key" not in statement
        assert "deleted_at" not in statement
        assert "artifact_bytes" not in statement

    async def test_a_completed_job_without_an_expiry_is_never_swept(self) -> None:
        conn = FakeConnection()
        store = _store(conn)

        await store.mark_expired(now=NOW)

        assert "expires_at IS NOT NULL" in conn.flat_query


class TestMarkDeleted:
    async def test_deletion_retains_the_row_for_audit(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(
            _row(status=STATUS_DELETED, deleted_at=NOW, deleted_by=REQUESTER)
        )
        store = _store(conn)

        job = await store.mark_deleted(JOB_ID, deleted_by=REQUESTER, now=NOW)

        assert job.status == STATUS_DELETED
        assert job.deleted_by == REQUESTER
        assert "DELETE FROM" not in conn.flat_query, "the row is retained for audit"
        assert "status = ANY($5::text[])" in conn.flat_query
        assert conn.args == (
            JOB_ID,
            STATUS_DELETED,
            NOW,
            REQUESTER,
            [STATUS_COMPLETED, STATUS_EXPIRED, STATUS_FAILED],
        )

    async def test_deletion_is_refused_from_retryable_or_active_states(self) -> None:
        conn = FakeConnection()  # the guarded UPDATE matches no row
        store = _store(conn)

        with pytest.raises(BackupJobConflictError):
            await store.mark_deleted(JOB_ID, deleted_by=REQUESTER, now=NOW)


class TestQueries:
    async def test_get_returns_none_for_an_unknown_id(self) -> None:
        conn = FakeConnection()
        store = _store(conn)

        assert await store.get(JOB_ID) is None
        assert conn.args == (JOB_ID,)
        assert "WHERE id = $1" in conn.flat_query

    async def test_get_returns_a_known_job(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row(status=STATUS_COMPLETED))
        store = _store(conn)

        job = await store.get(JOB_ID)

        assert job is not None
        assert job.status == STATUS_COMPLETED

    async def test_list_recent_is_newest_first_and_paged(self) -> None:
        conn = FakeConnection()
        conn.fetch_results.append(
            [
                _row(id=OTHER_JOB_ID, requested_at=LATER, status=STATUS_COMPLETED),
                _row(id=JOB_ID, requested_at=NOW, status=STATUS_FAILED),
            ]
        )
        store = _store(conn)

        jobs = await store.list_recent(limit=10, offset=20)

        assert [job.id for job in jobs] == [OTHER_JOB_ID, JOB_ID]
        assert conn.args == (10, 20)
        assert "ORDER BY requested_at DESC, id DESC LIMIT $1 OFFSET $2" in conn.flat_query

    async def test_an_empty_history_is_an_empty_list(self) -> None:
        conn = FakeConnection()
        store = _store(conn)

        assert await store.list_recent() == []
        assert conn.args == (50, 0)


class TestHelpers:
    @pytest.mark.parametrize(
        ("command_tag", "expected"),
        [
            ("UPDATE 3", 3),
            ("UPDATE 0", 0),
            ("DELETE 7", 7),
            ("INSERT 0 1", 0),
            ("UPDATE n", 0),
            ("", 0),
        ],
    )
    def test_affected_rows_parses_the_asyncpg_command_tag(
        self, command_tag: str, expected: int
    ) -> None:
        assert _affected_rows(command_tag) == expected

    def test_sanitise_reason_keeps_the_class_and_collapses_whitespace(self) -> None:
        exc = BackupExportError("copy failed\n  because\tCAP   broke")
        assert sanitise_reason(exc) == "BackupExportError: copy failed because CAP broke"

    def test_sanitise_reason_is_just_the_class_when_there_is_no_message(self) -> None:
        assert sanitise_reason(BackupExportError("")) == "BackupExportError"

    def test_sanitise_reason_bounds_the_length(self) -> None:
        reason = sanitise_reason(BackupExportError("x" * 500))
        assert reason.startswith("BackupExportError: ")
        assert len(reason) == MAX_ERROR_REASON_LENGTH

    def test_sanitise_reason_accepts_any_exception(self) -> None:
        assert sanitise_reason(ValueError("nope")) == "ValueError: nope"


# ---------------------------------------------------------------------------
# Worker entrypoints
# ---------------------------------------------------------------------------
class TestRunClaimedJob:
    async def test_a_successful_run_closes_the_job_with_the_artifact(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(
            _row(
                status=STATUS_COMPLETED,
                finished_at=NOW,
                storage_key=RECORD.object_key,
                artifact_bytes=RECORD.size_bytes,
                manifest="{}",
            )
        )
        store = _store(conn)
        service = StubService(record=RECORD)

        job = await run_claimed_job(
            store,
            _running_job(release_commit="abc123"),
            service,
            storage_bucket="ct-backups",
            retention_days=30,
            now=NOW,
        )

        assert job.status == STATUS_COMPLETED
        assert service.calls == [
            {"requested_by": REQUESTER, "reason": f"backup job {JOB_ID}"}
        ], "the worker hands over identity and reason only — never a key or a path"

    async def test_the_manifest_carries_the_job_provenance(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row(status=STATUS_COMPLETED, manifest="{}"))
        store = _store(conn)

        await run_claimed_job(
            store,
            _running_job(release_commit="abc123"),
            StubService(record=RECORD),
            now=NOW,
        )

        manifest = json.loads(conn.args[8])
        assert manifest["job_id"] == JOB_ID
        assert manifest["scope"] == SCOPE_FULL
        assert manifest["attempt_count"] == 1
        assert manifest["requested_by"] == REQUESTER
        assert manifest["release_commit"] == "abc123"
        assert manifest["backup_id"] == RECORD.backup_id

    async def test_an_explicit_release_commit_overrides_the_row(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row(status=STATUS_COMPLETED, manifest="{}"))
        store = _store(conn)

        await run_claimed_job(
            store,
            _running_job(release_commit="abc123"),
            StubService(record=RECORD),
            release_commit="def456",
            now=NOW,
        )

        assert json.loads(conn.args[8])["release_commit"] == "def456"

    async def test_a_row_without_a_release_commit_omits_it(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row(status=STATUS_COMPLETED, manifest="{}"))
        store = _store(conn)

        await run_claimed_job(store, _running_job(), StubService(record=RECORD), now=NOW)

        assert "release_commit" not in json.loads(conn.args[8])

    async def test_an_export_failure_is_absorbed_into_the_row(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row(status=STATUS_FAILED, finished_at=NOW))
        store = _store(conn)
        service = StubService(error=BackupExportError("copy failed"))

        job = await run_claimed_job(store, _running_job(), service, now=NOW)  # must not raise

        assert job.status == STATUS_FAILED
        assert conn.args[0] == JOB_ID
        assert conn.args[3] == "BackupExportError: copy failed"

    async def test_an_unexpected_failure_is_absorbed_too(self) -> None:
        """One poisoned job must not be able to kill the worker loop."""
        conn = FakeConnection()
        conn.fetchrow_results.append(_row(status=STATUS_FAILED))
        store = _store(conn)
        service = StubService(error=RuntimeError("kaboom"))

        job = await run_claimed_job(store, _running_job(), service, now=NOW)

        assert job.status == STATUS_FAILED
        assert conn.args[3] == "RuntimeError: kaboom"

    async def test_a_failure_reason_is_bounded_before_it_is_stored(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row(status=STATUS_FAILED))
        store = _store(conn)
        service = StubService(error=BackupExportError("x" * 1000))

        await run_claimed_job(store, _running_job(), service, now=NOW)

        assert len(conn.args[3]) == MAX_ERROR_REASON_LENGTH

    async def test_an_impossible_transition_is_surfaced_not_swallowed(self) -> None:
        """A job another actor moved is an anomaly, not a run outcome."""
        conn = FakeConnection()  # mark_failed's guarded UPDATE matches no row
        store = _store(conn)
        service = StubService(error=BackupExportError("boom"))

        with pytest.raises(BackupJobConflictError):
            await run_claimed_job(store, _running_job(), service, now=NOW)

    async def test_the_worker_never_persists_key_material(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_row(status=STATUS_COMPLETED, manifest="{}"))
        store = _store(conn)

        await run_claimed_job(
            store,
            _running_job(),
            StubService(record=RECORD),
            storage_bucket="ct-backups",
            now=NOW,
        )

        assert conn.args[7] == "unit-key-v1", "only the key identifier travels"
        assert KEY_MATERIAL_CANARY not in json.dumps([str(arg) for arg in conn.args])


class TestRunNextJob:
    async def test_an_empty_queue_does_not_call_the_service(self) -> None:
        conn = FakeConnection()
        store = _store(conn)
        service = StubService(record=RECORD)

        assert await run_next_job(store, service) is None
        assert service.calls == []

    async def test_a_claim_is_followed_by_a_run_under_a_fresh_lock_token(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_running_row())
        conn.fetchrow_results.append(_row(status=STATUS_COMPLETED, manifest="{}"))
        store = _store(conn)

        job = await run_next_job(
            store, StubService(record=RECORD), storage_bucket="ct-backups"
        )

        assert job is not None
        assert job.status == STATUS_COMPLETED
        token = conn.calls[0][1][3]
        assert isinstance(token, str)
        assert len(token) == 32, "the default token is uuid4().hex — one lock per run"
        assert all(char in "0123456789abcdef" for char in token)

    async def test_an_explicit_lock_token_is_passed_through(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_running_row())
        conn.fetchrow_results.append(_row(status=STATUS_COMPLETED, manifest="{}"))
        store = _store(conn)

        await run_next_job(store, StubService(record=RECORD), lock_token="worker-7")

        assert conn.calls[0][1][3] == "worker-7"
        assert "FOR UPDATE SKIP LOCKED" in conn.flat_queries[0]

    async def test_the_run_uses_the_claim_metadata_not_a_fresh_lookup(self) -> None:
        conn = FakeConnection()
        conn.fetchrow_results.append(_running_row(release_commit="abc123"))
        conn.fetchrow_results.append(_row(status=STATUS_COMPLETED, manifest="{}"))
        store = _store(conn)

        await run_next_job(store, StubService(record=RECORD), lock_token="worker-7")

        assert len(conn.calls) == 2, "one claim, one completion — no extra round trips"
        assert conn.calls[0][1][0] == DEFAULT_MAX_ATTEMPTS


# ---------------------------------------------------------------------------
# The migration is the database half of this model — assert both halves agree
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
_MIGRATIONS_DIR = _REPO_ROOT / "supabase" / "migrations"
BACKUP_01_MIGRATION = "20261026000000_ct_backup_01_backup_jobs.sql"
#: BACKUP-02 (§12/§14) — the additive backup-set + verification columns and the
#: per-kind single-flight index. It must follow BACKUP-01, never precede it.
BACKUP_02_MIGRATION = "20261027000000_ct_backup_02_backup_sets_and_verification.sql"
#: The migration BACKUP-01 must follow in the (strictly ordered) chain.
_PREVIOUS_MIGRATION = "20261025000000_ct_step2_documents_bucket_size_alignment.sql"

#: ``<name> <TYPE>`` lines of the CREATE TABLE block (identifiers may contain
#: digits, e.g. ``checksum_sha256``). ``CONSTRAINT`` lines start with an
#: uppercase keyword, so they cannot be mistaken for columns.
_COLUMN_LINE = re.compile(r"^ {4}([a-z][a-z0-9_]*) +[A-Z]", re.MULTILINE)

#: ``ADD COLUMN IF NOT EXISTS <name> <TYPE>`` lines of the BACKUP-02 migration —
#: the ADDITIVE half of the same table, formatted the same way.
_ADDED_COLUMN_LINE = re.compile(
    r"^ {4}ADD COLUMN IF NOT EXISTS ([a-z][a-z0-9_]*) +[A-Z]", re.MULTILINE
)


def _migration_sql() -> str:
    return (_MIGRATIONS_DIR / BACKUP_01_MIGRATION).read_text(encoding="utf-8")


def _backup_02_sql() -> str:
    return (_MIGRATIONS_DIR / BACKUP_02_MIGRATION).read_text(encoding="utf-8")


def _create_table_block(sql: str) -> str:
    start = sql.index("CREATE TABLE IF NOT EXISTS public.backup_jobs (")
    return sql[start : sql.index("\n);", start)]


def _declared_columns() -> tuple[str, ...]:
    """Every column the two backup migrations leave on ``public.backup_jobs``.

    BACKUP-01 creates the table; BACKUP-02 only *adds* columns, so the effective
    schema is the concatenation in migration order — which is exactly the order
    the ``_COLUMNS`` projection selects.
    """
    return tuple(_COLUMN_LINE.findall(_create_table_block(_migration_sql()))) + tuple(
        _ADDED_COLUMN_LINE.findall(_backup_02_sql())
    )


class TestMigrationAlignment:
    def test_the_backup_migrations_are_the_newest_in_the_chain(self) -> None:
        names = sorted(path.name for path in _MIGRATIONS_DIR.glob("*.sql"))

        assert BACKUP_01_MIGRATION in names
        assert BACKUP_02_MIGRATION in names
        assert names.index(BACKUP_01_MIGRATION) > names.index(_PREVIOUS_MIGRATION)
        assert names.index(BACKUP_02_MIGRATION) > names.index(BACKUP_01_MIGRATION)
        # The backup pair are the newest *in their own block* — the invariant this
        # test owns is adjacency: BACKUP-02 immediately follows BACKUP-01, and
        # BACKUP-01 immediately follows the migration it depends on. It
        # deliberately does NOT claim to be the chain tip: later features (e.g.
        # FINAL-03's 20261028000000/20261029000000 RLS migrations) legitimately
        # sort after the backup block, so asserting
        # ``names[-1] == BACKUP_02_MIGRATION`` would fail every subsequent
        # migration for no reason — the anti-pattern avoided in
        # ``tests/unit/api/test_storage_management_step2.py``.
        assert names.index(BACKUP_02_MIGRATION) == names.index(BACKUP_01_MIGRATION) + 1
        assert names.index(BACKUP_01_MIGRATION) == names.index(_PREVIOUS_MIGRATION) + 1

    def test_only_the_backup_migrations_touch_the_table(self) -> None:
        touching = sorted(
            path.name
            for path in _MIGRATIONS_DIR.glob("*.sql")
            if "public.backup_jobs" in path.read_text(encoding="utf-8")
        )
        creating = sorted(
            path.name
            for path in _MIGRATIONS_DIR.glob("*.sql")
            if "CREATE TABLE IF NOT EXISTS public.backup_jobs" in path.read_text(encoding="utf-8")
        )

        assert touching == [BACKUP_01_MIGRATION, BACKUP_02_MIGRATION]
        assert creating == [BACKUP_01_MIGRATION], (
            "a second migration creating public.backup_jobs would make the "
            "table's owner ambiguous"
        )

    def test_the_column_projection_matches_the_table_exactly(self) -> None:
        assert _declared_columns() == tuple(name.strip() for name in _COLUMNS.split(","))

    def test_the_scripted_row_is_shaped_like_the_real_one(self) -> None:
        """The double must carry the real schema's columns, or these tests lie."""
        assert set(_row()) == set(_declared_columns())

    def test_the_status_check_matches_the_python_vocabulary(self) -> None:
        check = re.search(r"status IN \(([^)]*)\)", _create_table_block(_migration_sql()))

        assert check is not None, "the status vocabulary is no longer constrained"
        assert tuple(re.findall(r"'([a-z]+)'", check.group(1))) == ALL_STATUSES

    def test_the_scope_check_matches_the_python_vocabulary(self) -> None:
        check = re.search(r"scope IN \(([^)]*)\)", _create_table_block(_migration_sql()))

        assert check is not None, "the scope vocabulary is no longer constrained"
        assert tuple(re.findall(r"'([^']+)'", check.group(1))) == ALLOWED_SCOPES

    def test_the_single_flight_guard_matches_the_active_states(self) -> None:
        sql = _migration_sql()
        listed = ", ".join(f"'{status}'" for status in ACTIVE_STATUSES)

        assert f"WHERE status IN ({listed})" in sql
        assert "CREATE UNIQUE INDEX IF NOT EXISTS backup_jobs_single_flight_idx" in sql
        assert "CREATE UNIQUE INDEX IF NOT EXISTS backup_jobs_idempotency_key_idx" in sql, (
            "without the idempotency index a retried request would queue a "
            "second dump"
        )

    def test_the_table_is_internal_only(self) -> None:
        sql = _migration_sql()

        assert "ALTER TABLE public.backup_jobs ENABLE ROW LEVEL SECURITY;" in sql
        assert "REVOKE ALL ON TABLE public.backup_jobs FROM anon;" in sql
        assert "REVOKE ALL ON TABLE public.backup_jobs FROM authenticated;" in sql
        assert "CREATE POLICY" not in sql, (
            "§10 requires the table to be internal-admin only; a policy would "
            "widen it at the database"
        )

    def test_the_capability_is_granted_to_the_admin_roles_only(self) -> None:
        sql = _migration_sql()

        assert '"can_manage_backups": true' in sql
        assert "WHERE name IN ('admin', 'system_admin')" in sql, (
            "PO Decision 2 makes system_admin a superset of the legacy admin "
            "role, so both names must receive the capability"
        )

    def test_no_key_material_column_exists(self) -> None:
        """The schema must be structurally incapable of holding a key."""
        columns = _declared_columns()

        assert "key_version" in columns, "the key *identifier* is recorded"
        assert "idempotency_key" in columns, "an identifier, never key material"
        assert "key" not in columns
