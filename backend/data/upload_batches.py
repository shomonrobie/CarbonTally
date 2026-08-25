"""Upload batches repository (V3 legacy-capability reimplementation).

Persistence for the RC2 ``upload_batches`` table — grouping records for batch
uploads of documents.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.operations import UploadBatch

_BATCH_COLUMNS = (
    "id, organization_id, batch_name, total_files, processed_files, status, "
    "created_by_user_id, created_at, completed_at, metadata"
)


def _row_to_batch(row: Any) -> UploadBatch:
    r = dict(row)
    return UploadBatch(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        batch_name=str(r["batch_name"]),
        total_files=int(r.get("total_files") or 0),
        processed_files=int(r.get("processed_files") or 0),
        status=str(r.get("status") or "pending"),
        created_by_user_id=str(r.get("created_by_user_id") or ""),
        created_at=r.get("created_at"),
        completed_at=r.get("completed_at"),
        metadata=loads_jsonb(r.get("metadata")) or {},
    )


class UploadBatchesRepository(AbstractRepository[UploadBatch]):
    """CRUD and lifecycle for upload batches."""

    async def create(
        self,
        org_id: str,
        batch_name: str,
        created_by_user_id: str,
        metadata: Optional[dict] = None,
    ) -> UploadBatch:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.upload_batches (
                organization_id, batch_name, total_files, processed_files,
                status, created_by_user_id, created_at, metadata
            ) VALUES ($1, $2, 0, 0, 'pending', $3, NOW(), $4)
            RETURNING {_BATCH_COLUMNS}
            """,
            org_id,
            batch_name,
            created_by_user_id,
            dumps_jsonb(metadata or {}),
        )
        if row is None:
            raise RuntimeError("upload_batches insert returned no row")
        return _row_to_batch(row)

    async def get(self, batch_id: str) -> Optional[UploadBatch]:
        row = await self._fetch_one(
            f"SELECT {_BATCH_COLUMNS} FROM public.upload_batches WHERE id = $1",
            batch_id,
        )
        return _row_to_batch(row) if row is not None else None

    async def list_for_org(self, org_id: str) -> list[UploadBatch]:
        rows = await self._fetch_all(
            f"SELECT {_BATCH_COLUMNS} FROM public.upload_batches "
            "WHERE organization_id = $1 ORDER BY created_at DESC",
            org_id,
        )
        return [_row_to_batch(r) for r in rows]

    async def update_progress(self, batch_id: str, processed_files: int, status: str) -> Optional[UploadBatch]:
        row = await self._fetch_one(
            f"""
            UPDATE public.upload_batches
            SET processed_files = $2, status = $3
            WHERE id = $1
            RETURNING {_BATCH_COLUMNS}
            """,
            batch_id,
            processed_files,
            status,
        )
        return _row_to_batch(row) if row is not None else None

    async def complete(self, batch_id: str) -> Optional[UploadBatch]:
        row = await self._fetch_one(
            f"""
            UPDATE public.upload_batches
            SET status = 'completed', completed_at = NOW()
            WHERE id = $1
            RETURNING {_BATCH_COLUMNS}
            """,
            batch_id,
        )
        return _row_to_batch(row) if row is not None else None

    async def save(self, entity: UploadBatch) -> UploadBatch:
        return entity

    async def delete(self, id: str) -> None:
        return None
