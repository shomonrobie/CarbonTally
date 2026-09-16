"""P8-D17-MIGRATION-REVISION-001 — provider-ownership migration revision (structural).

The D-17 production run stopped on two ownership-sensitive statements against
Supabase provider-managed tables (`storage.objects` owned by
`supabase_storage_admin`; `auth.users` owned by `supabase_auth_admin`). The
migration role (`postgres`) holds the relevant *privileges* but not *ownership*,
and `ALTER TABLE`, `CREATE/DROP POLICY` and `DROP TRIGGER` all require ownership.

This revision removes the two ownership-sensitive statements:

* D32 — `ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY` (a semantic no-op:
  RLS is already enabled), replaced by a read-only precondition assertion;
* D35 — `DROP TRIGGER IF EXISTS ... ON auth.users`, replaced by the
  semantically identical `CREATE OR REPLACE TRIGGER`.

These tests pin the intended end state of both migrations and prove that no other
migration changed. Runtime privilege behaviour is proven separately by the local
production-topology privilege lab and the disposable replay (see the task report);
it is not re-proven here.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

D32 = "20260823000000_d32_private_documents_storage.sql"
D35 = "20260824010000_d35_self_service_onboarding.sql"
RELEASE_SHA = "32083ee"
POLICIES = {
    "d32_documents_select_org_member": "SELECT",
    "d32_documents_insert_org_member": "INSERT",
    "d32_documents_update_org_member": "UPDATE",
    "d32_documents_delete_org_member": "DELETE",
}


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "supabase" / "migrations").is_dir():
            return parent
    raise AssertionError("could not locate repo root (supabase/migrations)")


def _read(name: str) -> str:
    return (_repo_root() / "supabase" / "migrations" / name).read_text(encoding="utf-8")


def _executable(sql: str) -> str:
    """SQL minus comment lines (guards must not match prose about the revision)."""
    return "\n".join(
        line for line in sql.splitlines() if not line.lstrip().startswith("--")
    )


class TestD32Revision:
    def test_no_longer_issues_the_ownership_sensitive_rls_alter(self) -> None:
        sql = _executable(_read(D32))
        assert "ALTER TABLE" not in sql.upper(), (
            "D32 must no longer issue any ownership-sensitive ALTER TABLE"
        )
        assert "ENABLE ROW LEVEL SECURITY" not in sql.upper()

    def test_asserts_rls_is_already_enabled_without_ownership(self) -> None:
        sql = _executable(_read(D32))
        assert "relrowsecurity" in sql
        assert "'storage'" in sql and "'objects'" in sql
        assert "RAISE EXCEPTION" in sql
        assert "D32 precondition failed" in sql
        # the guard must be read-only: no DDL, no DML inside the DO block
        guard = sql.split("DO $d32_rls$")[1].split("$d32_rls$;")[0]
        for forbidden in ("ALTER ", "UPDATE ", "INSERT ", "DELETE ", "DROP "):
            assert forbidden not in guard.upper(), (
                f"the D32 RLS guard must be read-only; found {forbidden}"
            )

    def test_preserves_bucket_privacy_behaviour(self) -> None:
        sql = _executable(_read(D32))
        assert "UPDATE storage.buckets SET public = FALSE WHERE name = 'documents'" in sql

    def test_preserves_all_four_intended_policies(self) -> None:
        sql = _executable(_read(D32))
        found = re.findall(
            r"CREATE POLICY\s+\"([a-z0-9_]+)\"\s+ON\s+storage\.objects\s+FOR\s+(\w+)", sql)
        assert dict(found) == POLICIES, f"policy set changed: {dict(found)}"
        for name in POLICIES:
            body = sql.split(f'CREATE POLICY "{name}"')[1]
            body = body.split("CREATE POLICY")[0]
            assert "TO authenticated" in body
            assert "bucket_id = 'documents'" in body
            assert "(storage.foldername(name))[1] = 'uploads'" in body
            assert "public.organization_members" in body
            assert "auth.uid()" in body
            assert "is_active = TRUE" in body

    def test_does_not_weaken_or_replace_the_policies(self) -> None:
        sql = _executable(_read(D32)).upper()
        assert "DROP POLICY" not in sql
        assert "ALTER POLICY" not in sql
        assert "FORCE ROW LEVEL SECURITY" not in sql
        assert "GRANT " not in sql
        assert "REVOKE " not in sql
        assert "DISABLE ROW LEVEL SECURITY" not in sql


class TestD35Revision:
    def test_no_longer_drops_the_auth_users_trigger(self) -> None:
        sql = _executable(_read(D35))
        assert "DROP TRIGGER" not in sql.upper(), (
            "D35 must not DROP a trigger on the provider-managed auth.users table"
        )

    def test_uses_create_or_replace_trigger_with_identical_semantics(self) -> None:
        sql = _executable(_read(D35))
        assert "CREATE OR REPLACE TRIGGER trg_sync_auth_user_to_public_users" in sql
        assert "AFTER INSERT ON auth.users" in sql
        assert "FOR EACH ROW" in sql
        assert "EXECUTE FUNCTION public.sync_auth_user_to_public_users()" in sql

    def test_preserves_the_created_trigger_and_its_guard(self) -> None:
        sql = _executable(_read(D35))
        # the supabase-auth-schema guard is unchanged
        assert "pg_tables" in sql and "schemaname = 'auth'" in sql and "tablename = 'users'" in sql
        assert sql.count("CREATE OR REPLACE TRIGGER") == 1

    def test_preserves_the_sync_function_contract(self) -> None:
        sql = _read(D35)
        assert "CREATE OR REPLACE FUNCTION public.sync_auth_user_to_public_users()" in sql
        assert "SECURITY DEFINER" in sql
        assert "SET search_path = public" in sql
        assert "ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email" in sql
        assert "EXCEPTION" in sql and "never block authentication" in sql

    def test_preserves_the_self_service_onboarding_changes(self) -> None:
        sql = _executable(_read(D35))
        assert "ALTER COLUMN organization_id DROP NOT NULL" in sql
        assert "ADD COLUMN IF NOT EXISTS created_by UUID" in sql
        assert "uq_data_discovery_requests_onboarding_candidate" in sql
        assert "COMMENT ON COLUMN public.data_discovery_requests.organization_id" in sql
        assert "COMMENT ON COLUMN public.data_discovery_requests.created_by" in sql


class TestRevisionScope:
    def test_only_the_two_authorised_migrations_differ_from_the_release(self) -> None:
        """Part C guard: no other migration may change in this revision."""
        root = _repo_root()
        names = sorted(p.name for p in (root / "supabase" / "migrations").glob("*.sql"))
        differing = []
        for name in names:
            try:
                original = subprocess.run(
                    ["git", "show", f"{RELEASE_SHA}:supabase/migrations/{name}"],
                    cwd=root, capture_output=True, text=True, timeout=30,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                pytest.skip(f"git unavailable for release comparison: {exc}")
            if original.returncode != 0:
                pytest.skip(f"release commit {RELEASE_SHA} not available locally")
            if original.stdout != (root / "supabase" / "migrations" / name).read_text(
                    encoding="utf-8"):
                differing.append(name)
        assert differing == [D32, D35], (
            f"unexpected migration changes for this revision: {differing}"
        )

    def test_gate4_migration_is_untouched(self) -> None:
        gate4 = "20260905000000_gate4_actor_provenance.sql"
        root = _repo_root()
        original = subprocess.run(
            ["git", "show", f"{RELEASE_SHA}:supabase/migrations/{gate4}"],
            cwd=root, capture_output=True, text=True, timeout=30,
        )
        if original.returncode != 0:
            pytest.skip("release commit not available locally")
        assert original.stdout == (root / "supabase" / "migrations" / gate4).read_text(
            encoding="utf-8")
        sql = _read(gate4)
        assert "REFERENCES auth.users(id)" in sql

    def test_migration_ordering_is_unchanged(self) -> None:
        names = sorted(p.name for p in
                       (_repo_root() / "supabase" / "migrations").glob("*.sql"))
        assert len(names) == 71
        versions = [n.split("_", 1)[0] for n in names]
        assert versions == sorted(versions)
        assert versions == sorted(set(versions)), "duplicate migration versions"
        assert names.index(D32) < names.index(D35)
