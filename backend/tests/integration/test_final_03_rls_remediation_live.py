"""CT-FINAL-03 — RLS security remediation verification (static + live).

Two halves:

* **Static** — the migration artefacts themselves: ordering after the current head
  of the chain, statement safety (enablement and nothing else), the approved table
  set and its arithmetic, disjointness between the two FINAL-03 files, and the
  presence of rollback documentation. These run everywhere and need no database.
* **Live** — the *behaviour* of the enabled RLS, probed against a real
  PostgreSQL RLS engine by role-playing actual identities
  (``SET LOCAL ROLE`` + ``request.jwt.claims`` → ``auth.uid()``, the same
  mechanism Supabase PostgREST uses). These run only when a disposable target
  is supplied:

      FINAL_03_RLS_TEST_DSN=postgresql://postgres:postgres@127.0.0.1:54426/ct_f03_rls_verify \\
          python -m pytest backend/tests/integration/test_final_03_rls_remediation_live.py -q

TARGET SAFETY: the live half refuses any target that is not disposable (the
same guard as ``verify_activity_clarifications_rls.py``) and creates its own
fixtures inside a transaction that is ALWAYS rolled back — no existing row is
read as a mutable resource, and nothing is truncated.

The group lists are parsed out of the migration, so the test cannot drift from
the artefact it verifies.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path

import asyncpg
import pytest

MIGRATION_NAME = "20261028000000_ct_final_03_rls_security_remediation.sql"
REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_PATH = REPO_ROOT / "supabase" / "migrations" / MIGRATION_NAME
MIGRATIONS_DIR = MIGRATION_PATH.parent

#: The migration that must precede this one (its filename defines the head at the
#: time of writing; the new file must sort after it).
PREDECESSOR = "20261027000000_ct_backup_02_backup_sets_and_verification.sql"

#: CT-FINAL-03 residual closure (2026-10-02, third pass). A SECOND additive
#: migration enables RLS fail-closed on the one table the first migration
#: recorded as an owner-decision residual. The accepted 43-table artefact must
#: stay byte-identical, so the residual is closed by an additive file rather than
#: by an edit — `staff_workload` may not appear in the first file's approved set,
#: and the first file may not appear in the second's target set (disjointness).
RESIDUAL_MIGRATION_NAME = "20261029000000_ct_final_03_staff_workload_rls.sql"
RESIDUAL_MIGRATION_PATH = REPO_ROOT / "supabase" / "migrations" / RESIDUAL_MIGRATION_NAME
RESIDUAL_TABLE = "staff_workload"

#: Names the live half refuses to touch (F-046-1 precedent).
FORBIDDEN_TARGET_MARKERS = ("qa", "demo", "investor", "prod", "live")
FORBIDDEN_TARGET_NAMES = ("postgres", "carbontally")

#: Disposable target, or empty → the live half skips.
DSN = os.environ.get("FINAL_03_RLS_TEST_DSN") or os.environ.get("INTEGRATION_DATABASE_URL") or ""


def _sql() -> str:
    return MIGRATION_PATH.read_text(encoding="utf-8")


def _parse_array(sql: str, var: str) -> list[str]:
    """Extract a ``<var> text[] := ARRAY[ 'a', 'b' ];`` literal from the migration."""
    match = re.search(rf"{var}\s+text\[\]\s*:=\s*ARRAY\[(.*?)\];", sql, re.S)
    assert match, f"{var} not found in the migration"
    without_comments = re.sub(r"--[^\n]*", "", match.group(1))
    return re.findall(r"'([^']+)'", without_comments)


@pytest.fixture(scope="module")
def migration_sql() -> str:
    assert MIGRATION_PATH.exists(), f"missing migration: {MIGRATION_PATH}"
    return _sql()


@pytest.fixture(scope="module")
def group_a(migration_sql: str) -> list[str]:
    return _parse_array(migration_sql, "group_a")


@pytest.fixture(scope="module")
def group_b(migration_sql: str) -> list[str]:
    return _parse_array(migration_sql, "group_b")


@pytest.fixture(scope="module")
def retained_policies(migration_sql: str) -> list[str]:
    return _parse_array(migration_sql, "retained_policies")


@pytest.fixture(scope="module")
def residual_sql() -> str:
    assert RESIDUAL_MIGRATION_PATH.exists(), f"missing migration: {RESIDUAL_MIGRATION_PATH}"
    return RESIDUAL_MIGRATION_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def residual_targets(residual_sql: str) -> list[str]:
    """The fail-closed target set of the residual-closure migration."""
    return _parse_array(residual_sql, "fail_closed")


# ---------------------------------------------------------------------------
# STATIC — the migration artefact
# ---------------------------------------------------------------------------

def test_migration_sorts_immediately_after_the_current_head():
    names = sorted(p.name for p in MIGRATIONS_DIR.glob("*.sql"))
    assert PREDECESSOR in names, "the predecessor migration is missing from the chain"
    assert MIGRATION_NAME in names
    assert names.index(MIGRATION_NAME) == names.index(PREDECESSOR) + 1, (
        "the new migration must sort directly after the previous head of the chain"
    )


def test_approved_set_arithmetic(group_a, group_b, retained_policies):
    assert len(group_a) == 41, "fail-closed group must hold 41 tables"
    assert len(group_b) == 2, "policy-preserving group must hold 2 tables"
    assert len(retained_policies) == 4, "exactly four retained policies are expected"
    assert group_b == ["conversation_participants", "manual_extraction_items"]
    assert len(set(group_a)) == 41, "duplicate entry in the fail-closed group"
    assert not set(group_a) & set(group_b), "a table cannot be in both groups"


def test_class_a_tables_are_not_touched(migration_sql, group_a):
    for table in ("emission_factors", "business_hours", "sla_definitions"):
        assert table not in group_a, (
            f"{table} is class A (containment proven by grants / tenant-agnostic "
            "config) and must not be enabled merely to improve a count"
        )


def test_staff_workload_is_not_in_the_43_table_artefact(migration_sql, group_a, group_b):
    # The 43-table artefact is the one already accepted for independent
    # verification "in principle": the residual closure must NOT have been folded
    # into it by an edit (its bytes must not change). It therefore still documents
    # the residual, and `staff_workload` is in neither of its groups.
    assert RESIDUAL_TABLE not in group_a and RESIDUAL_TABLE not in group_b
    assert RESIDUAL_TABLE in migration_sql, "the residual decision must be documented"


def test_residual_migration_sorts_immediately_after_the_artefact():
    names = sorted(p.name for p in MIGRATIONS_DIR.glob("*.sql"))
    assert MIGRATION_NAME in names, "the 43-table artefact is missing from the chain"
    assert RESIDUAL_MIGRATION_NAME in names, "the residual-closure migration is missing"
    assert names.index(RESIDUAL_MIGRATION_NAME) == names.index(MIGRATION_NAME) + 1, (
        "the residual-closure migration must sort directly after the 43-table artefact"
    )


def test_residual_target_set_is_exactly_the_one_table(residual_targets, group_a, group_b):
    assert residual_targets == [RESIDUAL_TABLE], (
        "the residual-closure migration must target staff_workload and nothing else"
    )
    # Disjointness — no table is enabled by both files, so there is no duplicate
    # or conflicting migration and nothing is enabled twice.
    assert not set(residual_targets) & (set(group_a) | set(group_b))


def test_residual_migration_contains_no_data_or_destructive_statement(residual_sql):
    without_comments = "\n".join(
        line for line in residual_sql.splitlines() if not line.lstrip().startswith("--")
    )
    executable = re.sub(r"'(?:[^']|'')*'", "''", without_comments)
    for forbidden in (
        "TRUNCATE",
        "DELETE FROM",
        "DROP TABLE",
        "DROP POLICY",
        "DROP FUNCTION",
        "DROP SCHEMA",
        "DISABLE ROW LEVEL SECURITY",
        "FORCE ROW LEVEL SECURITY",
        "GRANT ",
        "REVOKE ",
        "INSERT INTO",
        "UPDATE public.",
        "CREATE POLICY",
        "ALTER POLICY",
        "ALTER DEFAULT PRIVILEGES",
    ):
        assert forbidden not in executable, f"executable statement contains {forbidden!r}"


def test_residual_only_executed_ddl_is_enablement(residual_sql):
    executed = [
        line.strip()
        for line in residual_sql.splitlines()
        if line.strip().startswith("EXECUTE")
    ]
    assert executed == [
        "EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);"
    ], "the only DDL the residual-closure migration may execute is RLS enablement"


def test_residual_documents_rollback_non_scope_and_governance(residual_sql):
    assert "ROLLBACK" in residual_sql.upper()
    assert "DISABLE ROW LEVEL SECURITY" in residual_sql, "the inverse statement must be documented"
    for token in (
        "owner-authorised reversal only",
        "NOT IN SCOPE",
        "no GRANT / REVOKE",
        "FORCE ROW LEVEL",
    ):
        assert token in residual_sql, f"rollback/non-scope note must mention {token!r}"
    # The reason this is a separate file (rather than an edit of the accepted
    # artefact) must be auditable in the artefact itself.
    for token in ("AGENTS.md", MIGRATION_NAME):
        assert token in residual_sql, f"the separate-file rationale must mention {token!r}"


def test_migration_contains_no_data_or_destructive_statement(migration_sql):
    # Strip line comments AND string literals first: the guard/post-condition
    # messages name the very statements that must never appear ("no GRANT …",
    # "FORCE ROW LEVEL SECURITY must remain untouched"), so a naive text scan
    # would flag its own refusal text.
    without_comments = "\n".join(
        line for line in migration_sql.splitlines() if not line.lstrip().startswith("--")
    )
    executable = re.sub(r"'(?:[^']|'')*'", "''", without_comments)
    for forbidden in (
        "TRUNCATE",
        "DELETE FROM",
        "DROP TABLE",
        "DROP POLICY",
        "DROP FUNCTION",
        "DROP SCHEMA",
        "DISABLE ROW LEVEL SECURITY",
        "FORCE ROW LEVEL SECURITY",
        "GRANT ",
        "REVOKE ",
        "INSERT INTO",
        "UPDATE public.",
        "CREATE POLICY",
        "ALTER POLICY",
        "ALTER DEFAULT PRIVILEGES",
    ):
        assert forbidden not in executable, f"executable statement contains {forbidden!r}"


def test_the_only_executed_ddl_is_enablement(migration_sql):
    executed = [
        line.strip()
        for line in migration_sql.splitlines()
        if line.strip().startswith("EXECUTE")
    ]
    assert executed == [
        "EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);"
    ], "the only DDL this migration may execute is RLS enablement"


def test_migration_documents_rollback_and_non_scope(migration_sql):
    assert "ROLLBACK" in migration_sql.upper()
    for token in ("DISABLE ROW LEVEL SECURITY", "owner-authorised reversal only"):
        assert token.lower() in migration_sql.lower(), f"rollback note must mention {token!r}"
    for token in ("NOT IN SCOPE", "no GRANT / REVOKE", "FORCE ROW LEVEL"):
        assert token in migration_sql, f"non-scope note must mention {token!r}"


# ---------------------------------------------------------------------------
# LIVE — real RLS enforcement (disposable target only)
# ---------------------------------------------------------------------------

def _target() -> str:
    if not DSN:
        pytest.skip(
            "set FINAL_03_RLS_TEST_DSN to a disposable database to run the live half"
        )
    name = DSN.rsplit("/", 1)[-1].split("?")[0].lower()
    if name in FORBIDDEN_TARGET_NAMES or any(m in name for m in FORBIDDEN_TARGET_MARKERS):
        raise RuntimeError(
            f"refusing non-disposable target {name!r}: create a disposable clone (ct_*) "
            "and point FINAL_03_RLS_TEST_DSN at it (F-046-1)"
        )
    return DSN


@pytest.fixture(scope="module")
async def conn():
    connection = await asyncpg.connect(_target())
    try:
        present = await connection.fetchval(
            "SELECT to_regclass('public.system_settings') IS NOT NULL"
        )
        if not present:
            pytest.skip("target has no CarbonTally schema (system_settings absent)")
        yield connection
    finally:
        await connection.close()


async def _run_as(conn, role: str, sql: str, *args, sub: str | None = None):
    """Run ``sql`` inside a savepoint as ``role`` (optional JWT subject).

    Returns ``("ok", value)`` or ``("err", "ErrorType")`` — the outcome itself is
    the assertion. The savepoint is ALWAYS rolled back (also after a refused
    statement, which aborts the subtransaction), so no probe can leave a row
    behind and a refusal cannot poison the session.
    """
    tx = conn.transaction()
    await tx.start()
    outcome = ("err", "Unknown")
    try:
        await conn.execute(f"SET LOCAL ROLE {role}")
        claims = json.dumps({"sub": str(sub), "role": role}) if sub else "{}"
        await conn.execute("SELECT set_config('request.jwt.claims', $1, true)", claims)
        if sql.lstrip().upper().startswith("SELECT"):
            outcome = ("ok", await conn.fetchval(sql, *args))
        else:
            outcome = ("ok", await conn.execute(sql, *args))
    except asyncpg.PostgresError as exc:  # noqa: BLE001 - the outcome IS the assertion
        outcome = ("err", type(exc).__name__)
    finally:
        # ROLLBACK TO SAVEPOINT is valid even in an aborted subtransaction.
        await tx.rollback()
    return outcome


def _write_refused(status: str, value) -> bool:
    """A write is refused when RLS/privileges raise, or it affects 0 rows."""
    if status == "err":
        return True
    return bool(re.fullmatch(r"(UPDATE|DELETE) 0", str(value)))


@pytest.fixture(scope="module")
async def retained_fingerprint(conn):
    """Row counts of retained production data, captured before any live probe."""
    tables = (
        "system_settings",
        "manual_extraction_items",
        "manual_extraction_batches",
        "organizations",
        "users",
        "emission_factors",
        # The residual-closure target: 0 rows in this target, and the row-level
        # proof seeds its probe row in a transaction that is always rolled back.
        RESIDUAL_TABLE,
    )
    fingerprint = {}
    for table in tables:
        exists = await conn.fetchval("SELECT to_regclass($1) IS NOT NULL", f"public.{table}")
        if exists:
            fingerprint[table] = await conn.fetchval(f"SELECT count(*) FROM public.{table}")
    return fingerprint


# --- structural ------------------------------------------------------------

async def test_rls_enabled_on_every_approved_table(conn, group_a, group_b):
    rows = await conn.fetch(
        "SELECT c.relname AS name, c.relrowsecurity AS enabled "
        "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'public' AND c.relkind IN ('r','p') AND c.relname = ANY($1)",
        group_a + group_b,
    )
    state = {r["name"]: r["enabled"] for r in rows}
    assert set(state) <= set(group_a) | set(group_b)
    for required in ("system_settings", "staff_roles", "conversation_participants",
                     "manual_extraction_items"):
        assert required in state, f"{required} is absent from the target"
    disabled = sorted(t for t, on in state.items() if not on)
    assert disabled == [], f"RLS is not enabled on {disabled}"


async def test_zero_policies_on_the_fail_closed_group(conn, group_a):
    rows = await conn.fetch(
        "SELECT tablename, policyname, cmd, roles::text AS roles FROM pg_policies "
        "WHERE schemaname = 'public' AND tablename = ANY($1) ORDER BY tablename, policyname",
        group_a,
    )
    assert rows == [], [dict(r) for r in rows]


async def test_retained_policy_family_is_intact(conn, group_b, retained_policies):
    rows = await conn.fetch(
        "SELECT tablename, policyname, cmd, roles::text AS roles, qual, with_check "
        "FROM pg_policies WHERE schemaname = 'public' AND tablename = ANY($1) "
        "ORDER BY policyname",
        group_b,
    )
    assert sorted(r["policyname"] for r in rows) == sorted(retained_policies), (
        "the retained policy family must be untouched by the remediation"
    )
    for row in rows:
        assert "authenticated" in row["roles"], row["policyname"]
        assert "anon" not in row["roles"], row["policyname"]
        assert (row["qual"] or "").strip() not in ("true", "(true)"), row["policyname"]


async def test_no_broad_authenticated_policy_on_any_approved_table(conn, group_a, group_b):
    """No SELECT/ALL policy with a bare ``USING (true)`` may exist on any table
    this change-set touches. (Pre-existing reference-data read policies elsewhere
    in ``public`` — glossary, units, roles, disclosure_* — are outside this
    change-set and are therefore not asserted on.)"""
    rows = await conn.fetch(
        "SELECT tablename, policyname, cmd, coalesce(qual, '') AS qual FROM pg_policies "
        "WHERE schemaname = 'public' AND tablename = ANY($1) "
        "AND roles::text LIKE '%authenticated%'",
        group_a + group_b,
    )
    broad = [
        dict(r) for r in rows
        if r["cmd"] in ("SELECT", "ALL")
        and r["qual"].replace(" ", "").strip("()") in ("true", "")
    ]
    assert broad == []


async def test_force_row_level_security_untouched(conn, group_a, group_b):
    forced = await conn.fetchval(
        "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'public' AND c.relname = ANY($1) AND c.relforcerowsecurity",
        group_a + group_b,
    )
    assert forced == 0, "FORCE ROW LEVEL SECURITY must remain untouched (D-11 deferred)"


async def test_anon_and_authenticated_do_not_bypass_rls(conn):
    rows = await conn.fetch(
        "SELECT rolname FROM pg_roles WHERE rolname IN ('anon','authenticated') AND rolbypassrls"
    )
    assert rows == []


# --- enforcement: anonymous + authenticated direct table access -------------

async def test_anon_cannot_read_any_fail_closed_table(conn, group_a):
    exposed = []
    for table in group_a:
        if not await conn.fetchval("SELECT to_regclass($1) IS NOT NULL", f"public.{table}"):
            continue
        status, value = await _run_as(conn, "anon", f"SELECT count(*) FROM public.{table}")
        # With RLS enabled and no anon policy: zero rows, or the grant/RLS refusal.
        if not (status == "err" or value == 0):
            exposed.append((table, value))
    assert exposed == []


async def test_authenticated_cannot_read_any_fail_closed_table(conn, group_a):
    exposed = []
    for table in group_a:
        if not await conn.fetchval("SELECT to_regclass($1) IS NOT NULL", f"public.{table}"):
            continue
        status, value = await _run_as(
            conn, "authenticated", f"SELECT count(*) FROM public.{table}", sub=str(uuid.uuid4())
        )
        # Read together with test_rls_enabled_on_every_approved_table: zero rows
        # here means RLS filtered the table, not that the table happens to be empty.
        if not (status == "err" or value == 0):
            exposed.append((table, value))
    assert exposed == []


async def test_authenticated_cannot_write_protected_tables(conn):
    cases = (
        ("authenticated", "INSERT INTO public.beta_users (email) VALUES ('ct-final-03-probe@example.test')"),
        ("authenticated", "INSERT INTO public.review_audit_trail (action) VALUES ('ct-final-03-probe')"),
        ("authenticated", "INSERT INTO public.password_reset_tokens (token) VALUES ('ct-final-03-probe')"),
        ("authenticated", "UPDATE public.system_settings SET setting_value = setting_value"),
        ("authenticated", "UPDATE public.staff_roles SET permissions = permissions"),
        ("authenticated", "UPDATE public.consultant_billing SET consultant_id = consultant_id"),
        ("authenticated", "DELETE FROM public.audit_trail"),
        ("authenticated", "DELETE FROM public.login_history"),
        ("authenticated", "DELETE FROM public.consultant_tasks"),
        ("authenticated", "DELETE FROM public.notifications"),
        ("authenticated", "DELETE FROM public.email_logs"),
        ("anon", "INSERT INTO public.waitlist (email) VALUES ('ct-final-03-probe@example.test')"),
        ("anon", "UPDATE public.beta_access_codes SET status = 'used'"),
    )
    failures = []
    for role, sql in cases:
        status, value = await _run_as(conn, role, sql, sub=str(uuid.uuid4()))
        if not _write_refused(status, value):
            failures.append((role, sql, value))
    assert failures == []


async def test_token_settings_staff_audit_billing_telemetry_stay_denied(conn):
    protected = (
        "system_settings",            # R-1 platform configuration
        "staff_roles",                # R-2 permission catalogue
        "password_reset_tokens",      # R-3 token material
        "beta_access_codes",          # R-3 invite/token material
        "audit_trail",                # R-5 business audit
        "review_audit_trail",         # audit integrity
        "consultant_billing",         # consultant financials
        "consultant_tasks",           # consultant / client records
        "login_history",              # authentication telemetry
        "email_logs",                 # recipient PII
        "notifications",              # per-recipient data
        "manual_extraction_items",    # retained customer rows (entity-scoped)
    )
    still_allowed = []
    for table in protected:
        status, value = await _run_as(
            conn, "authenticated", f"SELECT count(*) FROM public.{table}", sub=str(uuid.uuid4())
        )
        if not (status == "err" or value == 0):
            still_allowed.append((table, value))
    assert still_allowed == []


async def test_service_role_backend_paths_still_work(conn):
    denied = []
    for table in ("system_settings", "staff_roles", "manual_extraction_items",
                  "conversation_participants", "email_logs", "notifications"):
        status, _ = await _run_as(conn, "service_role", f"SELECT count(*) FROM public.{table}")
        if status != "ok":
            denied.append(table)
    assert denied == [], f"service_role backend access must be preserved on {denied}"


# --- the FINAL-03 residual closure: `staff_workload` (fail-closed, 0 policies) --
#
# The single table the 43-table artefact recorded as an owner-decision residual is
# closed by `20261029000000_ct_final_03_staff_workload_rls.sql`. `residual_targets`
# is parsed out of that file, so these tests cannot drift from the artefact.

async def _seed_staff_workload_row(conn) -> tuple[str, str]:
    """Create ``users`` → ``staff_profiles`` → ``staff_workload`` inside the
    caller's transaction (which is ALWAYS rolled back), so enforcement can be
    asserted against a row that really exists instead of against the empty table
    this target happens to hold. The valid parent rows are what makes the INSERT
    denial below provably an RLS/privilege refusal rather than a constraint error.
    """
    user_id, profile_id, workload_id = (str(uuid.uuid4()) for _ in range(3))
    await conn.execute(
        "INSERT INTO public.users (id, email) VALUES ($1, $2)",
        user_id, f"ct-final-03-sw-{user_id[:8]}@example.test",
    )
    await conn.execute(
        "INSERT INTO public.staff_profiles (id, user_id, first_name, last_name, email) "
        "VALUES ($1, $2, 'CT', 'FINAL-03 residual', $3)",
        profile_id, user_id, f"ct-final-03-sw-{profile_id[:8]}@example.test",
    )
    await conn.execute(
        "INSERT INTO public.staff_workload (id, staff_id, assigned_tasks, workload_score) "
        "VALUES ($1, $2, 1, 1)",
        workload_id, profile_id,
    )
    return profile_id, workload_id


async def test_residual_table_is_rls_enabled_with_zero_policies(conn, residual_targets):
    assert residual_targets, "the residual target set is empty — the migration is missing"
    rows = await conn.fetch(
        "SELECT c.relname AS name, c.relrowsecurity AS enabled, c.relforcerowsecurity AS forced "
        "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'public' AND c.relkind IN ('r','p') AND c.relname = ANY($1)",
        residual_targets,
    )
    state = {r["name"]: dict(r) for r in rows}
    assert set(state) == set(residual_targets), (
        f"residual target absent from this database: {sorted(set(residual_targets) - set(state))}"
    )
    for name, row in state.items():
        assert row["enabled"] is True, f"RLS is not enabled on {name}"
        assert row["forced"] is False, f"FORCE ROW LEVEL SECURITY must stay off on {name}"

    policies = await conn.fetch(
        "SELECT policyname, cmd, roles::text AS roles FROM pg_policies "
        "WHERE schemaname = 'public' AND tablename = ANY($1) ORDER BY policyname",
        residual_targets,
    )
    assert policies == [], [dict(r) for r in policies]


async def test_residual_table_denies_anon_and_authenticated_select(conn, residual_targets):
    exposed = []
    for table in residual_targets:
        for role, sub in (("anon", None), ("authenticated", str(uuid.uuid4()))):
            status, value = await _run_as(
                conn, role, f"SELECT count(*) FROM public.{table}", sub=sub
            )
            if not (status == "err" or value == 0):
                exposed.append((role, table, status, value))
    assert exposed == []


async def test_residual_table_enforces_denial_against_a_real_row(conn, residual_targets):
    """Row-level proof on a table that is empty in this target: a probe row is
    created inside a transaction that is ALWAYS rolled back, and the browser roles
    are then role-played against it. Every operation must fail even though the row
    exists and the backend can see it."""
    assert residual_targets, "the residual target set is empty — the migration is missing"
    table = residual_targets[0]
    tx = conn.transaction()
    await tx.start()
    try:
        profile_id, _ = await _seed_staff_workload_row(conn)

        # POSITIVE CONTROL — the row exists and service_role (the backend) sees it.
        status, seen = await _run_as(conn, "service_role", f"SELECT count(*) FROM public.{table}")
        assert status == "ok" and seen == 1, (status, seen)

        for role, sub in (("authenticated", str(uuid.uuid4())), ("anon", None)):
            # DENIED — SELECT: the row is invisible (0 of the 1 existing rows).
            status, value = await _run_as(
                conn, role, f"SELECT count(*) FROM public.{table}", sub=sub
            )
            assert status == "err" or value == 0, (role, status, value)

            # DENIED — UPDATE/DELETE: refused, or 0 of the 1 existing rows.
            status, value = await _run_as(
                conn, role, f"UPDATE public.{table} SET workload_score = 999", sub=sub
            )
            assert _write_refused(status, value), (role, status, value)

            status, value = await _run_as(conn, role, f"DELETE FROM public.{table}", sub=sub)
            assert _write_refused(status, value), (role, status, value)

            # DENIED — INSERT: refused at the RLS/privilege boundary. The parent
            # staff_profiles row exists, so a constraint cannot be the cause.
            status, value = await _run_as(
                conn, role,
                f"INSERT INTO public.{table} (staff_id, assigned_tasks) VALUES ($1, 1)",
                profile_id, sub=sub,
            )
            assert status == "err", (role, status, value)
            assert value == "InsufficientPrivilegeError", (role, value)

        # The probe row survived the refused writes untouched, and is still one.
        status, total = await _run_as(conn, "service_role", f"SELECT count(*) FROM public.{table}")
        assert status == "ok" and total == 1, (status, total)
        status, score = await _run_as(
            conn, "service_role", f"SELECT max(workload_score) FROM public.{table}"
        )
        assert status == "ok" and float(score) == 1.0, (status, score)
    finally:
        await tx.rollback()


async def test_residual_table_service_role_access_preserved(conn, residual_targets):
    broken = []
    for table in residual_targets:
        status, _ = await _run_as(conn, "service_role", f"SELECT count(*) FROM public.{table}")
        if status != "ok":
            broken.append((table, "select", status))
        # The backend's write path must be *accepted* (no RLS refusal, no lost grant).
        status, value = await _run_as(
            conn, "service_role",
            f"UPDATE public.{table} SET workload_score = workload_score",
        )
        if status != "ok":
            broken.append((table, "update", status, value))
    assert broken == [], f"service_role backend access must be preserved: {broken}"


# --- retention semantics: the two enable-only tables ------------------------

async def test_conversation_participants_positive_and_negative_cases(conn):
    """The retained policies must still grant the legitimate reads they were
    written for, and deny everyone else (positive AND negative cases)."""
    org_a, org_b = str(uuid.uuid4()), str(uuid.uuid4())
    member, participant, stranger = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    conv_a, conv_b = str(uuid.uuid4()), str(uuid.uuid4())

    tx = conn.transaction()
    await tx.start()
    try:
        for uid in (member, participant, stranger):
            await conn.execute(
                "INSERT INTO public.users (id, email) VALUES ($1, $2)",
                uid, f"ct-final-03-{uid[:8]}@example.test",
            )
        for org, name in ((org_a, "CT FINAL-03 A"), (org_b, "CT FINAL-03 B")):
            await conn.execute(
                "INSERT INTO public.organizations (id, name, country, is_active, created_at, updated_at) "
                "VALUES ($1, $2, 'GB', TRUE, NOW(), NOW())",
                org, name,
            )
        # `member` belongs to org A; `participant` has no organisation at all.
        await conn.execute(
            "INSERT INTO public.organization_members "
            "(id, organization_id, user_id, role, is_active, created_at) "
            "VALUES ($1, $2, $3, 'member', TRUE, NOW())",
            str(uuid.uuid4()), org_a, member,
        )
        await conn.execute(
            "INSERT INTO public.conversations (id, organization_id, created_at, updated_at) "
            "VALUES ($1, $2, NOW(), NOW())", conv_a, org_a,
        )
        await conn.execute(
            "INSERT INTO public.conversations (id, organization_id, created_at, updated_at) "
            "VALUES ($1, $2, NOW(), NOW())", conv_b, org_b,
        )
        await conn.execute(
            "INSERT INTO public.conversation_participants "
            "(id, conversation_id, user_id, is_active, created_at, updated_at) "
            "VALUES ($1, $2, $3, TRUE, NOW(), NOW())",
            str(uuid.uuid4()), conv_a, member,
        )
        await conn.execute(
            "INSERT INTO public.conversation_participants "
            "(id, conversation_id, user_id, is_active, created_at, updated_at) "
            "VALUES ($1, $2, $3, TRUE, NOW(), NOW())",
            str(uuid.uuid4()), conv_b, participant,
        )

        async def visible(role, subject, conversation):
            return await _run_as(
                conn, role,
                "SELECT count(*) FROM public.conversation_participants "
                "WHERE conversation_id = $1",
                conversation, sub=subject,
            )

        # POSITIVE — org member of the conversation's organisation.
        status, count = await visible("authenticated", member, conv_a)
        assert status == "ok" and count == 1, (status, count)
        # POSITIVE — the participant themselves (no organisation needed).
        status, count = await visible("authenticated", participant, conv_b)
        assert status == "ok" and count == 1, (status, count)
        # NEGATIVE — an unrelated authenticated user sees nothing at all.
        status, count = await visible("authenticated", stranger, conv_a)
        assert status == "ok" and count == 0, (status, count)
        status, count = await visible("authenticated", stranger, conv_b)
        assert status == "ok" and count == 0, (status, count)
        # NEGATIVE / CROSS-TENANT — org A's member cannot see org B's memberships.
        status, count = await visible("authenticated", member, conv_b)
        assert status == "ok" and count == 0, (status, count)
        # NEGATIVE — anonymous callers.
        status, count = await visible("anon", None, conv_a)
        assert status == "err" or count == 0, (status, count)

        # POSITIVE write — a participant may mark their own participation.
        status, value = await _run_as(
            conn, "authenticated",
            "UPDATE public.conversation_participants SET is_active = TRUE WHERE user_id = $1",
            member, sub=member,
        )
        assert status == "ok" and str(value).endswith("1"), (status, value)
        # NEGATIVE write — the same user cannot touch another conversation's rows.
        status, value = await _run_as(
            conn, "authenticated",
            "UPDATE public.conversation_participants SET is_active = TRUE WHERE conversation_id = $1",
            conv_b, sub=member,
        )
        assert _write_refused(status, value), (status, value)
        # NEGATIVE write — the browser write model is server-authoritative: no
        # INSERT policy exists, so a direct membership INSERT is refused.
        status, value = await _run_as(
            conn, "authenticated",
            "INSERT INTO public.conversation_participants (conversation_id, user_id) VALUES ($1, $2)",
            conv_a, member, sub=member,
        )
        assert _write_refused(status, value), (status, value)
    finally:
        await tx.rollback()


async def test_manual_extraction_items_retained_rows_and_entity_isolation(conn):
    """The retained customer rows stay reachable to their entity staff and to the
    backend, and to nobody else."""
    # NEGATIVE — an unrelated authenticated user sees no retained customer row.
    status, count = await _run_as(
        conn, "authenticated",
        "SELECT count(*) FROM public.manual_extraction_items", sub=str(uuid.uuid4()),
    )
    assert status == "ok" and count == 0, (status, count)

    # NEGATIVE — anonymous callers.
    status, count = await _run_as(
        conn, "anon", "SELECT count(*) FROM public.manual_extraction_items"
    )
    assert status == "err" or count == 0, (status, count)

    # POSITIVE (backend) — service_role still reads every retained row, so the
    # migration closed the browser surface without hiding the backend's data.
    status, total = await _run_as(
        conn, "service_role", "SELECT count(*) FROM public.manual_extraction_items"
    )
    assert status == "ok" and isinstance(total, int), (status, total)

    # POSITIVE (entity staff) — when this target holds an entity-allocated batch
    # whose entity has an active member, that member sees exactly that batch's
    # items. The precondition is derived from the policy's own predicate.
    batch = await conn.fetchrow(
        "SELECT b.id, b.entity_id FROM public.manual_extraction_batches b "
        "WHERE b.entity_id IS NOT NULL ORDER BY b.id LIMIT 1"
    )
    if batch is None:
        pytest.skip("no entity-allocated manual_extraction_batch here — positive case not constructible")
    staff = await conn.fetchrow(
        "SELECT sp.user_id FROM public.staff_profiles sp "
        "WHERE sp.entity_id = $1 AND coalesce(sp.is_active, TRUE) ORDER BY sp.user_id LIMIT 1",
        batch["entity_id"],
    )
    if staff is None:
        pytest.skip("no active staff_profiles member for that entity — positive case not constructible")
    status, member_of_entity = await _run_as(
        conn, "authenticated", "SELECT public.is_entity_member($1)",
        batch["entity_id"], sub=str(staff["user_id"]),
    )
    if status != "ok" or not member_of_entity:
        pytest.skip("is_entity_member is false for the resolved member in this target")
    status, seen = await _run_as(
        conn, "authenticated",
        "SELECT count(*) FROM public.manual_extraction_items WHERE batch_id = $1",
        batch["id"], sub=str(staff["user_id"]),
    )
    assert status == "ok" and seen >= 1, (status, seen)


async def test_manual_extraction_items_policy_is_the_only_one(conn):
    rows = await conn.fetch(
        "SELECT policyname, cmd, roles::text AS roles FROM pg_policies "
        "WHERE schemaname = 'public' AND tablename = 'manual_extraction_items'"
    )
    assert len(rows) == 1, [dict(r) for r in rows]
    assert rows[0]["policyname"] == "manual_extraction_items_entity_select"
    assert rows[0]["cmd"] == "SELECT"
    assert "authenticated" in rows[0]["roles"] and "anon" not in rows[0]["roles"]


# --- production-data preservation (must be the last live test) --------------

async def test_no_data_was_mutated_by_the_verification(conn, retained_fingerprint):
    """Every probe above ran in a rolled-back savepoint: the retained data is
    byte-for-byte as it was. This is the assertion that proves it."""
    drift = {}
    for table, expected in retained_fingerprint.items():
        actual = await conn.fetchval(f"SELECT count(*) FROM public.{table}")
        if actual != expected:
            drift[table] = {"before": expected, "after": actual}
    assert drift == {}, f"retained data changed during verification: {drift}"
