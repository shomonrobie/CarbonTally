"""Restore engine — rebuild a database from a CarbonTally backup artifact (D4).

This module closes the largest gap recorded by the Phase-1 implementation and by
the workstream-F recovery drill: *"Restore from the project's own artifact — NOT
IMPLEMENTED (D4). The artifact is verified as an artifact; it cannot rebuild a
database today."*  It rebuilds a database from the artifact's own members.

Scope and boundaries
--------------------

* **Input** — the artifact produced by :mod:`backup.service`: a deterministic tar
  archive (optionally gzip-compressed) encrypted with AES-256-GCM, containing
  ``manifest.json``, ``catalog/catalog.json`` (authoritative), ``catalog/ddl.sql``
  (informational only — deliberately **not** used here), ``catalog/sequences.json``
  and ``data/<schema>__<table>.copy``.
* **Authoritative source** — ``catalog.json``. Every executable statement is
  derived from the *structured* catalog, i.e. from server-produced definitions
  (``pg_get_constraintdef``, ``pg_get_indexdef``, ``pg_get_functiondef``,
  ``pg_get_triggerdef``, ``pg_policies``). ``ddl.sql`` is never executed: it is
  documented in-code as informational, and it does not enable RLS (finding 2 of
  the drill), which would leave a restored database unprotected.
* **Storage objects** are *not* here — they are the separate, sequenced job in
  :mod:`backup.objects` (§14). A database-only restore proves the database half.
* **No subprocess, no CLI, no ``pg_dump``** (D1): data is loaded with
  ``asyncpg``'s ``COPY … FROM STDIN``.
* **Restore is not a normal admin action** (§13/D4). This module knows nothing
  about HTTP, capabilities or tenants: it is the engine an operator tool (and the
  recovery drill) drives against a *disposable* target. No ``Restore production``
  surface is created anywhere.

Correctness details that matter (each one is a real failure mode):

1. **Identity columns are deferred.** ``COPY`` cannot insert into a
   ``GENERATED ALWAYS AS IDENTITY`` column, and PostgreSQL's ``COPY`` has no
   ``OVERRIDING SYSTEM VALUE``. Tables are therefore created with the identity
   column as an ordinary ``NOT NULL`` column, the data is loaded, and the
   identity is added afterwards — the same ordering ``pg_dump`` uses.
2. **Generated columns are excluded from the load.** A ``GENERATED … STORED``
   column cannot be written, so the ``COPY`` column list omits it and the value
   is recomputed by the target.
3. **Constraint-backed indexes are not recreated.** A ``PRIMARY KEY``/``UNIQUE``
   constraint already creates its index; re-running the index definition would
   fail with "relation already exists". Both primary indexes and indexes whose
   name matches a constraint on the same table are skipped.
4. **Partition leaves come from the partition section.** Only partition *parents*
   are exported as tables (finding F1); leaves are created as
   ``… PARTITION OF parent FOR VALUES …`` so the loaded parent data routes into
   them exactly once.
5. **Standalone sequences are created before tables** (a column ``DEFAULT
   nextval(...)`` needs its sequence to exist), and their ``OWNED BY`` is set
   after the table exists.
6. **RLS is enabled explicitly and policies installed**, so a restored database
   is *protected*, not merely shaped like the original.
"""
from __future__ import annotations

import io
import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, Sequence

from core.logging import get_logger

from backup import crypto
from backup.artifact import (
    ARCHIVE_MEMBER_CATALOG,
    ARCHIVE_MEMBER_MANIFEST,
    ARCHIVE_MEMBER_SEQUENCES,
    BACKUP_FORMAT_NAME,
    BACKUP_FORMAT_VERSION,
    read_archive,
    verify_content_checksums,
)
from backup.errors import (
    BackupArtifactError,
    BackupRestoreError,
    BackupRestoreTargetError,
)

logger = get_logger(__name__)

#: Order in which the phases are applied. Recorded in the result so an operator
#: (and the drill) can see exactly what ran, in what order.
RESTORE_PHASES: tuple[str, ...] = (
    "extensions",
    "schemas",
    "sequences",
    "tables",
    "partitions",
    "sequence_ownership",
    "data",
    "identity_columns",
    "sequence_state",
    "constraints",
    "indexes",
    "functions",
    "views",
    "triggers",
    "rls",
    "policies",
    "comments",
)

#: Constraint application order: referenced uniqueness must exist before a
#: foreign key can be added.
_CONSTRAINT_ORDER: dict[str, int] = {"p": 0, "u": 1, "x": 2, "c": 3, "f": 4}


def quote_ident(identifier: Any) -> str:
    """Quote one identifier for executable SQL (doubling embedded quotes).

    Identifiers reaching this function originate from the **server** (a catalog
    read), never from a request: the exporter stores server-produced names, so
    quoting them can only ever reproduce the original object name.
    """
    return '"' + str(identifier).replace('"', '""') + '"'


