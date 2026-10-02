"""Integration test: the D4 restore library reconstructs a **local disposable**
PostgreSQL database from a real artifact.

Safety properties of this test (same shape as ``test_exporter_local.py``):

* it runs **only** against a loopback host (``127.0.0.1``/``localhost``) and is
  **skipped** when the DSN is not loopback — it can never touch production;
* it creates its **own uniquely-named databases** (``ct_backup_rs_src_<hex>`` and
  ``ct_backup_rs_dst_<hex>``), populates only the source, and drops **only those
  two** in teardown;
* it never mutates an existing database.

What is proven here, in one pass over the shipped code paths:

* ``BackupService`` publishes an encrypted artifact for the source;
* ``restore_members``/``restore_artifact`` (D4) rebuild the schema, the data, the
  sequence **state**, RLS, policies, triggers and comments in a *different*
  database;
* ``verify_restored`` compares that target against the artifact's own catalog and
  returns ``ok`` — and, for a schema-only rehearsal, honestly returns ``ok`` false
  (verification is not vacuous);
* the fail-closed target guard refuses a target that is not disposable, both as a
  pure function and on the execution path.
"""
from __future__ import annotations

import base64
import os
import pathlib
import uuid
from typing import Any, AsyncIterator

import asyncpg
import pytest

from backup.errors import BackupRestoreTargetError
from backup.restore import (
    assert_disposable_target,
    read_members_from_envelope,
    restore_artifact,
    restore_members,
    verify_restored,
)
from backup.service import BackupService
from backup.settings import BackupSettings
from backup.storage import LocalFilesystemObjectStore

DEFAULT_DSN = "postgresql://postgres:postgres@127.0.0.1:54426/postgres"
DSN = os.environ.get("CT_BACKUP_TEST_DSN", DEFAULT_DSN)

_SETUP_SQL = """
CREATE TABLE public.widgets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    qty integer NOT NULL DEFAULT 0,
    price numeric(12,2),
    active boolean DEFAULT true,
    payload jsonb,
    tags text[],
    on_date date,
    CONSTRAINT widgets_qty_check CHECK (qty >= 0),
    CONSTRAINT widgets_name_unique UNIQUE (name)
);
CREATE INDEX widgets_qty_idx ON public.widgets (qty);
COMMENT ON TABLE public.widgets IS 'restore integration fixture';
CREATE TABLE public.secure_things (id integer PRIMARY KEY, organization_id uuid);
ALTER TABLE public.secure_things ENABLE ROW LEVEL SECURITY;
CREATE POLICY secure_things_select ON public.secure_things FOR SELECT USING (true);
CREATE SEQUENCE public.seq_widgets;
SELECT setval('public.seq_widgets', 42, true);
CREATE OR REPLACE FUNCTION public.touch_widget() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN
    RETURN NEW;
END;
$fn$;
CREATE TRIGGER widgets_touch BEFORE UPDATE ON public.widgets
    FOR EACH ROW EXECUTE FUNCTION public.touch_widget();
CREATE VIEW public.widget_names AS SELECT name FROM public.widgets;
INSERT INTO public.widgets (id, name, qty, price, active, payload, tags, on_date)
VALUES
    ('11111111-1111-4111-8111-111111111111', 'Acme', 5, 12.34, true,
     '{"a": 1}'::jsonb, ARRAY['x','y'], '2026-09-11'),
    ('22222222-2222-4222-8222-222222222222', 'Widget, Ltd', 0, NULL, false,
     NULL, NULL, NULL);
INSERT INTO public.secure_things (id, organization_id)
VALUES (1, '33333333-3333-4333-8333-333333333333');
"""


def _is_loopback(dsn: str) -> bool:
    host = dsn.split("@")[-1].split("/")[0].split(":")[0]
    return host in {"127.0.0.1", "localhost", "::1"}


