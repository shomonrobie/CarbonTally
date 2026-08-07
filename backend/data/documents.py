"""Documents repository (Backend v2.1 §10).

Persistence for the RC2 ``customer_documents`` aggregate — the source document
uploaded by a customer. ``status`` follows the widened RC2 vocabulary
(``uploaded``, ``pending``, ``processing``, ``processed``, ...).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, cast

from data.base import AbstractRepository
from domain.document import Document

#: Service-role placeholder for the NOT NULL ``organization_member_id`` column
#: the v2.1 ``create_from_upload`` contract does not receive.
_SYSTEM_UUID = "00000000-0000-0000-0000-000000000000"

_DOC_COLUMNS = """
    id, organization_id, file_name, file_url, file_type, status,
    upload_date, created_at, updated_at, uploaded_by, organization_member_id
"""


def _row_to_document(row: Any) -> Document:
    r = dict(row)
    uploaded_at = r.get("upload_date") or r.get("created_at")
    if uploaded_at is None:
        raise RuntimeError("document row has neither upload_date nor created_at")
    uploaded_by = r.get("uploaded_by") or r.get("organization_member_id") or ""
    return Document(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        filename=str(r["file_name"]),
        storage_path=str(r["file_url"]),
        file_type=str(r["file_type"]),
        status=str(r["status"]),
        uploaded_at=cast(datetime, uploaded_at),
        uploaded_by=str(uploaded_by),
    )


class DocumentsRepository(AbstractRepository[Document]):
    """CRUD and lookup for customer documents."""

    async def create_from_upload(
        self, org_id: str, storage_path: str, filename: str, file_type: str
    ) -> Document:
        """Create a pending document record from an uploaded file."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.customer_documents (
                organization_id, organization_member_id, file_name, file_url,
                file_type, status, upload_date, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, 'pending', NOW(), NOW(), NOW())
            RETURNING {_DOC_COLUMNS}
            """,
            org_id,
            _SYSTEM_UUID,
            filename,
            storage_path,
            file_type,
        )
        if row is None:
            raise RuntimeError("document insert returned no row")
        return _row_to_document(row)

    async def update_status(self, doc_id: str, status: str) -> Document:
        """Update the document's processing status."""
        row = await self._fetch_one(
            f"""
            UPDATE public.customer_documents
            SET status = $2, updated_at = NOW()
            WHERE id = $1
            RETURNING {_DOC_COLUMNS}
            """,
            doc_id,
            status,
        )
        if row is None:
            raise RuntimeError(f"document {doc_id!r} does not exist")
        return _row_to_document(row)

    async def get_pending_extraction(self) -> list[Document]:
        """Return documents ready for extraction, oldest first."""
        rows = await self._fetch_all(
            f"""
            SELECT {_DOC_COLUMNS} FROM public.customer_documents
            WHERE status IN ('pending', 'uploaded')
            ORDER BY created_at, id
            """
        )
        return [_row_to_document(r) for r in rows]

    async def get_by_org(self, org_id: str) -> list[Document]:
        """Return every document belonging to the organisation."""
        rows = await self._fetch_all(
            f"""
            SELECT {_DOC_COLUMNS} FROM public.customer_documents
            WHERE organization_id = $1
            ORDER BY created_at DESC, id
            """,
            org_id,
        )
        return [_row_to_document(r) for r in rows]

    async def get(self, id: str) -> Optional[Document]:
        """Return the document with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_DOC_COLUMNS} FROM public.customer_documents WHERE id = $1",
            id,
        )
        return _row_to_document(row) if row is not None else None

    async def save(self, entity: Document) -> Document:
        """Upsert a document by id and return the stored state."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.customer_documents (
                id, organization_id, file_name, file_url, file_type, status,
                upload_date, created_at, updated_at, uploaded_by, organization_member_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $7, NOW(), $8, $8)
            ON CONFLICT (id)
            DO UPDATE SET
                file_name = EXCLUDED.file_name,
                file_url = EXCLUDED.file_url,
                file_type = EXCLUDED.file_type,
                status = EXCLUDED.status,
                updated_at = NOW()
            RETURNING {_DOC_COLUMNS}
            """,
            entity.id,
            entity.organization_id,
            entity.filename,
            entity.storage_path,
            entity.file_type,
            entity.status,
            entity.uploaded_at,
            entity.uploaded_by,
        )
        if row is None:
            raise RuntimeError("document upsert returned no row")
        return _row_to_document(row)

    async def delete(self, id: str) -> None:
        """Delete a document record."""
        await self._execute(
            "DELETE FROM public.customer_documents WHERE id = $1", id
        )