def qualify(schema: Any, name: Any) -> str:
    return f"{quote_ident(schema)}.{quote_ident(name)}"


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RestoreMembers:
    """The decrypted, integrity-verified members of one artifact."""

    manifest: dict[str, Any]
    catalog: dict[str, Any]
    sequences: list[dict[str, Any]]
    data: dict[str, bytes]

    @property
    def schemas(self) -> list[str]:
        return [str(name) for name in (self.catalog.get("schemas") or [])]

    def inventory(self) -> list[dict[str, Any]]:
        return list((self.manifest.get("inventory") or {}).get("tables") or [])

    @property
    def tables(self) -> list[dict[str, Any]]:
        return list(self.catalog.get("tables") or [])


def read_members_from_envelope(
    envelope: bytes, key: bytes, *, compression: str = "gzip"
) -> RestoreMembers:
    """Decrypt, decompress and integrity-verify an artifact envelope.

    The three independent checks are all performed **before** any statement is
    executed against a target:

    1. authenticated decryption of the stored bytes (AES-256-GCM tag);
    2. structure — the manifest, catalog and sequences members must be present
       and parseable, and the format must be one this engine supports;
    3. content checksums — ``integrity/checksums.sha256`` must match every member,
       so a tampered *plaintext* archive is refused even if it was re-encrypted.
    """
    if not isinstance(envelope, (bytes, bytearray)):
        raise BackupArtifactError("artifact envelope must be bytes")
    archive = crypto.decrypt(bytes(envelope), key)
    members = read_archive(archive, compression=compression)
    verify_content_checksums(members)

    manifest_raw = members.get(ARCHIVE_MEMBER_MANIFEST)
    catalog_raw = members.get(ARCHIVE_MEMBER_CATALOG)
    sequences_raw = members.get(ARCHIVE_MEMBER_SEQUENCES)
    if manifest_raw is None or catalog_raw is None:
        raise BackupArtifactError("artifact is missing its manifest or catalog member")
    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
        catalog = json.loads(catalog_raw.decode("utf-8"))
        sequences = json.loads(sequences_raw.decode("utf-8")) if sequences_raw else []
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BackupArtifactError("artifact members are not valid JSON") from exc

    fmt = manifest.get("backup_format") or {}
    if fmt.get("name") != BACKUP_FORMAT_NAME:
        raise BackupArtifactError(
            "artifact is not a CarbonTally logical backup",
            details={"format": fmt.get("name")},
        )
    if fmt.get("version") != BACKUP_FORMAT_VERSION:
        raise BackupArtifactError(
            "unsupported backup format version", details={"version": fmt.get("version")}
        )

    if not isinstance(manifest, dict) or not isinstance(catalog, dict):
        raise BackupArtifactError("artifact members are not JSON objects")
    if not isinstance(sequences, list):
        raise BackupArtifactError("artifact sequence member is not a list")

    data = {
        path: payload for path, payload in members.items() if path.startswith("data/")
    }
    return RestoreMembers(
        manifest=manifest, catalog=catalog, sequences=sequences, data=data
    )


# ---------------------------------------------------------------------------
# Statement rendering (pure — unit-testable without a database)
# ---------------------------------------------------------------------------


