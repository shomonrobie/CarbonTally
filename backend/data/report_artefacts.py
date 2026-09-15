"""Phase 8 B4/S5 — frozen report artefact persistence (APPEND-ONLY).

There is deliberately **no update path** and no delete path: PO `B4-D5/D6/D7`
requires the object key and content hash to be immutable, with corrections made
by creating a new report version (D15/DM-7). The repository exposes creation and
reads only.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository

_COLUMNS = """
    id, organization_id, report_id, report_version_id, storage_bucket, object_key,
    content_sha256, byte_size, content_type, produced_by, produced_at, created_at
"""


def _row_to_artefact(row: Any) -> dict:
    r = dict(row)
    return {
        "id": str(r["id"]),
        "organization_id": str(r["organization_id"]),
        "report_id": str(r["report_id"]),
        "report_version_id": str(r["report_version_id"]),
        "storage_bucket": str(r["storage_bucket"]),
        "object_key": str(r["object_key"]),
        "content_sha256": str(r["content_sha256"]).strip(),
        "byte_size": int(r["byte_size"]),
        "content_type": str(r["content_type"]),
        "produced_by": str(r["produced_by"]) if r.get("produced_by") else None,
        "produced_at": r["produced_at"].isoformat() if r.get("produced_at") else None,
        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
    }


class ReportArtefactRepository(AbstractRepository[dict]):
    """Append-only access to ``report_version_artifacts``."""

    async def get(self, id: str) -> Optional[dict]:
        row = await self._fetch_one(
            f"SELECT {_COLUMNS} FROM public.report_version_artifacts WHERE id = $1", id
        )
        return _row_to_artefact(row) if row is not None else None

    async def get_for_version(self, report_version_id: str) -> Optional[dict]:
        row = await self._fetch_one(
            f"SELECT {_COLUMNS} FROM public.report_version_artifacts "
            "WHERE report_version_id = $1",
            report_version_id,
        )
        return _row_to_artefact(row) if row is not None else None

    async def list_for_report(self, report_id: str) -> list[dict]:
        rows = await self._fetch_all(
            f"SELECT {_COLUMNS} FROM public.report_version_artifacts "
            "WHERE report_id = $1 ORDER BY produced_at",
            report_id,
        )
        return [_row_to_artefact(row) for row in rows]

    async def create(self, record: dict) -> Optional[dict]:
        """Insert the single artefact record for a version.

        Returns ``None`` when the version already has an artefact (the UNIQUE
        constraint is the enforcement point, so a concurrent caller cannot create
        a second record or overwrite the first).
        """
        row = await self._fetch_one(
            f"""
            INSERT INTO public.report_version_artifacts
                (organization_id, report_id, report_version_id, storage_bucket,
                 object_key, content_sha256, byte_size, content_type, produced_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (report_version_id) DO NOTHING
            RETURNING {_COLUMNS}
            """,
            record["organization_id"],
            record["report_id"],
            record["report_version_id"],
            record["storage_bucket"],
            record["object_key"],
            record["content_sha256"],
            record["byte_size"],
            record["content_type"],
            record.get("produced_by"),
        )
        return _row_to_artefact(row) if row is not None else None

    async def save(self, entity: dict) -> dict:
        created = await self.create(entity)
        if created is None:
            existing = await self.get_for_version(str(entity["report_version_id"]))
            return existing or {}
        return created

    async def delete(self, id: str) -> None:
        raise NotImplementedError(
            "B4-D5/D6/D7: report_version_artifacts is append-only - a frozen artefact "
            "is never rewritten or deleted; corrections create a new report version"
        )
