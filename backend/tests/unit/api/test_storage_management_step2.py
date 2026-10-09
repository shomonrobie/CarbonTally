"""Storage Management Step 2 — completion-layer tests.

Covers the Step 2 deliverables that sit on top of the Step 1 foundation:

* the browser-facing direct-upload contract (start → signed PUT → completion);
* the explicit malware-scanning configuration and its fail-closed states
  (clean / malware / scanner-unavailable / scanner-error / structural rejection)
  with no false "virus scanned" claim;
* abandoned-upload reaping (idempotent, non-destructive, bounded by the existing
  completion window) and the recorded physical-disposition gap;
* hardening of the three legacy ingresses (shared gate + security gate before any
  write + canonical tenant key + signed URL instead of a public URL);
* derived-artefact provenance (the original is never replaced);
* the storage-layer limit alignment migration;
* the report-artefact model (private bucket, ratified key, append-only);
* entitlement integration (metered through the existing billing model);
* consultant provenance across relationship end and direct-customer conversion.

No storage, no database and no network: the storage surface and the processing
enqueue are replaced with in-memory doubles.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from services.document_cleanup import (
    physical_disposition_policy,
    reap_abandoned_uploads,
    reap_cutoff,
)
from services.document_security import (
    SCAN_STATE_CLEAN,
    SCAN_STATE_MALWARE,
    SCAN_STATE_SCANNER_ERROR,
    SCAN_STATE_SCANNER_UNAVAILABLE,
    SCAN_STATE_STRUCTURAL_REJECTION,
    SCANNER_ENV_VAR,
    SCANNER_REQUIRED_ENV_VAR,
    STATUS_CLEAN,
    STATUS_PENDING_UPLOAD,
    STATUS_REJECTED,
    STATUS_UPLOAD_EXPIRED,
    can_transition,
    external_scan_status,
    installed_scanners,
    is_downloadable,
    is_processable,
    register_scanner,
    resolve_scanner,
    scan_document,
    unregister_scanner,
)
from services.storage import UPLOAD_COMPLETION_WINDOW_SECONDS
from services.storage_keys import (
    DERIVED_KEY_SEGMENT,
    build_derived_artifact_key,
    build_document_storage_key,
    is_derived_artifact_key,
)
from tests.unit.api.fakes import consultant_user, member_user, org_viewer_user

BACKEND = Path(__file__).resolve().parents[3]
REPO_ROOT = BACKEND.parent

ORG_A = "org-a"
ORG_B = "org-b"
MB = 1024 * 1024

PDF_BYTES = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\n%%EOF\n"
EICAR_BYTES = b"%PDF-1.4\n" + (
    b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
)


class _FakeStorage:
    """In-memory stand-in for the Supabase Storage surface the flow uses."""

    def __init__(self, objects: dict[str, bytes] | None = None) -> None:
        self.objects: dict[str, bytes] = dict(objects or {})
        self.signed_uploads: list[str] = []

    def create_signed_upload_url(self, path: str, bucket: str | None = None) -> dict:
        self.signed_uploads.append(path)
        return {
            "url": f"https://storage.example/object/upload/sign/documents/{path}?token=tok",
            "token": "tok-123",
            "path": path,
            "expires_in": 900,
        }

    def object_info(self, path: str, bucket: str | None = None) -> dict | None:
        if path not in self.objects:
            return None
        return {"size": len(self.objects[path]), "mimetype": "application/pdf"}

    def download_object(
        self, path: str, max_bytes: int | None = None, bucket: str | None = None
    ) -> bytes | None:
        if path not in self.objects:
            return None
        raw = self.objects[path]
        return raw if max_bytes is None else raw[:max_bytes]

    def download_object_prefix(
        self, path: str, max_bytes: int = 262_144, bucket: str | None = None
    ) -> bytes | None:
        return self.download_object(path, max_bytes)


class _EnqueueRecorder:
    """Capture the processing-pipeline enqueue calls (must be CLEAN-only)."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def __call__(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        return kwargs.get("record")


@pytest.fixture
def storage(monkeypatch):
    import api.v3_document_uploads as uploads

    fake = _FakeStorage()
    monkeypatch.setattr(uploads, "create_signed_upload_url", fake.create_signed_upload_url)
    monkeypatch.setattr(uploads, "object_info", fake.object_info)
    monkeypatch.setattr(uploads, "download_object", fake.download_object)
    monkeypatch.setattr(uploads, "download_object_prefix", fake.download_object_prefix)
    return fake


@pytest.fixture
def enqueued(monkeypatch):
    import api.v3_document_uploads as uploads

    recorder = _EnqueueRecorder()
    monkeypatch.setattr(uploads, "enqueue_document_processing", recorder)
    return recorder


@pytest.fixture(autouse=True)
def _clean_scanner_env(monkeypatch):
    """No test inherits another test's scanner configuration."""
    monkeypatch.delenv(SCANNER_ENV_VAR, raising=False)
    monkeypatch.delenv(SCANNER_REQUIRED_ENV_VAR, raising=False)
    yield
    for provider in installed_scanners():
        unregister_scanner(provider)


def _org_initiate(client, user_provider, *, user=None, **overrides):
    payload = {
        "organization_id": ORG_A,
        "filename": "invoice.pdf",
        "size_bytes": len(PDF_BYTES),
        "content_type": "application/pdf",
        "data_type": "utility",
    }
    payload.update(overrides)
    user_provider.set_user(user or member_user(ORG_A, "u-1", "u1@example.test"))
    return client.post("/api/v3/documents/upload-url", json=payload)


def _complete(client, document_id: str):
    return client.post(f"/api/v3/documents/{document_id}/upload-complete")


def _actions(world) -> list[str]:
    return [entry.action for entry in world.audit._entries]


# ---------------------------------------------------------------------------
# Step 2D — malware/scanner state machine (fail-closed, no false claims)
# ---------------------------------------------------------------------------


def test_scan_states_are_distinct_and_the_structural_pass_is_clean() -> None:
    verdict = scan_document(
        content=PDF_BYTES, filename="invoice.pdf", declared_mime="application/pdf"
    )
    assert verdict.accepted is True
    assert verdict.scan_state == SCAN_STATE_CLEAN
    assert verdict.scanner == "structural"
    assert verdict.external_scan_available is False
    # The verdict never claims a virus scan it did not perform.
    assert verdict.external_scan_claimed() is False
    assert verdict.as_metadata()["virus_scanned"] is False


