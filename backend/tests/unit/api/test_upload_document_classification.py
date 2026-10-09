"""CT-PO-UPLOAD-UNIFY-001 — per-file document classification on upload.

The unified "Upload documents" surface no longer asks the user for a "Data type"
before uploading. Each file is instead classified server-side against the
EXISTING CarbonTally document taxonomy (``utils.document_classifier`` over the
``document_types`` reference table) and the verdict is returned per file.

These tests pin the whole contract in memory — no database, no storage, no
network:

* the verdict is computed once at initiation and persisted on the document;
* completion returns the SAME verdict the caller saw at initiation;
* an explicit ``document_type_code`` reaches the classifier (so an override is
  auditable as ``user_selected`` rather than indistinguishable from an auto
  result);
* a classification failure degrades to an honest "unavailable" verdict and never
  fails the upload;
* the verdict does NOT change the verified processing pipeline — ``data_type``
  and the ``enqueue_document_processing`` arguments are exactly as before.
"""
from __future__ import annotations

import pytest

from tests.unit.api.fakes import member_user

ORG_A = "org-a"
PDF_BYTES = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\n%%EOF\n"

CLASSIFIED = {
    "document_type_code": "invoice_electricity",
    "document_type_id": "dt-1",
    "confidence": 0.8,
    "suggested_type": "Electricity Invoice",
    "category": "invoice",
    "source": "auto_classified",
    "alternative_types": ["invoice_utility"],
}


class _FakeStorage:
    """In-memory stand-in for the Supabase Storage surface the flow uses."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def create_signed_upload_url(self, path: str, bucket: str | None = None) -> dict:
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


class _ClassifierRecorder:
    """Records what the upload path asked the classifier, and answers with a verdict."""

    def __init__(self, verdict: dict | None = None, error: Exception | None = None) -> None:
        self.calls: list[tuple] = []
        self.verdict = verdict or CLASSIFIED
        self.error = error

    async def __call__(self, file_name, file_content=None, user_selected_type=None):
        self.calls.append((file_name, file_content, user_selected_type))
        if self.error is not None:
            raise self.error
        return dict(self.verdict)


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


@pytest.fixture
def classifier(monkeypatch):
    import api.v3_document_uploads as uploads

    recorder = _ClassifierRecorder()
    monkeypatch.setattr(uploads, "classify_document", recorder)
    return recorder


def _initiate(client, user_provider, *, user=None, **overrides):
    payload = {
        "organization_id": ORG_A,
        "filename": "electricity-invoice.pdf",
        "size_bytes": len(PDF_BYTES),
        "content_type": "application/pdf",
        "data_type": "utility",
    }
    payload.update(overrides)
    user_provider.set_user(user or member_user(ORG_A, "u-1", "u1@example.test"))
    return client.post("/api/v3/documents/upload-url", json=payload)


def _land_and_complete(client, storage, body):
    storage.objects[body["storage_path"]] = PDF_BYTES
    return client.post(f"/api/v3/documents/{body['document_id']}/upload-complete")


def test_initiation_returns_the_verdict_and_persists_it_on_the_document(
    client, world, user_provider, classifier, storage
):
    started = _initiate(client, user_provider)
    assert started.status_code == 201, started.text
    body = started.json()

    # The caller is told what CarbonTally classified the file as.
    assert body["classification"]["document_type_code"] == "invoice_electricity"
    assert body["classification"]["suggested_type"] == "Electricity Invoice"
    assert body["classification"]["source"] == "auto_classified"

    # ... and the verdict is durable, not just a response decoration.
    row = world.files._by_id[body["document_id"]]
    assert row["metadata"]["classification"]["document_type_code"] == "invoice_electricity"

    # The classifier was consulted with the document's own name and NO user choice.
    assert classifier.calls == [("electricity-invoice.pdf", None, None)]


def test_completion_reports_the_same_verdict_the_caller_already_saw(
    client, world, user_provider, classifier, storage, enqueued
):
    started = _initiate(client, user_provider).json()
    completed = _land_and_complete(client, storage, started)
    assert completed.status_code == 200, completed.text
    payload = completed.json()

    assert payload["classification"]["document_type_code"] == "invoice_electricity"
    assert payload["classification"]["confidence"] == 0.8
    # The verdict is advisory: it must not be re-derived into a different answer.
    assert classifier.calls == [("electricity-invoice.pdf", None, None)]


def test_a_repeat_completion_returns_the_recorded_verdict(
    client, user_provider, classifier, storage, enqueued
):
    started = _initiate(client, user_provider).json()
    first = _land_and_complete(client, storage, started).json()
    second = client.post(f"/api/v3/documents/{started['document_id']}/upload-complete").json()

    assert second["idempotent"] is True
    assert second["classification"] == first["classification"]


def test_an_explicit_document_type_code_reaches_the_classifier(
    client, user_provider, classifier, storage, enqueued
):
    started = _initiate(
        client, user_provider, document_type_code="invoice_fuel"
    ).json()
    # The override is the user's explicit choice, distinguishable from auto.
    assert classifier.calls == [("electricity-invoice.pdf", None, "invoice_fuel")]
    assert started["classification"]["document_type_code"] == "invoice_electricity"


def test_a_classification_failure_is_reported_honestly_and_never_fails_the_upload(
    client, world, user_provider, classifier, storage, enqueued
):
    classifier.error = RuntimeError("document_types reference data is unavailable")

    started = _initiate(client, user_provider)
    assert started.status_code == 201, started.text
    body = started.json()
    verdict = body["classification"]
    assert verdict["source"] == "unavailable"
    assert verdict["document_type_code"] is None
    assert verdict["suggested_type"] is None
    assert verdict["confidence"] == 0.0

    # The file still uploads and still enters processing.
    completed = _land_and_complete(client, storage, body)
    assert completed.status_code == 200, completed.text
    assert completed.json()["classification"]["source"] == "unavailable"
    assert len(enqueued.calls) == 1


def test_classification_does_not_change_the_verified_processing_pipeline(
    client, user_provider, classifier, storage, enqueued
):
    """The pipeline is enqueued with exactly the same arguments as before.

    ``data_type`` remains the processing hint supplied by the caller (default
    ``utility``); the classification verdict is metadata only.
    """
    started = _initiate(client, user_provider, data_type="fuel").json()
    completed = _land_and_complete(client, storage, started)
    assert completed.status_code == 200, completed.text

    assert len(enqueued.calls) == 1
    call = enqueued.calls[0]
    assert call["data_type"] == "fuel"
    assert call["organization_id"] == ORG_A
    assert call["storage_path"] == started["storage_path"]


def test_the_default_data_type_is_unchanged_when_the_caller_omits_it(
    client, user_provider, classifier, storage, enqueued
):
    """Omitting ``data_type`` still yields the platform default, as before."""
    user_provider.set_user(member_user(ORG_A, "u-1", "u1@example.test"))
    started = client.post(
        "/api/v3/documents/upload-url",
        json={
            "organization_id": ORG_A,
            "filename": "electricity-invoice.pdf",
            "size_bytes": len(PDF_BYTES),
            "content_type": "application/pdf",
        },
    ).json()
    assert started["status"] == "pending_upload"
    completed = _land_and_complete(client, storage, started)
    assert completed.status_code == 200, completed.text
    assert enqueued.calls[0]["data_type"] == "utility"
