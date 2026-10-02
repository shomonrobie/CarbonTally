"""Organization files repository (V3 legacy-capability reimplementation).

Persistence for the RC2 ``organization_files`` table — the upload/document
record written after a file is placed in Supabase Storage.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.operations import OrganizationFile

_FILES_COLUMNS = (
    "id, organization_id, name, path, size_bytes, file_type, mime_type, "
    "bucket, status, uploaded_by, uploaded_at, is_active, access_count, metadata"
)


def _row_to_file(row: Any) -> OrganizationFile:
    r = dict(row)
    return OrganizationFile(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        name=str(r["name"]),
        path=str(r["path"]),
        size_bytes=int(r.get("size_bytes") or 0),
        file_type=str(r.get("file_type") or "OTHER"),
        mime_type=str(r.get("mime_type") or ""),
        bucket=str(r.get("bucket") or "documents"),
        status=str(r.get("status") or "uploaded"),
        uploaded_by=str(r.get("uploaded_by") or ""),
        uploaded_at=r.get("uploaded_at"),
        is_active=bool(r.get("is_active", True)),
        metadata=loads_jsonb(r.get("metadata")) or {},
    )


class OrganizationFilesRepository(AbstractRepository[OrganizationFile]):
    """CRUD and lookup for organization_files records."""

    async def create(
        self,
        org_id: str,
        name: str,
        path: str,
        size_bytes: int,
        file_type: str,
        mime_type: str,
        bucket: str,
        uploaded_by: str,
        metadata: Optional[dict] = None,
        status: Optional[str] = None,
    ) -> OrganizationFile:
        """Insert one document row.

        ``status`` (Storage Management Step 1) is the security-lifecycle state
        produced by the upload gate — ``clean`` for an accepted document.  The
        historical default ``'uploaded'`` is kept for callers that do not run the
        lifecycle, so no existing behaviour changes.
        """
        row = await self._fetch_one(
            f"""
            INSERT INTO public.organization_files (
                organization_id, name, path, size_bytes, file_type, mime_type,
                bucket, status, uploaded_by, uploaded_at, is_active,
                access_count, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(),
                      TRUE, 0, $10)
            RETURNING {_FILES_COLUMNS}
            """,
            org_id,
            name,
            path,
            size_bytes,
            file_type,
            mime_type,
            bucket,
            status or "uploaded",
            uploaded_by,
            dumps_jsonb(metadata or {}),
        )
        if row is None:
            raise RuntimeError("organization_files insert returned no row")
        return _row_to_file(row)


    async def get(self, file_id: str) -> Optional[OrganizationFile]:
        row = await self._fetch_one(
            f"SELECT {_FILES_COLUMNS} FROM public.organization_files WHERE id = $1",
            file_id,
        )
        return _row_to_file(row) if row is not None else None

    async def get_by_path(self, path: str) -> Optional[OrganizationFile]:
        """D33 — resolve an organization file by its canonical storage path."""
        row = await self._fetch_one(
            f"SELECT {_FILES_COLUMNS} FROM public.organization_files WHERE path = $1",
            path,
        )
        return _row_to_file(row) if row is not None else None

    async def list_for_org(
        self,
        org_id: str,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[OrganizationFile]:
        query = (
            f"SELECT {_FILES_COLUMNS} FROM public.organization_files "
            "WHERE organization_id = $1 AND is_active = TRUE"
        )
        args: list[Any] = [org_id]
        if status is not None:
            query += f" AND status = ${len(args) + 1}"
            args.append(status)
        query += " ORDER BY uploaded_at DESC"
        query += f" LIMIT {int(limit)} OFFSET {int(offset)}"
        rows = await self._fetch_all(query, *args)
        return [_row_to_file(r) for r in rows]

    async def update_status(
        self, file_id: str, status: str, size_bytes: Optional[int] = None
    ) -> Optional[OrganizationFile]:
        """Advance the lifecycle status, optionally recording the verified size.

        ``size_bytes`` (Storage Management Step 1) lets the direct-upload
        completion path replace the browser-declared size with the size the
        platform actually verified in storage.  ``None`` leaves it untouched.
        """
        row = await self._fetch_one(
            f"""
            UPDATE public.organization_files
            SET status = $2, status_updated_at = NOW(),
                size_bytes = COALESCE($3::bigint, size_bytes)
            WHERE id = $1
            RETURNING {_FILES_COLUMNS}
            """,
            file_id,
            status,
            size_bytes,
        )
        return _row_to_file(row) if row is not None else None


    async def update_metadata(self, file_id: str, metadata: dict) -> Optional[OrganizationFile]:
        """Replace the ``metadata`` JSONB on an organization_files row.

        Used to persist OCR/extraction output without a schema change (the
        row-level traceability chain keeps pointing at ``organization_files``).
        """
        row = await self._fetch_one(
            f"""
            UPDATE public.organization_files
            SET metadata = $2
            WHERE id = $1
            RETURNING {_FILES_COLUMNS}
            """,
            file_id,
            dumps_jsonb(metadata),
        )
        return _row_to_file(row) if row is not None else None

    async def delete(self, file_id: str) -> None:
        await self._execute(
            "UPDATE public.organization_files SET is_active = FALSE WHERE id = $1",
            file_id,
        )

    async def expire_documents_older_than(
        self, cutoff, *, dry_run: bool = True
    ) -> dict[str, int]:
        """N3 — soft-expire documents created before ``cutoff`` (retention).

        Soft-delete only (``deleted_at = NOW()``); rows are never hard-deleted.
        ``dry_run=True`` (default) reports the eligible count without applying.
        """
        if dry_run:
            row = await self._fetch_one(
                "SELECT COUNT(*) AS n FROM public.organization_files "
                "WHERE deleted_at IS NULL AND created_at < $1",
                cutoff,
            )
            return {"eligible": int(row["n"]) if row else 0, "applied": 0}
        row = await self._fetch_one(
            """
            WITH expired AS (
                UPDATE public.organization_files SET deleted_at = NOW()
                WHERE deleted_at IS NULL AND created_at < $1
                RETURNING id
            )
            SELECT COUNT(*) AS n FROM expired
            """,
            cutoff,
        )
        return {"eligible": 0, "applied": int(row["n"]) if row else 0}

    async def list_abandoned_pending_uploads(
        self,
        cutoff,
        *,
        status: str = "pending_upload",
        limit: int = 500,
    ) -> list[OrganizationFile]:
        """Storage Management Step 2F — documents whose upload authorisation expired.

        An upload is *abandoned* when the browser was given a signed upload URL
        and never confirmed completion inside the completion window
        (``services.storage.UPLOAD_COMPLETION_WINDOW_SECONDS``).  This is a
        read-only query: the caller (``services.document_cleanup``) decides
        whether to apply the terminal ``upload_expired`` state.  Rows already
        soft-deleted by the platform retention rule are excluded — they are no
        longer live records.
        """
        rows = await self._fetch_all(
            f"""
            SELECT {_FILES_COLUMNS} FROM public.organization_files
            WHERE status = $1 AND uploaded_at < $2 AND deleted_at IS NULL
            ORDER BY uploaded_at ASC
            LIMIT {int(limit)}
            """,
            status,
            cutoff,
        )
        return [_row_to_file(r) for r in rows]

    async def save(self, entity: OrganizationFile) -> OrganizationFile:
        return entity
