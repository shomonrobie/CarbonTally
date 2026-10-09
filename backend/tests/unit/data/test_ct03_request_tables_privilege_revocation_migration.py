"""CT-CONSULTANT-MODEL-IMPLEMENTATION-03 closure (F-1) — privilege-revocation
migration for the two CT03 request tables (structural tests, no DB).

Statically verifies the closure migration that brings
``public.consultant_relationship_requests`` and
``public.consultant_mode_change_requests`` to the posture the rest of the CT03
delta already measured (``anon``/``authenticated`` = no privileges,
``service_role`` = DML, RLS enabled with zero policies):

* the migration exists, sorts strictly after the migration that created the
  tables, and re-uses no historical timestamp;
* it is a REVOKE-only hardening of exactly two tables and two client roles —
  it grants nothing to a client role and touches no other table;
* it keeps ``service_role`` on the path the backend already uses;
* it is additive and idempotent: one transaction, no DDL, no DML, no policy or
  RLS-flag change;
* the post-condition is FAIL-CLOSED (the DO block raises and rolls the whole
  transaction back if a client role retains any privilege, if ``service_role``
  lost DML, or if RLS is not enabled), so a partial or ineffective apply cannot
  pass;
* the posture matches the two immediately preceding migrations of the same
  delta (``20261030000000``, ``20261101000000``) — this file invents no new
  convention.

The *runtime* privilege behaviour was measured on the live project and is
recorded in the closure evidence (``client_grants=0``, service-role DML intact,
RLS intact); it is deliberately not re-measured by this unit test.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

#: The closure/hardening migration under test (finding F-1).
MIGRATION = (
    "20261105000000_ct_consultant_model_03_request_tables_revoke_client_roles.sql"
)
#: The migration that created both tables (20261103000000) — it relied on
#: deny-by-RLS only, which is the gap this file closes.
CREATING_MIGRATION = "20261103000000_ct_consultant_model_03_client_access_and_mode.sql"
#: The two preceding migrations of the same delta that already revoke.
PREDECESSORS = (
    "20261030000000_manual_processing_routing.sql",
    "20261101000000_ct_mp_sub_003_consultant_coverage.sql",
)

TABLES = (
    "public.consultant_relationship_requests",
    "public.consultant_mode_change_requests",
)
CLIENT_ROLES = ("anon", "authenticated")

#: ``PRIVILEGES`` is optional sugar: the predecessors use the short form
#: (``REVOKE ALL ON TABLE ...``), this file uses the long form. Both are the
#: same absolute, re-runnable statement, so parity is asserted semantically.
_REVOKE = re.compile(
    r"REVOKE\s+ALL(?:\s+PRIVILEGES)?\s+ON\s+TABLE\s+(public\.\w+)\s+FROM\s+(\w+)"
)
_GRANT = re.compile(
    r"GRANT\s+ALL(?:\s+PRIVILEGES)?\s+ON\s+TABLE\s+(public\.\w+)\s+TO\s+(\w+)"
)


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "supabase" / "migrations").is_dir():
            return parent
    raise AssertionError("could not locate repo root (supabase/migrations)")


def _read(name: str) -> str:
    path = _repo_root() / "supabase" / "migrations" / name
    assert path.exists(), f"migration missing: {name}"
    return path.read_text(encoding="utf-8")


def _executable(sql: str) -> str:
    """SQL minus comment lines (guards must not match prose about the ruling)."""
    return "\n".join(
        line for line in sql.splitlines() if not line.lstrip().startswith("--")
    )


SQL = _read(MIGRATION)
CODE = _executable(SQL)
UPPER = CODE.upper()



# ---------------------------------------------------------------------------
# Placement / stamp hygiene
# ---------------------------------------------------------------------------
def test_migration_exists_and_sorts_after_the_creating_migration() -> None:
    names = sorted(
        p.name for p in (_repo_root() / "supabase" / "migrations").glob("*.sql")
    )
    assert MIGRATION in names
    assert names.index(MIGRATION) > names.index(CREATING_MIGRATION)
    for predecessor in PREDECESSORS:
        assert names.index(MIGRATION) > names.index(predecessor)


def test_migration_reuses_no_historical_timestamp() -> None:
    stamp = MIGRATION.split("_")[0]
    migrations_dir = _repo_root() / "supabase" / "migrations"
    sharing = sorted(p.name for p in migrations_dir.glob(f"{stamp}_*.sql"))
    assert sharing == [MIGRATION], sharing


# ---------------------------------------------------------------------------
# The hardening itself: two tables, two client roles, no widening
# ---------------------------------------------------------------------------
def test_revokes_every_privilege_from_both_client_roles_on_both_tables() -> None:
    revokes = _REVOKE.findall(CODE)
    assert len(revokes) == 4, revokes
    assert {table for table, _ in revokes} == set(TABLES)
    assert {role for _, role in revokes} == set(CLIENT_ROLES)


def test_revokes_from_client_roles_only() -> None:
    assert set(role for _, role in _REVOKE.findall(CODE)) <= set(CLIENT_ROLES)
    assert "FROM service_role" not in CODE


def test_grants_nothing_to_a_client_role() -> None:
    """Hardening only: it may never widen the client-role posture."""
    grants = _GRANT.findall(CODE)
    assert {table for table, _ in grants} == set(TABLES)
    assert {role for _, role in grants} == {"service_role"}, grants
    assert "TO anon" not in CODE
    assert "TO authenticated" not in CODE


def test_keeps_service_role_on_the_backend_path() -> None:
    """The backend service path (backend/data/consultants.py) must still work."""
    for table in TABLES:
        assert (table, "service_role") in _GRANT.findall(CODE), table


def test_is_a_single_self_contained_transaction() -> None:
    assert CODE.count("BEGIN;") == 1
    assert CODE.count("COMMIT;") == 1


def test_is_additive_and_leaves_every_other_object_alone() -> None:
    for forbidden in (
        "CREATE TABLE",
        "CREATE INDEX",
        "CREATE POLICY",
        "DROP POLICY",
        "ALTER POLICY",
        "ALTER TABLE",
        "ALTER DEFAULT PRIVILEGES",
        "ENABLE ROW LEVEL SECURITY",
        "DISABLE ROW LEVEL SECURITY",
        "FORCE ROW LEVEL SECURITY",
        "INSERT INTO",
        "UPDATE PUBLIC",
        "DELETE FROM",
        "TRUNCATE",
        "DROP ",
    ):
        assert forbidden not in UPPER, f"unexpected statement: {forbidden}"


# ---------------------------------------------------------------------------
# Fail-closed post-condition
# ---------------------------------------------------------------------------
def test_fails_closed_when_a_client_role_retains_any_privilege() -> None:
    assert "still grants % to a client role" in CODE
    # The ACL is read directly, so a future privilege type cannot slip through.
    assert "aclexplode(" in CODE
    assert "relacl" in CODE
    assert "IN ('anon', 'authenticated')" in CODE


def test_fails_closed_when_service_role_lost_dml() -> None:
    assert "has_table_privilege('service_role'" in CODE
    assert "'SELECT', 'INSERT', 'UPDATE', 'DELETE'" in CODE
    assert "service_role lost % on public.%" in CODE


def test_fails_closed_when_rls_is_not_enabled() -> None:
    """This file hardens; it must never be the reason RLS is off."""
    assert "relrowsecurity" in CODE
    assert "RLS is not enabled on public.%" in CODE


def test_fail_closed_guard_covers_both_tables() -> None:
    for table in (
        "consultant_relationship_requests",
        "consultant_mode_change_requests",
    ):
        assert CODE.count(f"'{table}'") >= 1, table


# ---------------------------------------------------------------------------
# Parity with the established house convention
# ---------------------------------------------------------------------------
def test_matches_the_preceding_delta_convention_it_cites() -> None:
    """The shared convention is the client-role revocation — not the GRANT.

    Measured against the two predecessors: both revoke ALL from both client
    roles, and only ``20261030000000`` also writes the explicit
    ``GRANT ALL ON TABLE ... TO service_role``. ``20261101000000`` omits it and
    leaves ``service_role`` on the platform default, which yields the same
    effective privileges. This file follows the explicit form and *asserts*
    service_role DML in its fail-closed guard, so the effective posture it
    establishes is the one both predecessors establish.
    """
    for predecessor in PREDECESSORS:
        predecessor_code = _executable(_read(predecessor))
        revokes = _REVOKE.findall(predecessor_code)
        assert revokes, predecessor
        assert {role for _, role in revokes} == set(CLIENT_ROLES), predecessor
        # ... and no predecessor re-revokes this file's tables.
        assert {table for table, _ in revokes} & set(TABLES) == set(), predecessor

    assert (
        "GRANT ALL ON TABLE public.manual_processing_processors TO service_role;"
        in _executable(_read(PREDECESSORS[0]))
    )


def test_documents_why_it_exists() -> None:
    assert "CT-CARBONTALLY-LIVE-SUPABASE-UPDATE-01" in SQL
    assert CREATING_MIGRATION in SQL
    assert "F-1" in SQL
    assert "ROLLBACK" in SQL
    assert "service-role" in SQL


# ---------------------------------------------------------------------------
# The applied artefact is frozen
# ---------------------------------------------------------------------------
#: sha256 of this migration exactly as applied to the live project. Recorded in
#: the F-1 live-apply evidence (2026-10-09, git HEAD f3df392933a17b4d690de91a12f5f92195db2a7d),
#: together with the ledger row
#: ``20261105000000/ct_consultant_model_03_request_tables_revoke_client_roles/stmt=null``
#: and the post-apply ledger (104 rows, tip ``20261105000000``).
APPLIED_SHA256 = "76f1261a6f8e9d704f659a3003bf0447263c3957b1665d48e45648174730c78e"


def test_file_is_the_artefact_that_was_applied_live() -> None:
    """An applied migration is immutable: the tree file must be that artefact.

    The hash is taken over the file with CRLF normalised to LF, so a checkout
    with different line endings cannot produce a false failure.

    If this test fails, do NOT edit the applied migration to make it pass. The
    live migration ledger records this version as applied, so any change to its
    statements requires a NEW migration; refreshing this pin is only legitimate
    alongside new apply evidence for the changed file.
    """
    raw = (_repo_root() / "supabase" / "migrations" / MIGRATION).read_bytes()
    assert hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() == APPLIED_SHA256

