"""Unit tests for ``backup.service`` using a fake asyncpg connection.

These tests prove the orchestration contract **without any database**: the
storage boundary receives ciphertext only, temporary material is always removed,
and a failed export never publishes an artifact or a partial file.
"""
from __future__ import annotations

import json
import os
from typing import Any, Iterable

import pytest

from backup import crypto
from backup.artifact import (
    ARCHIVE_MEMBER_CATALOG,
    ARCHIVE_MEMBER_CHECKSUMS,
    ARCHIVE_MEMBER_DDL,
    ARCHIVE_MEMBER_MANIFEST,
    ARCHIVE_MEMBER_SEQUENCES,
    BACKUP_FORMAT_NAME,
    BACKUP_FORMAT_VERSION,
    read_archive,
    sha256_hex,
    verify_content_checksums,
)
from backup.catalog import (
    _IDENTITY_SQL,
    _SCHEMAS_SQL,
    _VIEWS_SQL,
)
from backup.errors import BackupConfigurationError, BackupExportError
from backup.service import BackupService
from backup.settings import BackupSettings
from backup.storage import InMemoryObjectStore

WIDGET_A = "11111111-1111-4111-8111-111111111111"
WIDGET_B = "22222222-2222-4222-8222-222222222222"

#: COPY text payload for ``public.widgets``: a NULL (``\N``) and an escaped tab.
WIDGETS_COPY = (
    f"{WIDGET_A}\tAcme\t5\t\\N\n"
    f"{WIDGET_B}\tWidget, Ltd\t0\thas\\ttab\n"
).encode("utf-8")


