"""Integration test: pure-Python logical export against a **local disposable**
PostgreSQL database.

Safety properties of this test:

* it runs **only** against a loopback host (``127.0.0.1``/``localhost``) and is
  **skipped** when the DSN is not loopback — it can never touch production;
* it creates its **own uniquely-named database** (``ct_backup_it_<hex>``), sets
  up fixtures in it, and drops **only that database** in teardown;
* it never mutates an existing database.
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Any, AsyncIterator

import asyncpg
import pytest

from backup import crypto
from backup.artifact import (
    ARCHIVE_MEMBER_CATALOG,
    ARCHIVE_MEMBER_MANIFEST,
    ARCHIVE_MEMBER_SEQUENCES,
    read_archive,
    sha256_hex,
    verify_content_checksums,
)
from backup.errors import BackupConfigurationError, BackupExportError
from backup.exporter import export_schemas
from backup.service import BackupService
from backup.settings import BackupSettings
from backup.storage import LocalFilesystemObjectStore

DEFAULT_DSN = "postgresql://postgres:postgres@127.0.0.1:54426/postgres"
DSN = os.environ.get("CT_BACKUP_TEST_DSN", DEFAULT_DSN)

WIDGET_1 = uuid.UUID("11111111-1111-4111-8111-111111111111")
WIDGET_2 = uuid.UUID("22222222-2222-4222-8222-222222222222")

_SETUP_SQL = """
CREATE TABLE public.widgets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    qty integer NOT NULL DEFAULT 0,
    price numeric(12,2),
    active boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    on_date date,
    payload jsonb,
    tags text[],
    blob bytea,
    CONSTRAINT widgets_qty_check CHECK (qty >= 0),
    CONSTRAINT widgets_name_unique UNIQUE (name)
);
CREATE TABLE public.empty_things (id integer PRIMARY KEY);
CREATE TABLE public.notes (id integer PRIMARY KEY, body text);
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
CREATE TABLE public."Mixed Case" ("Id" integer PRIMARY KEY, "Order" text);
INSERT INTO public."Mixed Case" ("Id", "Order") VALUES (1, 'quoted-identifier');
INSERT INTO public.widgets
    (id, name, qty, price, active, created_at, on_date, payload, tags, blob)
VALUES
    ('11111111-1111-4111-8111-111111111111', 'Acme', 5, 12.34, true,
     '2026-09-11T10:00:00Z', '2026-09-11', '{"a": 1}'::jsonb,
     ARRAY['x','y'], '\\xdeadbeef'::bytea),
    ('22222222-2222-4222-8222-222222222222', 'Widget, Ltd', 0, NULL, false,
     NULL, NULL, NULL, NULL, NULL);