def test_malware_signature_is_reported_as_malware_not_structural() -> None:
    verdict = scan_document(
        content=EICAR_BYTES, filename="invoice.pdf", declared_mime="application/pdf"
    )
    assert verdict.accepted is False
    assert verdict.scan_state == SCAN_STATE_MALWARE
    assert verdict.status == STATUS_REJECTED
    assert "malware_signature" in {f.code for f in verdict.blockers}
    assert verdict.external_scan_claimed() is False


def test_structural_rejection_is_distinct_from_malware() -> None:
    verdict = scan_document(
        content=b"MZ\x90\x00definitely-not-a-pdf",
        filename="invoice.pdf",
        declared_mime="application/pdf",
    )
    assert verdict.accepted is False
    assert verdict.scan_state == SCAN_STATE_STRUCTURAL_REJECTION
    assert verdict.status == STATUS_REJECTED


def test_scanner_registry_installs_a_provider_without_inventing_one(monkeypatch) -> None:
    assert installed_scanners() == ()
    assert resolve_scanner().name == "structural"

    class _Provider:
        name = "example-av"

        def scan(self, *, content, filename, declared_mime, extension):
            from services.document_security import ScanVerdict

            return ScanVerdict(
                verdict=STATUS_CLEAN,
                scanner=self.name,
                scanned_bytes=len(content),
                external_scan_available=True,
            )

    register_scanner("example-av", _Provider)
    assert installed_scanners() == ("example-av",)
    # The provider is only used when the deployment configures it.
    monkeypatch.setenv(SCANNER_ENV_VAR, "example-av")
    assert resolve_scanner().name == "example-av"
    verdict = scan_document(
        content=PDF_BYTES, filename="invoice.pdf", declared_mime="application/pdf"
    )
    assert verdict.accepted is True
    assert verdict.external_scan_claimed() is True


def test_a_required_external_scan_that_is_unavailable_quarantines_the_document(
    monkeypatch,
) -> None:
    """Scanner-unavailable must NEVER be collapsed into clean (Step 2D)."""
    monkeypatch.setenv(SCANNER_REQUIRED_ENV_VAR, "true")
    verdict = scan_document(
        content=PDF_BYTES, filename="invoice.pdf", declared_mime="application/pdf"
    )
    assert verdict.accepted is False
    assert verdict.status == STATUS_REJECTED
    assert verdict.scan_state == SCAN_STATE_SCANNER_UNAVAILABLE
    assert verdict.external_scan_required is True
    assert "scanner_unavailable" in {f.code for f in verdict.blockers}
    assert verdict.as_metadata()["virus_scanned"] is False


def test_a_broken_scanner_fails_closed_rather_than_open(monkeypatch) -> None:
    class _Exploding:
        name = "exploding-av"

        def scan(self, **kwargs):
            raise RuntimeError("provider unavailable")

    verdict = scan_document(
        content=PDF_BYTES,
        filename="invoice.pdf",
        declared_mime="application/pdf",
        scanner=_Exploding(),
    )
    assert verdict.accepted is False
    assert verdict.scan_state == SCAN_STATE_SCANNER_ERROR
    assert verdict.scanner_error


def test_scanning_configuration_is_explicit_and_read_only(monkeypatch) -> None:
    monkeypatch.setenv(SCANNER_ENV_VAR, "not-installed-vendor")
    status = external_scan_status()
    assert status["configured_provider"] == "not-installed-vendor"
    assert status["external_scan_available"] is False
    assert status["built_in_scanner"] == "structural"
    # An uninstalled provider still degrades honestly to the structural gate.
    assert resolve_scanner().name == "structural"


# ---------------------------------------------------------------------------
# Step 2F/2E — abandoned uploads: terminal state, idempotent non-destructive reap
# ---------------------------------------------------------------------------


def _age_row(world, document_id: str, *, seconds: int) -> None:
    """Backdate a pending document row inside the in-memory files fake."""
    row = world.files._by_id[str(document_id)]
    row["uploaded_at"] = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    world.files._by_id[str(document_id)] = row


def test_expired_pending_upload_state_is_terminal_and_never_processable() -> None:
    assert can_transition(STATUS_PENDING_UPLOAD, STATUS_UPLOAD_EXPIRED) is True
    assert can_transition(STATUS_UPLOAD_EXPIRED, STATUS_CLEAN) is False
    assert can_transition(STATUS_UPLOAD_EXPIRED, STATUS_PENDING_UPLOAD) is False
    assert is_processable(STATUS_UPLOAD_EXPIRED) is False
    assert is_downloadable(STATUS_UPLOAD_EXPIRED) is False


def test_reap_cutoff_uses_the_existing_completion_window() -> None:
    now = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    cutoff = reap_cutoff(now=now)
    assert (now - cutoff).total_seconds() == UPLOAD_COMPLETION_WINDOW_SECONDS