def _fixture_rows() -> dict[str, list[dict[str, Any]]]:
    """Fixture catalog rows keyed by a distinctive SQL marker."""
    return {
        "current_database()": [
            {"database": "ct_backup_unit", "server_version": "17.6",
             "server_encoding": "UTF8"}
        ],
        "FROM pg_catalog.pg_attribute a": [
            {"schema": "public", "table_name": "widgets", "column_name": "id",
             "data_type": "uuid", "not_null": True, "default_expression": None,
             "identity_kind": "", "generated_kind": "", "collation": None,
             "comment": None, "ordinal": 1},
            {"schema": "public", "table_name": "widgets", "column_name": "name",
             "data_type": "text", "not_null": False, "default_expression": None,
             "identity_kind": "", "generated_kind": "", "collation": None,
             "comment": None, "ordinal": 2},
            {"schema": "public", "table_name": "empty_things", "column_name": "id",
             "data_type": "integer", "not_null": True, "default_expression": None,
             "identity_kind": "", "generated_kind": "", "collation": None,
             "comment": None, "ordinal": 1},
            {"schema": "public", "table_name": "ident_demo", "column_name": "id",
             "data_type": "integer", "not_null": True, "default_expression": None,
             "identity_kind": "a", "generated_kind": "", "collation": None,
             "comment": None, "ordinal": 1},
            {"schema": "public", "table_name": "ident_demo", "column_name": "label",
             "data_type": "text", "not_null": False, "default_expression": None,
             "identity_kind": "", "generated_kind": "", "collation": None,
             "comment": "label column comment", "ordinal": 2},
            {"schema": "public", "table_name": "ident_demo", "column_name": "slug",
             "data_type": "text", "not_null": False, "default_expression": "lower(label)",
             "identity_kind": "", "generated_kind": "s", "collation": None,
             "comment": None, "ordinal": 3},
            {"schema": "public", "table_name": "ident_demo", "column_name": "code",
             "data_type": "text", "not_null": False, "default_expression": None,
             "identity_kind": "", "generated_kind": "",
             "collation": '"pg_catalog"."C"', "comment": None, "ordinal": 4},
        ],
        "FROM pg_catalog.pg_constraint con": [
            {"schema": "public", "table_name": "widgets", "constraint_name": "widgets_pkey",
             "constraint_type": "p", "definition": "PRIMARY KEY (id)"},
            {"schema": "public", "table_name": "empty_things",
             "constraint_name": "empty_things_pkey", "constraint_type": "p",
             "definition": "PRIMARY KEY (id)"},
        ],
        "FROM pg_catalog.pg_index ix": [
            {"schema": "public", "table_name": "widgets", "index_name": "widgets_pkey",
             "is_unique": True, "is_primary": True,
             "definition": "CREATE UNIQUE INDEX widgets_pkey ON public.widgets USING btree (id)"},
        ],
        "FROM pg_catalog.pg_sequence s": [
            {"schema": "public", "name": "seq_widgets", "start_value": 1, "increment_by": 1,
             "min_value": 1, "max_value": 9223372036854775807, "cache_size": 1,
             "is_cycled": False, "qualified_name": '"public"."seq_widgets"',
             "owned_by": "public.widgets.id"},
        ],
        "FROM pg_catalog.pg_proc p": [
            {"schema": "public", "name": "touch_widget", "arguments": "", "kind": "f",
             "definition": "CREATE OR REPLACE FUNCTION public.touch_widget() RETURNS trigger "
                           "LANGUAGE plpgsql AS $function$ BEGIN RETURN NEW; END; $function$\n"},
        ],
        "FROM pg_catalog.pg_trigger t": [
            {"schema": "public", "table_name": "widgets", "trigger_name": "widgets_touch",
             "enabled": "O",
             "definition": "CREATE TRIGGER widgets_touch BEFORE UPDATE ON public.widgets "
                           "FOR EACH ROW EXECUTE FUNCTION public.touch_widget()"},
        ],
        "FROM pg_catalog.pg_policies": [
            {"schema": "public", "table_name": "widgets", "policy_name": "widgets_tenant_select",
             "permissive": "PERMISSIVE", "roles": ["authenticated"], "command": "SELECT",
             "using_expression": "(organization_id = auth.uid())", "with_check_expression": None},
        ],
        "FROM pg_catalog.pg_extension e": [
            {"name": "pgcrypto", "version": "1.3", "schema": "extensions"},
        ],
        "FROM pg_catalog.pg_roles r": [
            {"name": "authenticated", "can_login": False, "is_superuser": False,
             "can_create_role": False, "can_create_db": False, "bypasses_rls": False,
             "connection_limit": -1},
        ],
        "FROM pg_catalog.pg_class c": [
            {"schema": "public", "name": "widgets", "relkind": "r", "rls_enabled": True,
             "rls_forced": False, "is_partitioned": False, "persistence": "p",
             "comment": None, "qualified_name": '"public"."widgets"'},
            {"schema": "public", "name": "empty_things", "relkind": "r", "rls_enabled": False,
             "rls_forced": False, "is_partitioned": False, "persistence": "p",
             "comment": None, "qualified_name": '"public"."empty_things"'},
            {"schema": "public", "name": "ident_demo", "relkind": "r", "rls_enabled": False,
             "rls_forced": False, "is_partitioned": False, "persistence": "p",
             "comment": "demo table comment", "qualified_name": '"public"."ident_demo"'},
            # Partitioned parent: exported once (F1). Its leaves are deliberately
            # absent, mirroring what ``NOT relispartition`` returns on real PostgreSQL.
            {"schema": "public", "name": "events", "relkind": "p", "rls_enabled": False,
             "rls_forced": False, "is_partitioned": True, "persistence": "p",
             "comment": None, "qualified_name": '"public"."events"'},
        ],
        "FROM pg_catalog.pg_inherits i": [
            {"schema": "public", "parent_name": "events",
             "parent_qualified_name": '"public"."events"',
             "partition_key": "LIST (kind)",
             "partition_schema": "public", "partition_name": "events_a",
             "partition_qualified_name": '"public"."events_a"',
             "partition_bound": "FOR VALUES IN ('a')"},
            {"schema": "public", "parent_name": "events",
             "parent_qualified_name": '"public"."events"',
             "partition_key": "LIST (kind)",
             "partition_schema": "public", "partition_name": "events_b",
             "partition_qualified_name": '"public"."events_b"',
             "partition_bound": "FOR VALUES IN ('b')"},
        ],
    }