@pytest.fixture
async def disposable_databases() -> AsyncIterator[dict[str, str]]:
    """A disposable populated SOURCE and a disposable empty TARGET."""
    if not _is_loopback(DSN):
        pytest.skip("CT_BACKUP_TEST_DSN is not a loopback host; refusing to run")
    try:
        admin = await asyncpg.connect(dsn=DSN, timeout=5)
    except Exception as exc:  # noqa: BLE001 - environment gate, not a test failure
        pytest.skip(f"local PostgreSQL not reachable for restore integration test: {exc}")

    suffix = uuid.uuid4().hex[:8]
    source_name = f"ct_backup_rs_src_{suffix}"
    target_name = f"ct_backup_rs_dst_{suffix}"
    created: list[str] = []
    try:
        for name in (source_name, target_name):
            try:
                await admin.execute(f'CREATE DATABASE "{name}"')
            except Exception as exc:  # noqa: BLE001
                pytest.skip(f"cannot create a disposable local database: {exc}")
            created.append(name)

        prefix = DSN.rsplit("/", 1)[0]
        source_dsn = f"{prefix}/{source_name}"
        connection = await asyncpg.connect(dsn=source_dsn, timeout=5)
        try:
            await connection.execute(_SETUP_SQL)
        finally:
            await connection.close()
        yield {
            "source": source_dsn,
            "target": f"{prefix}/{target_name}",
            "source_name": source_name,
            "target_name": target_name,
        }
    finally:
        for name in created:
            try:
                await admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
            except Exception:  # noqa: BLE001 - teardown best effort only
                pass
        await admin.close()


async def _artifact_for(
    databases: dict[str, str], tmp_path: Any
) -> tuple[BackupSettings, bytes]:
    """Publish one real artifact for the disposable source and return it."""
    store_root = tmp_path / "object_store"
    key = base64.b64encode(os.urandom(32)).decode()  # test-only, never committed
    settings = BackupSettings.from_env(
        {
            "CT_BACKUP_OBJECT_STORE": "local",
            "CT_BACKUP_LOCAL_ROOT": str(store_root),
            "CT_BACKUP_SCHEMAS": "public",
            "CT_BACKUP_ENCRYPTION_KEY": key,
            "CT_BACKUP_TEMP_ROOT": str(tmp_path),
            "CT_BACKUP_VERIFY_READBACK": "1",
        }
    )

    async def factory() -> Any:
        return await asyncpg.connect(databases["source"], timeout=5)

    await BackupService(
        settings,
        object_store=LocalFilesystemObjectStore(str(store_root)),
        connection_factory=factory,
    ).create_backup(
        requested_by="ct-restore-integration-test",
        reason="disposable restore integration test (local)",
        backup_id=uuid.uuid4().hex,
    )

    stored = sorted(path for path in pathlib.Path(store_root).rglob("*") if path.is_file())
    assert stored, "the backup service must publish an artifact"
    return settings, stored[0].read_bytes()


@pytest.mark.parametrize(
    "name",
    [
        "production_main",
        "carbon_prod",
        "carbon_qa",
        "demo_live",
        "investor_preview",
        "live",
        "ct_prod_restore",  # disposable prefix, persistent token: still refused
    ],
)
def test_guard_refuses_a_target_that_is_not_disposable(name: str) -> None:
    with pytest.raises(BackupRestoreTargetError) as excinfo:
        assert_disposable_target(name, "restore target")
    assert "refusing" in str(excinfo.value)


@pytest.mark.parametrize(
    "name", ["ct_backup_rs_dst_deadbeef", "ct_anything", "carbontally_test"]
)
def test_guard_accepts_disposable_targets(name: str) -> None:
    assert assert_disposable_target(name, "restore target") == name


