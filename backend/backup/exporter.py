"""Pure-Python logical exporter (D1) built on ``asyncpg`` COPY.

There is **no** ``pg_dump``, no Supabase CLI, no Docker and no subprocess
anywhere in this module: data is streamed with ``copy_from_query`` and schema is
read from the PostgreSQL catalog (``backup.catalog``).

Snapshot semantics (documented in the implementation report):

* the whole export runs inside **one read-only ``REPEATABLE READ`` transaction**,
  so catalog reads and every ``COPY`` observe a single consistent snapshot;
* the artifact is only produced if that transaction completes successfully — a
  failure removes the temporary directory and raises, so a partial export can
  never be mistaken for a valid backup;
* the export is read-only and idempotent, therefore **re-running it is safe**
  (a retry simply produces a fresh artifact);
* row ordering is deterministic when the table has a primary key (``ORDER BY``
  the key columns) and unspecified otherwise — recorded per table in the manifest;
* partition **parents** are exported once and partition **leaves** are not (F1), so
  logical rows are captured exactly once and row counts are exact;
* credential-bearing/private schemas are refused **before** the snapshot starts (F2).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

from core.logging import get_logger

from backup.artifact import (
    ARCHIVE_DATA_PREFIX,
    ARCHIVE_MEMBER_CATALOG,
    ARCHIVE_MEMBER_DDL,
    ARCHIVE_MEMBER_MANIFEST,
    ARCHIVE_MEMBER_SEQUENCES,
    TableInventoryEntry,
)
from backup.catalog import CatalogSnapshot, collect_catalog, read_sequence_state
from backup.errors import BackupConfigurationError, BackupExportError
from backup.settings import validate_schemas

logger = get_logger(__name__)

_MEMBER_SEPARATOR = "__"


@dataclass
class ExportResult:
    """Everything the service needs in order to assemble the artifact."""

    catalog: CatalogSnapshot = field(default_factory=CatalogSnapshot)
    inventory: list[TableInventoryEntry] = field(default_factory=list)
    data_member_paths: dict[str, str] = field(default_factory=dict)
    sequence_states: list[dict[str, Any]] = field(default_factory=list)
    total_rows: int = 0


def _data_member_name(schema: str, table: str) -> str:
    return f"{ARCHIVE_DATA_PREFIX}{schema}{_MEMBER_SEPARATOR}{table}.copy"


async def export_schemas(
    connection: Any,
    schemas: Sequence[str],
    *,
    output_dir: str,
    include_sequence_state: bool = True,
    allow_denied_schemas: bool = False,
) -> ExportResult:
    """Export the requested schemas, normalising every failure to a typed error.

    Args:
        connection: an ``asyncpg`` connection (for example from a pool acquire).
        schemas: schema names to export.
        output_dir: directory that receives ``catalog/`` and ``data/`` material.
        include_sequence_state: read each sequence's current values (OID-2).
        allow_denied_schemas: ``True`` only when the deliberate administrative
            override is in force (F2). Defaults to ``False`` so a direct caller of
            this function also fails closed on credential-bearing schemas.

    Returns:
        An :class:`ExportResult` describing what was written.

    Raises:
        BackupConfigurationError: a credential-bearing/private schema was requested
            without the override (F2).
        BackupExportError: for **any** other failure — connection/transaction setup,
            catalog introspection, COPY, or writing the staged files. Callers
            therefore never see a raw driver exception, and a failed export can
            never be mistaken for a successful one.
    """
    # F2: refuse credential-bearing schemas *before* opening the snapshot.
    validate_schemas(schemas, allow_override=allow_denied_schemas)
    try:
        return await _export_schemas_inner(
            connection,
            schemas,
            output_dir=output_dir,
            include_sequence_state=include_sequence_state,
        )
    except (BackupConfigurationError, BackupExportError):
        raise
    except Exception as exc:  # noqa: BLE001 - normalised into a typed error
        raise BackupExportError(
            "logical export failed", details={"reason": exc.__class__.__name__}
        ) from exc


async def _export_schemas_inner(
    connection: Any,
    schemas: Sequence[str],
    *,
    output_dir: str,
    include_sequence_state: bool = True,
) -> ExportResult:
    """Implementation of :func:`export_schemas` (see its docstring)."""
    result = ExportResult()
    catalog_dir = os.path.join(output_dir, "catalog")
    data_dir = os.path.join(output_dir, "data")
    os.makedirs(catalog_dir, mode=0o700, exist_ok=True)
    os.makedirs(data_dir, mode=0o700, exist_ok=True)

    async with connection.transaction(isolation="repeatable_read", readonly=True):
        result.catalog = await collect_catalog(connection, schemas)

        for table in result.catalog.tables:
            schema = str(table["schema"])
            name = str(table["name"])
            qualified = str(table["qualified_name"])
            primary_key = result.catalog.primary_key_columns(schema, name)
            member = _data_member_name(schema, name)
            member_path = os.path.join(output_dir, member)
            query = _select_query(qualified, primary_key)
            try:
                await connection.copy_from_query(query, output=member_path)
            except Exception as exc:  # noqa: BLE001 - normalised into a typed error
                raise BackupExportError(
                    "table export failed",
                    details={"table": f"{schema}.{name}", "reason": exc.__class__.__name__},
                ) from exc
            rows = _count_copy_rows(member_path)
            result.data_member_paths[f"{schema}.{name}"] = member
            result.inventory.append(
                TableInventoryEntry(
                    schema=schema,
                    name=name,
                    data_member=member,
                    row_count=rows,
                    has_primary_key=bool(primary_key),
                    ordered_by_primary_key=bool(primary_key),
                    column_count=len(result.catalog.columns_for(schema, name)),
                    rls_enabled=bool(table.get("rls_enabled")),
                )
            )
            result.total_rows += rows

        if include_sequence_state:
            for sequence in result.catalog.sequences:
                state = await read_sequence_state(connection, str(sequence["qualified_name"]))
                result.sequence_states.append({**sequence, **state})

    _write_text(
        os.path.join(catalog_dir, "catalog.json"),
        json.dumps(result.catalog.as_dict(), sort_keys=True, indent=2, ensure_ascii=False) + "\n",
    )
    _write_text(
        os.path.join(catalog_dir, "ddl.sql"),
        "\n".join(result.catalog.to_ddl_lines()) + "\n",
    )
    _write_text(
        os.path.join(catalog_dir, "sequences.json"),
        json.dumps(result.sequence_states, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
    )
    logger.info(
        "backup export completed: %d tables, %d rows, %d sequences",
        len(result.inventory),
        result.total_rows,
        len(result.sequence_states),
    )
    return result


def _select_query(qualified_name: str, primary_key: Sequence[str]) -> str:
    """Build the COPY source query.

    ``qualified_name`` is the server-produced, already-quoted identifier from
    ``catalog._TABLES_SQL``; ``primary_key`` values are parsed from the primary-key
    constraint definition. Both are quoted defensively here — **no value ever
    originates from an HTTP request**.
    """
    if primary_key:
        order = ", ".join(_quote_ident(column) for column in primary_key)
        return f"SELECT * FROM {qualified_name} ORDER BY {order}"
    return f"SELECT * FROM {qualified_name}"


def _quote_ident(identifier: str) -> str:
    return '"' + str(identifier).replace('"', '""') + '"'


def _count_copy_rows(path: str) -> int:
    """Count data rows in a COPY text payload.

    Each physical line is one row; PostgreSQL escapes embedded newlines inside
    COPY text values, so a line count is exact. An empty table yields 0.
    """
    total = 0
    with open(path, "rb") as handle:
        for _line in handle:
            total += 1
    return total


def _write_text(path: str, payload: str) -> None:
    directory = os.path.dirname(path)
    os.makedirs(directory, mode=0o700, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    os.chmod(path, 0o600)


def collect_members(
    output_dir: str, *, manifest_json: Optional[bytes] = None
) -> list[tuple[str, bytes]]:
    """Collect every file under ``output_dir`` as ``(relative_path, bytes)``.

    ``manifest.json`` is skipped during the walk and (optionally) appended last,
    because the manifest carries the content checksums of the other members.
    """
    members: list[tuple[str, bytes]] = []
    for directory, _dirs, files in os.walk(output_dir):
        for name in sorted(files):
            absolute = os.path.join(directory, name)
            relative = os.path.relpath(absolute, output_dir).replace(os.sep, "/")
            if relative == ARCHIVE_MEMBER_MANIFEST:
                continue
            with open(absolute, "rb") as handle:
                members.append((relative, handle.read()))
    if manifest_json is not None:
        members.append((ARCHIVE_MEMBER_MANIFEST, manifest_json))
    return members


__all__ = [
    "ARCHIVE_MEMBER_CATALOG",
    "ARCHIVE_MEMBER_DDL",
    "ARCHIVE_MEMBER_SEQUENCES",
    "ExportResult",
    "collect_members",
    "export_schemas",
]