class _FakeTransaction:
    """Async context manager mirroring ``asyncpg``'s transaction object."""

    def __init__(self) -> None:
        self.committed = False

    async def __aenter__(self) -> "_FakeTransaction":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        self.committed = exc_type is None
        return False


class FakeConnection:
    """Minimal asyncpg-compatible double for the exporter path."""

    def __init__(self, *, fail_table: str | None = None) -> None:
        self.fail_table = fail_table
        self.copy_calls: list[str] = []

    def transaction(self, **_kwargs: Any) -> _FakeTransaction:
        return _FakeTransaction()

    async def fetch(self, query: str, *_args: Any) -> list[dict[str, Any]]:
        stripped = query.strip()
        if stripped == _SCHEMAS_SQL.strip():
            return [{"schema": "public"}]
        if stripped == _VIEWS_SQL.strip():
            return []
        for marker, rows in _fixture_rows().items():
            if marker in query:
                return [dict(row) for row in rows]
        raise AssertionError(f"unexpected query: {query[:80]}")

    async def fetchrow(self, query: str, *_args: Any) -> dict[str, Any] | None:
        if "last_value" in query:
            return {"last_value": 42, "is_called": True}
        if query.strip() == _IDENTITY_SQL.strip():
            return dict(_fixture_rows()["current_database()"][0])
        for marker, rows in _fixture_rows().items():
            if marker in query:
                return dict(rows[0])
        raise AssertionError(f"unexpected fetchrow: {query[:80]}")

    async def copy_from_query(self, query: str, *, output: str) -> None:
        self.copy_calls.append(query)
        if self.fail_table and self.fail_table in query:
            raise RuntimeError("simulated COPY failure")
        payload = WIDGETS_COPY if "widgets" in query else b""
        with open(output, "wb") as handle:
            handle.write(payload)


def _factory(connection: FakeConnection) -> Any:
    async def create() -> FakeConnection:
        return connection

    return create


def _settings(tmp_path: Any, compression: str = "gzip") -> BackupSettings:
    return BackupSettings.from_env(
        {
            "CT_BACKUP_OBJECT_STORE": "memory",
            "CT_BACKUP_ENCRYPTION_KEY": crypto.encode_key(crypto.generate_key()),
            "CT_BACKUP_KEY_ID": "unit-key-v1",
            "CT_BACKUP_TEMP_ROOT": str(tmp_path),
            "CT_BACKUP_COMPRESSION": compression,
        }
    )


def _leftover_temp_dirs(tmp_path: Any) -> Iterable[str]:
    return [name for name in os.listdir(tmp_path) if name.startswith("ct_backup_")]


async def _run(
    tmp_path: Any, *, fail_table: str | None = None, compression: str = "gzip",
    created_at: Any = None, backup_id: str | None = None,
) -> tuple[Any, InMemoryObjectStore, BackupSettings]:
    settings = _settings(tmp_path, compression=compression)
    store = InMemoryObjectStore()
    service = BackupService(
        settings, object_store=store, connection_factory=_factory(FakeConnection(fail_table=fail_table))
    )
    record = await service.create_backup(
        requested_by="admin@example.test",
        reason="unit-test",
        created_at=created_at,
        backup_id=backup_id,
    )
    return record, store, settings