class TestRestoreAgainstRealPostgres:
    async def test_restore_reconstructs_schema_data_and_sequence_state(
        self, disposable_databases: dict[str, str], tmp_path: Any
    ) -> None:
        settings, envelope = await _artifact_for(disposable_databases, tmp_path)
        target = await asyncpg.connect(dsn=disposable_databases["target"], timeout=5)
        try:
            result, verification = await restore_artifact(
                target,
                envelope,
                settings.require_encryption_key(),
                target_database=disposable_databases["target_name"],
            )

            assert result.target_database == disposable_databases["target_name"]
            assert result.backup_id, "the artifact's own backup id is reported"
            assert result.tables_loaded == 2
            assert result.rows_loaded == 3
            assert result.phases["policies"] == 1
            assert result.phases["triggers"] == 1
            assert result.statements_applied > 10

            assert verification["ok"] is True, verification
            for key in (
                "missing_schemas",
                "missing_tables",
                "extra_tables",
                "missing_indexes",
                "extra_indexes",
                "missing_constraints",
                "extra_constraints",
                "missing_policies",
                "extra_policies",
                "missing_triggers",
                "extra_triggers",
                "missing_functions",
                "rls_missing",
                "row_count_mismatches",
                "sequence_state_mismatches",
            ):
                assert verification[key] == [], (key, verification[key])
            assert verification["row_counts"]["public.widgets"] == {
                "expected": 2,
                "actual": 2,
            }

            # The rows themselves round-tripped, including NULLs and arrays.
            rows = await target.fetch(
                """
                SELECT name, qty, price::text AS price, active,
                       payload::text AS payload, tags, on_date::text AS on_date
                FROM public.widgets ORDER BY name
                """
            )
            assert [row["name"] for row in rows] == ["Acme", "Widget, Ltd"]
            assert rows[0]["qty"] == 5
            assert rows[0]["price"] == "12.34"
            assert rows[0]["payload"] == '{"a": 1}'
            assert rows[0]["tags"] == ["x", "y"]
            assert rows[0]["on_date"] == "2026-09-11"
            assert rows[1]["price"] is None
            assert rows[1]["payload"] is None
            assert rows[1]["tags"] is None
            assert rows[1]["on_date"] is None

            # Sequence *state* was restored, not merely the sequence object.
            state = await target.fetchrow(
                "SELECT last_value, is_called FROM public.seq_widgets"
            )
            assert (int(state["last_value"]), bool(state["is_called"])) == (42, True)

            # RLS, the policy, the trigger, the view and the comment are live.
            assert await target.fetchval(
                "SELECT relrowsecurity FROM pg_class"
                " WHERE oid = 'public.secure_things'::regclass"
            ) is True
            assert await target.fetchval(
                "SELECT count(*) FROM pg_policy WHERE polname = 'secure_things_select'"
            ) == 1
            assert await target.fetchval(
                "SELECT count(*) FROM pg_trigger"
                " WHERE tgname = 'widgets_touch' AND NOT tgisinternal"
            ) == 1
            assert await target.fetchval(
                "SELECT count(*) FROM pg_views WHERE viewname = 'widget_names'"
            ) == 1
            assert await target.fetchval(
                "SELECT obj_description('public.widgets'::regclass, 'pg_class')"
            ) == "restore integration fixture"

            # A default that depends on the restored catalog still works.
            inserted = await target.fetchrow(
                "INSERT INTO public.widgets (name, qty) VALUES ('Gamma', 1) RETURNING id"
            )
            assert inserted["id"] is not None
        finally:
            await target.close()


    async def test_schema_only_rehearsal_is_reported_as_incomplete(
        self, disposable_databases: dict[str, str], tmp_path: Any
    ) -> None:
        """Verification must fail a target that has objects but no data."""
        settings, envelope = await _artifact_for(disposable_databases, tmp_path)
        members = read_members_from_envelope(envelope, settings.require_encryption_key())
        target = await asyncpg.connect(dsn=disposable_databases["target"], timeout=5)
        try:
            # No explicit target name: the guard derives it from the server.
            result = await restore_members(target, members, skip_data=True)
            assert result.target_database == disposable_databases["target_name"]
            assert result.tables_loaded == 0
            assert result.rows_loaded == 0
            assert "data" not in result.phases

            report = await verify_restored(
                target,
                members.catalog,
                expected_row_counts={"public.widgets": 2, "public.secure_things": 1},
                sequences=members.sequences,
            )
            assert report["missing_tables"] == [], "the DDL half did run"
            assert report["ok"] is False
            assert sorted(report["row_count_mismatches"]) == [
                "public.secure_things",
                "public.widgets",
            ]
            # ``skip_data`` skips the data phase only: sequence state belongs to the
            # DDL plan, so it is applied even in a rehearsal.
            assert report["sequence_state_mismatches"] == []
            state = await target.fetchrow(
                "SELECT last_value, is_called FROM public.seq_widgets"
            )
            assert (int(state["last_value"]), bool(state["is_called"])) == (42, True)
        finally:
            await target.close()

    async def test_restore_refuses_a_named_persistent_target(
        self, disposable_databases: dict[str, str], tmp_path: Any
    ) -> None:
        settings, envelope = await _artifact_for(disposable_databases, tmp_path)
        members = read_members_from_envelope(envelope, settings.require_encryption_key())
        target = await asyncpg.connect(dsn=disposable_databases["target"], timeout=5)
        try:
            with pytest.raises(BackupRestoreTargetError):
                await restore_members(
                    target, members, target_database="carbon_prod_snapshot", skip_data=True
                )
            # The guard ran before the first statement: nothing was created.
            assert await target.fetchval(
                """
                SELECT count(*) FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = 'widgets'
                """
            ) == 0
        finally:
            await target.close()
