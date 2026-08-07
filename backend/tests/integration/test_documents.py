"""Integration tests for DocumentsRepository."""
from __future__ import annotations

import asyncpg
import pytest

from data.documents import DocumentsRepository
from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio


async def test_create_from_upload_and_get(pool: asyncpg.Pool) -> None:
    repo = DocumentsRepository(pool)
    org_id = await make_org(pool)
    doc = await repo.create_from_upload(
        org_id=org_id,
        storage_path="uploads/invoice.pdf",
        filename="invoice.pdf",
        file_type="invoice",
    )
    assert doc.id
    assert doc.status == "pending"
    assert doc.file_type == "invoice"
    fetched = await repo.get(doc.id)
    assert fetched is not None
    assert fetched.storage_path == "uploads/invoice.pdf"
    assert fetched.filename == "invoice.pdf"
    assert fetched.organization_id == org_id


async def test_update_status(pool: asyncpg.Pool) -> None:
    repo = DocumentsRepository(pool)
    org_id = await make_org(pool)
    doc = await repo.create_from_upload(
        org_id=org_id, storage_path="s/a.pdf", filename="a.pdf", file_type="other"
    )
    updated = await repo.update_status(doc.id, "processing")
    assert updated.status == "processing"
    refreshed = await repo.get(doc.id)
    assert refreshed is not None
    assert refreshed.status == "processing"


async def test_get_pending_extraction(pool: asyncpg.Pool) -> None:
    repo = DocumentsRepository(pool)
    pending = await repo.create_from_upload(
        org_id=await make_org(pool), storage_path="s/p.pdf", filename="p.pdf", file_type="other"
    )
    done = await repo.create_from_upload(
        org_id=await make_org(pool), storage_path="s/done.pdf", filename="done.pdf", file_type="other"
    )
    await repo.update_status(done.id, "processing")
    pending_ids = {d.id for d in await repo.get_pending_extraction()}
    assert pending.id in pending_ids
    assert done.id not in pending_ids


async def test_get_by_org(pool: asyncpg.Pool) -> None:
    repo = DocumentsRepository(pool)
    org_a = await make_org(pool)
    org_b = await make_org(pool)
    doc_a = await repo.create_from_upload(
        org_id=org_a, storage_path="s/a.pdf", filename="a.pdf", file_type="other"
    )
    await repo.create_from_upload(
        org_id=org_b, storage_path="s/b.pdf", filename="b.pdf", file_type="other"
    )
    org_a_docs = await repo.get_by_org(org_a)
    assert {d.id for d in org_a_docs} == {doc_a.id}


async def test_save_updates_document(pool: asyncpg.Pool) -> None:
    repo = DocumentsRepository(pool)
    doc = await repo.create_from_upload(
        org_id=await make_org(pool), storage_path="s/x.pdf", filename="x.pdf", file_type="other"
    )
    from dataclasses import replace

    renamed = replace(doc, filename="renamed.pdf", status="approved")
    saved = await repo.save(renamed)
    assert saved.filename == "renamed.pdf"
    assert saved.status == "approved"


async def test_delete(pool: asyncpg.Pool) -> None:
    repo = DocumentsRepository(pool)
    doc = await repo.create_from_upload(
        org_id=await make_org(pool), storage_path="s/y.pdf", filename="y.pdf", file_type="other"
    )
    await repo.delete(doc.id)
    assert await repo.get(doc.id) is None