class TestBackupServiceSuccess:
    async def test_record_describes_the_artifact(self, tmp_path) -> None:
        record, _store, _settings_ = await _run(tmp_path)
        assert record.format_version == BACKUP_FORMAT_VERSION
        assert record.exporter_version == "0.1.0"
        assert record.key_id == "unit-key-v1"
        assert record.compression == "gzip"
        assert record.table_count == 4
        assert record.total_rows == 2
        assert len(record.archive_sha256) == 64
        assert len(record.ciphertext_sha256) == 64
        assert record.object_key.startswith("backups/")
        assert BACKUP_FORMAT_NAME in record.object_key

    async def test_store_receives_ciphertext_only(self, tmp_path) -> None:
        record, store, settings = await _run(tmp_path)
        stored = await store.get_object(record.object_key)
        assert stored.startswith(crypto.MAGIC)
        assert WIDGET_A.encode() not in stored
        assert b"Acme" not in stored
        assert sha256_hex(stored) == record.ciphertext_sha256
        assert settings.require_encryption_key() not in stored
        metadata = (await store.head_object(record.object_key)).metadata
        assert metadata["encrypted"] == "true"

    async def test_artifact_decrypts_to_a_verifiable_archive(self, tmp_path) -> None:
        record, store, settings = await _run(tmp_path)
        key = settings.require_encryption_key()
        archive = crypto.decrypt(await store.get_object(record.object_key), key)
        assert sha256_hex(archive) == record.archive_sha256

        members = read_archive(archive, compression="gzip")
        assert set(members) >= {
            ARCHIVE_MEMBER_MANIFEST,
            ARCHIVE_MEMBER_CATALOG,
            ARCHIVE_MEMBER_DDL,
            ARCHIVE_MEMBER_SEQUENCES,
            ARCHIVE_MEMBER_CHECKSUMS,
            "data/public__widgets.copy",
            "data/public__empty_things.copy",
        }
        verify_content_checksums(members)  # raises on any mismatch

    async def test_manifest_records_format_inventory_and_sequence_state(self, tmp_path) -> None:
        record, store, settings = await _run(tmp_path)
        members = read_archive(
            crypto.decrypt(
                await store.get_object(record.object_key), settings.require_encryption_key()
            )
        )
        manifest = json.loads(members[ARCHIVE_MEMBER_MANIFEST].decode("utf-8"))
        assert manifest["backup_format"] == {
            "name": BACKUP_FORMAT_NAME,
            "version": BACKUP_FORMAT_VERSION,
        }
        assert manifest["requested_by"] == "admin@example.test"
        assert manifest["reason"] == "unit-test"
        assert manifest["compression"] == {"algorithm": "gzip", "level": 6}
        assert manifest["encryption"]["key_id"] == "unit-key-v1"
        assert manifest["counts"]["tables"] == 4
        assert manifest["counts"]["rows"] == 2
        assert manifest["database_identity"]["database"] == "ct_backup_unit"
        table_entry = manifest["inventory"]["tables"][0]
        assert table_entry["schema"] == "public"
        assert table_entry["ordered_by_primary_key"] is True
        assert table_entry["rls_enabled"] is True
        # OID-2: sequence definitions AND current state travel together.
        sequences = manifest["inventory"]["sequences"]
        assert sequences and sequences[0]["last_value"] == 42
        assert sequences[0]["is_called"] is True

    async def test_null_and_empty_table_payloads_are_captured(self, tmp_path) -> None:
        record, store, settings = await _run(tmp_path)
        members = read_archive(
            crypto.decrypt(
                await store.get_object(record.object_key), settings.require_encryption_key()
            )
        )
        widgets = members["data/public__widgets.copy"]
        assert b"\\N" in widgets          # NULL marker preserved
        assert b"has\\ttab" in widgets    # COPY escaping preserved
        assert members["data/public__empty_things.copy"] == b""
        manifest = json.loads(members[ARCHIVE_MEMBER_MANIFEST].decode("utf-8"))
        empty = [t for t in manifest["inventory"]["tables"] if t["name"] == "empty_things"][0]
        assert empty["row_count"] == 0

    async def test_uncompressed_artifact_round_trips(self, tmp_path) -> None:
        record, store, settings = await _run(tmp_path, compression="none")
        assert record.compression == "none"
        archive = crypto.decrypt(
            await store.get_object(record.object_key), settings.require_encryption_key()
        )
        members = read_archive(archive, compression="none")
        assert ARCHIVE_MEMBER_MANIFEST in members

    async def test_artifact_is_deterministic_for_a_fixed_identity(self, tmp_path) -> None:
        from datetime import datetime, timezone

        moment = datetime(2026, 9, 11, 9, 0, tzinfo=timezone.utc)
        first, _s1, _c1 = await _run(tmp_path, created_at=moment, backup_id="fixed-id")
        second, _s2, _c2 = await _run(tmp_path, created_at=moment, backup_id="fixed-id")
        assert first.archive_sha256 == second.archive_sha256

    async def test_temp_directory_is_removed_on_success(self, tmp_path) -> None:
        await _run(tmp_path)
        assert list(_leftover_temp_dirs(tmp_path)) == []