def test_abandoned_upload_reaping_reports_without_writing_by_default(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    document_id = started.json()["document_id"]
    _age_row(world, document_id, seconds=UPLOAD_COMPLETION_WINDOW_SECONDS + 60)

    report = asyncio.run(reap_abandoned_uploads(world.bundle()))
    assert report["dry_run"] is True
    assert report["eligible"] == 1
    assert report["changed"] == 0
    assert report["document_ids"] == [document_id]
    # Nothing was written and nothing was deleted.
    assert world.files._by_id[document_id]["status"] == STATUS_PENDING_UPLOAD
    assert report["objects_deleted"] == 0
    assert "document.cleanup" not in _actions(world)


def test_abandoned_upload_reaping_is_idempotent_and_audited(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    document_id = started.json()["document_id"]
    _age_row(world, document_id, seconds=UPLOAD_COMPLETION_WINDOW_SECONDS + 60)

    first = asyncio.run(reap_abandoned_uploads(world.bundle(), dry_run=False))
    assert first["changed"] == 1
    assert first["objects_deleted"] == 0
    assert world.files._by_id[document_id]["status"] == STATUS_UPLOAD_EXPIRED
    actions = _actions(world)
    assert "document.upload_authorisation_expired" in actions
    assert "document.cleanup" in actions
    # The row (and its provenance) still exists — it was never deleted.
    assert world.files._by_id[document_id]["organization_id"] == ORG_A

    second = asyncio.run(reap_abandoned_uploads(world.bundle(), dry_run=False))
    assert second["eligible"] == 0
    assert second["changed"] == 0


def test_reaping_never_touches_a_document_that_was_accepted(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    body = started.json()
    storage.objects[body["storage_path"]] = PDF_BYTES
    assert _complete(client, body["document_id"]).status_code == 200
    _age_row(world, body["document_id"], seconds=UPLOAD_COMPLETION_WINDOW_SECONDS + 60)

    report = asyncio.run(reap_abandoned_uploads(world.bundle(), dry_run=False))
    assert report["eligible"] == 0
    assert world.files._by_id[body["document_id"]]["status"] == STATUS_CLEAN


def test_a_reaped_upload_can_never_be_completed_later(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    document_id = started.json()["document_id"]
    _age_row(world, document_id, seconds=UPLOAD_COMPLETION_WINDOW_SECONDS + 60)
    asyncio.run(reap_abandoned_uploads(world.bundle(), dry_run=False))

    refused = _complete(client, document_id)
    assert refused.status_code == 409
    assert "cannot be completed" in refused.text
    assert enqueued.calls == []


def test_reaping_reports_when_the_repository_cannot_support_it() -> None:
    class _NoLister:
        pass

    class _Repos:
        files = _NoLister()

    report = asyncio.run(reap_abandoned_uploads(_Repos()))
    assert report["supported"] is False
    assert "list_abandoned_pending_uploads" in report["reason"]


def test_rejected_and_orphaned_object_deletion_is_not_authorized() -> None:
    """Step 2E: no ratified destruction rule → no destructive behaviour exists."""
    policy = physical_disposition_policy()
    assert policy["rejected_objects"]["physical_deletion"] == "not_authorized"
    assert policy["orphaned_objects"]["physical_deletion"] == "not_authorized"
    assert policy["expired_pending_uploads"]["physical_deletion"] == "not_authorized"
    # The retention duration is only ever the configured one.
    assert "document_retention_days" in policy["retention_duration_source"]


# ---------------------------------------------------------------------------
# Step 2A/2J — the browser-facing direct-upload contract + processing parity
# ---------------------------------------------------------------------------


def test_the_upload_authorisation_advertises_the_security_posture(
    client, world, user_provider, storage
) -> None:
    started = _org_initiate(client, user_provider)
    assert started.status_code == 201
    body = started.json()
    # The browser is told exactly what will scan the bytes, and no credential.
    gate = body["security_gate"]
    assert gate["configured_provider"] is None
    assert gate["external_scan_required"] is False
    assert gate["built_in_scanner"] == "structural"
    assert gate["external_scan_available"] is False
    assert body["upload"]["expires_in_seconds"] == 900
    assert "service" not in body["upload"]["url"].lower()
    assert "token" in body["upload"]["url"]  # object-scoped authorisation only


def test_direct_completion_passes_the_verified_bytes_to_the_pipeline(
    client, world, user_provider, storage, enqueued
) -> None:
    """Step 2J — a direct upload must not lose OCR/page-count parity."""
    started = _org_initiate(client, user_provider)
    body = started.json()
    storage.objects[body["storage_path"]] = PDF_BYTES

    completed = _complete(client, body["document_id"])
    assert completed.status_code == 200, completed.text
    assert len(enqueued.calls) == 1
    assert enqueued.calls[0]["content"] == PDF_BYTES
    assert enqueued.calls[0]["storage_path"] == body["storage_path"]
    assert enqueued.calls[0]["document_id"] == body["document_id"]


def test_the_accepted_document_records_its_scan_state_without_a_virus_claim(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    body = started.json()
    storage.objects[body["storage_path"]] = PDF_BYTES

    completed = _complete(client, body["document_id"])
    payload = completed.json()
    assert payload["status"] == STATUS_CLEAN
    assert payload["scan_state"] == SCAN_STATE_CLEAN
    assert payload["virus_scanned"] is False
    assert payload["external_scan_available"] is False
    assert payload["security_gate"]["scanner"] == "structural"
    row = world.files._by_id[body["document_id"]]
    assert row["status"] == STATUS_CLEAN
    assert row["metadata"]["security_gate"]["scan_state"] == SCAN_STATE_CLEAN
    assert row["metadata"]["security_gate"]["virus_scanned"] is False


def test_a_required_external_scan_quarantines_a_would_be_clean_upload(
    client, world, user_provider, storage, enqueued, monkeypatch
) -> None:
    monkeypatch.setenv(SCANNER_REQUIRED_ENV_VAR, "true")
    started = _org_initiate(client, user_provider)
    body = started.json()
    storage.objects[body["storage_path"]] = PDF_BYTES

    rejected = _complete(client, body["document_id"])
    assert rejected.status_code == 422
    assert world.files._by_id[body["document_id"]]["status"] == STATUS_REJECTED
    assert enqueued.calls == []
    actions = _actions(world)
    assert "document.security_scan_unavailable" in actions
    assert "document.security_rejected" in actions


def test_a_quarantined_document_is_never_downloadable(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    body = started.json()
    storage.objects[body["storage_path"]] = EICAR_BYTES

    assert _complete(client, body["document_id"]).status_code == 422
    assert enqueued.calls == []

    refused = client.get(f"/api/v3/documents/{body['document_id']}/signed-url")
    assert refused.status_code == 409
    assert "security gate" in refused.text


def test_storage_metering_is_reported_and_never_blocks_an_upload(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    body = started.json()
    storage.objects[body["storage_path"]] = PDF_BYTES

    completed = _complete(client, body["document_id"])
    assert completed.status_code == 200
    metering = completed.json()["storage_metering"]
    assert isinstance(metering, dict)
    assert "recorded" in metering
    assert metering["integration"] == "billing_storage_usage"


def test_entitlement_integration_states_exactly_what_is_and_is_not_wired() -> None:
    from services.storage_metering import capacity_integration_status

    status = capacity_integration_status()
    assert "billing_plans" in status["integrated"]["included_storage_bytes"]
    assert "meter_storage" in status["integrated"]["metering"]
    # No parallel entitlement system, and no invented upload refusal.
    assert "second_entitlement_system" in status["not_integrated"]
    assert "upload_refusal_on_capacity" in status["not_integrated"]


# ---------------------------------------------------------------------------
# Step 2B/2C — legacy ingresses: same gate, same canonical keys, no public URL
# ---------------------------------------------------------------------------


class _Settings:
    def __init__(self, **overrides) -> None:
        self._overrides = overrides

    async def get_upload_policy(self):
        return dict(self._overrides)


class _Audit:
    def __init__(self) -> None:
        self.entries: list = []

    async def record(self, entry) -> None:
        self.entries.append(entry)


class _Bundle:
    """Minimal repository bundle for the legacy routes (policy + audit only)."""

    def __init__(self, **policy_overrides) -> None:
        self.settings = _Settings(**policy_overrides)
        self.audit = _Audit()


class _Response:
    def __init__(self, data):
        self.data = data


class _Table:
    """Chainable in-memory table double (select/insert/update + eq + execute)."""

    def __init__(self, name: str, sink: dict) -> None:
        self.name = name
        self.sink = sink
        self._rows: list = []

    def select(self, *args, **kwargs):
        self._rows = self.sink.setdefault(self.name, [])
        return self

    def insert(self, payload):
        row = dict(payload)
        row.setdefault("id", f"row-{len(self.sink.get(self.name, [])) + 1}")
        self.sink.setdefault(self.name, []).append(row)
        self._rows = list(self.sink[self.name])
        return self

    def update(self, payload):
        self._rows = [dict(payload)]
        return self

    def eq(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def maybe_single(self):
        return self

    def execute(self):
        return _Response(self._rows)


class _Bucket:
    def __init__(self, sink: dict) -> None:
        self.sink = sink

    def upload(self, path, data, file_options=None):
        self.sink.setdefault("storage_uploads", []).append(
            {
                "path": path,
                "bytes": len(data) if data is not None else 0,
                "options": file_options or {},
            }
        )
        return {"path": path}

    def get_public_url(self, path):  # must never be called (Step 2C)
        raise AssertionError("a customer document must never be given a public URL")

    def create_signed_url(self, path, expires_in=3600):
        return {"signedURL": f"https://signed.example/documents/{path}?token=t"}


class _Storage:
    def __init__(self, sink: dict) -> None:
        self.sink = sink

    def from_(self, bucket):
        self.sink.setdefault("buckets", []).append(bucket)
        return _Bucket(self.sink)


class _LegacyClient:
    def __init__(self) -> None:
        self.sink: dict = {}
        self.storage = _Storage(self.sink)

    def from_(self, name):
        return _Table(name, self.sink)

    @property
    def uploads(self) -> list:
        return self.sink.get("storage_uploads", [])


def _upload_file(filename: str, payload: bytes, content_type: str = "text/csv") -> UploadFile:
    import io

    return UploadFile(
        file=io.BytesIO(payload),
        filename=filename,
        headers={"content-type": content_type},
    )


CSV_BYTES = b"period,kwh\n2026-01,1200\n2026-02,980\n"


def test_legacy_api_upload_runs_the_security_gate_before_any_write(monkeypatch) -> None:
    """Step 2B — the legacy ingress may not store unvalidated content."""
    from routes import upload as upload_module

    client_double = _LegacyClient()
    monkeypatch.setattr(upload_module, "get_supabase_client", lambda: client_double)

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            upload_module.upload_document(
                file=_upload_file("invoice.pdf", EICAR_BYTES, "application/pdf"),
                data_type="utility",
                organization_id=ORG_A,
                special_instructions=None,
                current_user=member_user(ORG_A, "u-1", "u1@example.test"),
                repos=_Bundle(),
            )
        )
    assert excinfo.value.status_code == 422
    assert "security gate" in str(excinfo.value.detail)
    # Nothing was written: no object and no row.
    assert client_double.uploads == []
    assert client_double.sink.get("organization_files", []) == []


def test_legacy_api_upload_uses_a_canonical_key_and_a_signed_url(monkeypatch) -> None:
    from routes import upload as upload_module

    client_double = _LegacyClient()
    monkeypatch.setattr(upload_module, "get_supabase_client", lambda: client_double)
    monkeypatch.setattr(
        upload_module, "storage_signed_url", lambda path, *a, **k: f"signed::{path}"
    )

    result = asyncio.run(
        upload_module.upload_document(
            file=_upload_file("meter.csv", CSV_BYTES),
            data_type="utility",
            organization_id=ORG_A,
            special_instructions="feb reading",
            current_user=member_user(ORG_A, "u-1", "u1@example.test"),
            repos=_Bundle(),
        )
    )
    assert len(client_double.uploads) == 1
    stored_path = client_double.uploads[0]["path"]
    assert stored_path.startswith(f"uploads/{ORG_A}/")
    # The user file name is provenance only — never path identity.
    assert "meter.csv" not in stored_path
    assert stored_path.endswith(".csv")
    assert result["file_url"] == f"signed::{stored_path}"
    row = client_double.sink["organization_files"][-1]
    assert row["path"] == stored_path
    assert row["metadata"]["security_gate"]["scan_state"] == SCAN_STATE_CLEAN
    assert row["metadata"]["security_gate"]["virus_scanned"] is False


def test_legacy_org_files_upload_denies_a_viewer_before_any_write(monkeypatch) -> None:
    from routes.organizations import files as files_module

    client_double = _LegacyClient()
    monkeypatch.setattr(files_module, "get_supabase_client", lambda: client_double)

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            files_module.upload_file(
                org_id=ORG_A,
                file=_upload_file("meter.csv", CSV_BYTES),
                asset_id=None,
                document_type_code=None,
                billing_period_start=None,
                billing_period_end=None,
                facility_id=None,
                notes=None,
                current_user=org_viewer_user(ORG_A, "u-2", "v@example.test"),
                repos=_Bundle(),
            )
        )
    assert excinfo.value.status_code == 403
    assert "read-only" in str(excinfo.value.detail)
    assert client_double.uploads == []


def test_legacy_org_files_upload_is_hardened_in_source() -> None:
    """Step 2B/2C/2Q — no public URL, no org-less prefix, shared gate + scan."""
    text = (BACKEND / "routes" / "organizations" / "files.py").read_text(encoding="utf-8")
    assert "get_public_url" not in text
    assert "authorize_organization_upload" in text
    assert "scan_document(" in text
    assert "build_document_storage_key" in text
    # The document-upload route no longer derives the key from the file name in
    # the legacy org-less prefix (the bulk route keeps its own legacy path).
    upload_handler = text.split('@router.post("/api/organizations/{org_id}/files/upload")')[1]
    upload_handler = upload_handler.split("@router.")[0]
    assert "get_organization_upload_path(" not in upload_handler
    assert "build_document_storage_key(org_id" in upload_handler


def test_legacy_upload_routes_are_hardened_in_source() -> None:
    text = (BACKEND / "routes" / "upload.py").read_text(encoding="utf-8")
    assert "get_public_url" not in text
    assert "authorize_organization_upload" in text
    assert "scan_document(" in text
    assert "build_derived_artifact_key" in text
    # No new object is written to the legacy org-less repaired_pdfs prefix.
    assert 'f"repaired_pdfs/' not in text
    # The derived artefact is labelled as such and never replaces the original.
    assert '"derived": True' in text
    assert '"original_replaced": False' in text


# ---------------------------------------------------------------------------
# Step 2P — derived artefacts are distinct objects in the client's namespace
# ---------------------------------------------------------------------------


def test_derived_artefact_key_is_distinct_and_tenant_scoped() -> None:
    key = build_derived_artifact_key(ORG_A, "repaired.pdf")
    parts = key.split("/")
    assert parts[0] == "uploads"
    assert parts[1] == ORG_A
    assert parts[2] == DERIVED_KEY_SEGMENT
    assert parts[-1].endswith(".pdf")
    assert is_derived_artifact_key(key)
    # It is deliberately NOT the canonical document key, so a derived artefact
    # can never be mistaken for (or overwrite) the original evidence object.
    assert build_document_storage_key(ORG_A, "repaired.pdf") != key
    # Two derived artefacts never collide.
    assert build_derived_artifact_key(ORG_A, "repaired.pdf") != key


def test_derived_artefact_key_rejects_a_path_injecting_tenant() -> None:
    for bad in ("org/../other", "..", ""):
        with pytest.raises(ValueError):
            build_derived_artifact_key(bad, "repaired.pdf")


def test_the_storage_helpers_never_rewrite_a_stored_document() -> None:
    """Step 2P — the module that owns storage has no update/overwrite surface."""
    text = (BACKEND / "services" / "storage.py").read_text(encoding="utf-8")
    assert "upsert" not in text
    assert ".update(" not in text
    assert "remove(" not in text


# ---------------------------------------------------------------------------
# Step 2I — application vs storage-layer limits
# ---------------------------------------------------------------------------


def _step2_migration() -> str:
    return (
        REPO_ROOT
        / "supabase"
        / "migrations"
        / "20261025000000_ct_step2_documents_bucket_size_alignment.sql"
    ).read_text(encoding="utf-8")


def test_the_ratified_limits_are_unchanged_and_single_sourced() -> None:
    from utils.upload_limits import (
        DEFAULT_MAX_FILE_SIZE_MB,
        PLATFORM_MAX_FILE_SIZE_MB,
        effective_file_limit_bytes,
    )

    assert PLATFORM_MAX_FILE_SIZE_MB == 10  # ratified cap — unchanged by Step 2
    assert DEFAULT_MAX_FILE_SIZE_MB == 6  # effective default when unconfigured
    assert effective_file_limit_bytes() == 6 * MB
    assert effective_file_limit_bytes(10) == 10 * MB


def test_the_storage_layer_alignment_migration_pins_the_ratified_cap() -> None:
    text = _step2_migration()
    assert "10485760" in text
    assert "file_size_limit" in text
    assert "'documents'" in text
    # Storage-less databases must not break the chain, and the file is idempotent.
    assert "to_regclass('storage.buckets') IS NULL" in text
    assert "RETURN;" in text
    assert "SET public = FALSE" in text
    assert "RAISE EXCEPTION" in text
    # It aligns in BOTH directions — a lower storage cap must not silently
    # refuse uploads the application would accept (the Step 2I defect).
    assert "file_size_limit IS NULL OR file_size_limit <> ratified_limit" in text


def test_the_storage_alignment_migration_is_storage_only() -> None:
    lowered = _step2_migration().lower()
    for forbidden in ("alter table public.", "drop table", "delete from", "truncate"):
        assert forbidden not in lowered
    # It never writes to the report-artefact bucket or any other bucket: the only
    # bucket it addresses is `documents`.
    assert "name = 'documents'" in lowered
    assert "name = 'report-artifacts'" not in lowered
    assert "report_version_artifacts" not in lowered


def test_the_historical_ct_final_01_migration_was_not_rewritten() -> None:
    """Step 2U — historical migrations are not modified to make tests pass."""
    historical = (
        REPO_ROOT
        / "supabase"
        / "migrations"
        / "20261024000000_ct_final_01_documents_bucket_size_limit.sql"
    ).read_text(encoding="utf-8")
    assert "file_size_limit IS NULL OR file_size_limit > ratified_limit" in historical
    assert "10485760" in historical


def test_the_alignment_migration_follows_the_existing_chain() -> None:
    migrations = sorted(
        path.name for path in (REPO_ROOT / "supabase" / "migrations").glob("*.sql")
    )
    step2 = "20261025000000_ct_step2_documents_bucket_size_alignment.sql"
    step1 = "20261024000000_ct_final_01_documents_bucket_size_limit.sql"
    assert step2 in migrations
    assert migrations.index(step2) > migrations.index(step1)
    # Step 2 is the migration that immediately follows Step 1 — the invariant this
    # test owns.  It deliberately does NOT claim to be the chain tip: a later
    # revision (BACKUP-01's 20261026000000 backup_jobs migration) legitimately
    # sorts after it, and asserting `migrations[-1] == step2` would make every
    # subsequent migration fail this test for no reason.
    assert migrations.index(step2) == migrations.index(step1) + 1


# ---------------------------------------------------------------------------
# Step 2M — the report-artefact model (private, ratified key, append-only)
# ---------------------------------------------------------------------------


def test_report_artefact_model_is_private_ratified_and_append_only() -> None:
    from domain.report_artefact import (
        ARTEFACT_BUCKET,
        ARTEFACT_CONTENT_TYPE,
        object_key_for,
    )
    from services.report_artefact_storage import (
        InMemoryReportArtefactStorage,
        SupabaseReportArtefactStorage,
    )

    assert ARTEFACT_BUCKET == "report-artifacts"
    assert ARTEFACT_CONTENT_TYPE == "application/pdf"
    assert object_key_for("org-a", "rep-1", "ver-1") == "org-a/rep-1/ver-1.pdf"

    store = InMemoryReportArtefactStorage()
    assert store.bucket == ARTEFACT_BUCKET
    key = object_key_for("org-a", "rep-1", "ver-1")
    store.upload(object_key=key, payload=b"%PDF-1.4 frozen")
    assert store.exists(object_key=key) is True
    # Append-only: an existing frozen artefact is never overwritten.
    with pytest.raises(FileExistsError):
        store.upload(object_key=key, payload=b"%PDF-1.4 different")
    assert store.objects[key] == b"%PDF-1.4 frozen"
    assert key in store.signed_url(object_key=key)
    # The real adapter checks the private bucket's provisioning; no public-URL
    # path exists at all on this model.
    assert hasattr(SupabaseReportArtefactStorage(), "bucket_exists")


def test_step_2_does_not_move_documents_into_the_report_artefact_bucket() -> None:
    keys = (BACKEND / "services" / "storage_keys.py").read_text(encoding="utf-8")
    uploads = (BACKEND / "api" / "v3_document_uploads.py").read_text(encoding="utf-8")
    legacy = (BACKEND / "routes" / "upload.py").read_text(encoding="utf-8")
    for text in (keys, uploads, legacy):
        assert "report-artifacts" not in text
        assert "report_artifacts" not in text


# ---------------------------------------------------------------------------
# Step 2H — storage access model: backend-authorized signed access only
# ---------------------------------------------------------------------------


def test_the_direct_flow_never_needs_direct_user_jwt_storage_access() -> None:
    """The client organisation remains the owner; authorization stays server-side."""
    uploads = (BACKEND / "api" / "v3_document_uploads.py").read_text(encoding="utf-8")
    assert "get_service_client" not in uploads  # no credential in the API layer
    assert "get_user_client" not in uploads
    storage = (BACKEND / "services" / "storage.py").read_text(encoding="utf-8")
    assert "get_service_client" in storage  # the single credential boundary
    assert "create_signed_upload_url" in storage


def test_the_d32_storage_policies_are_unchanged() -> None:
    d32 = (
        REPO_ROOT
        / "supabase"
        / "migrations"
        / "20260823000000_d32_private_documents_storage.sql"
    ).read_text(encoding="utf-8")
    # The client organisation stays the storage tenancy anchor: no consultant
    # branch is added to storage RLS by Step 2.
    assert "(storage.foldername(name))[1] = 'uploads'" in d32
    assert "organization_members" in d32


# ---------------------------------------------------------------------------
# Step 2K — consultant provenance without a second storage tenancy
# ---------------------------------------------------------------------------


def _seed_consultant(
    world, user_id="u-cons", *, can_upload_documents=True, client_status="active"
):
    world.consultants.seed_profile("firm-1", user_id, "Acme Consultants")
    world.consultants.seed_firm_member(
        "firm-1",
        user_id,
        role="manager",
        can_manage_clients=True,
        can_upload_documents=can_upload_documents,
        can_generate_reports=True,
        can_manage_team=True,
    )
    world.consultants.seed_client(
        "client-a", "firm-1", ORG_A, "ACME LTD", status=client_status
    )
    world.consultants.seed_client("client-c", "firm-2", "org-c", "Example Retail")
    return consultant_user(user_id, "cons@example.test")


def _consultant_initiate(client, world, user_provider, **kwargs):
    user_provider.set_user(_seed_consultant(world, **kwargs))
    return client.post(
        "/api/v3/consultants/clients/client-a/documents/upload-url",
        json={
            "filename": "client-invoice.pdf",
            "size_bytes": len(PDF_BYTES),
            "content_type": "application/pdf",
            "data_type": "utility",
        },
    )


def test_consultant_direct_upload_keeps_client_ownership_and_provenance(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _consultant_initiate(client, world, user_provider)
    assert started.status_code == 201, started.text
    body = started.json()
    assert body["organization_id"] == ORG_A  # the client owns the bytes
    assert body["storage_path"].startswith(f"uploads/{ORG_A}/")
    assert "firm-1" not in body["storage_path"]
    storage.objects[body["storage_path"]] = PDF_BYTES

    completed = client.post(
        f"/api/v3/consultants/clients/client-a/documents/{body['document_id']}/upload-complete"
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["organization_id"] == ORG_A
    row = world.files._by_id[body["document_id"]]
    assert row["organization_id"] == ORG_A
    assert row["metadata"]["upload_actor_type"] == "consultant"
    assert row["metadata"]["uploaded_by_consultant_firm_id"] == "firm-1"
    assert row["metadata"]["consultant_originated"] is True


def test_an_ended_consultant_grant_cannot_complete_a_direct_upload(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _consultant_initiate(client, world, user_provider)
    body = started.json()
    storage.objects[body["storage_path"]] = PDF_BYTES

    # The client relationship ends between initiation and completion.
    # (The fake appends client rows, so the EXISTING grant is flipped in place —
    # appending a second row would leave the original active one discoverable.)
    from dataclasses import replace as _replace

    rows = world.consultants._clients
    for index, row in enumerate(rows):
        if getattr(row, "id", None) == "client-a":
            rows[index] = _replace(row, status="ended")
    refused = client.post(
        f"/api/v3/consultants/clients/client-a/documents/{body['document_id']}/upload-complete"
    )
    assert refused.status_code in (403, 404)
    assert enqueued.calls == []
    # No byte was moved and the pending row still belongs to the client.
    row = world.files._by_id[body["document_id"]]
    assert row["organization_id"] == ORG_A
    assert row["status"] == STATUS_PENDING_UPLOAD


# ---------------------------------------------------------------------------
# CT-PO-UPLOAD-BATCH-REMEDIATION-001 (Part B) — an abandoned direct upload now
# has a reachable, auditable terminal state instead of a ghost `pending_upload`
# row. The endpoint reuses the SAME terminal state and audit action the 24-hour
# reaper uses; nothing is hard-deleted and nothing is enqueued for processing.
# ---------------------------------------------------------------------------


def test_abandoning_a_pending_upload_makes_it_terminal_and_audited(
    client, world, user_provider, storage, enqueued
) -> None:
    from api.upload_gate import ACTION_UPLOAD_EXPIRED

    started = _org_initiate(client, user_provider)
    assert started.status_code == 201, started.text
    document_id = started.json()["document_id"]

    resp = client.post(f"/api/v3/documents/{document_id}/upload-abandon")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["abandoned"] is True
    assert body["idempotent"] is False
    assert body["status"] == STATUS_UPLOAD_EXPIRED
    assert body["organization_id"] == ORG_A

    # The row is retained (evidence is not destroyed) and is terminal.
    row = world.files._by_id[document_id]
    assert row["status"] == STATUS_UPLOAD_EXPIRED
    # An abandoned upload never enters the processing pipeline.
    assert enqueued.calls == []
    assert ACTION_UPLOAD_EXPIRED in _actions(world)


def test_abandoning_an_upload_is_idempotent(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    document_id = started.json()["document_id"]

    first = client.post(f"/api/v3/documents/{document_id}/upload-abandon")
    assert first.status_code == 200, first.text
    assert first.json()["idempotent"] is False

    second = client.post(f"/api/v3/documents/{document_id}/upload-abandon")
    assert second.status_code == 200, second.text
    assert second.json()["idempotent"] is True
    assert second.json()["status"] == STATUS_UPLOAD_EXPIRED
    assert world.files._by_id[document_id]["status"] == STATUS_UPLOAD_EXPIRED
    assert enqueued.calls == []


def test_abandoning_an_upload_that_reached_storage_is_refused(
    client, world, user_provider, storage
) -> None:
    """A real upload must never be mislabelled as abandoned."""
    started = _org_initiate(client, user_provider)
    body = started.json()
    storage.objects[body["storage_path"]] = PDF_BYTES  # the PUT actually landed

    resp = client.post(f"/api/v3/documents/{body['document_id']}/upload-abandon")
    assert resp.status_code == 409, resp.text
    assert world.files._by_id[body["document_id"]]["status"] == STATUS_PENDING_UPLOAD


def test_abandoning_an_already_accepted_upload_is_refused(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    body = started.json()
    storage.objects[body["storage_path"]] = PDF_BYTES
    assert _complete(client, body["document_id"]).status_code == 200

    resp = client.post(f"/api/v3/documents/{body['document_id']}/upload-abandon")
    assert resp.status_code == 409, resp.text
    assert world.files._by_id[body["document_id"]]["status"] == STATUS_CLEAN


def test_abandoning_another_organisations_upload_is_denied(
    client, world, user_provider, storage
) -> None:
    started = _org_initiate(client, user_provider)  # ORG_A
    document_id = started.json()["document_id"]

    user_provider.set_user(member_user(ORG_B, "u-b", "ub@example.test"))
    resp = client.post(f"/api/v3/documents/{document_id}/upload-abandon")
    assert resp.status_code in (403, 404), resp.text
    assert world.files._by_id[document_id]["status"] == STATUS_PENDING_UPLOAD


def test_an_abandoned_upload_can_never_be_completed_later(
    client, world, user_provider, storage, enqueued
) -> None:
    """Even if the bytes arrive late, the terminal state refuses completion."""
    started = _org_initiate(client, user_provider)
    document_id = started.json()["document_id"]
    assert client.post(f"/api/v3/documents/{document_id}/upload-abandon").status_code == 200

    storage.objects[started.json()["storage_path"]] = PDF_BYTES
    refused = _complete(client, document_id)
    assert refused.status_code == 409
    assert enqueued.calls == []


def test_a_consultant_can_abandon_a_client_upload_without_changing_ownership(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _consultant_initiate(client, world, user_provider)
    assert started.status_code == 201, started.text
    body = started.json()

    resp = client.post(
        f"/api/v3/consultants/clients/client-a/documents/{body['document_id']}/upload-abandon"
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["organization_id"] == ORG_A  # the CLIENT still owns it
    assert resp.json()["client_id"] == "client-a"

    row = world.files._by_id[body["document_id"]]
    assert row["organization_id"] == ORG_A
    assert row["status"] == STATUS_UPLOAD_EXPIRED
    assert enqueued.calls == []



# ---------------------------------------------------------------------------
# CT-PO-UPLOAD-BATCH-REMEDIATION-001 (Part C) — batch upload is a wired V3
# capability again. The grouping record's lifecycle (create → real per-file
# progress → complete) is exposed over the EXISTING upload_batches repository
# and is organisation-scoped; no state is invented client-side.
# ---------------------------------------------------------------------------


class _FakeUploadBatches:
    """In-memory ``upload_batches`` lifecycle for the restored batch surface."""

    def __init__(self) -> None:
        self._by_id: dict = {}
        self._seq = 0

    async def create(self, org_id, batch_name, created_by_user_id, metadata=None):
        from domain.operations import UploadBatch

        self._seq += 1
        batch = UploadBatch(
            id=f"batch-{self._seq}",
            organization_id=org_id,
            batch_name=batch_name,
            total_files=0,
            processed_files=0,
            status="pending",
            created_by_user_id=created_by_user_id,
            metadata=dict(metadata or {}),
        )
        self._by_id[batch.id] = batch
        return batch

    async def get(self, batch_id):
        return self._by_id.get(batch_id)

    async def update_progress(self, batch_id, processed_files, status):
        from dataclasses import replace

        batch = self._by_id.get(batch_id)
        if batch is None:
            return None
        updated = replace(batch, processed_files=processed_files, status=status)
        self._by_id[batch_id] = updated
        return updated

    async def complete(self, batch_id):
        from dataclasses import replace

        batch = self._by_id.get(batch_id)
        if batch is None:
            return None
        updated = replace(
            batch, status="completed", completed_at=datetime.now(timezone.utc)
        )
        self._by_id[batch_id] = updated
        return updated


def _use_fake_batches(app, world) -> _FakeUploadBatches:
    """Swap the (otherwise unused) stub batches repo for a real lifecycle."""
    from dataclasses import replace

    from api.dependencies import get_repositories

    fake = _FakeUploadBatches()
    app.dependency_overrides[get_repositories] = lambda: replace(
        world.bundle(), batches=fake
    )
    return fake


def _create_batch(client, org_id=ORG_A) -> str:
    resp = client.post(
        f"/api/v3/batches?organization_id={org_id}",
        json={
            "batch_name": "September invoices",
            "metadata": {"surface": "v3_documents_batch", "file_count": 3},
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_a_batch_is_created_pending_and_reports_its_real_progress(
    client, app, world, user_provider
) -> None:
    user_provider.set_user(member_user(ORG_A, "u-1", "u1@example.test"))
    _use_fake_batches(app, world)
    batch_id = _create_batch(client)

    created = client.get(f"/api/v3/batches/{batch_id}")
    assert created.status_code == 200, created.text
    assert created.json()["status"] == "pending"
    assert created.json()["processed_files"] == 0

    mid = client.patch(
        f"/api/v3/batches/{batch_id}",
        json={"processed_files": 1, "status": "processing"},
    )
    assert mid.status_code == 200, mid.text
    assert mid.json()["processed_files"] == 1
    assert mid.json()["status"] == "processing"

    done = client.patch(
        f"/api/v3/batches/{batch_id}",
        json={"processed_files": 3, "status": "completed"},
    )
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "completed"
    assert done.json()["completed_at"] is not None


def test_a_partial_batch_is_recorded_as_partial_not_completed(
    client, app, world, user_provider
) -> None:
    user_provider.set_user(member_user(ORG_A, "u-1", "u1@example.test"))
    _use_fake_batches(app, world)
    batch_id = _create_batch(client)

    resp = client.patch(
        f"/api/v3/batches/{batch_id}",
        json={"processed_files": 3, "status": "partial"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "partial"
    assert resp.json()["completed_at"] is None



def test_batch_progress_cannot_report_another_organisations_batch(
    client, app, world, user_provider
) -> None:
    user_provider.set_user(member_user(ORG_A, "u-1", "u1@example.test"))
    _use_fake_batches(app, world)
    batch_id = _create_batch(client)

    user_provider.set_user(member_user(ORG_B, "u-b", "ub@example.test"))
    denied = client.patch(
        f"/api/v3/batches/{batch_id}",
        json={"processed_files": 1, "status": "processing"},
    )
    assert denied.status_code == 403, denied.text

    user_provider.set_user(member_user(ORG_A, "u-1", "u1@example.test"))
    unchanged = client.get(f"/api/v3/batches/{batch_id}")
    assert unchanged.json()["processed_files"] == 0
    assert unchanged.json()["status"] == "pending"


def test_batch_progress_rejects_an_unknown_batch(
    client, app, world, user_provider
) -> None:
    user_provider.set_user(member_user(ORG_A, "u-1", "u1@example.test"))
    _use_fake_batches(app, world)

    resp = client.patch(
        "/api/v3/batches/does-not-exist",
        json={"processed_files": 1, "status": "processing"},
    )
    assert resp.status_code == 404


def test_batch_progress_cannot_invent_a_lifecycle_state(
    client, app, world, user_provider
) -> None:
    user_provider.set_user(member_user(ORG_A, "u-1", "u1@example.test"))
    _use_fake_batches(app, world)
    batch_id = _create_batch(client)

    resp = client.patch(
        f"/api/v3/batches/{batch_id}",
        json={"processed_files": 1, "status": "definitely-not-a-status"},
    )
    assert resp.status_code == 422


def test_batch_progress_refuses_a_negative_processed_count(
    client, app, world, user_provider
) -> None:
    user_provider.set_user(member_user(ORG_A, "u-1", "u1@example.test"))
    _use_fake_batches(app, world)
    batch_id = _create_batch(client)

    resp = client.patch(
        f"/api/v3/batches/{batch_id}",
        json={"processed_files": -1, "status": "processing"},
    )
    assert resp.status_code == 422


def test_the_batch_progress_write_is_audited(client, app, world, user_provider) -> None:
    user_provider.set_user(member_user(ORG_A, "u-1", "u1@example.test"))
    _use_fake_batches(app, world)
    batch_id = _create_batch(client)

    assert (
        client.patch(
            f"/api/v3/batches/{batch_id}",
            json={"processed_files": 2, "status": "processing"},
        ).status_code
        == 200
    )
    assert "batch.progress" in _actions(world)


def test_the_unified_upload_surface_reuses_the_approved_protocol_in_source() -> None:
    """The multi-file upload panel must drive the SAME signed-direct flow — not a
    legacy fork (CT-PO-UPLOAD-UNIFY-001 unifies the single-file form and the
    separate batch panel into this one surface)."""
    panel = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "v3"
        / "customer"
        / "UploadDocumentsPanel.jsx"
    ).read_text(encoding="utf-8")
    assert "v3UploadDocumentDirect" in panel
    assert "v3CreateUploadBatch" in panel
    assert "v3UpdateUploadBatchProgress" in panel
    # No legacy bulk-upload machinery is revived.
    assert "BulkUpload" not in panel
    assert "UploadManager" not in panel
    assert "PDFIngestionPortal" not in panel
    assert "XMLHttpRequest" not in panel  # transport stays inside the shared client


def test_the_upload_panel_is_wired_into_the_documents_surface_in_source() -> None:
    page = (
        REPO_ROOT / "frontend" / "src" / "v3" / "customer" / "DocumentsPage.jsx"
    ).read_text(encoding="utf-8")
    assert "UploadDocumentsPanel" in page
    assert "<UploadDocumentsPanel" in page
    # CT-PO-UPLOAD-UNIFY-001 — exactly ONE upload surface: the old single-file
    # form and the separate batch panel are gone, and the mandatory pre-upload
    # "Data type" selector is gone with them.
    assert "BatchUploadPanel" not in page
    assert "Data type" not in page

