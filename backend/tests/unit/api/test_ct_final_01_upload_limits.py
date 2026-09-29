"""CT-FINAL-01 — canonical upload policy (admin-configurable) regression tests.

Ratified scope: **one** authoritative source for the effective upload limits —
the persisted, admin-configurable policy (``system_settings`` /
``/api/v3/settings/upload-policy``, exposed in the CarbonTally Admin Panel).
Every application upload ingress path must enforce those effective values
server-side; the UI is never the limit boundary.

Two distinct numbers matter and must not be confused:

* the out-of-the-box **effective defaults** when nothing is configured —
  **6 MB per file**, **50 files per batch**, **500 MB per batch**;
* the **ratified platform caps** an administrator may never exceed —
  10 MB per file, 50 files per batch, 500 MB per batch (the ``documents``
  bucket is additionally pinned at the 10 MB ceiling by
  ``20261024000000_ct_final_01_documents_bucket_size_limit.sql``).

Covers the primitive contract, configuration validation, the admin API
(ALLOW/DENY/persistence) and the per-ingress wiring — including the legacy
``POST /api/upload`` route whose hard-coded 50 MB check (plus the shadowed
``fastapi.status``) CT-VERIFY-06 D-2 identified.
"""
from __future__ import annotations

import asyncio
import io
import re
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from utils.upload_limits import (
    CODE_BATCH_TOO_LARGE,
    CODE_FILE_TOO_LARGE,
    CODE_SIZE_UNKNOWN,
    CODE_TOO_MANY_FILES,
    DEFAULT_MAX_BATCH_TOTAL_MB,
    DEFAULT_MAX_FILE_SIZE_MB,
    DEFAULT_MAX_FILES_PER_BATCH,
    MAX_BATCH_TOTAL_BYTES,
    MAX_FILE_SIZE_BYTES,
    MAX_FILES_PER_BATCH,
    PLATFORM_MAX_BATCH_TOTAL_MB,
    PLATFORM_MAX_FILE_SIZE_MB,
    PLATFORM_MAX_FILES_PER_BATCH,
    UploadLimitExceeded,
    default_limits,
    effective_batch_total_bytes,
    effective_file_limit_bytes,
    effective_file_limit_mb,
    effective_max_files,
    effective_policy,
    enforce_batch,
    enforce_single_file,
    human_summary,
    platform_limits,
    resolve_policy,
    validate_upload_policy,
)

_MB = 1024 * 1024


# ---------------------------------------------------------------------------
# ratified caps vs effective defaults
# ---------------------------------------------------------------------------


def test_ratified_platform_caps_are_the_documented_ceilings() -> None:
    assert PLATFORM_MAX_FILE_SIZE_MB == 10
    assert PLATFORM_MAX_FILES_PER_BATCH == 50
    assert PLATFORM_MAX_BATCH_TOTAL_MB == 500
    assert MAX_FILE_SIZE_BYTES == 10 * _MB
    assert MAX_FILES_PER_BATCH == 50
    assert MAX_BATCH_TOTAL_BYTES == 500 * _MB
    assert platform_limits()["max_file_size_mb"] == 10


def test_effective_defaults_when_nothing_is_configured() -> None:
    """Required defaults: 6MB/file · 50 files/batch · 500MB/batch."""
    assert DEFAULT_MAX_FILE_SIZE_MB == 6
    assert DEFAULT_MAX_FILES_PER_BATCH == 50
    assert DEFAULT_MAX_BATCH_TOTAL_MB == 500
    assert default_limits() == {
        "max_file_size_mb": 6,
        "max_files_per_batch": 50,
        "max_batch_size_mb": 500,
    }
    assert effective_policy(None) == default_limits()
    assert effective_policy({}) == default_limits()
    assert effective_file_limit_bytes() == 6 * _MB
    assert effective_file_limit_mb(None) == 6
    assert effective_max_files(None) == 50
    assert effective_batch_total_bytes(None) == 500 * _MB
    assert human_summary() == "6MB per file, 50 files per batch, 500MB per batch"