class TestBackupServiceFailure:
    async def test_temp_directory_is_removed_on_failure(self, tmp_path) -> None:
        settings = _settings(tmp_path)
        store = InMemoryObjectStore()
        service = BackupService(
            settings,
            object_store=store,
            connection_factory=_factory(FakeConnection(fail_table="widgets")),
        )
        with pytest.raises(BackupExportError):
            await service.create_backup()
        assert list(_leftover_temp_dirs(tmp_path)) == []

    async def test_failed_export_publishes_nothing(self, tmp_path) -> None:
        settings = _settings(tmp_path)
        store = InMemoryObjectStore()
        service = BackupService(
            settings,
            object_store=store,
            connection_factory=_factory(FakeConnection(fail_table="empty_things")),
        )
        with pytest.raises(BackupExportError):
            await service.create_backup()
        assert await store.list_objects() == []

    async def test_missing_key_prevents_any_work(self, tmp_path) -> None:
        settings = BackupSettings.from_env(
            {"CT_BACKUP_OBJECT_STORE": "memory", "CT_BACKUP_TEMP_ROOT": str(tmp_path)}
        )
        store = InMemoryObjectStore()
        connection = FakeConnection()
        service = BackupService(
            settings, object_store=store, connection_factory=_factory(connection)
        )
        with pytest.raises(BackupConfigurationError):
            await service.create_backup()
        assert await store.list_objects() == []
        assert connection.copy_calls == []
        assert list(_leftover_temp_dirs(tmp_path)) == []



