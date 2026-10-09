"""Storage Management Step 1 — secure document-upload foundation tests.

Covers the ratified Step 1 behaviour:

* one authoritative authorization gate for both upload ingresses;
* server-generated storage keys (no client-supplied path, no raw file name in
  the key) under the client organisation's ``uploads/{org}/...`` namespace;
* direct-to-storage signed upload URLs (no service-role credential to the
  browser, no backend byte proxy for ordinary uploads);
* the security-gate lifecycle (pending → clean → processing / rejected) with the
  invariant that an uncleared document never enters processing;
* single authoritative per-file limit;
* consultant provenance in application metadata only, including after the client
  becomes a direct customer, with no byte movement;
* audit events for the significant document actions.

No storage, no database and no network are involved: the storage functions and
the pipeline enqueue are replaced with in-memory doubles.
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta, timezone

import pytest

from services.document_security import (
    EICAR_TEST_SIGNATURE,
    SCANNER_ENV_VAR,
    STATUS_CLEAN,
    STATUS_PENDING_UPLOAD,
    STATUS_REJECTED,
    can_transition,
    is_downloadable,
    is_processable,
    resolve_scanner,
    scan_document,
)
from services.storage_keys import (
    build_document_storage_key,
    is_safe_filename,
    key_belongs_to_organization,
    sanitize_display_name,
    split_extension,
)
from tests.unit.api.fakes import consultant_user, member_user, org_viewer_user

ORG_A = "org-a"
ORG_B = "org-b"
MB = 1024 * 1024

PDF_BYTES = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\n%%EOF\n"


# ---------------------------------------------------------------------------
# doubles
# ---------------------------------------------------------------------------


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

    def download_object_prefix(
        self, path: str, max_bytes: int = 262_144, bucket: str | None = None
    ) -> bytes | None:
        if path not in self.objects:
            return None
        return self.objects[path][:max_bytes]


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
    monkeypatch.setattr(uploads, "download_object_prefix", fake.download_object_prefix)
    return fake


@pytest.fixture
def enqueued(monkeypatch):
    import api.v3_document_uploads as uploads

    recorder = _EnqueueRecorder()
    monkeypatch.setattr(uploads, "enqueue_document_processing", recorder)
    return recorder


def _seed_consultant(world, user_id="u-cons", *, can_upload_documents=True, client_status="active"):
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
    world.consultants.seed_client("client-a", "firm-1", ORG_A, "ACME LTD", status=client_status)
    world.consultants.seed_client("client-c", "firm-2", "org-c", "Example Retail")
    return consultant_user(user_id, "cons@example.test")


def _actions(world) -> list[str]:
    return [entry.action for entry in world.audit._entries]


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


# ---------------------------------------------------------------------------
# 1. storage keys — server-generated, tenant-scoped, no user file name
# ---------------------------------------------------------------------------


def test_storage_key_is_server_generated_and_tenant_scoped() -> None:
    key = build_document_storage_key(ORG_A, "Invoice 2025 (final).PDF")
    parts = key.split("/")
    assert parts[0] == "uploads"
    assert parts[1] == ORG_A
    assert len(parts) == 6
    assert parts[-1].endswith(".pdf")
    assert "Invoice" not in key
    assert "final" not in key
    assert key_belongs_to_organization(key, ORG_A)
    assert not key_belongs_to_organization(key, ORG_B)


def test_storage_key_rejects_a_tenant_token_that_could_inject_a_path() -> None:
    for bad in ("org/../other", "org/../..", "..", ""):
        with pytest.raises(ValueError):
            build_document_storage_key(bad, "invoice.pdf")


def test_filename_safety_and_extension_sanitisation() -> None:
    assert is_safe_filename("invoice.pdf")
    assert not is_safe_filename("../../etc/passwd")
    assert not is_safe_filename("dir\\invoice.pdf")
    assert not is_safe_filename("bad\x00.pdf")
    assert not is_safe_filename("")
    assert sanitize_display_name("../invoice.pdf") == ".._invoice.pdf"
    assert split_extension("invoice.PDF") == "pdf"
    assert split_extension("archive.tar.gz") == "gz"
    assert split_extension("noextension") == ""
    assert split_extension("evil.<script>") == ""


# ---------------------------------------------------------------------------
# 2. the security gate itself
# ---------------------------------------------------------------------------


def test_ratified_cap_is_unchanged_and_single_sourced() -> None:
    from utils.upload_limits import (
        DEFAULT_MAX_FILE_SIZE_MB,
        PLATFORM_MAX_FILE_SIZE_MB,
        effective_file_limit_bytes,
    )

    assert PLATFORM_MAX_FILE_SIZE_MB == 10          # ratified ceiling
    assert DEFAULT_MAX_FILE_SIZE_MB == 6            # out-of-the-box effective
    assert effective_file_limit_bytes(None) == 6 * MB


def test_security_gate_accepts_a_real_pdf_and_reports_the_structural_scanner() -> None:
    verdict = scan_document(
        content=PDF_BYTES, filename="invoice.pdf", declared_mime="application/pdf"
    )
    assert verdict.accepted
    assert verdict.status == STATUS_CLEAN
    assert verdict.scanner == "structural"
    # No vendor was claimed: the structural gate does not run antivirus.
    assert verdict.external_scan_available is False
    codes = {f.code for f in verdict.findings}
    assert "content_type_confirmed" in codes


def test_security_gate_tolerates_unrecognised_bytes_but_never_trusts_the_mime() -> None:
    verdict = scan_document(
        content=b"sample pdf bytes", filename="x.pdf", declared_mime="application/pdf"
    )
    assert verdict.accepted
    assert "content_type_unverified" in {f.code for f in verdict.findings}


def test_security_gate_rejects_executables_mismatches_and_the_eicar_signature() -> None:
    executable = scan_document(
        content=b"MZ\x90\x00\x03", filename="invoice.pdf", declared_mime="application/pdf"
    )
    assert not executable.accepted
    assert "executable_content" in {f.code for f in executable.blockers}

    eicar = scan_document(
        content=EICAR_TEST_SIGNATURE, filename="invoice.pdf", declared_mime="application/pdf"
    )
    assert not eicar.accepted
    assert "malware_signature" in {f.code for f in eicar.blockers}

    mismatch = scan_document(
        content=b"PK\x03\x04rest", filename="invoice.pdf", declared_mime="application/pdf"
    )
    assert not mismatch.accepted
    assert "content_type_mismatch" in {f.code for f in mismatch.blockers}

    disallowed = scan_document(content=b"#!/bin/sh\n", filename="run.sh", declared_mime="text/x-sh")
    assert not disallowed.accepted
    assert "extension_not_allowed" in {f.code for f in disallowed.blockers}


def test_unconfigured_external_scanner_never_claims_a_malware_scan(monkeypatch) -> None:
    monkeypatch.setenv(SCANNER_ENV_VAR, "some-vendor-not-installed")
    scanner = resolve_scanner()
    verdict = scanner.scan(
        content=PDF_BYTES,
        filename="invoice.pdf",
        declared_mime="application/pdf",
        extension="pdf",
    )
    assert scanner.name == "structural"
    assert verdict.external_scan_available is False
    assert verdict.scanner == "structural"


def test_lifecycle_status_rules_fail_closed() -> None:
    assert can_transition(STATUS_PENDING_UPLOAD, STATUS_CLEAN) is False
    assert can_transition(STATUS_PENDING_UPLOAD, STATUS_REJECTED) is True
    assert can_transition(STATUS_REJECTED, STATUS_CLEAN) is False
    assert is_processable(STATUS_CLEAN) is True
    assert is_processable(STATUS_REJECTED) is False
    assert is_processable(STATUS_PENDING_UPLOAD) is False
    assert is_downloadable(STATUS_REJECTED) is False
    assert is_downloadable(STATUS_PENDING_UPLOAD) is False
    assert is_downloadable(None) is True          # pre-lifecycle legacy rows


# ---------------------------------------------------------------------------
# 1. authorized organisation upload — full lifecycle
# ---------------------------------------------------------------------------


def test_authorized_organization_upload_full_lifecycle(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    assert started.status_code == 201, started.text
    body = started.json()
    assert body["status"] == STATUS_PENDING_UPLOAD
    assert body["storage_path"].startswith(f"uploads/{ORG_A}/")
    assert body["bucket"] == "documents"
    # the browser receives a short-lived signed URL and no credential
    assert body["upload"]["url"].startswith("https://storage.example/")
    assert "service" not in body["upload"]["url"].lower()
    assert body["upload"]["expires_in_seconds"] == 900
    assert body["resumable"]["supported"] is False
    assert storage.signed_uploads == [body["storage_path"]]
    row = world.files._by_id[body["document_id"]]
    assert row["status"] == STATUS_PENDING_UPLOAD
    assert "token" not in str(row["metadata"])
    assert enqueued.calls == []          # nothing is processed before the gate

    # the browser uploads the bytes straight to storage
    storage.objects[body["storage_path"]] = PDF_BYTES
    done = _complete(client, body["document_id"])
    assert done.status_code == 200, done.text
    result = done.json()
    assert result["status"] == STATUS_CLEAN
    assert result["idempotent"] is False
    assert result["security_gate"]["scanner"] == "structural"
    assert world.files._by_id[body["document_id"]]["status"] == STATUS_CLEAN
    assert len(enqueued.calls) == 1
    assert enqueued.calls[0]["organization_id"] == ORG_A
    assert enqueued.calls[0]["storage_path"] == body["storage_path"]

    actions = _actions(world)
    for expected in (
        "document.upload_initiated",
        "document.security_scan_started",
        "document.security_scan_completed",
        "document.upload_completed",
        "document.accepted",
    ):
        assert expected in actions, actions

    # completion is idempotent and never re-enqueues
    again = _complete(client, body["document_id"])
    assert again.status_code == 200
    assert again.json()["idempotent"] is True
    assert len(enqueued.calls) == 1


# ---------------------------------------------------------------------------
# 2. unauthorized organisation upload
# ---------------------------------------------------------------------------


def test_cross_tenant_upload_is_denied_before_any_write(
    client, world, user_provider, storage, enqueued
) -> None:
    denied = _org_initiate(
        client, user_provider, user=member_user(ORG_B, "u-b", "b@example.test")
    )
    assert denied.status_code == 403
    assert world.files._by_id == {}
    assert storage.signed_uploads == []
    assert enqueued.calls == []
    assert "document.upload_denied" in _actions(world)


def test_viewer_cannot_start_an_upload(
    client, world, user_provider, storage
) -> None:
    denied = _org_initiate(
        client, user_provider, user=org_viewer_user(ORG_A, "u-v", "v@example.test")
    )
    assert denied.status_code == 403
    assert "read-only" in denied.text.lower()
    assert world.files._by_id == {}
    assert storage.signed_uploads == []


# ---------------------------------------------------------------------------
# 3/4/5. consultant uploads
# ---------------------------------------------------------------------------


def _consultant_initiate(client, *, client_id="client-a", **overrides):
    payload = {
        "filename": "bill.pdf",
        "size_bytes": len(PDF_BYTES),
        "content_type": "application/pdf",
        "data_type": "utility",
    }
    payload.update(overrides)
    return client.post(
        f"/api/v3/consultants/clients/{client_id}/documents/upload-url", json=payload
    )


def test_consultant_upload_is_scoped_to_the_client_organization(
    client, world, user_provider, storage, enqueued
) -> None:
    user_provider.set_user(_seed_consultant(world))
    started = _consultant_initiate(client)
    assert started.status_code == 201, started.text
    body = started.json()
    # the CLIENT organisation owns the bytes; no consultant namespace exists
    assert body["organization_id"] == ORG_A
    assert body["storage_path"].startswith(f"uploads/{ORG_A}/")
    assert "firm-1" not in body["storage_path"]
    assert body["client_id"] == "client-a"
    assert body["completion"]["path"].startswith(
        "/api/v3/consultants/clients/client-a/documents/"
    )
    metadata = world.files._by_id[body["document_id"]]["metadata"]
    assert metadata["consultant_originated"] is True
    assert metadata["uploaded_by_consultant_firm_id"] == "firm-1"
    assert metadata["upload_actor_type"] == "consultant"

    storage.objects[body["storage_path"]] = PDF_BYTES
    done = client.post(
        f"/api/v3/consultants/clients/client-a/documents/"
        f"{body['document_id']}/upload-complete"
    )
    assert done.status_code == 200, done.text
    assert done.json()["status"] == STATUS_CLEAN
    assert len(enqueued.calls) == 1


def test_consultant_upload_after_relationship_termination_is_denied(
    client, world, user_provider, storage, enqueued
) -> None:
    user_provider.set_user(_seed_consultant(world, client_status="ended"))
    denied = _consultant_initiate(client)
    assert denied.status_code == 403
    assert storage.signed_uploads == []
    assert world.files._by_id == {}
    assert enqueued.calls == []
    assert "document.upload_denied" in _actions(world)


def test_consultant_upload_without_the_capability_is_denied(
    client, world, user_provider, storage
) -> None:
    user_provider.set_user(_seed_consultant(world, can_upload_documents=False))
    denied = _consultant_initiate(client)
    assert denied.status_code == 403
    assert storage.signed_uploads == []
    assert world.files._by_id == {}


def test_consultant_cannot_start_an_upload_for_another_firms_client(
    client, world, user_provider, storage
) -> None:
    user_provider.set_user(_seed_consultant(world))
    denied = _consultant_initiate(client, client_id="client-c")
    assert denied.status_code == 403
    assert storage.signed_uploads == []


# ---------------------------------------------------------------------------
# 6/7/8. cross-organisation, arbitrary path, oversize
# ---------------------------------------------------------------------------


def test_completing_another_organizations_document_is_denied(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    document_id = started.json()["document_id"]
    storage.objects[started.json()["storage_path"]] = PDF_BYTES

    user_provider.set_user(member_user(ORG_B, "u-b", "b@example.test"))
    denied = _complete(client, document_id)
    assert denied.status_code == 403
    assert world.files._by_id[document_id]["status"] == STATUS_PENDING_UPLOAD
    assert enqueued.calls == []


def test_arbitrary_storage_path_and_disallowed_extensions_are_refused(
    client, world, user_provider, storage
) -> None:
    for bad_name in ("../../etc/passwd", "dir\\invoice.pdf", "payload.exe", "noextension"):
        refused = _org_initiate(client, user_provider, filename=bad_name)
        assert refused.status_code == 422, (bad_name, refused.text)
    assert world.files._by_id == {}
    assert storage.signed_uploads == []


def test_oversized_upload_is_refused_before_any_write(
    client, world, user_provider, storage, enqueued
) -> None:
    refused = _org_initiate(client, user_provider, size_bytes=7 * MB)
    assert refused.status_code == 413
    assert "never compressed" in refused.text
    assert world.files._by_id == {}
    assert storage.signed_uploads == []
    assert enqueued.calls == []


def test_zero_byte_declared_upload_is_refused(client, world, user_provider, storage) -> None:
    refused = _org_initiate(client, user_provider, size_bytes=0)
    assert refused.status_code == 400
    assert storage.signed_uploads == []


# ---------------------------------------------------------------------------
# 9/10. content-type mismatch, malware signature, quarantine
# ---------------------------------------------------------------------------


def test_mismatched_content_type_is_quarantined_at_completion(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    body = started.json()
    # the browser claims a PDF but the bytes are an executable
    storage.objects[body["storage_path"]] = b"MZ\x90\x00\x03\x00\x00\x00"

    refused = _complete(client, body["document_id"])
    assert refused.status_code == 422
    assert "security gate" in refused.text
    assert world.files._by_id[body["document_id"]]["status"] == STATUS_REJECTED
    assert enqueued.calls == []            # never enters normal processing
    actions = _actions(world)
    assert "document.security_rejected" in actions
    # a quarantined document is never signed for viewing
    assert client.get(f"/api/v3/documents/{body['document_id']}/signed-url").status_code == 409


def test_malware_signature_upload_is_rejected_and_never_processed(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    body = started.json()
    storage.objects[body["storage_path"]] = EICAR_TEST_SIGNATURE

    refused = _complete(client, body["document_id"])
    assert refused.status_code == 422
    assert "malware" in refused.text.lower() or "EICAR" in refused.text
    assert world.files._by_id[body["document_id"]]["status"] == STATUS_REJECTED
    assert enqueued.calls == []


# ---------------------------------------------------------------------------
# 11/12. clean lifecycle, expired authorisation
# ---------------------------------------------------------------------------


def test_expired_upload_authorisation_is_refused(client, world, user_provider, storage, enqueued) -> None:
    started = _org_initiate(client, user_provider)
    body = started.json()
    row = world.files._by_id[body["document_id"]]
    row["uploaded_at"] = datetime.now(timezone.utc) - timedelta(days=2)
    storage.objects[body["storage_path"]] = PDF_BYTES

    refused = _complete(client, body["document_id"])
    assert refused.status_code == 409
    assert "expired" in refused.text.lower()
    assert world.files._by_id[body["document_id"]]["status"] == STATUS_PENDING_UPLOAD
    assert enqueued.calls == []


def test_completion_without_the_stored_object_is_refused(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    body = started.json()
    refused = _complete(client, body["document_id"])   # nothing was uploaded
    assert refused.status_code == 409
    assert world.files._by_id[body["document_id"]]["status"] == STATUS_PENDING_UPLOAD
    assert enqueued.calls == []


def test_stored_object_larger_than_the_limit_is_quarantined(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider, size_bytes=1024)
    body = started.json()
    storage.objects[body["storage_path"]] = b"%PDF-" + b"0" * (7 * MB)
    refused = _complete(client, body["document_id"])
    assert refused.status_code == 413
    assert world.files._by_id[body["document_id"]]["status"] == STATUS_REJECTED
    assert enqueued.calls == []


# ---------------------------------------------------------------------------
# 13. signed download authorization
# ---------------------------------------------------------------------------


def test_signed_download_requires_authorization_and_is_audited(
    client, world, user_provider, storage, enqueued, monkeypatch
) -> None:
    import api.v3_documents as docs

    monkeypatch.setattr(docs, "storage_signed_url", lambda path: f"https://signed/{path}")
    started = _org_initiate(client, user_provider)
    body = started.json()
    storage.objects[body["storage_path"]] = PDF_BYTES
    assert _complete(client, body["document_id"]).status_code == 200

    allowed = client.get(f"/api/v3/documents/{body['document_id']}/signed-url")
    assert allowed.status_code == 200
    assert allowed.json()["url"].startswith("https://signed/")
    assert "document.signed_url_issued" in _actions(world)
    # the signed URL itself is never persisted anywhere
    for entry in world.audit._entries:
        assert "https://" not in str(entry.changed_fields)

    user_provider.set_user(member_user(ORG_B, "u-b", "b@example.test"))
    assert client.get(f"/api/v3/documents/{body['document_id']}/signed-url").status_code == 403


# ---------------------------------------------------------------------------
# 14/15/16. consultant provenance, client conversion, original preservation
# ---------------------------------------------------------------------------


def test_consultant_provenance_survives_client_conversion_without_moving_bytes(
    client, world, user_provider, storage, enqueued
) -> None:
    # 1. the consultant uploads for the client organisation
    user_provider.set_user(_seed_consultant(world))
    started = _consultant_initiate(client)
    consultant_doc = started.json()
    consultant_path = consultant_doc["storage_path"]
    storage.objects[consultant_path] = PDF_BYTES
    assert (
        client.post(
            "/api/v3/consultants/clients/client-a/documents/"
            f"{consultant_doc['document_id']}/upload-complete"
        ).status_code
        == 200
    )

    # 2. the client later becomes a DIRECT CarbonTally customer (same
    #    organisation, same data) and uploads its own document. Under the
    #    ratified consultant model an organisation is a consultant-managed CLIENT
    #    only while a consultant relationship is LIVE, so "becomes a direct
    #    customer" means the relationship has ENDED with nothing retained
    #    (CT-CONSULTANT-CLIENT-PLANE-AUTH-REMEDIATION-05; PO-CONSOLIDATION-01
    #    §16). Ending it restores the direct-customer organisation surface.
    asyncio.run(world.consultants.transition_client_lifecycle("client-a", "ended"))
    user_provider.set_user(member_user(ORG_A, "u-1", "u1@example.test"))
    own = _org_initiate(client, user_provider, filename="client-own.pdf")
    own_body = own.json()
    storage.objects[own_body["storage_path"]] = PDF_BYTES
    assert _complete(client, own_body["document_id"]).status_code == 200

    # no copy, move, export or re-import happened anywhere
    assert len(storage.objects) == 2
    assert storage.objects[consultant_path] == PDF_BYTES
    row = world.files._by_id[consultant_doc["document_id"]]
    assert row["path"] == consultant_path                     # unmoved
    assert row["organization_id"] == ORG_A                     # same tenant
    assert row["metadata"]["consultant_originated"] is True    # provenance kept
    assert row["metadata"]["uploaded_by_consultant_firm_id"] == "firm-1"


def test_the_original_document_is_never_rewritten(
    client, world, user_provider, storage, enqueued
) -> None:
    started = _org_initiate(client, user_provider)
    body = started.json()
    original = PDF_BYTES + b"<< trailing original bytes >>"
    storage.objects[body["storage_path"]] = original
    assert _complete(client, body["document_id"]).status_code == 200
    # byte-for-byte identical: the gate read a prefix and never wrote back
    assert storage.objects[body["storage_path"]] == original
    row = world.files._by_id[body["document_id"]]
    # the browser-declared size is replaced by the size actually verified
    assert row["size_bytes"] == len(original)
    assert row["metadata"]["verified_size_bytes"] == len(original)


# ---------------------------------------------------------------------------
# 17. audit + the server-proxied ingress shares the gate
# ---------------------------------------------------------------------------


def test_upload_audit_entries_carry_provenance_and_no_credential(
    client, world, user_provider, storage
) -> None:
    user_provider.set_user(_seed_consultant(world))
    started = _consultant_initiate(client)
    assert started.status_code == 201
    entries = world.audit._entries
    initiated = [e for e in entries if e.action == "document.upload_initiated"]
    assert initiated, "upload initiation must be audited"
    fields = initiated[-1].changed_fields
    assert fields["upload_actor_type"] == "consultant"
    assert fields["uploaded_by_consultant_firm_id"] == "firm-1"
    assert fields["organization_id"] == ORG_A          # the CLIENT tenant
    assert fields["status"] == STATUS_PENDING_UPLOAD
    assert "token" not in str(fields)
    assert "https://" not in str(fields)


def test_server_proxied_upload_uses_the_same_gate_and_security_check(
    client, world, user_provider
) -> None:
    """The legacy proxied ingress is hardened by the same gate: a rejected
    document leaves no storage object and no database row."""
    user_provider.set_user(member_user(ORG_A, "u-1", "u1@example.test"))
    refused = client.post(
        "/api/v3/uploads",
        data={"organization_id": ORG_A, "data_type": "utility"},
        files={"file": ("statement.pdf", b"MZ\x90\x00bad", "application/pdf")},
    )
    assert refused.status_code == 422
    assert "security gate" in refused.text
    assert world.files._by_id == {}
    assert "document.security_rejected" in _actions(world)
