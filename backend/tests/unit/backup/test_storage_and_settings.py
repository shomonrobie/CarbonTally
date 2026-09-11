"""Unit tests for backup settings and the object-storage abstraction."""
from __future__ import annotations

import base64
import os

import pytest

from backup.crypto import encode_key, generate_key
from backup.errors import BackupConfigurationError, BackupStorageError
from backup.settings import DEFAULT_KEY_ID, BackupSettings
from backup.storage import (
    InMemoryObjectStore,
    LocalFilesystemObjectStore,
    ObjectStore,
    build_object_store,
)


class TestSettings:
    def test_defaults_are_safe(self) -> None:
        settings = BackupSettings.from_env({})
        assert settings.object_store == "local"
        assert settings.compression == "gzip"
        assert settings.compression_level == 6
        assert settings.schemas == ("public",)
        assert settings.key_id == DEFAULT_KEY_ID
        assert settings.encryption_key is None

    def test_missing_key_raises_when_required(self) -> None:
        with pytest.raises(BackupConfigurationError):
            BackupSettings.from_env({}).require_encryption_key()

    def test_key_is_accepted_and_never_repr_ed(self) -> None:
        key = generate_key()
        settings = BackupSettings.from_env({"CT_BACKUP_ENCRYPTION_KEY": encode_key(key)})
        assert settings.require_encryption_key() == key
        assert base64.b64encode(key).decode("ascii") not in repr(settings)
        assert "encryption_key=<set>" in repr(settings)

    def test_invalid_key_forms_are_rejected(self) -> None:
        with pytest.raises(BackupConfigurationError):
            BackupSettings.from_env({"CT_BACKUP_ENCRYPTION_KEY": "not-base64!!"})
        with pytest.raises(BackupConfigurationError):
            BackupSettings.from_env(
                {"CT_BACKUP_ENCRYPTION_KEY": base64.b64encode(b"short").decode("ascii")}
            )

    def test_invalid_store_and_compression_are_rejected(self) -> None:
        with pytest.raises(BackupConfigurationError):
            BackupSettings.from_env({"CT_BACKUP_OBJECT_STORE": "s3"})
        with pytest.raises(BackupConfigurationError):
            BackupSettings.from_env({"CT_BACKUP_COMPRESSION": "zstd"})

    def test_invalid_compression_level_is_rejected(self) -> None:
        with pytest.raises(BackupConfigurationError):
            BackupSettings.from_env({"CT_BACKUP_COMPRESSION_LEVEL": "0"})
        with pytest.raises(BackupConfigurationError):
            BackupSettings.from_env({"CT_BACKUP_COMPRESSION_LEVEL": "abc"})

    def test_schema_list_is_parsed(self) -> None:
        settings = BackupSettings.from_env({"CT_BACKUP_SCHEMAS": "public, audit ,"})
        assert settings.schemas == ("public", "audit")

    def test_build_object_store_selects_the_memory_provider(self) -> None:
        assert isinstance(
            build_object_store(BackupSettings.from_env({"CT_BACKUP_OBJECT_STORE": "memory"})),
            InMemoryObjectStore,
        )


class TestInMemoryStore:
    async def test_put_get_head_list_delete_round_trip(self) -> None:
        store = InMemoryObjectStore()
        assert isinstance(store, ObjectStore)
        stored = await store.put_object("backups/1/art.enc", b"ciphertext")
        assert stored.size_bytes == len(b"ciphertext")
        assert await store.get_object("backups/1/art.enc") == b"ciphertext"
        assert (await store.head_object("backups/1/art.enc")).key == "backups/1/art.enc"
        assert [item.key for item in await store.list_objects("backups/")] == [
            "backups/1/art.enc"
        ]
        await store.delete_object("backups/1/art.enc")
        assert await store.list_objects() == []
        await store.delete_object("backups/1/art.enc")  # idempotent

    async def test_missing_object_raises_typed_error(self) -> None:
        with pytest.raises(BackupStorageError):
            await InMemoryObjectStore().get_object("absent")


class TestLocalFilesystemStore:
    async def test_round_trip_and_private_permissions(self, tmp_path) -> None:
        store = LocalFilesystemObjectStore(str(tmp_path / "store"))
        await store.put_object("backups/ab/art.enc", b"ciphertext")
        path = tmp_path / "store" / "backups" / "ab" / "art.enc"
        assert path.read_bytes() == b"ciphertext"
        assert os.stat(path).st_mode & 0o777 == 0o600
        assert await store.get_object("backups/ab/art.enc") == b"ciphertext"
        assert [item.key for item in await store.list_objects("backups/")] == [
            "backups/ab/art.enc"
        ]
        await store.delete_object("backups/ab/art.enc")
        assert not path.exists()

    async def test_key_escaping_the_root_is_rejected(self, tmp_path) -> None:
        store = LocalFilesystemObjectStore(str(tmp_path / "store"))
        with pytest.raises(BackupStorageError):
            await store.put_object("../escape.enc", b"ciphertext")

    async def test_missing_object_raises_typed_error(self, tmp_path) -> None:
        store = LocalFilesystemObjectStore(str(tmp_path / "store"))
        with pytest.raises(BackupStorageError):
            await store.get_object("absent.enc")
