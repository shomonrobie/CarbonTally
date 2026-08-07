"""Import-batches repository (Backend v2.1 §10).

Persistence for the versioned ``import_batches`` aggregate. Batches are
immutable after creation except for the documented state transitions
(pending → importing → completed | failed | rolled_back) and the
activation flag; ``delete`` is implemented for contract completeness only.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.provider import ImportBatch, ImportError

_BATCH_COLUMNS = """
    id, provider_key, provider_version, source_file, source_checksum,
    reporting_year, status, rows_total, rows_imported, rows_skipped,
    rows_duplicate, errors, is_active, created_at, created_by,
    rolled_back_from, updated_at
"""


def _errors_to_jsonb(errors: tuple[ImportError, ...]) -> str:
    payload = [
        {
            "row_number": e.row_number,
            "field": e.field,
            "message": e.message,
            "severity": e.severity,
        }
        for e in errors
    ]
    return dumps_jsonb(payload)


def _errors_from_jsonb(raw: object) -> tuple[ImportError, ...]:
    if not raw:
        return ()
    items = loads_jsonb(raw) or []
    result = []
    for item in items:
        result.append(
            ImportError(
                row_number=int(item["row_number"]),
                field=str(item.get("field") or ""),
                message=str(item.get("message") or ""),
                severity=str(item.get("severity") or "error"),
            )
        )
    return tuple(result)


def _row_to_batch(row: Any) -> ImportBatch:
    r = dict(row)
    return ImportBatch(
        id=str(r["id"]),
        provider_key=str(r["provider_key"]),
        provider_version=str(r["provider_version"]),
        source_file=str(r["source_file"]),
        source_checksum=str(r["source_checksum"]),
        reporting_year=int(r["reporting_year"]),
        status=str(r["status"]),
        rows_total=int(r.get("rows_total") or 0),
        rows_imported=int(r.get("rows_imported") or 0),
        rows_skipped=int(r.get("rows_skipped") or 0),
        rows_duplicate=int(r.get("rows_duplicate") or 0),
        errors=_errors_from_jsonb(r.get("errors")),
        is_active=bool(r["is_active"]),
        created_at=r["created_at"],
        created_by=str(r["created_by"]) if r.get("created_by") else "",
        rolled_back_from=str(r["rolled_back_from"]) if r.get("rolled_back_from") else None,
    )

class ImportsRepository(AbstractRepository[ImportBatch]):
    """Versioned import-batch lifecycle management."""

    async def create_batch(
        self,
        provider: str,
        version: str,
        year: int,
        source: str,
        checksum: str,
        created_by: str,
    ) -> ImportBatch:
        """Create a pending batch."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.import_batches (
                provider_key, provider_version, source_file, source_checksum,
                reporting_year, status, rows_total, rows_imported,
                rows_skipped, rows_duplicate, errors, is_active,
                created_at, created_by, updated_at
            ) VALUES ($1, $2, $3, $4, $5, 'pending', 0, 0, 0, 0,
                      NULL, FALSE, NOW(), $6::uuid, NOW())
            RETURNING {_BATCH_COLUMNS}
            """,
            provider,
            version,
            source,
            checksum,
            year,
            created_by,
        )
        if row is None:
            raise RuntimeError("import batch insert returned no row")
        return _row_to_batch(row)

    async def complete_batch(
        self,
        batch_id: str,
        total: int,
        imported: int,
        skipped: int,
        duplicates: int,
        errors: list[ImportError],
    ) -> ImportBatch:
        """Mark the batch as completed with final row counts."""
        row = await self._fetch_one(
            f"""
            UPDATE public.import_batches
            SET status = 'completed',
                rows_total = $2,
                rows_imported = $3,
                rows_skipped = $4,
                rows_duplicate = $5,
                errors = $6::jsonb,
                updated_at = NOW()
            WHERE id = $1
            RETURNING {_BATCH_COLUMNS}
            """,
            batch_id,
            total,
            imported,
            skipped,
            duplicates,
            _errors_to_jsonb(tuple(errors)),
        )
        if row is None:
            raise RuntimeError(f"import batch {batch_id!r} does not exist")
        return _row_to_batch(row)

    async def fail_batch(
        self, batch_id: str, errors: list[ImportError]
    ) -> ImportBatch:
        """Mark the batch as failed with the collected errors."""
        row = await self._fetch_one(
            f"""
            UPDATE public.import_batches
            SET status = 'failed',
                errors = $2::jsonb,
                is_active = FALSE,
                updated_at = NOW()
            WHERE id = $1
            RETURNING {_BATCH_COLUMNS}
            """,
            batch_id,
            _errors_to_jsonb(tuple(errors)),
        )
        if row is None:
            raise RuntimeError(f"import batch {batch_id!r} does not exist")
        return _row_to_batch(row)


    async def activate_batch(self, batch_id: str) -> ImportBatch:
        """Activate the batch, deactivating any other active batch for the
        same provider/year so the single-active-batch invariant holds."""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                current = await conn.fetchrow(
                    "SELECT provider_key, reporting_year FROM public.import_batches WHERE id = $1",
                    batch_id,
                )
                if current is None:
                    raise RuntimeError(f"import batch {batch_id!r} does not exist")
                await conn.execute(
                    """
                    UPDATE public.import_batches
                    SET is_active = FALSE, updated_at = NOW()
                    WHERE provider_key = $1
                      AND reporting_year = $2
                      AND is_active = TRUE
                      AND id <> $3
                    """,
                    current["provider_key"],
                    current["reporting_year"],
                    batch_id,
                )
                row = await conn.fetchrow(
                    f"""
                    UPDATE public.import_batches
                    SET is_active = TRUE, updated_at = NOW()
                    WHERE id = $1
                    RETURNING {_BATCH_COLUMNS}
                    """,
                    batch_id,
                )
        if row is None:
            raise RuntimeError(f"import batch {batch_id!r} does not exist")
        return _row_to_batch(row)

    async def deactivate_batch(self, batch_id: str) -> ImportBatch:
        """Set ``is_active = FALSE`` on the batch."""
        row = await self._fetch_one(
            f"""
            UPDATE public.import_batches
            SET is_active = FALSE, updated_at = NOW()
            WHERE id = $1
            RETURNING {_BATCH_COLUMNS}
            """,
            batch_id,
        )
        if row is None:
            raise RuntimeError(f"import batch {batch_id!r} does not exist")
        return _row_to_batch(row)

    async def rollback_batch(self, batch_id: str, replaced_by: str) -> ImportBatch:
        """Roll the batch back, recording the replacement batch id."""
        row = await self._fetch_one(
            f"""
            UPDATE public.import_batches
            SET status = 'rolled_back',
                is_active = FALSE,
                rolled_back_from = $2::uuid,
                updated_at = NOW()
            WHERE id = $1
            RETURNING {_BATCH_COLUMNS}
            """,
            batch_id,
            replaced_by,
        )
        if row is None:
            raise RuntimeError(f"import batch {batch_id!r} does not exist")
        return _row_to_batch(row)


    async def get_active(self, provider: str, year: int) -> Optional[ImportBatch]:
        """Return the currently active batch for ``provider`` + ``year``."""
        row = await self._fetch_one(
            f"""
            SELECT {_BATCH_COLUMNS} FROM public.import_batches
            WHERE provider_key = $1 AND reporting_year = $2 AND is_active = TRUE
            LIMIT 1
            """,
            provider,
            year,
        )
        return _row_to_batch(row) if row is not None else None

    async def get_history(self, provider: str) -> list[ImportBatch]:
        """Return the full batch history for ``provider`` (newest first)."""
        rows = await self._fetch_all(
            f"""
            SELECT {_BATCH_COLUMNS} FROM public.import_batches
            WHERE provider_key = $1
            ORDER BY created_at DESC
            """,
            provider,
        )
        return [_row_to_batch(r) for r in rows]

    async def get(self, id: str) -> Optional[ImportBatch]:
        """Return the single batch with ``id``, or ``None``."""
        row = await self._fetch_one(
            f"SELECT {_BATCH_COLUMNS} FROM public.import_batches WHERE id = $1",
            id,
        )
        return _row_to_batch(row) if row is not None else None

    async def save(self, entity: ImportBatch) -> ImportBatch:
        """Update a batch row from the (immutable) domain object's fields."""
        row = await self._fetch_one(
            f"""
            UPDATE public.import_batches
            SET provider_key = $2,
                provider_version = $3,
                source_file = $4,
                source_checksum = $5,
                reporting_year = $6,
                status = $7,
                rows_total = $8,
                rows_imported = $9,
                rows_skipped = $10,
                rows_duplicate = $11,
                errors = $12::jsonb,
                is_active = $13,
                rolled_back_from = $14::uuid,
                updated_at = NOW()
            WHERE id = $1
            RETURNING {_BATCH_COLUMNS}
            """,
            entity.id,
            entity.provider_key,
            entity.provider_version,
            entity.source_file,
            entity.source_checksum,
            entity.reporting_year,
            entity.status,
            entity.rows_total,
            entity.rows_imported,
            entity.rows_skipped,
            entity.rows_duplicate,
            _errors_to_jsonb(entity.errors),
            entity.is_active,
            entity.rolled_back_from,
        )
        if row is None:
            raise RuntimeError(f"import batch {entity.id!r} does not exist")
        return _row_to_batch(row)

    async def delete(self, id: str) -> None:
        """Delete a batch (not used — batches are immutable)."""
        await self._execute(
            "DELETE FROM public.import_batches WHERE id = $1", id
        )