def test_configured_values_are_effective_and_clamped_to_the_caps() -> None:
    assert effective_file_limit_mb(2) == 2
    assert effective_file_limit_bytes(2) == 2 * _MB
    # A configured value above the ratified cap is clamped, never honoured.
    assert effective_file_limit_mb(999) == PLATFORM_MAX_FILE_SIZE_MB
    assert effective_max_files(999) == PLATFORM_MAX_FILES_PER_BATCH
    assert effective_batch_total_bytes(99999) == MAX_BATCH_TOTAL_BYTES
    # Unusable stored values fall back to the defaults — never "unlimited".
    assert effective_file_limit_mb(0) == DEFAULT_MAX_FILE_SIZE_MB
    assert effective_file_limit_mb("nonsense") == DEFAULT_MAX_FILE_SIZE_MB
    assert effective_file_limit_mb(-4) == DEFAULT_MAX_FILE_SIZE_MB
    assert effective_file_limit_mb(True) == DEFAULT_MAX_FILE_SIZE_MB
    assert human_summary({"max_file_size_mb": 3}) == (
        "3MB per file, 50 files per batch, 500MB per batch"
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_file_size_mb": 0},
        {"max_file_size_mb": -1},
        {"max_file_size_mb": "abc"},
        {"max_file_size_mb": 1.5},
        {"max_files_per_batch": 0},
        {"max_files_per_batch": "fifty"},
        {"max_batch_size_mb": -10},
        {"max_file_size_mb": PLATFORM_MAX_FILE_SIZE_MB + 1},
        {"max_files_per_batch": PLATFORM_MAX_FILES_PER_BATCH + 1},
        {"max_batch_size_mb": PLATFORM_MAX_BATCH_TOTAL_MB + 1},
    ],
)
def test_validation_rejects_invalid_values(kwargs) -> None:
    with pytest.raises(ValueError):
        validate_upload_policy(**kwargs)


def test_validation_accepts_boundaries_and_omissions() -> None:
    assert validate_upload_policy(max_file_size_mb=1)["max_file_size_mb"] == 1
    assert (
        validate_upload_policy(max_file_size_mb=PLATFORM_MAX_FILE_SIZE_MB)[
            "max_file_size_mb"
        ]
        == PLATFORM_MAX_FILE_SIZE_MB
    )
    # Omitted fields mean "leave the stored value unchanged".
    assert validate_upload_policy(max_files_per_batch=10)["max_file_size_mb"] is None


def test_resolve_policy_fails_closed_to_the_defaults() -> None:
    """An unavailable settings repository must never widen a limit."""

    class _Broken:
        async def get_upload_policy(self):
            raise RuntimeError("settings unavailable")

    class _Empty:
        async def get_upload_policy(self):
            return {
                "max_file_size_mb": None,
                "max_files_per_batch": None,
                "max_batch_size_mb": None,
            }

    class _Configured:
        async def get_upload_policy(self):
            return {
                "max_file_size_mb": 2,
                "max_files_per_batch": 5,
                "max_batch_size_mb": 7,
            }

    assert asyncio.run(resolve_policy(None)) == default_limits()
    assert asyncio.run(resolve_policy(_Broken())) == default_limits()
    assert asyncio.run(resolve_policy(_Empty())) == default_limits()
    assert asyncio.run(resolve_policy(_Configured())) == {
        "max_file_size_mb": 2,
        "max_files_per_batch": 5,
        "max_batch_size_mb": 7,
    }


# ---------------------------------------------------------------------------
# enforcement primitives
# ---------------------------------------------------------------------------


def test_file_within_the_effective_limit_is_accepted() -> None:
    assert enforce_single_file("meter.csv", 5 * _MB) == 5 * _MB
    # Exactly at the limit is allowed (the limit is inclusive).
    assert enforce_single_file("meter.csv", 6 * _MB) == 6 * _MB
    # A configured limit is what is actually applied.
    assert enforce_single_file("meter.csv", 2 * _MB, configured_limit_mb=3) == 2 * _MB


def test_file_over_the_effective_limit_is_rejected() -> None:
    with pytest.raises(UploadLimitExceeded) as excinfo:
        enforce_single_file("huge.pdf", 6 * _MB + 1)
    assert excinfo.value.code == CODE_FILE_TOO_LARGE
    assert excinfo.value.status_code == 413
    assert "6MB" in excinfo.value.detail

    with pytest.raises(UploadLimitExceeded) as excinfo:
        enforce_single_file("huge.pdf", 2 * _MB, configured_limit_mb=1)
    assert "1MB" in excinfo.value.detail