class TestPhase11CatalogCapture:
    """Phase 1.1 catalogue capture (F1, F3–F9) — via the extended fake fixture.

    Real-PostgreSQL proof lives in the integration suite; these tests pin the
    contract cheaply (including that partition **leaves** are absent from the
    exported table set while the parent is present).
    """

    async def _manifest(self, tmp_path) -> dict:
        record, store, settings = await _run(tmp_path)
        members = read_archive(
            crypto.decrypt(
                await store.get_object(record.object_key), settings.require_encryption_key()
            )
        )
        return json.loads(members[ARCHIVE_MEMBER_MANIFEST].decode("utf-8"))

    async def test_partition_parent_exported_and_leaves_absent(self, tmp_path) -> None:
        manifest = await self._manifest(tmp_path)
        names = {table["name"] for table in manifest["inventory"]["tables"]}
        assert "events" in names, "partition parent must be exported"
        assert "events_a" not in names and "events_b" not in names, (
            "partition leaves must not be exported separately (F1)"
        )

    async def test_partition_metadata_in_manifest_and_counts(self, tmp_path) -> None:
        manifest = await self._manifest(tmp_path)
        partitions = manifest["inventory"]["partitions"]
        assert manifest["counts"]["partitions"] == 2
        assert {p["partition_name"] for p in partitions} == {"events_a", "events_b"}
        first = partitions[0]
        assert first["partition_key"] == "LIST (kind)"
        assert first["parent_qualified_name"] == '"public"."events"'
        assert first["partition_bound"].startswith("FOR VALUES IN")

    async def test_partition_leaves_have_no_data_member(self, tmp_path) -> None:
        """Only the parent contributes a data member, so rows are exported once."""
        record, store, settings = await _run(tmp_path)
        members = read_archive(
            crypto.decrypt(
                await store.get_object(record.object_key), settings.require_encryption_key()
            )
        )
        data_members = {name for name in members if name.startswith("data/")}
        assert "data/public__events.copy" in data_members
        assert not any("events_a" in name or "events_b" in name for name in data_members)

    async def test_identity_generated_collation_and_column_comment(self, tmp_path) -> None:
        manifest = await self._manifest(tmp_path)
        record, store, settings = await _run(tmp_path)
        members = read_archive(
            crypto.decrypt(
                await store.get_object(record.object_key), settings.require_encryption_key()
            )
        )
        catalog_members = json.loads(members["catalog/catalog.json"].decode("utf-8"))
        columns = {
            column["column_name"]: column
            for column in catalog_members["columns"]
            if column["table_name"] == "ident_demo"
        }
        assert columns["id"]["identity_kind"] == "ALWAYS"           # F3
        assert columns["label"]["comment"] == "label column comment"  # F9
        assert columns["slug"]["generated_kind"] == "STORED"          # F4
        assert columns["slug"]["generation_expression"] == "lower(label)"
        assert columns["slug"]["default_expression"] is None, (
            "a generated column must never be represented as an ordinary default (F4)"
        )
        assert columns["code"]["collation"] == '"pg_catalog"."C"'     # F5
        assert columns["label"]["generated_kind"] is None
        assert columns["label"]["identity_kind"] is None
        # sanity: the manifest still describes the artifact
        assert manifest["counts"]["tables"] == 4

    async def test_table_comment_and_unlogged_persistence(self, tmp_path) -> None:
        record, store, settings = await _run(tmp_path)
        members = read_archive(
            crypto.decrypt(
                await store.get_object(record.object_key), settings.require_encryption_key()
            )
        )
        catalog_members = json.loads(members["catalog/catalog.json"].decode("utf-8"))
        tables = {table["name"]: table for table in catalog_members["tables"]}
        assert tables["ident_demo"]["comment"] == "demo table comment"   # F9
        assert tables["ident_demo"]["persistence"] == "p"                # F6
        assert tables["events"]["is_partitioned"] is True                # F8
        assert tables["widgets"]["comment"] is None

    async def test_sequence_ownership_captured(self, tmp_path) -> None:
        manifest = await self._manifest(tmp_path)
        sequences = manifest["inventory"]["sequences"]
        assert sequences and sequences[0]["owned_by"] == "public.widgets.id"  # F7
        assert sequences[0]["last_value"] == 42, "current state must still be captured (OID-2)"

    async def test_ddl_renders_identity_generated_collation_and_comments(self, tmp_path) -> None:
        record, store, settings = await _run(tmp_path)
        members = read_archive(
            crypto.decrypt(
                await store.get_object(record.object_key), settings.require_encryption_key()
            )
        )
        ddl = members["catalog/ddl.sql"].decode("utf-8")
        assert 'GENERATED ALWAYS AS IDENTITY' in ddl
        assert 'GENERATED ALWAYS AS (lower(label)) STORED' in ddl
        assert 'COLLATE "pg_catalog"."C"' in ddl
        assert '"public"."ident_demo"' in ddl
        assert "COMMENT ON TABLE \"public\".\"ident_demo\" IS 'demo table comment';" in ddl
        assert (
            "COMMENT ON COLUMN \"public\".\"ident_demo\".\"label\" IS "
            "'label column comment';" in ddl
        )
        assert "OWNED BY" in ddl
        assert "-- partition:" in ddl
        assert 'OF "public"."events"' in ddl
        assert "FOR VALUES IN ('a')" in ddl

