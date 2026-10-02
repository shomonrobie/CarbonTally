"""B7 regression — a backup worker tick must never keep a pooled connection.

FINAL-02 §15.2/§18 (finding **B7**) recorded the symptom: after a handful of
worker ticks every database-backed endpoint hung. The cause was not pool size —
it was the connection idiom. The shared service-role pool is
``min_size=1, max_size=5`` (:func:`infra.supabase.get_service_pool`), and:

* the default connection factory did ``connection = await pool.acquire()``.
  ``asyncpg`` allows ``acquire()`` to be awaited as well as used as a context
  manager, and the awaited *proxy* holds a pool slot until it is released; and
* every call site then used that connection and dropped it, so there was no
  release path at all. One tick, one lost connection: about five ticks and the
  pool had nothing left to hand out, which is why unrelated DB-backed endpoints
  hung.

The fix (``backup.jobs`` and ``backup.service``) makes the default factory return
the **acquire context** (``pool.acquire()``) and enters it with ``async with``
inside ``_connection()``, so the connection goes back on every exit path —
normal return, raised exception and cancellation — while a *bare* connection from
an injected factory is still yielded unchanged (the unit doubles, the loopback
integration suites and the recovery drill keep their own lifecycle).

The same finding also carried the *other* half of FINAL-03 gate P1: an undeployed
BACKUP schema must be a **terminal, backed-off** condition rather than a per-tick
error. That is covered here too, because it was one finding and one remediation.

These tests deliberately drive the **production default path** (no injected
factory) against :class:`ServicePoolDouble`, which models asyncpg's capacity
rules and raises when the pool is empty. The first test is the control: it shows
the double *does* reproduce the pre-fix leak, so the tests after it are capable
of failing. ``test_jobs.py`` and ``test_service.py`` could not catch B7 because
each of their doubles hands the store a connection it also keeps a reference to:
there, a missing release is invisible.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Optional

import pytest

from backup import crypto
from backup.artifact import (
    ARCHIVE_MEMBER_CATALOG,
    ARCHIVE_MEMBER_DDL,
    ARCHIVE_MEMBER_SEQUENCES,
)
from backup.errors import (
    BackupExportError,
    BackupJobConflictError,
    BackupJobError,
    BackupJobNotFoundError,
)
from backup.exporter import ExportResult
from backup.jobs import BackupJobStore
from backup.service import BackupService
from backup.settings import BackupSettings
from backup.storage import InMemoryObjectStore
from backup.worker import BackupWorker, is_missing_backup_table

#: Mirrors ``infra.supabase.get_service_pool()`` (``min_size=1, max_size=5``).
POOL_MAX_SIZE = 5

#: Far more ticks than the pool has slots: the pre-fix code needs only
#: ``POOL_MAX_SIZE`` acquisitions to starve every DB-backed endpoint.
TICKS = 12

JOB_ID = "11111111-1111-4111-8111-111111111111"
BACKUP_SET_ID = "22222222-2222-4222-8222-222222222222"


class PoolExhaustedError(RuntimeError):
    """What asyncpg reports when ``pool.acquire()`` cannot be satisfied."""


class PooledConnection:
    """The connection surface the store needs, answering "no rows".

    Every statement is recorded, so a test can also assert *that* work happened
    on a leased connection rather than on a connection the store invented.

    ``release()`` is the pool-return the pre-fix worker never called. It is kept
    because an awaited ``pool.acquire()`` (the old idiom) can only be given back
    explicitly — exactly asyncpg's contract, and what makes this double able to
    detect the bug instead of hiding it.
    """

    def __init__(self, pool: "ServicePoolDouble") -> None:
        self._pool = pool
        self.released = False
        self.statements: list[str] = []

    def release(self) -> None:
        """Return this connection to the pool (idempotent, as asyncpg's is)."""
        self._pool.checkin(self)

    async def fetch(self, query: str, *args: Any) -> list[Any]:
        self.statements.append(query)
        return []

    async def fetchrow(self, query: str, *args: Any) -> Optional[dict]:
        self.statements.append(query)
        return None

    async def execute(self, query: str, *args: Any) -> str:
        self.statements.append(query)
        return "UPDATE 0"


class AcquireContext:
    """``pool.acquire()``: an async context manager **and** an awaitable.

    ``async with pool.acquire() as connection`` gives the connection back when the
    block exits, whatever the block did. ``connection = await pool.acquire()``
    keeps the slot until ``connection.release()`` is called. Supporting both
    shapes is what lets this double detect the pre-fix leak.
    """

    def __init__(self, pool: "ServicePoolDouble") -> None:
        self._pool = pool
        self._connection: Optional[PooledConnection] = None

    async def __aenter__(self) -> PooledConnection:
        self._connection = self._pool.checkout()
        return self._connection

    async def __aexit__(self, *exc_info: Any) -> bool:
        self._pool.checkin(self._connection)
        return False  # never swallow the body's exception or cancellation

    def __await__(self) -> Any:
        return self.__aenter__().__await__()


class ServicePoolDouble:
    """``asyncpg.Pool`` as the worker and the API see it: bounded, loud when empty."""

    def __init__(self, *, max_size: int = POOL_MAX_SIZE) -> None:
        self.max_size = max_size
        #: Connections currently leased (``0`` means the pool is whole again).
        self.leases = 0
        #: High-water mark of ``leases`` — proves *reuse*, not merely release.
        self.peak_leases = 0
        self.acquisitions = 0
        self.releases = 0
        #: How often a caller was refused because the pool was empty.
        self.exhausted_attempts = 0

    def acquire(self) -> AcquireContext:
        """The only supported entry point, exactly as asyncpg exposes it."""
        return AcquireContext(self)

    def checkout(self) -> PooledConnection:
        if self.leases >= self.max_size:
            self.exhausted_attempts += 1
            raise PoolExhaustedError(
                f"pool exhausted: {self.leases}/{self.max_size} connections still leased"
            )
        self.leases += 1
        self.acquisitions += 1
        self.peak_leases = max(self.peak_leases, self.leases)
        return PooledConnection(self)

    def checkin(self, connection: Optional[PooledConnection]) -> None:
        if connection is None or connection.released:
            return
        connection.released = True
        self.leases -= 1
        self.releases += 1


@pytest.fixture()
def service_pool(monkeypatch: pytest.MonkeyPatch) -> ServicePoolDouble:
    """The **default** factory path: patch ``infra.supabase.get_service_pool``.

    Both default factories import ``get_service_pool`` lazily *inside* the
    factory, so patching the module attribute is exactly what production code
    resolves.
    """
    import infra.supabase

    pool = ServicePoolDouble()

    async def _get_service_pool() -> ServicePoolDouble:
        return pool

    monkeypatch.setattr(infra.supabase, "get_service_pool", _get_service_pool)
    return pool


@pytest.fixture()
def settings(tmp_path: Any) -> BackupSettings:
    """A complete in-memory configuration (no provider credentials involved)."""
    return BackupSettings.from_env(
        {
            "CT_BACKUP_OBJECT_STORE": "memory",
            "CT_BACKUP_ENCRYPTION_KEY": crypto.encode_key(crypto.generate_key()),
            "CT_BACKUP_KEY_ID": "b7-key-v1",
            "CT_BACKUP_TEMP_ROOT": str(tmp_path),
        }
    )


def _assert_pool_whole(pool: ServicePoolDouble, where: str) -> None:
    """Every lease taken before ``where`` must be back in the pool."""
    assert pool.leases == 0, f"{where} did not return its pooled connection"


def _assert_no_leak_accumulated(pool: ServicePoolDouble) -> None:
    """No caller was ever refused, and one connection was reused throughout."""
    assert pool.exhausted_attempts == 0, "a caller starved on its own pool"
    assert pool.peak_leases == 1, "more than one connection was held at once"
    assert pool.acquisitions == pool.releases, "acquire/release are not balanced"


def _write_staged_members(output_dir: str) -> None:
    """Write the staged material ``collect_members`` archives (metadata only)."""
    for relative, payload in (
        (ARCHIVE_MEMBER_CATALOG, b'{"schemas": ["public"]}'),
        (ARCHIVE_MEMBER_DDL, b"-- B7 regression: no DDL body required\n"),
        (ARCHIVE_MEMBER_SEQUENCES, b"[]"),
    ):
        path = os.path.join(output_dir, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(payload)


# ---------------------------------------------------------------------------
# Control: the double must be able to *see* the B7 leak
# ---------------------------------------------------------------------------


async def test_control_the_double_reproduces_the_pre_fix_leak(
    service_pool: ServicePoolDouble,
) -> None:
    """The pre-fix idiom must exhaust this double, or nothing below proves anything.

    ``connection = await pool.acquire()`` is the body of the old factory. Nothing
    released the proxy, so after ``POOL_MAX_SIZE`` calls the pool is empty — the
    exact process that hung the DB-backed endpoints in FINAL-02 §15.2.
    """
    held = [await service_pool.acquire() for _ in range(POOL_MAX_SIZE)]
    assert all(isinstance(connection, PooledConnection) for connection in held)

    assert service_pool.leases == POOL_MAX_SIZE
    with pytest.raises(PoolExhaustedError):
        await service_pool.acquire()
    assert service_pool.exhausted_attempts == 1


# ---------------------------------------------------------------------------
# B7: the worker's store returns every lease — success and exception paths
# ---------------------------------------------------------------------------


async def test_store_returns_every_lease_across_repeated_tick_cycles(
    service_pool: ServicePoolDouble,
) -> None:
    """Every store statement the tick uses releases its connection.

    The store is built with **no injected factory**, so this is the production
    path: the default factory is the patched pool's acquire context. The loop runs
    ``TICKS`` (12) cycles of the tick's statement set — well over 100 acquisitions
    against a five-slot pool, so the pre-fix code cannot reach the end.
    """
    store = BackupJobStore()

    for tick in range(TICKS):
        # -- the statements of one worker tick
        await store.release_stale(stale_after_seconds=300)
        _assert_pool_whole(service_pool, f"tick {tick}: release_stale")

        await store.mark_expired()
        _assert_pool_whole(service_pool, f"tick {tick}: mark_expired")

        assert await store.claim_next(lock_token="b7-tick") is None
        _assert_pool_whole(service_pool, f"tick {tick}: claim_next")

        # -- the retention/pruning half of the same sweep
        assert await store.list_expired(limit=10) == []
        _assert_pool_whole(service_pool, f"tick {tick}: list_expired")

        # -- the admin/metadata reads the API serves around every tick
        assert await store.get(JOB_ID) is None
        assert await store.get_active() is None
        assert await store.list_recent(limit=5) == []
        assert await store.list_by_backup_set(BACKUP_SET_ID) == []
        _assert_pool_whole(service_pool, f"tick {tick}: admin reads")

        # -- the failure paths must release too: each of these raises, because
        #    the double reports "no row affected"
        with pytest.raises(BackupJobError):
            await store.create_queued_job(requested_by="b7@example.test")
        with pytest.raises(BackupJobConflictError):
            await store.mark_failed(JOB_ID, error_reason="B7 regression")
        with pytest.raises(BackupJobConflictError):
            await store.mark_verified(JOB_ID, verified=True)
        with pytest.raises(BackupJobConflictError):
            await store.mark_deleted(JOB_ID, deleted_by="b7@example.test")
        with pytest.raises(BackupJobNotFoundError):
            await store.attach_backup_set(JOB_ID, BACKUP_SET_ID)
        _assert_pool_whole(service_pool, f"tick {tick}: exception paths")

    _assert_no_leak_accumulated(service_pool)
    # 10 secured statements per tick (release_stale, mark_expired, claim_next,
    # list_expired, get, get_active, list_recent, list_by_backup_set + raises).
    assert service_pool.acquisitions >= TICKS * 10


async def test_worker_tick_never_holds_a_connection_between_ticks(
    service_pool: ServicePoolDouble,
) -> None:
    """The **real** ``BackupWorker.tick()`` on the default factory, over many ticks.

    A tick is stale-lock reclaim → retention sweep → claim. With an empty queue
    that is four statements, so four leases per tick, every one returned before the
    next tick begins. Twelve ticks is more than twice the pool's capacity.
    """
    worker = BackupWorker(
        job_store=BackupJobStore(),  # default factory → the patched pool
        object_store=InMemoryObjectStore(),
        poll_interval_seconds=0.0,
        batch_size=1,
        retention_prune=True,  # also exercises the pruning read
    )

    for tick in range(TICKS):
        assert await worker.tick() == []
        _assert_pool_whole(service_pool, f"tick {tick}: BackupWorker.tick")

    _assert_no_leak_accumulated(service_pool)
    # release_stale + mark_expired + list_expired + claim_next per tick.
    assert service_pool.acquisitions >= TICKS * 4


# ---------------------------------------------------------------------------
# B7: the service's backup job returns its lease on all three exit paths
# ---------------------------------------------------------------------------


async def test_create_backup_returns_the_lease_after_the_export(
    service_pool: ServicePoolDouble,
    settings: BackupSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The export is the only step holding the lease; archiving/publishing is not.

    ``export_schemas`` is replaced by a stub that records how many connections
    were leased *while it ran* — the export must run on a real lease (1) — and the
    loop then proves the lease is returned, attempt after attempt, with no
    accumulation.
    """
    observed: dict[str, int] = {}

    async def _export(
        connection: Any,
        schemas: Any,
        *,
        output_dir: str,
        allow_denied_schemas: bool = False,
    ) -> ExportResult:
        observed["leases_during_export"] = service_pool.leases
        assert isinstance(connection, PooledConnection), "export ran off-pool"
        _write_staged_members(output_dir)
        return ExportResult()

    monkeypatch.setattr("backup.service.export_schemas", _export)
    service = BackupService(settings, object_store=InMemoryObjectStore())

    for attempt in range(TICKS):
        record = await service.create_backup(
            requested_by="b7@example.test", reason=f"B7 regression #{attempt}"
        )
        assert record.object_key.endswith(".tar.gz.enc")
        _assert_pool_whole(service_pool, f"attempt {attempt}: create_backup")

    assert observed["leases_during_export"] == 1, "the export ran without a lease"
    _assert_no_leak_accumulated(service_pool)
    assert service_pool.acquisitions == TICKS


async def test_create_backup_returns_the_lease_when_the_export_raises(
    service_pool: ServicePoolDouble,
    settings: BackupSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed export must still give the connection back.

    Repeated failures are the interesting case: before the fix each failed attempt
    cost one connection, so a provider outage would have starved the pool even
    though nothing was ever published.
    """
    attempts: list[int] = []

    async def _export(*args: Any, **kwargs: Any) -> ExportResult:
        attempts.append(service_pool.leases)
        raise BackupExportError("simulated export failure")

    monkeypatch.setattr("backup.service.export_schemas", _export)
    service = BackupService(settings, object_store=InMemoryObjectStore())

    for attempt in range(TICKS):
        with pytest.raises(BackupExportError):
            await service.create_backup(requested_by="b7@example.test")
        _assert_pool_whole(service_pool, f"attempt {attempt}: failed export")

    assert attempts == [1] * TICKS, "the export must run on a leased connection"
    _assert_no_leak_accumulated(service_pool)
    assert service_pool.acquisitions == TICKS


async def test_create_backup_returns_the_lease_when_the_export_is_cancelled(
    service_pool: ServicePoolDouble,
    settings: BackupSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cancellation is the path that would otherwise leak silently.

    A worker shutdown, a request that goes away or a task-group teardown cancels
    the export mid-flight. The ``async with`` unwinds on ``CancelledError``, so the
    connection is returned and the pool survives the cancellation.
    """
    entered = asyncio.Event()

    async def _export(*args: Any, **kwargs: Any) -> ExportResult:
        entered.set()
        await asyncio.Event().wait()  # hold the lease until the task is cancelled
        raise AssertionError("unreachable: the export should have been cancelled")

    monkeypatch.setattr("backup.service.export_schemas", _export)
    service = BackupService(settings, object_store=InMemoryObjectStore())

    for attempt in range(TICKS):
        task = asyncio.create_task(
            service.create_backup(requested_by="b7@example.test")
        )
        await entered.wait()
        entered.clear()
        assert service_pool.leases == 1, "the export never took a lease"
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        _assert_pool_whole(service_pool, f"attempt {attempt}: cancelled export")

    _assert_no_leak_accumulated(service_pool)
    assert service_pool.acquisitions == TICKS


# ---------------------------------------------------------------------------
# B7 must not break injected factories (unit doubles, integration suites, drill)
# ---------------------------------------------------------------------------


async def test_injected_bare_connection_keeps_its_own_lifecycle() -> None:
    """A factory that returns a *connection* is still yielded unchanged.

    The existing unit doubles, the loopback integration suites and the recovery
    drill inject a ready connection and own it themselves, so the store must never
    release a connection it did not acquire.
    """
    connection = PooledConnection(ServicePoolDouble())
    calls = 0

    async def _factory() -> PooledConnection:
        nonlocal calls
        calls += 1
        return connection

    store = BackupJobStore(connection_factory=_factory)

    assert await store.list_recent(limit=1) == []
    assert await store.get(JOB_ID) is None
    assert calls == 2, "the injected factory must be called once per statement"
    assert connection.released is False, "the injector still owns the connection"


async def test_injected_acquire_context_is_entered_and_released(
    service_pool: ServicePoolDouble,
) -> None:
    """A factory returning an acquire context has it entered *and* exited.

    This is the shape the recovery drill and any future caller should use: hand the
    store ``pool.acquire()`` and the connection is returned on the way out.
    """

    async def _factory() -> Any:
        return service_pool.acquire()

    store = BackupJobStore(connection_factory=_factory)

    for attempt in range(TICKS):
        assert await store.list_recent(limit=1) == []
        _assert_pool_whole(service_pool, f"attempt {attempt}: injected context")

    _assert_no_leak_accumulated(service_pool)
    assert service_pool.acquisitions == TICKS


# ---------------------------------------------------------------------------
# B7 clause 2 (FINAL-03 gate P1) — an undeployed BACKUP schema is terminal
# ---------------------------------------------------------------------------


class UndefinedTableError(Exception):
    """Stands in for ``asyncpg.exceptions.UndefinedTableError`` (SQLSTATE 42P01)."""

    sqlstate = "42P01"


class SchemaPendingStore:
    """A ``BackupJobStore`` whose statements meet an absent BACKUP schema.

    ``release_stale`` is the statement the 2026-10-02 rehearsal actually failed on
    (FINAL-02 §15.2 traceback), so that is where this double fails too. ``broken``
    models an operator applying the two BACKUP migrations while the process runs.
    """

    def __init__(self) -> None:
        self.broken = True
        self.release_stale_calls = 0
        self.claim_next_calls = 0

    async def release_stale(self, *, stale_after_seconds: int) -> int:
        self.release_stale_calls += 1
        if self.broken:
            raise UndefinedTableError('relation "public.backup_jobs" does not exist')
        return 0

    async def mark_expired(self, *, now: Any = None) -> int:
        return 0

    async def claim_next(self, **kwargs: Any) -> Any:
        self.claim_next_calls += 1
        return None


#: Poll interval / missing-table backoff for the loop tests below. Their ratio is
#: the point: a call count can tell the two cadences apart without depending on
#: wall-clock precision.
POLL_SECONDS = 0.01
BACKOFF_SECONDS = 0.08


def _messages(caplog: pytest.LogCaptureFixture, needle: str) -> list[str]:
    """Every captured log message containing ``needle``."""
    return [
        record.getMessage()
        for record in caplog.records
        if needle in record.getMessage()
    ]


def test_is_missing_backup_table_matches_only_backup_relations() -> None:
    """SQLSTATE 42P01 on a ``backup_*`` relation counts; nothing else does."""
    assert is_missing_backup_table(
        UndefinedTableError('relation "public.backup_jobs" does not exist')
    )
    assert is_missing_backup_table(
        UndefinedTableError('relation "public.backup_sets" does not exist')
    )
    assert not is_missing_backup_table(
        UndefinedTableError('relation "public.emissions" does not exist')
    )
    assert not is_missing_backup_table(RuntimeError("connection refused"))
    assert not is_missing_backup_table(
        ValueError('relation "public.backup_jobs" does not exist')
    )


def test_asyncpg_undefined_table_error_is_recognised() -> None:
    """The real driver exception carries SQLSTATE 42P01 — what the check matches."""
    asyncpg = pytest.importorskip("asyncpg")
    error = asyncpg.exceptions.UndefinedTableError(
        'relation "public.backup_jobs" does not exist'
    )
    assert getattr(error, "sqlstate", None) == "42P01"
    assert is_missing_backup_table(error)


async def test_missing_backup_schema_is_reported_once_and_backed_off(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """One report, then re-checks on the backoff — never a traceback per tick.

    The pre-fix loop logged ``backup worker tick failed`` every tick, each with an
    undeployed-table traceback (FINAL-02 §15.2 measured exactly that). This asserts
    the opposite: a single report, no per-tick failure records, and an attempt
    cadence that cannot be the poll interval.
    """
    store = SchemaPendingStore()
    worker = BackupWorker(
        job_store=store,
        object_store=InMemoryObjectStore(),
        poll_interval_seconds=POLL_SECONDS,
        missing_table_backoff_seconds=BACKOFF_SECONDS,
    )

    with caplog.at_level(logging.ERROR, logger="backup.worker"):
        await worker.start()
        await asyncio.sleep(0.4)
        await worker.stop()

    assert len(_messages(caplog, "backup tables are absent")) == 1
    assert _messages(caplog, "backup worker tick failed") == []
    assert store.release_stale_calls >= 3, "the loop stopped re-checking"
    assert store.release_stale_calls < 0.4 / POLL_SECONDS / 2, (
        "attempts were spaced by the poll interval, not the backoff"
    )
    assert worker.is_running is False


async def test_report_is_re_armed_once_a_tick_succeeds(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A tick that succeeds re-arms the one-shot report for a later failure.

    The migrations are applied (the store stops failing): the loop must return to the
    poll interval and drain the queue again. A later regression — a rolled-back
    migration, say — is then reported afresh instead of being swallowed by the flag.
    """
    store = SchemaPendingStore()
    worker = BackupWorker(
        job_store=store,
        object_store=InMemoryObjectStore(),
        poll_interval_seconds=POLL_SECONDS,
        missing_table_backoff_seconds=BACKOFF_SECONDS,
    )

    with caplog.at_level(logging.ERROR, logger="backup.worker"):
        await worker.start()
        await asyncio.sleep(0.2)  # absent schema: reported once, then backed off
        store.broken = False  # the two BACKUP migrations are applied
        await asyncio.sleep(0.2)  # a tick succeeds: the queue is drained again
        store.broken = True  # a later schema regression
        await asyncio.sleep(0.3)
        await worker.stop()

    assert len(_messages(caplog, "backup tables are absent")) == 2
    assert store.claim_next_calls >= 1, "a successful tick must drain the queue"
    assert worker.is_running is False