def test_unknown_size_never_bypasses_the_limit() -> None:
    with pytest.raises(UploadLimitExceeded) as excinfo:
        enforce_single_file("mystery.bin", None)
    assert excinfo.value.code == CODE_SIZE_UNKNOWN


def test_batch_within_the_limits_is_accepted() -> None:
    files = [(f"f{i}.bin", 1 * _MB) for i in range(MAX_FILES_PER_BATCH)]
    assert enforce_batch(files) == MAX_FILES_PER_BATCH * _MB


def test_batch_over_the_file_count_limit_is_rejected() -> None:
    files = [(f"f{i}.csv", 1024) for i in range(MAX_FILES_PER_BATCH + 1)]
    with pytest.raises(UploadLimitExceeded) as excinfo:
        enforce_batch(files)
    assert excinfo.value.code == CODE_TOO_MANY_FILES
    assert excinfo.value.status_code == 400
    # A configured (tighter) count is applied.
    with pytest.raises(UploadLimitExceeded) as excinfo:
        enforce_batch(files[:2], configured_max_files=1)
    assert excinfo.value.code == CODE_TOO_MANY_FILES


def test_batch_over_the_aggregate_size_limit_is_rejected() -> None:
    files = [(f"f{i}.bin", 1 * _MB) for i in range(3)]
    assert enforce_batch(files) == 3 * _MB
    with pytest.raises(UploadLimitExceeded) as excinfo:
        enforce_batch(files, configured_total_mb=2)
    assert excinfo.value.code == CODE_BATCH_TOO_LARGE
    assert excinfo.value.status_code == 413


def test_batch_applies_the_configured_per_file_limit() -> None:
    """The per-file ceiling must follow the batch, not a module constant."""
    files = [("a.bin", 2 * _MB), ("b.bin", 2 * _MB)]
    assert enforce_batch(files, configured_limit_mb=2) == 4 * _MB
    with pytest.raises(UploadLimitExceeded) as excinfo:
        enforce_batch(files, configured_limit_mb=1)
    assert excinfo.value.code == CODE_FILE_TOO_LARGE



# ---------------------------------------------------------------------------
# admin surface — Admin Panel → Upload Policy (ALLOW / DENY / persistence)
# ---------------------------------------------------------------------------

SETTINGS_PATH = "/api/v3/settings/upload-policy"


def _admin(user_provider):
    from tests.unit.api.fakes import staff_user

    user_provider.set_user(
        staff_user("u-admin", email="admin@example.test", role_name="admin")
    )


def test_upload_policy_route_is_registered() -> None:
    from api.router import router as v3_router
    from tests.unit.api.route_paths import flatten_router_paths

    assert any(SETTINGS_PATH in path for path in flatten_router_paths(v3_router))


def test_upload_policy_get_returns_the_effective_defaults(
    client, world, user_provider
) -> None:
    _admin(user_provider)
    response = client.get(SETTINGS_PATH)
    assert response.status_code == 200
    settings = response.json()["settings"]
    assert settings["effective"] == {
        "max_file_size_mb": 6,
        "max_files_per_batch": 50,
        "max_batch_size_mb": 500,
    }
    assert settings["configured"] == {
        "max_file_size_mb": None,
        "max_files_per_batch": None,
        "max_batch_size_mb": None,
    }
    assert settings["defaults"] == {
        "max_file_size_mb": 6,
        "max_files_per_batch": 50,
        "max_batch_size_mb": 500,
    }
    assert settings["platform_caps"]["max_file_size_mb"] == 10
    assert settings["summary"] == "6MB per file, 50 files per batch, 500MB per batch"