INSERT INTO public.notes (id, body) VALUES (1, NULL);
-- ---------------------------------------------------------------------------
-- Phase 1.1 fixtures (F1, F3-F9)
-- ---------------------------------------------------------------------------
CREATE TABLE public.identity_demo (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label text,
    slug text GENERATED ALWAYS AS (lower(label)) STORED,
    code text COLLATE "C"
);
CREATE TABLE public.unlogged_demo (id integer PRIMARY KEY);
CREATE UNLOGGED TABLE public.unlogged_only (id integer PRIMARY KEY);
CREATE SEQUENCE public.seq_owned;
ALTER SEQUENCE public.seq_owned OWNED BY public.widgets.qty;
CREATE TABLE public.events (id integer, kind text) PARTITION BY LIST (kind);
CREATE TABLE public.events_a PARTITION OF public.events FOR VALUES IN ('a');
CREATE TABLE public.events_b PARTITION OF public.events FOR VALUES IN ('b');
CREATE TABLE public.events_c PARTITION OF public.events FOR VALUES IN ('c');
COMMENT ON TABLE public.identity_demo IS 'identity demo table';
COMMENT ON COLUMN public.identity_demo.label IS 'label column comment';
INSERT INTO public.identity_demo (label, code) VALUES ('Alpha', 'x'), ('Beta', 'y');
INSERT INTO public.unlogged_only VALUES (1);
INSERT INTO public.events (id, kind) VALUES (1, 'a'), (2, 'b'), (3, 'b'), (4, 'c');
-- Synthetic scaffold for the F2 deny-list tests. NOT a credential: the value is a
-- literal marker that only exists to prove the schema is (or is not) exported.
CREATE SCHEMA auth;
CREATE TABLE auth.scaffold_credentials (
    id integer PRIMARY KEY,
    synthetic_credential_column text
);
INSERT INTO auth.scaffold_credentials VALUES (1, 'SYNTHETIC-NOT-A-CREDENTIAL');
"""


def _is_loopback(dsn: str) -> bool:
    host = dsn.split("@")[-1].split("/")[0].split(":")[0]
    return host in {"127.0.0.1", "localhost", "::1"}


@pytest.fixture
async def disposable_database() -> AsyncIterator[str]:
    """Create, populate and (always) drop a uniquely named local database."""
    if not _is_loopback(DSN):
        pytest.skip("CT_BACKUP_TEST_DSN is not a loopback host; refusing to run")
    try:
        admin = await asyncpg.connect(dsn=DSN, timeout=5)
    except Exception as exc:  # noqa: BLE001 - environment gate, not a test failure
        pytest.skip(f"local PostgreSQL not reachable for backup integration test: {exc}")

    name = f"ct_backup_it_{uuid.uuid4().hex[:8]}"
    created = False
    try:
        try:
            await admin.execute(f'CREATE DATABASE "{name}"')
        except Exception as exc:  # noqa: BLE001
            pytest.skip(f"cannot create a disposable local database: {exc}")
        created = True

        target_dsn = DSN.rsplit("/", 1)[0] + f"/{name}"
        connection = await asyncpg.connect(dsn=target_dsn, timeout=5)
        try:
            await connection.execute(_SETUP_SQL)
        finally:
            await connection.close()
        yield target_dsn
    finally:
        if created:
            try:
                await admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
            except Exception:  # noqa: BLE001 - teardown best effort only
                pass
        await admin.close()


class TestCatalogAndDataExtraction:
    async def test_export_captures_schema_data_and_sequence_state(
        self, disposable_database: str, tmp_path: Any
    ) -> None:
        connection = await asyncpg.connect(dsn=disposable_database, timeout=5)
        try:
            result = await export_schemas(connection, ["public"], output_dir=str(tmp_path))
        finally:
            await connection.close()

        names = {entry.name for entry in result.inventory}
        assert {"widgets", "empty_things", "notes", "secure_things", "Mixed Case"} <= names

        by_name = {entry.name: entry for entry in result.inventory}
        assert by_name["widgets"].row_count == 2
        assert by_name["widgets"].has_primary_key is True
        assert by_name["widgets"].ordered_by_primary_key is True
        assert by_name["widgets"].column_count == 10
        assert by_name["empty_things"].row_count == 0
        assert by_name["secure_things"].rls_enabled is True
        assert by_name["notes"].row_count == 1

        # Server-side identifier quoting: ``format('%I.%I', …)`` quotes each
        # identifier only when it requires quoting, so lowercase names stay bare
        # while mixed-case names are quoted.
        qualified = {table["name"]: table["qualified_name"] for table in result.catalog.tables}
        assert qualified["widgets"] == "public.widgets"
        assert qualified["Mixed Case"] == 'public."Mixed Case"'
        assert by_name["Mixed Case"].row_count == 1
        mixed_columns = {
            column["column_name"]
            for column in result.catalog.columns_for("public", "Mixed Case")
        }
        assert mixed_columns == {"Id", "Order"}

        # Representative PostgreSQL scalar types reached the catalog record.
        widget_types = {
            column["data_type"] for column in result.catalog.columns_for("public", "widgets")
        }
        for expected in {
            "uuid", "text", "integer", "numeric(12,2)", "boolean",
            "timestamp with time zone", "date", "jsonb", "text[]", "bytea",
        }:
            assert expected in widget_types, expected

        # Schema objects beyond plain tables.
        assert result.catalog.sequences, "sequences must be captured"
        sequence_names = {s["name"] for s in result.catalog.sequences}
        assert {"seq_widgets", "seq_owned", "identity_demo_id_seq"} <= sequence_names
        seq_widgets = {s["name"]: s for s in result.sequence_states}["seq_widgets"]
        assert seq_widgets["last_value"] == 42
        assert seq_widgets["is_called"] is True
        assert any(item["name"] == "touch_widget" for item in result.catalog.functions)
        assert any(item["trigger_name"] == "widgets_touch" for item in result.catalog.triggers)
        assert any(
            item["policy_name"] == "secure_things_select" for item in result.catalog.policies
        )
        assert any(item["name"] == "widget_names" for item in result.catalog.views)
        assert any(
            item["constraint_name"] == "widgets_qty_check" for item in result.catalog.constraints
        )

        # Extracted material on disk.
        catalog = json.loads((tmp_path / "catalog" / "catalog.json").read_text())
        assert catalog["identity"]["database"]
        assert (tmp_path / "catalog" / "ddl.sql").read_text().strip()
        sequences = json.loads((tmp_path / "catalog" / "sequences.json").read_text())
        sequence_json = {s["name"]: s for s in sequences}
        assert sequence_json["seq_widgets"]["qualified_name"] == "public.seq_widgets"

        # COPY payload semantics: NULL marker and row separators.
        widgets = (tmp_path / "data" / "public__widgets.copy").read_bytes()
        assert widgets.count(b"\n") == 2
        assert b"\\N" in widgets
        assert (tmp_path / "data" / "public__empty_things.copy").read_bytes() == b""


class TestFullServiceAgainstLocalDatabase:
    async def test_end_to_end_artifact_is_encrypted_complete_and_verifiable(
        self, disposable_database: str, tmp_path: Any
    ) -> None:
        settings = BackupSettings.from_env(
            {
                "CT_BACKUP_OBJECT_STORE": "local",
                "CT_BACKUP_LOCAL_ROOT": str(tmp_path / "store"),
                "CT_BACKUP_TEMP_ROOT": str(tmp_path / "tmp"),
                "CT_BACKUP_ENCRYPTION_KEY": crypto.encode_key(crypto.generate_key()),
                "CT_BACKUP_KEY_ID": "it-key-v1",
            }
        )
        os.makedirs(tmp_path / "tmp", exist_ok=True)
        store = LocalFilesystemObjectStore(str(tmp_path / "store"))

        async def factory() -> Any:
            return await asyncpg.connect(dsn=disposable_database, timeout=5)

        service = BackupService(settings, object_store=store, connection_factory=factory)
        record = await service.create_backup(requested_by="it@example.test", reason="integration")

        # Ciphertext only, checksum verified, stored outside the database.
        stored = await store.get_object(record.object_key)
        assert stored.startswith(crypto.MAGIC)
        assert b"Acme" not in stored
        assert sha256_hex(stored) == record.ciphertext_sha256
        assert record.key_id == "it-key-v1"
        assert record.table_count >= 4

        archive = crypto.decrypt(stored, settings.require_encryption_key())
        assert sha256_hex(archive) == record.archive_sha256
        members = read_archive(archive, compression="gzip")
        verify_content_checksums(members)
        manifest = json.loads(members[ARCHIVE_MEMBER_MANIFEST].decode("utf-8"))
        assert manifest["counts"]["tables"] == record.table_count
        assert manifest["counts"]["rows"] == record.total_rows
        manifest_sequences = {s["name"]: s for s in manifest["inventory"]["sequences"]}
        assert manifest_sequences["seq_widgets"]["last_value"] == 42
        assert members[ARCHIVE_MEMBER_CATALOG]
        assert members[ARCHIVE_MEMBER_SEQUENCES]

        # Temporary material is gone after a successful run.
        leftovers = [
            name for name in os.listdir(tmp_path / "tmp") if name.startswith("ct_backup_")
        ]
        assert leftovers == []


    async def test_broken_connection_publishes_nothing(
        self, disposable_database: str, tmp_path: Any
    ) -> None:
        """A failed snapshot must not publish an artifact or leave temp material."""
        settings = BackupSettings.from_env(
            {
                "CT_BACKUP_OBJECT_STORE": "local",
                "CT_BACKUP_LOCAL_ROOT": str(tmp_path / "store"),
                "CT_BACKUP_TEMP_ROOT": str(tmp_path / "tmp"),
                "CT_BACKUP_ENCRYPTION_KEY": crypto.encode_key(crypto.generate_key()),
            }
        )
        os.makedirs(tmp_path / "tmp", exist_ok=True)
        store = LocalFilesystemObjectStore(str(tmp_path / "store"))
        closed = await asyncpg.connect(dsn=disposable_database, timeout=5)
        await closed.close()

        async def factory() -> Any:
            return closed

        service = BackupService(settings, object_store=store, connection_factory=factory)
        with pytest.raises(BackupExportError):
            await service.create_backup()
        assert await store.list_objects() == []
        leftovers = [
            name for name in os.listdir(tmp_path / "tmp") if name.startswith("ct_backup_")
        ]
        assert leftovers == []



async def _exported_row_counts(dsn: str) -> dict[str, int]:
    """Authoritative oracle: per-table counts for exactly the tables the exporter exports.

    Mirrors the export predicate (base tables + partition parents, no leaves, no
    temporary objects) so a mismatch is a real defect rather than a fixture artefact.
    """
    connection = await asyncpg.connect(dsn=dsn, timeout=5)
    try:
        rows = await connection.fetch(
            "SELECT c.relname AS n FROM pg_class c "
            "JOIN pg_namespace s ON s.oid = c.relnamespace "
            "WHERE s.nspname = 'public' AND c.relkind IN ('r','p') "
            "  AND NOT c.relispartition AND c.relpersistence <> 't' "
            "ORDER BY c.relname"
        )
        counts: dict[str, int] = {}
        for row in rows:
            ident = '"public"."' + str(row["n"]).replace('"', '""') + '"'
            counts[str(row["n"])] = int(await connection.fetchval(f"SELECT count(*) FROM {ident}"))
        return counts
    finally:
        await connection.close()


class TestPhase11Capture:
    """Phase 1.1 real-database proof for F1 and F3–F9."""

    async def _export(self, dsn: str, tmp_path: Any):
        connection = await asyncpg.connect(dsn=dsn, timeout=5)
        try:
            return await export_schemas(connection, ["public"], output_dir=str(tmp_path))
        finally:
            await connection.close()

    async def test_partitioned_parent_exported_once_with_exact_counts(
        self, disposable_database: str, tmp_path: Any
    ) -> None:
        result = await self._export(disposable_database, tmp_path)
        by_name = {entry.name: entry for entry in result.inventory}

        assert "events" in by_name, "the partition parent must be exported (F1)"
        for leaf in ("events_a", "events_b", "events_c"):
            assert leaf not in by_name, f"partition leaf {leaf} must not be exported (F1)"

        assert by_name["events"].row_count == 4, "parent COPY carries every partition row"
        assert sum(entry.row_count for entry in result.inventory) == result.total_rows

        oracle = await _exported_row_counts(disposable_database)
        assert set(oracle) == set(by_name), (
            f"exported table set must match the oracle: db_only={set(oracle) - set(by_name)} "
            f"export_only={set(by_name) - set(oracle)}"
        )
        mismatches = {
            name: (by_name[name].row_count, count)
            for name, count in oracle.items()
            if by_name[name].row_count != count
        }
        assert not mismatches, f"row counts must equal the database oracle: {mismatches}"
        assert result.total_rows == sum(oracle.values()), "total must not double-count (F1)"

    async def test_partition_metadata_is_authoritative_in_catalog(
        self, disposable_database: str, tmp_path: Any
    ) -> None:
        result = await self._export(disposable_database, tmp_path)
        partitions = result.catalog.partitions
        assert {p["partition_name"] for p in partitions} == {"events_a", "events_b", "events_c"}
        first = partitions[0]
        assert first["partition_key"] == "LIST (kind)"
        assert first["parent_qualified_name"] == "public.events"
        assert first["partition_bound"].startswith("FOR VALUES IN")

        catalog = json.loads((tmp_path / "catalog" / "catalog.json").read_text())
        assert "partitions" in catalog, "structured catalog must carry partition metadata (F8)"
        events = [table for table in catalog["tables"] if table["name"] == "events"][0]
        assert events["is_partitioned"] is True
        assert events["relkind"] == "p"


    async def test_identity_generated_collation_and_comments(
        self, disposable_database: str, tmp_path: Any
    ) -> None:
        result = await self._export(disposable_database, tmp_path)
        columns = {
            column["column_name"]: column
            for column in result.catalog.columns_for("public", "identity_demo")
        }
        ident, slug, code = columns["id"], columns["slug"], columns["code"]

        assert ident["identity_kind"] == "ALWAYS", "identity must be captured (F3)"
        assert slug["generated_kind"] == "STORED", "generated storage must be captured (F4)"
        assert slug["generation_expression"], "generation expression must be captured"
        assert slug["default_expression"] is None, (
            "a generated column must never look like an ordinary default (F4)"
        )
        assert code["collation"] and '"C"' in code["collation"], "collation (F5)"
        assert ident["collation"] is None, "default collation must not be reported"

        tables = {table["name"]: table for table in result.catalog.tables}
        assert tables["identity_demo"]["comment"] == "identity demo table"     # F9
        assert columns["label"]["comment"] == "label column comment"           # F9
        assert tables["widgets"]["comment"] is None

        ddl = (tmp_path / "catalog" / "ddl.sql").read_text()
        assert "GENERATED ALWAYS AS IDENTITY" in ddl
        assert " STORED" in ddl
        assert "COMMENT ON TABLE" in ddl and "COMMENT ON COLUMN" in ddl

    async def test_unlogged_persistence_captured(
        self, disposable_database: str, tmp_path: Any
    ) -> None:
        result = await self._export(disposable_database, tmp_path)
        tables = {table["name"]: table for table in result.catalog.tables}
        assert tables["unlogged_only"]["persistence"] == "u", "unlogged state (F6)"
        assert tables["unlogged_demo"]["persistence"] == "p"
        ddl = (tmp_path / "catalog" / "ddl.sql").read_text()
        assert "CREATE UNLOGGED TABLE IF NOT EXISTS" in ddl

    async def test_sequence_ownership_and_state_are_distinct(
        self, disposable_database: str, tmp_path: Any
    ) -> None:
        result = await self._export(disposable_database, tmp_path)
        sequences = {sequence["name"]: sequence for sequence in result.sequence_states}
        assert sequences["seq_owned"]["owned_by"] == "public.widgets.qty"   # F7
        assert sequences["seq_widgets"]["owned_by"] is None
        assert sequences["identity_demo_id_seq"]["owned_by"] == "public.identity_demo.id", (
            "an identity sequence's internal dependency must also be captured (F3/F7)"
        )
        assert "last_value" in sequences["seq_widgets"], "state stays separate from ownership"
        ddl = (tmp_path / "catalog" / "ddl.sql").read_text()
        assert "OWNED BY" in ddl

    async def test_credential_schema_deny_list_is_enforced(
        self, disposable_database: str, tmp_path: Any
    ) -> None:
        """F2 against a real database: auth is refused by default, allowed on override only."""
        with pytest.raises(BackupConfigurationError):
            BackupSettings.from_env(
                {"CT_BACKUP_SCHEMAS": "public,auth", "CT_BACKUP_TEMP_ROOT": str(tmp_path)}
            )

        connection = await asyncpg.connect(dsn=disposable_database, timeout=5)
        try:
            with pytest.raises(BackupConfigurationError):
                await export_schemas(connection, ["public", "auth"], output_dir=str(tmp_path))
            result = await export_schemas(
                connection,
                ["public", "auth"],
                output_dir=str(tmp_path),
                allow_denied_schemas=True,
            )
        finally:
            await connection.close()

        assert any(entry.name == "scaffold_credentials" for entry in result.inventory)
        payload = (tmp_path / "data" / "auth__scaffold_credentials.copy").read_bytes()
        assert b"SYNTHETIC-NOT-A-CREDENTIAL" in payload, "override path must be genuine"

        default_result = await self._export(disposable_database, tmp_path / "default")
        assert not any(
            entry.name == "scaffold_credentials" for entry in default_result.inventory
        )
        assert not (tmp_path / "default" / "data" / "auth__scaffold_credentials.copy").exists()

