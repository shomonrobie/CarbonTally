"""CT-STEP2-FINAL-STABILIZATION-012 (WS-C) — enqueue visibility.

A document that is stored but never queued for automatic processing must not look
like a silently stalled upload: the enqueue outcome is persisted on the document
record (`automatic_processing` + `enqueue_error`) while the upload itself still
succeeds (the manual path stays available).

These tests call the shared upload pipeline directly with fakes, so no storage, no
database and no network are involved.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

import api.v3_documents as v3d


class _FakeUpload:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def upload(self, path, content, file_options=None):
        self.calls.append((path, content, file_options))


class _FakeBucket:
    def __init__(self) -> None:
        self.upload = _FakeUpload().upload


class _FakeStorageClient:
    def __init__(self) -> None:
        self.storage = SimpleNamespace(from_=lambda bucket: _FakeBucket())


def _repos(*, enqueue_fails: bool):
    files = SimpleNamespace(
        created=None,
        metadata_updates=[],
    )

    async def create(**kwargs):
        files.created = SimpleNamespace(
            id="doc-1", metadata=dict(kwargs.get("metadata") or {})
        )
        return files.created

    async def update_metadata(file_id, metadata):
        files.metadata_updates.append((file_id, dict(metadata)))

    files.create = create
    files.update_metadata = update_metadata

    manual = SimpleNamespace()
    manual.list_batches = lambda org: _async([])
    manual.create_batch = lambda **kw: _async(SimpleNamespace(id="batch-1"))
    manual.create_item = lambda *a, **kw: _async(SimpleNamespace(id="item-1"))

    processing = SimpleNamespace(calls=[])

    async def proc_create(**kwargs):
        processing.calls.append(kwargs)
        if enqueue_fails:
            raise RuntimeError(
                "permission denied for table document_processing_queue"
            )
        return SimpleNamespace(id="job-1")

    processing.create = proc_create

    return SimpleNamespace(files=files, manual_extraction=manual, processing=processing)


async def _async(value):
    return value


@pytest.fixture(autouse=True)
def _patch_storage_and_text(monkeypatch):
    monkeypatch.setattr(v3d, "get_service_client", lambda: _FakeStorageClient())
    monkeypatch.setattr(v3d, "storage_signed_url", lambda path: f"signed://{path}")
    monkeypatch.setattr(
        v3d,
        "_extract_document_text",
        lambda content, filename, mime: {"status": "no_text"},
    )


async def _run(repos):
    return await v3d.create_document_and_enqueue(
        organization_id="org-1",
        filename="fuel_card.csv",
        content=b"Transaction Date,Fuel Type,Volume (L),Total Cost (\xc2\xa3)\n01/10/2023,Diesel,53.8,85.21\n",
        mime_type="text/csv",
        file_type="SPREADSHEET",
        data_type="fuel",
        uploaded_by="user-1",
        repos=repos,
    )


@pytest.mark.asyncio
async def test_successful_enqueue_is_recorded_on_the_document():
    repos = _repos(enqueue_fails=False)

    record = await _run(repos)

    assert record.id == "doc-1"
    assert len(repos.processing.calls) == 1
    job = repos.processing.calls[0]
    assert job["organization_id"] == "org-1"          # tenant context preserved
    assert job["source_item_id"] == "item-1"           # item → job link preserved
    merged = {}
    for _file_id, metadata in repos.files.metadata_updates:
        merged.update(metadata)
    assert merged["automatic_processing"] == "enqueued"


@pytest.mark.asyncio
async def test_failed_enqueue_is_recorded_with_the_reason_and_never_aborts_the_upload():
    repos = _repos(enqueue_fails=True)

    record = await _run(repos)                          # must not raise

    assert record.id == "doc-1"
    merged = {}
    for _file_id, metadata in repos.files.metadata_updates:
        merged.update(metadata)
    assert merged["automatic_processing"] == "enqueue_failed"
    assert "document_processing_queue" in merged["enqueue_error"]
    # the document keeps its own data so the manual path still works
    assert merged["data_type"] == "fuel"


@pytest.mark.asyncio
async def test_the_ocr_write_does_not_clobber_the_enqueue_outcome():
    repos = _repos(enqueue_fails=False)
    v3d._extract_document_text = lambda content, filename, mime: {  # type: ignore[assignment]
        "status": "ok",
        "text": "diesel 53.8 litres",
        "method": "csv",
    }

    await _run(repos)

    merged = {}
    for _file_id, metadata in repos.files.metadata_updates:
        merged.update(metadata)
    assert merged["automatic_processing"] == "enqueued"
    assert merged["ocr"]["status"] == "ok"