def test_upload_policy_put_changes_every_setting_and_persists(
    client, world, user_provider
) -> None:
    _admin(user_provider)
    put = client.put(
        SETTINGS_PATH,
        json={
            "max_file_size_mb": 3,
            "max_files_per_batch": 7,
            "max_batch_size_mb": 40,
        },
    )
    assert put.status_code == 200
    assert put.json()["settings"]["effective"] == {
        "max_file_size_mb": 3,
        "max_files_per_batch": 7,
        "max_batch_size_mb": 40,
    }

    # Persistence: the following GET returns the stored configuration.
    get = client.get(SETTINGS_PATH)
    assert get.status_code == 200
    assert get.json()["settings"]["configured"] == {
        "max_file_size_mb": 3,
        "max_files_per_batch": 7,
        "max_batch_size_mb": 40,
    }
    # And the effective limits every ingress path resolves now follow suit.
    policy = asyncio.run(resolve_policy(world.bundle().settings))
    assert policy == {
        "max_file_size_mb": 3,
        "max_files_per_batch": 7,
        "max_batch_size_mb": 40,
    }


def test_upload_policy_put_omitted_fields_keep_their_stored_value(
    client, world, user_provider
) -> None:
    _admin(user_provider)
    client.put(SETTINGS_PATH, json={"max_file_size_mb": 4})
    second = client.put(SETTINGS_PATH, json={"max_files_per_batch": 9})
    assert second.status_code == 200
    assert second.json()["settings"]["configured"] == {
        "max_file_size_mb": 4,
        "max_files_per_batch": 9,
        "max_batch_size_mb": None,
    }


def test_upload_policy_put_rejects_an_out_of_range_value(
    client, world, user_provider
) -> None:
    _admin(user_provider)
    client.put(SETTINGS_PATH, json={"max_file_size_mb": 2})
    rejected = client.put(SETTINGS_PATH, json={"max_file_size_mb": 11})
    assert rejected.status_code == 422
    # A rejected value is never stored: the previous configuration still applies.
    assert client.get(SETTINGS_PATH).json()["settings"]["effective"][
        "max_file_size_mb"
    ] == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"max_file_size_mb": 0},
        {"max_file_size_mb": -3},
        {"max_files_per_batch": 0},
        {"max_batch_size_mb": -1},
        {"max_file_size_mb": 100},
        {"max_files_per_batch": 500},
        {"max_batch_size_mb": 5000},
    ],
)
def test_upload_policy_put_rejects_invalid_configuration(
    client, world, user_provider, payload
) -> None:
    _admin(user_provider)
    assert client.put(SETTINGS_PATH, json=payload).status_code == 422


def test_upload_policy_denied_for_non_admin_and_anonymous(
    client, world, user_provider
) -> None:
    from tests.unit.api.fakes import member_user

    user_provider.set_user(member_user("org-a", "u-member", "member@example.test"))
    assert client.get(SETTINGS_PATH).status_code in (401, 403)
    assert (
        client.put(SETTINGS_PATH, json={"max_file_size_mb": 1}).status_code
        in (401, 403)
    )

    user_provider.set_unauthenticated()
    assert client.get(SETTINGS_PATH).status_code == 401
    assert (
        client.put(SETTINGS_PATH, json={"max_file_size_mb": 1}).status_code == 401
    )



# ---------------------------------------------------------------------------
# ingress wiring — the canonical choke point, the legacy route and the batch
# ---------------------------------------------------------------------------

BACKEND = Path(__file__).resolve().parents[3]


class _PolicyRepo:
    """Stand-in for ``SettingsRepository`` with the configured policy."""

    def __init__(self, **policy) -> None:
        self._policy = policy

    async def get_upload_policy(self) -> dict:
        return dict(self._policy)


class _Bundle:
    """Stand-in for the DI ``RepositoryBundle`` (ingress handlers expect ``.settings``)."""

    def __init__(self, **policy) -> None:
        self.settings = _PolicyRepo(**policy)


def _upload_file(filename: str, size: int) -> UploadFile:
    return UploadFile(file=io.BytesIO(b"0" * size), filename=filename)


def _member(org_id: str = "org-a"):
    from tests.unit.api.fakes import member_user

    return member_user(org_id, "u-member", "member@example.test")


class _Poison:
    """A supabase client that fails loudly if it is ever touched."""

    def __getattr__(self, name):  # pragma: no cover - must never be reached
        raise AssertionError("the limit must block before any client use")


