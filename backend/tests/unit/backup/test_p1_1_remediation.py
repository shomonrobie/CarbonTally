"""Phase 1.1 remediation tests (findings F2, F10, F11).

Covers:
  * **F2** — credential-bearing schema deny-list is fail-closed, enforced at both
    the settings and exporter layers, with an unmistakable explicit override;
  * **F10** — ``backup_id`` validation (allow-list; traversal/separator/absolute/
    control-character forms rejected; valid identifiers accepted);
  * **F11** — provider-independent checksum semantics: a provider-native ETag never
    trips the guard, a mismatching provider SHA-256 and a bad read-back both fail
    with a typed error, the published object is discarded, and no false success is
    returned.

The fake asyncpg connection is shared with ``test_service`` so the two suites
cannot drift.
"""
from __future__ import annotations

import hashlib
import os

import pytest

from backup.artifact import sha256_hex, validate_backup_id
from backup.errors import (
    BackupConfigurationError,
    BackupIntegrityError,
    BackupStorageError,
    BackupValidationError,
)
from backup.exporter import export_schemas
from backup.service import BackupService
from backup.settings import (
    DENIED_SCHEMA_OVERRIDE_PHRASE,
    DENIED_SCHEMAS,
    BackupSettings,
    validate_schemas,
)
from backup.storage import InMemoryObjectStore, StoredObject
from tests.unit.backup.test_service import (
    FakeConnection,
    _factory,
    _leftover_temp_dirs,
    _settings,
)


def _key() -> bytes:
    return os.urandom(32)


def _encode(key: bytes) -> str:
    import base64

    return base64.b64encode(key).decode("ascii")


