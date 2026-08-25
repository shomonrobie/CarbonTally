"""Customer verification repository (V3 legacy-capability reimplementation).

Persistence for customer verification decisions over documents. The current V3
schema stores verification state on ``customer_documents`` (status, verified_by,
verified_at, metadata); a dedicated verification record table can be introduced
later without changing this surface.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.operations import Verification

_DOC_COLUMNS = (
    "id, organization_id, file_name, file_url, status, verified_by, "
    "verified_at, metadata"
)


class VerificationsRepository(AbstractRepository[Verification]):
    """List and decide document verifications."""

    async def get_document(self, document_id: str) -> Optional[dict]:
        row = await self._fetch_one(
            f"SELECT {_DOC_COLUMNS} FROM public.customer_documents WHERE id = $1",
            document_id,
        )
        return dict(row) if row is not None else None

    async def list_pending(self, org_id: str) -> list[dict]:
        rows = await self._fetch_all(
            f"""
            SELECT {_DOC_COLUMNS} FROM public.customer_documents
            WHERE organization_id = $1 AND status IN ('pending', 'processing', 'processed')
            ORDER BY created_at
            """,
            org_id,
        )
        return [dict(r) for r in rows]

    async def verify(
        self,
        document_id: str,
        org_id: str,
        status: str,
        verified_by: str,
        notes: Optional[str],
        extraction: Optional[dict],
    ) -> Optional[Verification]:
        """Record an approve/reject/correct decision on a document."""
        row = await self._fetch_one(
            f"""
            UPDATE public.customer_documents
            SET status = $2, verified_by = $3, verified_at = NOW(),
                metadata = COALESCE($4, metadata)
            WHERE id = $1 AND organization_id = $5
            RETURNING {_DOC_COLUMNS}
            """,
            document_id,
            status,
            verified_by,
            dumps_jsonb({"notes": notes, "extraction": extraction} if (notes or extraction) else None),
            org_id,
        )
        if row is None:
            return None
        r = dict(row)
        meta = loads_jsonb(r.get("metadata")) or {}
        return Verification(
            document_id=str(r["id"]),
            organization_id=str(r["organization_id"]),
            status=str(r["status"]),
            verified_by=r.get("verified_by"),
            verified_at=r.get("verified_at"),
            notes=meta.get("notes") if isinstance(meta, dict) else None,
            extraction=meta.get("extraction") if isinstance(meta, dict) else None,
        )

    async def get(self, id: str):
        return await self.get_document(id)

    async def save(self, entity: Verification) -> Verification:
        return entity

    async def delete(self, id: str) -> None:
        return None