def test_v3_document_upload_enforces_the_effective_limit_before_storage() -> None:
    """The canonical V3 choke point rejects oversize content before any write."""
    from api.v3_documents import create_document_and_enqueue

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            create_document_and_enqueue(
                organization_id="org-a",
                filename="huge.pdf",
                content=b"0" * (6 * _MB + 1),
                mime_type="application/pdf",
                file_type="pdf",
                data_type="utility",
                uploaded_by="user-1",
                repos=None,  # never reached: the limit blocks first
            )
        )
    assert excinfo.value.status_code == 413
    assert CODE_FILE_TOO_LARGE in str(excinfo.value.detail)

    # The configured limit is the one applied — not a module constant.
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            create_document_and_enqueue(
                organization_id="org-a",
                filename="small.pdf",
                content=b"0" * (2 * _MB),
                mime_type="application/pdf",
                file_type="pdf",
                data_type="utility",
                uploaded_by="user-1",
                repos=None,
                configured_limit_mb=1,
            )
        )
    assert excinfo.value.status_code == 413
    assert "1MB" in str(excinfo.value.detail)



def test_legacy_upload_route_uses_the_configured_limit_and_not_50mb(
    monkeypatch,
) -> None:
    """D-2: the legacy ingress enforced a hard-coded 50MB and bypassed the cap."""
    from routes import upload as upload_module

    monkeypatch.setattr(upload_module, "get_supabase_client", lambda: _Poison())

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            upload_module.upload_document(
                file=_upload_file("big.pdf", 7 * _MB),
                data_type="utility",
                organization_id="org-a",
                special_instructions=None,
                current_user=_member(),
                repos=_Bundle(max_file_size_mb=None),
            )
        )
    # 413 (the canonical code) — never the old 500 from the shadowed ``status``.
    assert excinfo.value.status_code == 413
    assert CODE_FILE_TOO_LARGE in str(excinfo.value.detail)
    assert "6MB" in str(excinfo.value.detail)

    # A file inside the old 50MB window but above the configured value is still
    # refused: the ratified ceiling can no longer be bypassed on this route.
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            upload_module.upload_document(
                file=_upload_file("big.pdf", 11 * _MB),
                data_type="utility",
                organization_id="org-a",
                special_instructions=None,
                current_user=_member(),
                repos=_Bundle(max_file_size_mb=3),
            )
        )
    assert excinfo.value.status_code == 413
    assert "3MB" in str(excinfo.value.detail)


def test_legacy_upload_route_rejects_a_foreign_organization(monkeypatch) -> None:
    """D-2/F-05-R1: the FORM organisation must be the caller's own."""
    from routes import upload as upload_module

    monkeypatch.setattr(upload_module, "get_supabase_client", lambda: _Poison())

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            upload_module.upload_document(
                file=_upload_file("meter.csv", 1024),
                data_type="utility",
                organization_id="org-b",  # not the caller's organisation
                special_instructions=None,
                current_user=_member(org_id="org-a"),
                repos=_Bundle(),
            )
        )
    assert excinfo.value.status_code == 403
    assert "access" in str(excinfo.value.detail).lower()


def test_bulk_upload_enforces_the_configured_count_and_aggregate_limits(
    monkeypatch,
) -> None:
    """The batch ingress applies the effective count *and* aggregate limits."""
    from routes.organizations import files as files_module

    monkeypatch.setattr(files_module, "get_supabase_client", lambda: _Poison())

    # Default policy: 50 files per batch → the 51st is refused (HTTP 400).
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            files_module.bulk_upload_files(
                files=[_upload_file(f"f{i}.csv", 512) for i in range(51)],
                metadata=None,
                current_user=_member(),
                repos=_Bundle(),
            )
        )
    assert excinfo.value.status_code == 400
    assert CODE_TOO_MANY_FILES in str(excinfo.value.detail)

    # A configured aggregate ceiling is enforced as a distinct trigger.
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            files_module.bulk_upload_files(
                files=[_upload_file("a.bin", 1 * _MB), _upload_file("b.bin", 1 * _MB)],
                metadata=None,
                current_user=_member(),
                repos=_Bundle(max_batch_size_mb=1),
            )
        )
    assert excinfo.value.status_code == 413
    assert CODE_BATCH_TOO_LARGE in str(excinfo.value.detail)

    # ... and a configured per-file ceiling still applies inside the batch.
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            files_module.bulk_upload_files(
                files=[_upload_file("a.bin", 2 * _MB)],
                metadata=None,
                current_user=_member(),
                repos=_Bundle(max_file_size_mb=1),
            )
        )
    assert excinfo.value.status_code == 413
    assert CODE_FILE_TOO_LARGE in str(excinfo.value.detail)


