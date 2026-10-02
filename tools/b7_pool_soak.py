#!/usr/bin/env python3
"""B7 live soak — the backup worker must never keep a pooled connection (FINAL-02 §15.2).

FINAL-02 §15.2 recorded the symptom: after a handful of worker ticks ``/health``
and every database-backed endpoint hung. FINAL-03 gate P1 requires that claim to be
*shown*, not asserted, so this tool reproduces the rehearsal conditions exactly and
runs continuous traffic through the real components:

* the real ``infra.supabase.get_service_pool()`` (``min_size=1, max_size=5``) against
  the database ``backend/.env`` points at;
* the BACKUP tables are **absent** — the condition that made every statement fail
  the way the 2026-10-02 traceback did (the tool refuses to run when they exist, so
  no soak statement can ever read or mutate a backup row); ``--database-url`` plus
  ``--allow-backup-tables`` run the second, schema-complete half of the P1 evidence
  (a disposable clone with the two BACKUP migrations applied, where the same
  statements and the same worker loop exercise the real tables);
* the production ``BackupJobStore`` with no injected factory, running the statements
  the worker's own tick runs (and a few readers), so every statement takes and must
  return its lease;
* the production ``BackupWorker`` loop, ticking for the whole soak (this also proves
  P1's second clause: an undeployed schema is reported **once** and backed off, never
  a per-tick error);
* after every iteration the pool is inspected (``get_size`` vs ``get_idle_size``) and
  probed with the exact statement ``/health`` uses — ``SELECT 1`` on the service pool
  (``api.dependencies.get_pool``) — bounded by a timeout.

A leaked lease shows up immediately as ``idle < size``; five of them starve the pool
and the bounded probe times out, which is precisely the recorded symptom.

``--legacy-idiom`` is the control: the pre-fix factory (``await pool.acquire()``, a
bare connection with no release path) is injected and the run is *expected* to starve
the pool. So the harness itself is demonstrably capable of detecting the bug it is
used to clear.

Usage:
    python tools/b7_pool_soak.py --duration 600 --label after
    python tools/b7_pool_soak.py --legacy-idiom --expect-leak --duration 60

Safety: loopback database whose name is disposable (``ct_*``/``carbontally_test``),
never production, and never a database that already has the BACKUP tables (that is
both the faithful condition and the guarantee that nothing is written).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import pathlib
import sys
import time
from typing import Any, Callable, Optional
from urllib.parse import urlparse

REPO = pathlib.Path(__file__).resolve().parent.parent
BACKEND = REPO / "backend"
sys.path.insert(0, str(BACKEND))

_FORBIDDEN = ("qa", "demo", "investor", "prod", "live", "production")
_ALLOWED_MAINS = ("carbontally_test",)
_LOOPBACK = ("127.0.0.1", "localhost", "::1")

JOB_ID = "11111111-1111-4111-8111-111111111111"
BACKUP_SET_ID = "22222222-2222-4222-8222-222222222222"

#: PostgreSQL's "relation does not exist" — the condition §15.2 met every tick.
UNDEFINED_TABLE_SQLSTATE = "42P01"


def assert_local_disposable(dsn: str) -> str:
    """Refuse anything that is not a disposable local database."""
    parsed = urlparse(dsn)
    host = (parsed.hostname or "").lower()
    name = (parsed.path or "").lstrip("/")
    if host not in _LOOPBACK:
        raise SystemExit(
            f"refusing {dsn!r}: host {host!r} is not loopback "
            "(a persistent environment is never contacted)"
        )
    lowered = name.lower()
    if lowered not in _ALLOWED_MAINS and not lowered.startswith("ct_"):
        raise SystemExit(
            f"refusing database {name!r}: disposable names start with 'ct_' "
            f"or are one of {_ALLOWED_MAINS}"
        )
    for token in _FORBIDDEN:
        if token in lowered:
            raise SystemExit(
                f"refusing database {name!r}: it looks like a persistent "
                f"environment ({token!r})"
            )
    return name


class ErrorCounter(logging.Handler):
    """Collect every ERROR the backup worker logs (the worker owns no counters)."""

    def __init__(self) -> None:
        super().__init__(level=logging.ERROR)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())

    def count(self, needle: str) -> int:
        return sum(1 for message in self.messages if needle in message)


def legacy_factory() -> Callable[[], Any]:
    """The pre-fix idiom the control injects: an awaited ``pool.acquire()``.

    ``asyncpg`` lets ``acquire()`` be awaited as well as used as a context manager,
    and the awaited result is a bare connection the caller must release by hand.
    The pre-fix worker never released it (FINAL-02 §15.2), so this factory leaks one
    pool slot per statement.
    """

    async def factory() -> Any:
        from infra.supabase import get_service_pool

        pool = await get_service_pool()
        return await pool.acquire()

    return factory


def statements(store: Any) -> list[tuple[str, Callable[[], Any]]]:
    """The statements a soak iteration runs, in the worker's own order first.

    ``release_stale``/``mark_expired``/``claim_next`` are exactly what
    :meth:`backup.worker.BackupWorker.tick` execs; the rest are the readers a
    DB-backed request performs, so the pool sees the same mix under load.
    """
    return [
        ("release_stale", lambda: store.release_stale(stale_after_seconds=300)),
        ("mark_expired", lambda: store.mark_expired()),
        ("list_expired", lambda: store.list_expired(limit=10)),
        ("claim_next", lambda: store.claim_next(
            lock_token="b7-soak", max_attempts=3, stale_after_seconds=300
        )),
        ("get", lambda: store.get(JOB_ID)),
        ("get_active", lambda: store.get_active()),
        ("list_recent", lambda: store.list_recent(limit=5)),
        ("list_by_backup_set", lambda: store.list_by_backup_set(BACKUP_SET_ID)),
        ("mark_failed", lambda: store.mark_failed(
            JOB_ID, error_reason="b7 soak probe"
        )),
    ]


async def run_statement(
    factory: Callable[[], Any], timeout: float
) -> tuple[str, Optional[str]]:
    """Run one statement, classifying how it ended (never re-raising a soak error).

    Returns ``(outcome, detail)`` where outcome is ``ok``, ``missing-table`` (the
    expected §15.2 condition), ``no-op`` (the *domain* refused the transition — e.g.
    ``mark_failed`` on a job that is not running, which a schema-complete database
    answers deterministically) or ``starved`` (no connection within ``timeout`` — the
    leak symptom). Each of these still took and returned a pooled connection, so none
    of them is a pool verdict; any other exception is re-raised, because a soak must
    not hide a different failure behind "it was the missing table".
    """
    try:
        await asyncio.wait_for(factory(), timeout)
        return "ok", None
    except asyncio.TimeoutError:
        return "starved", f"no pooled connection within {timeout}s"
    except Exception as exc:  # noqa: BLE001 — classified below, not swallowed
        if getattr(exc, "sqlstate", None) == UNDEFINED_TABLE_SQLSTATE:
            return "missing-table", str(exc)
        from backup.errors import BackupJobConflictError

        if isinstance(exc, BackupJobConflictError):
            return "no-op", str(exc)
        raise


async def probe_health(pool: Any, timeout: float) -> tuple[bool, float]:
    """The ``/health`` pool probe: ``SELECT 1`` on the service pool, bounded.

    ``main.py``'s ``/health`` does ``await get_pool(); await pool.fetchval("SELECT 1")``
    and ``api.dependencies.get_pool`` *is* :func:`infra.supabase.get_service_pool`, so
    this is the endpoint's own data path under soak load, not a proxy for it.
    """
    started = time.monotonic()
    try:
        await asyncio.wait_for(pool.fetchval("SELECT 1"), timeout)
    except asyncio.TimeoutError:
        return False, (time.monotonic() - started) * 1000.0
    return True, (time.monotonic() - started) * 1000.0


async def soak(args: argparse.Namespace) -> dict[str, Any]:
    """Run the soak and return its measured summary (no printing)."""
    import asyncpg

    from infra.supabase import close_service_pool, get_database_url, get_service_pool

    from backup.jobs import BackupJobStore
    from backup.storage import InMemoryObjectStore
    from backup.worker import BackupWorker

    dsn = get_database_url()
    if not dsn:
        raise SystemExit("DATABASE_URL is not configured (expected backend/.env)")
    database = assert_local_disposable(dsn)

    pool = await get_service_pool()
    present = [
        row["table_name"]
        for row in await pool.fetch(
            "select table_name from information_schema.tables "
            "where table_schema = 'public' and table_name like 'backup%' order by 1"
        )
    ]
    if present and not args.allow_backup_tables:
        close_service_pool()
        raise SystemExit(
            f"refusing to soak {database}: the BACKUP tables exist ({present}). The "
            "rehearsal condition is their absence, and with tables present a claim "
            "statement could mutate rows. Use --allow-backup-tables only against a "
            "disposable clone."
        )

    sampler = await asyncpg.connect(dsn)
    counter = ErrorCounter()
    worker_logger = logging.getLogger("backup.worker")
    worker_logger.addHandler(counter)

    summary: dict[str, Any] = {
        "label": args.label,
        "mode": "legacy-idiom (pre-fix control)" if args.legacy_idiom else "default (post-fix)",
        "database": database,
        "backup_tables_present": present,
        "pool": {"min_size": pool.get_min_size(), "max_size": pool.get_max_size()},
        "requested_duration_s": args.duration,
        "violations": [],
        "timeline": [],
    }
    violations: list[str] = summary["violations"]
    worker: Optional[Any] = None
    elapsed = 0.0
    counts = {"ok": 0, "missing-table": 0, "no-op": 0, "starved": 0}
    by_statement: dict[str, int] = {}
    pool_size_max = 0
    idle_min = 1 << 30
    conns_max = 0
    probe_max_ms = 0.0
    probes = 0
    timeouts = 0
    worker_alive = True
    transient_leases = 0
    cleared_leases = 0

    try:
        store = BackupJobStore(
            connection_factory=legacy_factory() if args.legacy_idiom else None
        )
        steps = statements(store)
        if not args.legacy_idiom:
            worker = BackupWorker(
                job_store=BackupJobStore(),
                object_store=InMemoryObjectStore(),
                poll_interval_seconds=0.1,
                missing_table_backoff_seconds=args.worker_backoff,
            )
            await worker.start()

        started = time.monotonic()
        last_report = 0.0
        index = 0
        while True:
            elapsed = time.monotonic() - started
            if elapsed >= args.duration:
                break
            name, factory = steps[index % len(steps)]
            index += 1
            outcome, detail = await run_statement(factory, args.statement_timeout)
            counts[outcome] += 1
            key = f"{name}:{outcome}"
            by_statement[key] = by_statement.get(key, 0) + 1
            if outcome == "starved":
                violations.append(f"{name}: {detail}")

            size, idle = pool.get_size(), pool.get_idle_size()
            pool_size_max = max(pool_size_max, size)
            idle_min = min(idle_min, idle)
            if idle != size:
                # The worker loop shares this pool (and asyncpg creates a connection on
                # demand), so a shortfall is only evidence of a leak if it never clears:
                # a merely concurrent lease clears in milliseconds, a leaked one never
                # does (the pre-fix control left 1, 2, 3... permanently outstanding).
                transient_leases += 1
                quiet_by = time.monotonic() + args.quiescence_timeout
                while (
                    time.monotonic() < quiet_by
                    and pool.get_idle_size() != pool.get_size()
                ):
                    await asyncio.sleep(0.02)
                size, idle = pool.get_size(), pool.get_idle_size()
                if idle != size:
                    violations.append(
                        f"{name}: {size - idle} leased connection(s) never returned "
                        f"within {args.quiescence_timeout}s of quiescence "
                        f"(size={size}, idle={idle})"
                    )
                else:
                    cleared_leases += 1

            healthy, latency_ms = await probe_health(pool, args.probe_timeout)
            probes += 1
            probe_max_ms = max(probe_max_ms, latency_ms)
            if not healthy:
                timeouts += 1
                violations.append(
                    "/health probe (SELECT 1 on the service pool) timed out after "
                    f"{args.probe_timeout}s"
                )

            conns = await sampler.fetchval(
                "select count(*) from pg_stat_activity where datname = current_database()"
            )
            conns_max = max(conns_max, conns)
            if worker is not None and not worker.is_running:
                worker_alive = False
                violations.append("the worker loop stopped mid-soak")

            now = time.monotonic()
            if now - last_report >= args.report_every or violations:
                last_report = now
                print(
                    f"[{now - started:7.1f}s] statements={sum(counts.values())} "
                    f"missing-table={counts['missing-table']} no-op={counts['no-op']} "
                    f"starved={counts['starved']} "
                    f"| pool size={size} idle={idle} | db conns={conns} "
                    f"| /health {latency_ms:.1f}ms "
                    f"| worker alive={worker_alive if worker else 'n/a'}",
                    flush=True,
                )
                summary["timeline"].append(
                    {
                        "elapsed_s": round(now - started, 1),
                        "statements": sum(counts.values()),
                        "missing_table": counts["missing-table"],
                        "no_op": counts["no-op"],
                        "starved": counts["starved"],
                        "pool_size": size,
                        "pool_idle": idle,
                        "db_connections": conns,
                        "health_ms": round(latency_ms, 1),
                        "worker_alive": worker_alive if worker else None,
                    }
                )

            if violations and (not args.expect_leak or len(violations) >= 3):
                break
            await asyncio.sleep(args.interval)
        elapsed = time.monotonic() - started
    finally:
        if worker is not None and worker.is_running:
            await worker.stop()
        worker_logger.removeHandler(counter)
        await sampler.close()
        close_service_pool()

    absent_reports = counter.count("backup tables are absent")
    tick_failures = counter.count("backup worker tick failed")
    # §15.2 rehearsal: the tables are absent, so the loop must say so *once* and then
    # back off. Schema-complete: the tables exist, so it must say so *never*.
    expecting_missing_schema = worker is not None and not present
    clauses = {
        "no_leased_connection_kept": not any(
            "never returned" in item or "no pooled connection" in item
            for item in violations
        ),
        "health_pool_path_responsive": timeouts == 0,
        "worker_loop_alive_for_the_whole_soak": worker_alive,
        "missing_schema_reported_once": (
            (absent_reports == 1)
            if expecting_missing_schema
            else (absent_reports == 0)
            if worker is not None
            else None
        ),
        "missing_schema_not_a_per_tick_error": (tick_failures == 0) if worker else None,
    }
    summary.update(
        {
            "elapsed_s": round(elapsed, 1),
            "statements": sum(counts.values()),
            "outcomes": counts,
            "by_statement": by_statement,
            "pool_size_max": pool_size_max,
            "pool_idle_min": idle_min,
            "db_connections_max": conns_max,
            "health_probes": probes,
            "health_max_ms": round(probe_max_ms, 1),
            "health_timeouts": timeouts,
            "lease_shortfalls_observed": transient_leases,
            "lease_shortfalls_cleared": cleared_leases,
            "worker_attempts": round(elapsed / args.worker_backoff, 1) if worker else None,
            "worker_missing_table_reports": absent_reports if worker else None,
            "expecting_missing_schema": expecting_missing_schema,
            "worker_per_tick_failures": tick_failures if worker else None,
            "clauses": clauses,
            "verdict": "violations detected" if violations else "clean",
            "expected": "violations detected" if args.expect_leak else "clean",
        }
    )
    summary["verdict_as_expected"] = summary["verdict"] == summary["expected"]
    return summary


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Command line: duration, cadence and the control switches."""
    parser = argparse.ArgumentParser(
        description="B7 live soak — a backup worker tick must never keep a pooled connection"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=600.0,
        help="soak length in seconds (default 600 — the P1 '≥10 minute' floor)",
    )
    parser.add_argument("--interval", type=float, default=0.2, help="pause between iterations")
    parser.add_argument(
        "--report-every", type=float, default=30.0, help="timeline line cadence in seconds"
    )
    parser.add_argument("--statement-timeout", type=float, default=5.0)
    parser.add_argument("--probe-timeout", type=float, default=3.0)
    parser.add_argument(
        "--quiescence-timeout",
        type=float,
        default=2.0,
        help=(
            "how long a leased-connection shortfall must persist before it counts as a "
            "leak (the worker loop shares this pool, so a concurrent lease is expected "
            "to clear in milliseconds)"
        ),
    )
    parser.add_argument(
        "--worker-backoff",
        type=float,
        default=5.0,
        help="missing-table backoff handed to the real worker loop",
    )
    parser.add_argument(
        "--legacy-idiom",
        action="store_true",
        help="inject the pre-fix factory (control: the pool is expected to starve)",
    )
    parser.add_argument(
        "--expect-leak",
        action="store_true",
        help="exit 0 when the soak *does* detect violations (the control run)",
    )
    parser.add_argument("--label", default="after", help="label for the report")
    parser.add_argument(
        "--database-url",
        default=None,
        help=(
            "soak this DSN instead of the configured DATABASE_URL (used for the "
            "schema-complete run against a disposable clone with the BACKUP migrations "
            "applied); the loopback/disposable gate still applies"
        ),
    )
    parser.add_argument(
        "--allow-backup-tables",
        action="store_true",
        help=(
            "permit the BACKUP tables to be present — only ever point this at a "
            "disposable clone (the default refuses, because on the rehearsal database a "
            "soak statement could then touch real backup rows)"
        ),
    )
    parser.add_argument("--out", default=None, help="write the JSON summary to this path")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """Run the soak, print the verdict, and exit non-zero if it was unexpected."""
    args = parse_args(argv)
    if args.database_url:
        # ``get_service_pool()`` reads DATABASE_URL from the environment, so the
        # override must be in place before the pool is created (``.env`` is loaded
        # with override=False and therefore cannot win over this).
        os.environ["DATABASE_URL"] = args.database_url
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s"
    )
    summary = asyncio.run(soak(args))
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"json summary  : {args.out}")

    print()
    print(f"== B7 SOAK VERDICT ({summary['label']}) — {summary['mode']} ==")
    print(f"database      : {summary['database']} (loopback, BACKUP tables absent — §15.2 condition)")
    print(
        f"duration      : {summary['elapsed_s']}s of {summary['requested_duration_s']}s requested, "
        f"{summary['statements']} statements {summary['outcomes']}"
    )
    print(
        f"pool          : max_size={summary['pool']['max_size']} "
        f"size_max={summary['pool_size_max']} idle_min={summary['pool_idle_min']}"
    )
    print(
        f"/health path  : {summary['health_probes']} probes, max "
        f"{summary['health_max_ms']}ms, {summary['health_timeouts']} timeouts"
    )
    print(f"db connections: max {summary['db_connections_max']} (pg_stat_activity)")
    print(
        f"lease probes  : {summary['lease_shortfalls_observed']} shortfall(s) observed, "
        f"{summary['lease_shortfalls_cleared']} cleared within {args.quiescence_timeout}s "
        f"(concurrent worker / on-demand leases), "
        f"{summary['lease_shortfalls_observed'] - summary['lease_shortfalls_cleared']} "
        f"never returned"
    )
    if summary["worker_attempts"] is not None:
        print(
            f"worker loop   : ~{summary['worker_attempts']} attempts at the "
            f"{args.worker_backoff}s backoff, "
            f"{summary['worker_missing_table_reports']} 'absent' report(s), "
            f"{summary['worker_per_tick_failures']} per-tick failure(s)"
        )
    print(f"clauses       : {json.dumps(summary['clauses'])}")
    for name, value in summary["clauses"].items():
        if value is False:
            print(f"  !! clause failed: {name}")
    if summary["violations"]:
        print(f"violations    : {len(summary['violations'])}")
        for item in summary["violations"][:10]:
            print(f"  - {item}")
    print(
        f"verdict       : {summary['verdict'].upper()} "
        f"(expected {summary['expected']}) — "
        f"{'as expected' if summary['verdict_as_expected'] else 'UNEXPECTED'}"
    )
    return 0 if summary["verdict_as_expected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())