def _columns_by_table(
    catalog: dict[str, Any],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for column in catalog.get("columns") or []:
        key = (str(column["schema"]), str(column["table_name"]))
        grouped.setdefault(key, []).append(column)
    for columns in grouped.values():
        columns.sort(key=lambda item: int(item.get("ordinal") or 0))
    return grouped


def _identity_targets(catalog: dict[str, Any]) -> set[str]:
    """Return ``schema.table.column`` paths carried by an identity column."""
    found: set[str] = set()
    for column in catalog.get("columns") or []:
        if column.get("identity_kind"):
            found.add(f"{column['schema']}.{column['table_name']}.{column['column_name']}")
    return found


def _sequence_name_map(
    sequences: Sequence[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Map ``owned_by`` (schema.table.column) to that sequence's catalog record."""
    mapped: dict[str, dict[str, Any]] = {}
    for sequence in sequences:
        owned_by = sequence.get("owned_by")
        if owned_by:
            mapped[str(owned_by)] = sequence
    return mapped


def render_restore_statements(
    catalog: dict[str, Any],
    sequences: Sequence[dict[str, Any]] = (),
    *,
    include_extensions: bool = True,
    include_comments: bool = True,
) -> list[tuple[str, str]]:
    """Render ``(phase, statement)`` pairs from the structured catalog.

    Pure function — no database, no I/O — so the whole reconstruction plan can be
    unit-tested (and inspected) without a target.
    """
    statements: list[tuple[str, str]] = []
    schemas = [str(name) for name in (catalog.get("schemas") or [])]

    if include_extensions:
        for extension in catalog.get("extensions") or []:
            name = quote_ident(extension["name"])
            statements.append(("extensions", f"CREATE EXTENSION IF NOT EXISTS {name}"))

    for schema in schemas:
        statements.append(("schemas", f"CREATE SCHEMA IF NOT EXISTS {quote_ident(schema)}"))

    identity_paths = _identity_targets(catalog)
    sequence_by_owner = _sequence_name_map(sequences)
    identity_sequence_names = {
        str(sequence["qualified_name"])
        for owner, sequence in sequence_by_owner.items()
        if owner in identity_paths
    }

    # Standalone sequences first: a column DEFAULT may call nextval() during load.
    for sequence in sequences:
        qualified = str(sequence["qualified_name"])
        if qualified in identity_sequence_names:
            continue
        statements.append(("sequences", _create_sequence(sequence)))

    partition_keys: dict[str, str] = {}
    leaves: dict[str, list[dict[str, Any]]] = {}
    for partition in catalog.get("partitions") or []:
        parent = str(partition["parent_qualified_name"])
        partition_keys[parent] = str(partition.get("partition_key") or "")
        leaves.setdefault(parent, []).append(partition)

    columns_by_table = _columns_by_table(catalog)
    for table in catalog.get("tables") or []:
        qualified = str(table["qualified_name"])
        key = (str(table["schema"]), str(table["name"]))
        rendered = _render_columns(columns_by_table.get(key, []))
        if not rendered:
            continue
        keyword = "UNLOGGED TABLE" if table.get("persistence") == "u" else "TABLE"
        statement = f"CREATE {keyword} IF NOT EXISTS {qualified} (\n"
        statement += ",\n".join(rendered) + "\n)"
        if table.get("is_partitioned") and partition_keys.get(qualified):
            statement += f" PARTITION BY {partition_keys[qualified]}"
        statements.append(("tables", statement))

    for parent, children in leaves.items():
        for child in children:
            statements.append(
                (
                    "partitions",
                    f"CREATE TABLE IF NOT EXISTS {child['partition_qualified_name']} "
                    f"PARTITION OF {parent} {child['partition_bound']}",
                )
            )

    for sequence in sequences:
        qualified = str(sequence["qualified_name"])
        if qualified in identity_sequence_names:
            continue
        owned_by = sequence.get("owned_by")
        if owned_by:
            statements.append(
                ("sequence_ownership", f"ALTER SEQUENCE {qualified} OWNED BY {owned_by}")
            )

    constraints = sorted(
        catalog.get("constraints") or [],
        key=lambda item: (
            str(item["schema"]),
            str(item["table_name"]),
            _CONSTRAINT_ORDER.get(str(item.get("constraint_type")), 9),
            str(item["constraint_name"]),
        ),
    )
    constraint_names: dict[tuple[str, str], set[str]] = {}
    for constraint in constraints:
        table_key = (str(constraint["schema"]), str(constraint["table_name"]))
        constraint_names.setdefault(table_key, set()).add(
            str(constraint["constraint_name"])
        )
        statements.append(
            (
                "constraints",
                f"ALTER TABLE {qualify(constraint['schema'], constraint['table_name'])} "
                f"ADD CONSTRAINT {quote_ident(constraint['constraint_name'])} "
                f"{constraint['definition']}",
            )
        )

    for index in catalog.get("indexes") or []:
        if index.get("is_primary"):
            continue
        table_key = (str(index["schema"]), str(index["table_name"]))
        if str(index["index_name"]) in constraint_names.get(table_key, set()):
            # Backs a PK/UNIQUE constraint that was already added — recreating it
            # would collide with the constraint's own index.
            continue
        statements.append(("indexes", str(index["definition"])))

    for function in catalog.get("functions") or []:
        statements.append(("functions", str(function["definition"])))

    for view in catalog.get("views") or []:
        keyword = "MATERIALIZED VIEW" if view.get("relkind") == "m" else "VIEW"
        statements.append(
            (
                "views",
                f"CREATE OR REPLACE {keyword} "
                f"{qualify(view['schema'], view['name'])} AS\n{view['definition']}",
            )
        )

    for trigger in catalog.get("triggers") or []:
        statements.append(("triggers", str(trigger["definition"])))

    for table in catalog.get("tables") or []:
        qualified = str(table["qualified_name"])
        if table.get("rls_enabled"):
            statements.append(("rls", f"ALTER TABLE {qualified} ENABLE ROW LEVEL SECURITY"))
        if table.get("rls_forced"):
            statements.append(("rls", f"ALTER TABLE {qualified} FORCE ROW LEVEL SECURITY"))

    for policy in catalog.get("policies") or []:
        roles = policy.get("roles")
        rendered_roles = (
            ", ".join(str(role) for role in roles)
            if isinstance(roles, (list, tuple))
            else str(roles)
        )
        statement = (
            f"CREATE POLICY {quote_ident(policy['policy_name'])} ON "
            f"{qualify(policy['schema'], policy['table_name'])} "
            f"AS {policy['permissive']} FOR {policy['command']} TO {rendered_roles}"
        )
        if policy.get("using_expression"):
            statement += f" USING ({policy['using_expression']})"
        if policy.get("with_check_expression"):
            statement += f" WITH CHECK ({policy['with_check_expression']})"
        statements.append(("policies", statement))

    if include_comments:
        for table in catalog.get("tables") or []:
            qualified = str(table["qualified_name"])
            if table.get("comment"):
                statements.append(
                    (
                        "comments",
                        f"COMMENT ON TABLE {qualified} IS "
                        f"{_sql_literal(str(table['comment']))}",
                    )
                )
        for column in catalog.get("columns") or []:
            if column.get("comment"):
                statements.append(
                    (
                        "comments",
                        f"COMMENT ON COLUMN "
                        f"{qualify(column['schema'], column['table_name'])}."
                        f"{quote_ident(column['column_name'])} IS "
                        f"{_sql_literal(str(column['comment']))}",
                    )
                )

    return statements


def render_data_statements(
    catalog: dict[str, Any], sequences: Sequence[dict[str, Any]] = ()
) -> list[tuple[str, str]]:
    """The two post-load steps that cannot be part of the DDL plan.

    * ``identity_columns`` — ``ALTER TABLE … ADD GENERATED … AS IDENTITY`` for
      every identity column (deferred so ``COPY`` can write the values);
    * they are emitted after the data load, and ``setval`` follows in
      :func:`render_sequence_state_statements`.
    """
    statements: list[tuple[str, str]] = []
    sequence_by_owner = _sequence_name_map(sequences)
    for column in catalog.get("columns") or []:
        identity_kind = column.get("identity_kind")
        if not identity_kind:
            continue
        path = f"{column['schema']}.{column['table_name']}.{column['column_name']}"
        sequence = sequence_by_owner.get(path)
        clause = ""
        if sequence is not None:
            cycle = "CYCLE" if sequence.get("is_cycled") else "NO CYCLE"
            clause = (
                " (SEQUENCE NAME "
                f"{sequence['qualified_name']}"
                f" START WITH {int(sequence['start_value'])}"
                f" INCREMENT BY {int(sequence['increment_by'])}"
                f" MINVALUE {int(sequence['min_value'])}"
                f" MAXVALUE {int(sequence['max_value'])}"
                f" CACHE {int(sequence['cache_size'])} {cycle})"
            )
        statements.append(
            (
                "identity_columns",
                f"ALTER TABLE {qualify(column['schema'], column['table_name'])} "
                f"ALTER COLUMN {quote_ident(column['column_name'])} "
                f"ADD GENERATED {identity_kind} AS IDENTITY{clause}",
            )
        )
    return statements


def render_sequence_state_statements(
    sequences: Sequence[dict[str, Any]],
) -> list[tuple[str, str]]:
    """``setval`` for every sequence whose state was captured (OID-2)."""
    statements: list[tuple[str, str]] = []
    for sequence in sequences:
        if sequence.get("last_value") is None:
            continue
        is_called = "true" if sequence.get("is_called") else "false"
        literal = "'" + str(sequence["qualified_name"]).replace("'", "''") + "'"
        statements.append(
            (
                "sequence_state",
                f"SELECT setval({literal}, {int(sequence['last_value'])}, {is_called})",
            )
        )
    return statements


def render_roles_statements(catalog: dict[str, Any]) -> list[tuple[str, str]]:
    """Role **definitions** without passwords (§15 / Q7) — never executed here.

    A disposable target carries its own roles, and creating login roles with
    unknown passwords in a recovery environment is a privilege change nobody
    asked for. The statements are rendered so an operator can review exactly what
    a roles-level rebuild would create (``NOLOGIN`` only — Superuser/BYPASSRLS
    attributes are deliberately not re-granted).
    """
    return [
        ("roles", f"CREATE ROLE {quote_ident(role['name'])} NOLOGIN")
        for role in catalog.get("roles") or []
    ]


def _create_sequence(sequence: dict[str, Any]) -> str:
    cycle = "CYCLE" if sequence.get("is_cycled") else "NO CYCLE"
    return (
        f"CREATE SEQUENCE IF NOT EXISTS {sequence['qualified_name']} "
        f"INCREMENT BY {int(sequence['increment_by'])} "
        f"MINVALUE {int(sequence['min_value'])} "
        f"MAXVALUE {int(sequence['max_value'])} "
        f"START WITH {int(sequence['start_value'])} "
        f"CACHE {int(sequence['cache_size'])} {cycle}"
    )


def _render_columns(columns: Iterable[dict[str, Any]]) -> list[str]:
    """Render column definitions, **deferring** identity to the post-data phase."""
    rendered: list[str] = []
    for column in columns:
        piece = f"    {quote_ident(column['column_name'])} {column['data_type']}"
        if column.get("collation"):
            piece += f" COLLATE {column['collation']}"
        if column.get("identity_kind"):
            # Deferred: the value is loaded first (see the module docstring).
            piece += " NOT NULL"
        elif column.get("generated_kind"):
            piece += (
                f" GENERATED ALWAYS AS ({column.get('generation_expression')}) "
                f"{column['generated_kind']}"
            )
        else:
            if column.get("default_expression"):
                piece += f" DEFAULT {column['default_expression']}"
            if column.get("not_null"):
                piece += " NOT NULL"
        rendered.append(piece)
    return rendered


def _sql_literal(text: str) -> str:
    return "'" + str(text).replace("'", "''") + "'"


def copy_column_names(columns: Sequence[dict[str, Any]]) -> list[str]:
    """Columns a ``COPY`` load may write (generated columns are excluded)."""
    return [
        str(column["column_name"])
        for column in columns
        if not column.get("generated_kind")
    ]


def restore_plan(
    catalog: dict[str, Any],
    sequences: Sequence[dict[str, Any]] = (),
    *,
    include_extensions: bool = True,
    include_comments: bool = True,
) -> str:
    """Render the whole reconstruction as a reviewable, executable SQL script.

    Deterministic and side-effect free: the drill and the operator runbook use the
    same function that executes, so what an operator reads is what runs.
    """
    statements = render_restore_statements(
        catalog,
        sequences,
        include_extensions=include_extensions,
        include_comments=include_comments,
    )
    statements += render_data_statements(catalog, sequences)
    statements += render_sequence_state_statements(sequences)
    return "\n\n".join(f"{statement};" for _phase, statement in statements) + "\n"


# ---------------------------------------------------------------------------
# Target guard
# ---------------------------------------------------------------------------

#: Names that are never a valid restore target, whatever a caller believes: a
#: restore overwrites what it finds, so pointing it at a persistent environment is
#: the destructive mistake §13 exists to prevent.
_FORBIDDEN_TARGET_TOKENS: tuple[str, ...] = (
    "qa",
    "demo",
    "investor",
    "prod",
    "production",
    "live",
)

#: A target whose name is explicitly disposable even though it is not ``ct_*``.
_ALLOWED_TARGET_MAINS: tuple[str, ...] = ("carbontally_test",)


def assert_disposable_target(name: str, role: str) -> str:
    """Refuse any restore target that could hold data worth keeping (fail closed).

    A disposable target is ``ct_*`` or one of :data:`_ALLOWED_TARGET_MAINS`, and
    must not contain a persistent-environment token (``qa``/``demo``/``investor``/
    ``prod``/``production``/``live``). The check is deliberately in the **library**
    as well as in the operator tools: a future caller cannot forget it.
    """
    lowered = str(name).lower()
    if lowered in _ALLOWED_TARGET_MAINS:
        return name
    if not lowered.startswith("ct_"):
        raise BackupRestoreTargetError(
            f"refusing to use {role} database {name!r}: a restore target must be "
            f"disposable (a name starting 'ct_' or one of {_ALLOWED_TARGET_MAINS})",
            details={"database": name, "role": role},
        )
    for token in _FORBIDDEN_TARGET_TOKENS:
        if token in lowered:
            raise BackupRestoreTargetError(
                f"refusing to use {role} database {name!r}: it looks like a "
                f"persistent environment ({token!r})",
                details={"database": name, "role": role},
            )
    return name


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

#: The order statements are actually applied. Data sits between the DDL that must
#: exist first and the objects that must be installed afterwards (constraints,
#: functions, views, triggers, RLS) — the ``pg_dump`` ordering.
_EXECUTION_ORDER: tuple[str, ...] = (
    "extensions",
    "schemas",
    "sequences",
    "tables",
    "partitions",
    "sequence_ownership",
    "data",
    "identity_columns",
    "sequence_state",
    "constraints",
    "indexes",
    "functions",
    "views",
    "triggers",
    "rls",
    "policies",
    "comments",
)


@dataclass
class RestoreResult:
    """What a restore actually did (evidence, not a claim)."""

    target_database: Optional[str] = None
    database_identity: dict[str, Any] = field(default_factory=dict)
    backup_id: Optional[str] = None
    phases: dict[str, int] = field(default_factory=dict)
    rows_loaded: int = 0
    tables_loaded: int = 0
    statements_applied: int = 0
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "target_database": self.target_database,
            "backup_id": self.backup_id,
            "database_identity": self.database_identity,
            "phases": dict(self.phases),
            "statements_applied": self.statements_applied,
            "tables_loaded": self.tables_loaded,
            "rows_loaded": self.rows_loaded,
            "warnings": list(self.warnings),
        }


def build_execution_plan(
    catalog: dict[str, Any],
    sequences: Sequence[dict[str, Any]] = (),
    *,
    include_extensions: bool = True,
    include_comments: bool = True,
) -> list[tuple[str, str]]:
    """``(phase, statement)`` pairs in the order they will be applied."""
    ddl = render_restore_statements(
        catalog,
        sequences,
        include_extensions=include_extensions,
        include_comments=include_comments,
    )
    ddl += render_data_statements(catalog, sequences)
    ddl += render_sequence_state_statements(sequences)
    rank = {phase: index for index, phase in enumerate(_EXECUTION_ORDER)}
    return sorted(ddl, key=lambda item: rank.get(item[0], len(rank)))


async def restore_members(
    connection: Any,
    members: RestoreMembers,
    *,
    target_database: Optional[str] = None,
    include_extensions: bool = True,
    include_comments: bool = True,
    skip_data: bool = False,
    statement_hook: Optional[Any] = None,
) -> RestoreResult:
    """Apply one artifact's members to ``connection``'s database.

    Every statement is executed against the supplied ``asyncpg`` connection; the
    caller owns the transaction policy and the target's lifecycle. A failure raises
    :class:`~backup.errors.BackupRestoreError` naming the **phase** and the failing
    statement — a partial restore is never reported as a success.

    ``skip_data`` exists for schema-only rehearsals (and for tests that only want
    to prove the DDL plan is executable).

    The target guard (:func:`assert_disposable_target`) is applied on this
    execution path itself, before any statement runs: restoring over a database
    whose data matters is the destructive mistake the safety rules exist to
    prevent, so a caller must not be able to bypass the check by forgetting it.
    When the caller does not name the target, the server's own
    ``current_database()`` is used — a value no caller can influence.
    """
    catalog = members.catalog
    resolved_target = target_database or await connection.fetchval(
        "SELECT current_database()"
    )
    assert_disposable_target(str(resolved_target), "restore target")
    result = RestoreResult(
        target_database=str(resolved_target),
        database_identity=dict(catalog.get("identity") or {}),
        backup_id=members.manifest.get("backup_id"),
    )
    columns_by_table = _columns_by_table(catalog)
    plan = build_execution_plan(
        catalog,
        members.sequences,
        include_extensions=include_extensions,
        include_comments=include_comments,
    )

    for phase, statement in plan:
        if skip_data and phase == "data":
            continue
        if statement_hook is not None:
            statement_hook(phase, statement)
        try:
            await connection.execute(statement)
            result.phases[phase] = result.phases.get(phase, 0) + 1
            result.statements_applied += 1
        except Exception as exc:  # noqa: BLE001 — normalised into a typed error
            if phase == "extensions":
                # A target may legitimately lack an extension; it is metadata in
                # the artifact (the architecture excludes extension internals).
                message = f"extension unavailable in target: {statement}"
                result.warnings.append(message)
                logger.warning("restore: %s", message)
                continue
            raise BackupRestoreError(
                f"restore failed in phase {phase!r}",
                details={
                    "phase": phase,
                    "statement": statement[:500],
                    "reason": f"{type(exc).__name__}: {str(exc).splitlines()[0][:200]}",
                },
            ) from exc

    if not skip_data:
        for entry in members.inventory():
            schema = str(entry["schema"])
            table = str(entry["name"])
            member_path = str(entry.get("data_member") or "")
            payload = members.data.get(member_path)
            if payload is None:
                raise BackupRestoreError(
                    "artifact is missing a data member listed in its manifest",
                    details={"member": member_path, "table": f"{schema}.{table}"},
                )
            columns = copy_column_names(columns_by_table.get((schema, table), []))
            if not columns:
                raise BackupRestoreError(
                    "table has no loadable columns (every column is generated)",
                    details={"table": f"{schema}.{table}"},
                )
            try:
                await connection.copy_to_table(
                    table,
                    schema_name=schema,
                    columns=columns,
                    source=io.BytesIO(payload),
                )
            except Exception as exc:  # noqa: BLE001 — normalised
                raise BackupRestoreError(
                    f"data load failed for {schema}.{table}",
                    details={
                        "phase": "data",
                        "table": f"{schema}.{table}",
                        "reason": f"{type(exc).__name__}: {str(exc).splitlines()[0][:200]}",
                    },
                ) from exc
            result.phases["data"] = result.phases.get("data", 0) + 1
            result.tables_loaded += 1
            result.rows_loaded += int(entry.get("row_count") or 0)

    return result


async def restore_artifact(
    connection: Any,
    envelope: bytes,
    key: bytes,
    *,
    compression: str = "gzip",
    target_database: Optional[str] = None,
    verify: bool = True,
    **kwargs: Any,
) -> tuple[RestoreResult, dict[str, Any]]:
    """Decrypt-and-restore one artifact, then (by default) verify the target.

    Returns ``(result, verification)``. The verification is the *post-restore*
    integrity evidence §10 requires (schema, indexes, constraints, RLS, policies,
    triggers, functions, data and sequence state) — computed from the same catalog
    the restore was built from, so it is a real comparison, not a restatement.
    """
    members = read_members_from_envelope(envelope, key, compression=compression)
    result = await restore_members(
        connection, members, target_database=target_database, **kwargs
    )
    verification: dict[str, Any] = {}
    if verify:
        expected_counts = {
            f"{entry['schema']}.{entry['name']}": int(entry.get("row_count") or 0)
            for entry in members.inventory()
        }
        verification = await verify_restored(
            connection,
            members.catalog,
            expected_row_counts=expected_counts,
            sequences=members.sequences,
        )
    return result, verification


# ---------------------------------------------------------------------------
# Post-restore verification (§10 "verify the restored integrity")
# ---------------------------------------------------------------------------


async def _names(connection: Any, query: str, *args: Any) -> set[str]:
    rows = await connection.fetch(query, *args)
    return {str(row["name"]) for row in rows}


async def verify_restored(
    connection: Any,
    catalog: dict[str, Any],
    *,
    expected_row_counts: Optional[dict[str, int]] = None,
    sequences: Sequence[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Compare a restored database against the artifact's own catalog.

    Returns a structured, honest report — every collection is a real set
    difference, so a *missing* object is visible rather than inferred. ``ok`` is
    true only when no expected object, row count or sequence state differs.

    Read-only: nothing is created, altered or dropped.
    """
    schemas = [str(name) for name in (catalog.get("schemas") or [])]
    report: dict[str, Any] = {
        "schemas": schemas,
        "missing_schemas": [],
        "missing_tables": [],
        "extra_tables": [],
        "missing_indexes": [],
        "extra_indexes": [],
        "missing_constraints": [],
        "extra_constraints": [],
        "missing_policies": [],
        "extra_policies": [],
        "missing_triggers": [],
        "extra_triggers": [],
        "missing_functions": [],
        "rls_missing": [],
        "row_count_mismatches": [],
        "sequence_state_mismatches": [],
        "row_counts": {},
    }
    if not schemas:
        report["ok"] = True
        return report

    present_schemas = await _names(
        connection,
        "SELECT nspname AS name FROM pg_namespace WHERE nspname = ANY($1::text[])",
        schemas,
    )
    report["missing_schemas"] = sorted(set(schemas) - present_schemas)

    expected_tables = {
        f"{table['schema']}.{table['name']}" for table in catalog.get("tables") or []
    }
    actual_tables = await _names(
        connection,
        """
        SELECT n.nspname || '.' || c.relname AS name
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = ANY($1::text[])
          AND c.relkind IN ('r', 'p') AND NOT c.relispartition
          AND c.relpersistence <> 't'
        """,
        schemas,
    )
    # Partition leaves are created by the restore but are not catalog "tables".
    expected_leaves = {
        f"{partition['partition_schema']}.{partition['partition_name']}"
        for partition in catalog.get("partitions") or []
    }
    actual_tables -= expected_leaves
    report["missing_tables"] = sorted(expected_tables - actual_tables)
    report["extra_tables"] = sorted(actual_tables - expected_tables)

    expected_indexes = {
        f"{index['schema']}.{index['index_name']}"
        for index in catalog.get("indexes") or []
        if not index.get("is_primary")
    }
    # A PRIMARY KEY/UNIQUE constraint owns its index and the catalog lists that
    # index too; excluding them on both sides keeps the comparison symmetric.
    expected_indexes -= {
        f"{constraint['schema']}.{constraint['constraint_name']}"
        for constraint in catalog.get("constraints") or []
    }
    actual_indexes = await _names(
        connection,
        """
        SELECT n.nspname || '.' || i.relname AS name
        FROM pg_index ix
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_class t ON t.oid = ix.indrelid
        JOIN pg_namespace n ON n.oid = i.relnamespace
        LEFT JOIN pg_constraint con ON con.conindid = ix.indexrelid
        WHERE n.nspname = ANY($1::text[])
          AND NOT ix.indisprimary
          AND con.oid IS NULL
        """,
        schemas,
    )
    report["missing_indexes"] = sorted(expected_indexes - actual_indexes)
    report["extra_indexes"] = sorted(actual_indexes - expected_indexes)

    expected_constraints = {
        f"{constraint['schema']}.{constraint['table_name']}.{constraint['constraint_name']}"
        for constraint in catalog.get("constraints") or []
    }
    actual_constraints = await _names(
        connection,
        """
        SELECT n.nspname || '.' || c.relname || '.' || con.conname AS name
        FROM pg_constraint con
        JOIN pg_class c ON c.oid = con.conrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = ANY($1::text[])
          AND con.contype IN ('p', 'f', 'u', 'c', 'x')
        """,
        schemas,
    )
    report["missing_constraints"] = sorted(expected_constraints - actual_constraints)
    report["extra_constraints"] = sorted(actual_constraints - expected_constraints)

    expected_policies = {
        f"{policy['schema']}.{policy['table_name']}.{policy['policy_name']}"
        for policy in catalog.get("policies") or []
    }
    actual_policies = await _names(
        connection,
        """
        SELECT schemaname || '.' || tablename || '.' || policyname AS name
        FROM pg_policies WHERE schemaname = ANY($1::text[])
        """,
        schemas,
    )
    report["missing_policies"] = sorted(expected_policies - actual_policies)
    report["extra_policies"] = sorted(actual_policies - expected_policies)

    expected_triggers = {
        f"{trigger['schema']}.{trigger['table_name']}.{trigger['trigger_name']}"
        for trigger in catalog.get("triggers") or []
    }
    actual_triggers = await _names(
        connection,
        """
        SELECT n.nspname || '.' || c.relname || '.' || t.tgname AS name
        FROM pg_trigger t
        JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = ANY($1::text[]) AND NOT t.tgisinternal
        """,
        schemas,
    )
    report["missing_triggers"] = sorted(expected_triggers - actual_triggers)
    report["extra_triggers"] = sorted(actual_triggers - expected_triggers)

    expected_functions = {
        f"{function['schema']}.{function['name']}({function.get('arguments') or ''})"
        for function in catalog.get("functions") or []
    }
    actual_functions = await _names(
        connection,
        """
        SELECT n.nspname || '.' || p.proname || '(' ||
               pg_get_function_identity_arguments(p.oid) || ')' AS name
        FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = ANY($1::text[])
        """,
        schemas,
    )
    report["missing_functions"] = sorted(expected_functions - actual_functions)

    expected_rls = {
        f"{table['schema']}.{table['name']}"
        for table in catalog.get("tables") or []
        if table.get("rls_enabled")
    }
    if expected_rls:
        actual_rls = await _names(
            connection,
            """
            SELECT n.nspname || '.' || c.relname AS name
            FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = ANY($1::text[]) AND c.relrowsecurity
            """,
            schemas,
        )
        report["rls_missing"] = sorted(expected_rls - actual_rls)

    if expected_row_counts:
        for qualified, expected in sorted(expected_row_counts.items()):
            schema, _, table = qualified.partition(".")
            actual = await connection.fetchval(
                f"SELECT count(*) FROM {qualify(schema, table)}"
            )
            report["row_counts"][qualified] = {
                "expected": int(expected),
                "actual": int(actual),
            }
            if int(actual) != int(expected):
                report["row_count_mismatches"].append(qualified)

    for sequence in sequences:
        if sequence.get("last_value") is None:
            continue
        qualified = str(sequence["qualified_name"])
        row = await connection.fetchrow(f"SELECT last_value, is_called FROM {qualified}")
        if row is None or int(row["last_value"]) != int(sequence["last_value"]) or bool(
            row["is_called"]
        ) != bool(sequence.get("is_called")):
            report["sequence_state_mismatches"].append(qualified)

    report["ok"] = not any(
        report[key]
        for key in (
            "missing_schemas",
            "missing_tables",
            "extra_tables",
            "missing_indexes",
            "extra_indexes",
            "missing_constraints",
            "extra_constraints",
            "missing_policies",
            "extra_policies",
            "missing_triggers",
            "extra_triggers",
            "missing_functions",
            "rls_missing",
            "row_count_mismatches",
            "sequence_state_mismatches",
        )
    )
    return report


__all__ = [
    "RESTORE_PHASES",
    "RestoreMembers",
    "RestoreResult",
    "assert_disposable_target",
    "build_execution_plan",
    "copy_column_names",
    "qualify",
    "quote_ident",
    "read_members_from_envelope",
    "render_data_statements",
    "render_restore_statements",
    "render_roles_statements",
    "render_sequence_state_statements",
    "restore_artifact",
    "restore_members",
    "restore_plan",
    "verify_restored",
]