def test_no_ingress_hard_codes_a_limit() -> None:
    """A route-local limit copy is exactly how the 50MB bypass happened."""
    for relative in (
        "routes/upload.py",
        "routes/organizations/files.py",
        "api/v3_documents.py",
        "api/v3_consultants.py",
        "routes/reports.py",
    ):
        text = (BACKEND / relative).read_text(encoding="utf-8")
        assert "50 * 1024 * 1024" not in text, relative
        assert "100 * 1024 * 1024" not in text, relative


def test_every_upload_ingress_resolves_the_canonical_policy() -> None:
    """Each ingress either resolves the policy itself or passes it down."""
    canonical = (BACKEND / "api" / "v3_documents.py").read_text(encoding="utf-8")
    assert "resolve_policy" in canonical
    assert "configured_limit_mb" in canonical

    legacy_upload = (BACKEND / "routes" / "upload.py").read_text(encoding="utf-8")
    assert "resolve_policy" in legacy_upload
    assert "enforce_single_file" in legacy_upload
    # The status-shadowing defect must not return: no bare ``status`` local may
    # be assigned in that module (``file_status`` is the corrected name).
    assert not re.search(r"^\s*status\s*=", legacy_upload, re.MULTILINE)

    legacy_org = (BACKEND / "routes" / "organizations" / "files.py").read_text(
        encoding="utf-8"
    )
    assert "resolve_policy" in legacy_org
    assert "enforce_single_file" in legacy_org
    assert "enforce_batch" in legacy_org

    consultants = (BACKEND / "api" / "v3_consultants.py").read_text(encoding="utf-8")
    assert "resolve_policy" in consultants

    reports = (BACKEND / "routes" / "reports.py").read_text(encoding="utf-8")
    assert "resolve_policy" in reports



# ---------------------------------------------------------------------------
# storage layer — bucket limit + private (direct-to-storage configuration)
# ---------------------------------------------------------------------------


def _bucket_migration() -> str:
    repo_root = Path(__file__).resolve().parents[4]
    return (
        repo_root
        / "supabase"
        / "migrations"
        / "20261024000000_ct_final_01_documents_bucket_size_limit.sql"
    ).read_text(encoding="utf-8")


def test_documents_bucket_size_limit_migration_pins_the_ratified_cap() -> None:
    text = _bucket_migration()
    assert "10485760" in text, "the ratified 10MB cap must be pinned"
    assert '"documents"' in text or "'documents'" in text
    assert "file_size_limit" in text


def test_documents_bucket_migration_is_idempotent_and_storage_aware() -> None:
    text = _bucket_migration()
    # A storage-less database must not break the chain (guarded no-op).
    assert "to_regclass('storage.buckets') IS NULL" in text
    assert "RETURN;" in text
    # Configuration may only tighten: a smaller limit must never be raised.
    assert "file_size_limit IS NULL OR file_size_limit > ratified_limit" in text
    # The private end state is re-asserted (D32) and verified fail-closed.
    assert "SET public = FALSE" in text
    assert "RAISE EXCEPTION" in text


def test_documents_bucket_migration_targets_no_application_table() -> None:
    """The migration is storage configuration only — no application change."""
    text = _bucket_migration()
    lowered = text.lower()
    for forbidden in ("alter table public.", "drop table", "delete from", "truncate"):
        assert forbidden not in lowered


def test_demo_lab_provisions_the_documents_bucket_at_the_ratified_cap() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    lab = (repo_root / "tools" / "demo_lab" / "storage.py").read_text(encoding="utf-8")
    assert "10485760" in lab
    assert "artefact" in lab.lower()