class _BaseStore:
    """Minimal store double; subclasses vary the digest semantics."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.put_calls: list[str] = []
        self.get_calls: list[str] = []
        self.delete_calls: list[str] = []

    async def put_object(self, key, data, *, content_type="application/octet-stream",
                         metadata=None):
        self.put_calls.append(key)
        self.objects[key] = bytes(data)
        return self._stored(key, bytes(data), metadata or {})

    def _stored(self, key, data, metadata) -> StoredObject:
        return StoredObject(
            key=key,
            size_bytes=len(data),
            created_at="2026-09-11T00:00:00Z",
            content_sha256=hashlib.sha256(data).hexdigest(),
            metadata=dict(metadata),
        )

    async def get_object(self, key):
        self.get_calls.append(key)
        try:
            return self.objects[key]
        except KeyError as exc:
            raise BackupStorageError("not found", details={"key": key}) from exc

    async def head_object(self, key):
        return self._stored(key, await self.get_object(key), {})

    async def list_objects(self, prefix=""):
        return [
            StoredObject(key=key, size_bytes=len(data), created_at="")
            for key, data in sorted(self.objects.items())
            if key.startswith(prefix)
        ]

    async def delete_object(self, key) -> None:
        self.delete_calls.append(key)
        self.objects.pop(key, None)


class EtagOnlyStore(_BaseStore):
    """Provider that exposes only a native ETag — must never be read as SHA-256."""

    def _stored(self, key, data, metadata) -> StoredObject:
        return StoredObject(
            key=key,
            size_bytes=len(data),
            created_at="2026-09-11T00:00:00Z",
            content_sha256=None,
            provider_checksum=hashlib.md5(data, usedforsecurity=False).hexdigest(),
            provider_checksum_algorithm="etag-md5",
            metadata=dict(metadata),
        )


class LyingDigestStore(_BaseStore):
    """Provider that declares a SHA-256 which does not match what it stored."""

    def _stored(self, key, data, metadata) -> StoredObject:
        return StoredObject(
            key=key,
            size_bytes=len(data),
            created_at="2026-09-11T00:00:00Z",
            content_sha256="0" * 64,
            metadata=dict(metadata),
        )


class CorruptingReadbackStore(_BaseStore):
    """Provider that returns different bytes on read than were written."""

    async def get_object(self, key):
        self.get_calls.append(key)
        self.objects[key] = b"tampered-in-flight"
        return self.objects[key]


class ExplodingConnection:
    """Connection double that fails if the exporter touches it at all."""

    def transaction(self, **_kwargs):
        raise AssertionError("the exporter must refuse before opening a transaction")

    async def fetch(self, *_args, **_kwargs):
        raise AssertionError("the exporter must refuse before querying")

    async def fetchrow(self, *_args, **_kwargs):
        raise AssertionError("the exporter must refuse before querying")


def _base_env(tmp_path) -> dict:
    return {
        "CT_BACKUP_OBJECT_STORE": "memory",
        "CT_BACKUP_TEMP_ROOT": str(tmp_path),
        "CT_BACKUP_ENCRYPTION_KEY": _encode(_key()),
        "CT_BACKUP_KEY_ID": "p11-key",
    }


def _run_with(tmp_path, store, *, connection=None, **env):
    """Build a service on a store/connection double with the given env overrides."""
    merged = _base_env(tmp_path)
    merged.update(env)
    settings = BackupSettings.from_env(merged)
    service = BackupService(
        settings,
        object_store=store,
        connection_factory=_factory(connection or FakeConnection()),
    )
    return service, settings


class TestSchemaDenyList:
    """F2 — credential-bearing schemas are refused by default (fail closed)."""

    def test_default_export_remains_public_only(self) -> None:
        settings = BackupSettings.from_env({})
        assert settings.schemas == ("public",)
        assert settings.allow_denied_schemas is False
        assert "auth" in DENIED_SCHEMAS

    @pytest.mark.parametrize("denied", ["auth", "storage", "vault", "realtime"])
    def test_requesting_a_denied_schema_fails_closed(self, denied: str) -> None:
        with pytest.raises(BackupConfigurationError) as excinfo:
            BackupSettings.from_env({"CT_BACKUP_SCHEMAS": f"public,{denied}"})
        assert denied in str(excinfo.value)
        assert denied in excinfo.value.details.get("denied_schemas", [])

    def test_denied_check_is_case_insensitive(self) -> None:
        with pytest.raises(BackupConfigurationError):
            BackupSettings.from_env({"CT_BACKUP_SCHEMAS": "PUBLIC,AUTH"})

    def test_override_requires_the_exact_phrase(self) -> None:
        with pytest.raises(BackupConfigurationError):
            BackupSettings.from_env(
                {"CT_BACKUP_SCHEMAS": "auth", "CT_BACKUP_DENIED_SCHEMA_OVERRIDE": "yes"}
            )
        settings = BackupSettings.from_env(
            {
                "CT_BACKUP_SCHEMAS": "auth",
                "CT_BACKUP_DENIED_SCHEMA_OVERRIDE": DENIED_SCHEMA_OVERRIDE_PHRASE,
            }
        )
        assert settings.schemas == ("auth",)
        assert settings.allow_denied_schemas is True

    def test_override_is_never_the_default(self) -> None:
        assert BackupSettings.from_env({"CT_BACKUP_SCHEMAS": "public"}).allow_denied_schemas is False
        assert BackupSettings().allow_denied_schemas is False

    def test_validate_schemas_helper(self) -> None:
        validate_schemas(["public", "audit"])                     # permitted
        validate_schemas(["auth"], allow_override=True)           # deliberate override
        with pytest.raises(BackupConfigurationError):
            validate_schemas(["auth"])
        with pytest.raises(BackupConfigurationError):
            validate_schemas([" public"])                         # whitespace rejected

    async def test_exporter_refuses_before_touching_the_connection(self, tmp_path) -> None:
        with pytest.raises(BackupConfigurationError):
            await export_schemas(
                ExplodingConnection(), ["public", "auth"], output_dir=str(tmp_path)
            )

    async def test_exporter_allows_denied_schema_only_with_override(self, tmp_path) -> None:
        connection = FakeConnection()
        result = await export_schemas(
            connection,
            ["public", "auth"],
            output_dir=str(tmp_path),
            allow_denied_schemas=True,
        )
        assert result.inventory, "override must actually proceed"

    async def test_service_refuses_hand_built_settings_that_bypass_from_env(self, tmp_path) -> None:
        """Defence in depth: a BackupSettings constructed directly still cannot export auth."""
        store = _BaseStore()
        settings = BackupSettings(
            schemas=("auth",), encryption_key=_key(), temp_root=str(tmp_path)
        )
        assert settings.allow_denied_schemas is False
        service = BackupService(
            settings, object_store=store, connection_factory=_factory(FakeConnection())
        )
        with pytest.raises(BackupConfigurationError):
            await service.create_backup()
        assert store.put_calls == []
        assert _leftover_temp_dirs(tmp_path) == []


class TestBackupIdValidation:
    """F10 — a backup identifier is validated before it can reach a storage key."""

    @pytest.mark.parametrize(
        "bad",
        [
            "../../escape-attempt",
            "..",
            ".",
            "a..b",
            "a/b",
            "a\\b",
            "/etc/passwd",
            "C:\\temp",
            "id name",
            " id",
            "id ",
            "id\nname",
            "id\x00",
            "-leading",
            "_leading",
            "",
            "x" * 129,
            "id.with.dot",
        ],
    )
    def test_unsafe_identifiers_are_rejected(self, bad: str) -> None:
        with pytest.raises(BackupValidationError):
            validate_backup_id(bad)

    @pytest.mark.parametrize("good", ["bkp1", "a", "A1_-z", "0" * 128, "e2f1a1b2c3d4"])
    def test_safe_identifiers_are_accepted(self, good: str) -> None:
        assert validate_backup_id(good) == good

    def test_non_string_is_rejected(self) -> None:
        with pytest.raises(BackupValidationError):
            validate_backup_id(None)  # type: ignore[arg-type]

    async def test_service_rejects_hostile_id_before_any_work(self, tmp_path) -> None:
        store = _BaseStore()
        connection = FakeConnection()
        service, _ = _run_with(tmp_path, store, connection=connection)
        with pytest.raises(BackupValidationError):
            await service.create_backup(backup_id="../../escape-attempt")
        assert connection.copy_calls == [], "no database work may happen first"
        assert store.put_calls == []
        assert _leftover_temp_dirs(tmp_path) == []

    async def test_service_accepts_a_valid_id_without_path_characters(self, tmp_path) -> None:
        store = _BaseStore()
        service, _ = _run_with(tmp_path, store)
        record = await service.create_backup(backup_id="p11-ok")
        assert "/p11-ok/" in record.object_key
        assert ".." not in record.object_key
        assert store.delete_calls == []

    async def test_service_rejects_explicit_empty_string_id_before_any_work(
        self, tmp_path
    ) -> None:
        """N1 regression: an explicitly supplied empty string is validated and rejected.

        ``None`` means "not supplied" (a generated id is correct), but ``""`` **is**
        supplied, so it must reach ``validate_backup_id`` and fail closed — no
        database work, no staging directory and no published artifact.
        """
        store = _BaseStore()
        service, _ = _run_with(tmp_path, store, connection=ExplodingConnection())
        with pytest.raises(BackupValidationError):
            await service.create_backup(backup_id="")
        assert store.put_calls == [], "nothing may be published for a rejected id"
        assert store.objects == {}
        assert _leftover_temp_dirs(tmp_path) == [], "no staging directory may be created"

    async def test_service_still_generates_an_id_when_the_id_is_omitted(self, tmp_path) -> None:
        """N1 regression guard: ``None`` keeps the generated-identifier behaviour."""
        store = _BaseStore()
        service, _ = _run_with(tmp_path, store)
        record = await service.create_backup(backup_id=None)
        assert len(record.backup_id) == 32, "an omitted id must be generated"
        assert record.backup_id.isalnum()



class TestDigestSemantics:
    """F11 — provider-independent checksum semantics; no false success."""

    async def test_provider_native_etag_never_false_trips(self, tmp_path) -> None:
        store = EtagOnlyStore()
        service, _ = _run_with(tmp_path, store)
        record = await service.create_backup()
        assert len(record.ciphertext_sha256) == 64
        assert store.delete_calls == [], "an ETag must not be compared against SHA-256"
        assert record.object_key in store.objects, "a valid backup must be retained"

    async def test_provider_declared_sha256_mismatch_fails_and_discards(self, tmp_path) -> None:
        store = LyingDigestStore()
        service, _ = _run_with(tmp_path, store)
        with pytest.raises(BackupIntegrityError):
            await service.create_backup()
        assert store.delete_calls == [store.put_calls[0]], "published object must be discarded"
        assert store.objects == {}, "no artifact may remain after a failed verification"

    async def test_bad_readback_fails_and_discards(self, tmp_path) -> None:
        store = CorruptingReadbackStore()
        service, _ = _run_with(tmp_path, store)
        with pytest.raises(BackupIntegrityError):
            await service.create_backup()
        assert store.delete_calls == [store.put_calls[0]]
        assert store.objects == {}

    async def test_readback_is_performed_by_default(self, tmp_path) -> None:
        store = _BaseStore()
        service, _ = _run_with(tmp_path, store)
        record = await service.create_backup()
        assert store.get_calls == [record.object_key], "default must read the object back"
        assert store.delete_calls == []

    async def test_readback_can_be_disabled(self, tmp_path) -> None:
        store = _BaseStore()
        service, _ = _run_with(tmp_path, store, CT_BACKUP_VERIFY_READBACK="0")
        record = await service.create_backup()
        assert store.get_calls == [], "read-back must be skipped when disabled"
        assert record.ciphertext_sha256

    async def test_verify_readback_default_is_true(self) -> None:
        assert BackupSettings.from_env({}).verify_readback is True
        assert BackupSettings.from_env({"CT_BACKUP_VERIFY_READBACK": "false"}).verify_readback is False

    async def test_discard_failure_does_not_mask_the_integrity_error(self, tmp_path) -> None:
        class UndeletableStore(LyingDigestStore):
            async def delete_object(self, key) -> None:  # pragma: no cover - error path
                self.delete_calls.append(key)
                raise BackupStorageError("cannot delete", details={"key": key})

        store = UndeletableStore()
        service, _ = _run_with(tmp_path, store)
        with pytest.raises(BackupIntegrityError):
            await service.create_backup()
        assert store.delete_calls, "a discard attempt must still be made"

