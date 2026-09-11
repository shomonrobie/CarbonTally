"""PostgreSQL catalog introspection for the logical exporter (OID-1).

Every query here is **read-only** and issued through ``asyncpg`` parameterised
SQL. Identifiers are never hand-quoted: the server itself produces fully quoted,
schema-qualified names with ``format('%I.%I', …)``, and those server-produced
strings are the only identifiers interpolated into later statements. That removes
the classic quote/escape/case hazards of hand-built SQL.

Covered: schemas, tables (with UNLOGGED persistence and comments), columns (type,
nullability, default, **identity**, **generated** storage, non-default
**collation**, comments), primary keys, foreign keys, unique/check/exclusion
constraints, indexes, sequences plus their **current state** (OID-2) and
**ownership** (F7), functions, triggers, RLS enablement and policies,
views/materialised views, extensions, safe role metadata, and **partition metadata**
(F8: key definition, leaf relationship, bounds).

Export policy: partition **parents** (`relkind='p'`) are exported and their
partition **leaves** are not (F1), because a parent's COPY already returns every
partition row — this keeps data exported exactly once and row counts exact.
Session-temporary objects are never captured (F6).

Not covered (recorded in the manifest `limitations` and the Phase-1 implementation
document): table/column ACLs are not dumped, extension internals are not dumped,
comments on objects other than tables and columns (for example constraints or
indexes) are not dumped, and role **passwords** are never read.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from backup.errors import BackupExportError

#: ``relkind`` values treated as exportable base tables. Partition **parents**
#: (``p``) are exported and partition **leaves** are not (F1): a parent's COPY
#: already returns every partition row, so exporting leaves as well would
#: duplicate data and double-count rows.
_TABLE_KINDS = ("r", "p")

#: Applied to every table-scoped query so the exported table set, its columns, its
#: constraints and its indexes always agree:
#:   * ``relkind = ANY($2::text[])`` — only base tables and partition parents;
#:   * ``NOT relispartition`` — exclude partition leaves (F1);
#:   * ``relpersistence <> 't'`` — never capture session-temporary objects (F6).
def _exportable_table_filter(alias: str) -> str:
    """Return the shared exportable-table predicate for a ``pg_class`` alias.

    ``alias`` is always a hard-coded literal (``c``/``t``) chosen by this module —
    never caller input — so interpolating it is safe.
    """
    return (
        f"  AND {alias}.relkind = ANY($2::text[])\n"
        f"  AND NOT {alias}.relispartition\n"
        f"  AND {alias}.relpersistence <> 't'\n"
    )

_SCHEMAS_SQL = """
SELECT n.nspname AS schema
FROM pg_catalog.pg_namespace n
WHERE n.nspname = ANY($1::text[])
ORDER BY n.nspname
"""

_TABLES_SQL = """
SELECT n.nspname                              AS schema,
       c.relname                              AS name,
       c.relkind                              AS relkind,
       (c.relkind = 'p')                      AS is_partitioned,
       c.relpersistence                       AS persistence,
       c.relrowsecurity                       AS rls_enabled,
       c.relforcerowsecurity                  AS rls_forced,
       pg_catalog.obj_description(c.oid, 'pg_class') AS comment,
       format('%I.%I', n.nspname, c.relname)  AS qualified_name
FROM pg_catalog.pg_class c
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = ANY($1::text[])
""" + _exportable_table_filter("c") + """ORDER BY n.nspname, c.relname
"""

_COLUMNS_SQL = """
SELECT n.nspname                                     AS schema,
       c.relname                                     AS table_name,
       a.attname                                     AS column_name,
       format_type(a.atttypid, a.atttypmod)          AS data_type,
       a.attnotnull                                  AS not_null,
       pg_catalog.pg_get_expr(ad.adbin, ad.adrelid)   AS default_expression,
       a.attidentity                                 AS identity_kind,
       a.attgenerated                                AS generated_kind,
       CASE WHEN a.attcollation <> 0
                 AND col.collname IS NOT NULL
                 AND col.collname <> 'default'
            THEN format('%I.%I', cn.nspname, col.collname)
       END                                           AS collation,
       pg_catalog.col_description(a.attrelid, a.attnum) AS comment,
       a.attnum                                      AS ordinal
FROM pg_catalog.pg_attribute a
JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_catalog.pg_attrdef ad ON ad.adrelid = a.attrelid AND ad.adnum = a.attnum
LEFT JOIN pg_catalog.pg_collation col ON col.oid = a.attcollation
LEFT JOIN pg_catalog.pg_namespace cn ON cn.oid = col.collnamespace
WHERE n.nspname = ANY($1::text[])
""" + _exportable_table_filter("c") + """  AND a.attnum > 0
  AND NOT a.attisdropped
ORDER BY n.nspname, c.relname, a.attnum
"""

_CONSTRAINTS_SQL = """
SELECT n.nspname                                       AS schema,
       c.relname                                       AS table_name,
       con.conname                                     AS constraint_name,
       con.contype                                     AS constraint_type,
       pg_catalog.pg_get_constraintdef(con.oid, true)  AS definition
FROM pg_catalog.pg_constraint con
JOIN pg_catalog.pg_class c ON c.oid = con.conrelid
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = ANY($1::text[])
""" + _exportable_table_filter("c") + """  AND con.contype IN ('p', 'f', 'u', 'c', 'x')
ORDER BY n.nspname, c.relname, con.conname
"""

_INDEXES_SQL = """
SELECT n.nspname                                    AS schema,
       t.relname                                    AS table_name,
       i.relname                                    AS index_name,
       ix.indisunique                               AS is_unique,
       ix.indisprimary                              AS is_primary,
       pg_catalog.pg_get_indexdef(ix.indexrelid)    AS definition
FROM pg_catalog.pg_index ix
JOIN pg_catalog.pg_class i ON i.oid = ix.indexrelid
JOIN pg_catalog.pg_class t ON t.oid = ix.indrelid
JOIN pg_catalog.pg_namespace n ON n.oid = i.relnamespace
WHERE n.nspname = ANY($1::text[])
""" + _exportable_table_filter("t") + """ORDER BY n.nspname, t.relname, i.relname
"""

_SEQUENCES_SQL = """
SELECT n.nspname                             AS schema,
       c.relname                             AS name,
       s.seqstart                            AS start_value,
       s.seqincrement                        AS increment_by,
       s.seqmin                              AS min_value,
       s.seqmax                              AS max_value,
       s.seqcache                            AS cache_size,
       s.seqcycle                            AS is_cycled,
       format('%I.%I', n.nspname, c.relname) AS qualified_name,
       (SELECT format('%I.%I.%I', tn.nspname, tc.relname, ta.attname)
          FROM pg_catalog.pg_depend d
          JOIN pg_catalog.pg_class tc ON tc.oid = d.refobjid
          JOIN pg_catalog.pg_namespace tn ON tn.oid = tc.relnamespace
          JOIN pg_catalog.pg_attribute ta
               ON ta.attrelid = d.refobjid AND ta.attnum = d.refobjsubid
         WHERE d.objid = c.oid
           AND d.classid = 'pg_class'::regclass
           AND d.refclassid = 'pg_class'::regclass
           AND d.deptype IN ('a', 'i')
         LIMIT 1)                            AS owned_by
FROM pg_catalog.pg_sequence s
JOIN pg_catalog.pg_class c ON c.oid = s.seqrelid
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = ANY($1::text[])
ORDER BY n.nspname, c.relname
"""

#: Partition metadata (F8): the key definition on the parent, plus every leaf's
#: identity and bound. Leaves are **not** exported as data (F1) — this section is
#: what makes the structured catalog authoritative about partitioning.
_PARTITIONS_SQL = """
SELECT pn.nspname                                        AS schema,
       pr.relname                                        AS parent_name,
       format('%I.%I', pn.nspname, pr.relname)            AS parent_qualified_name,
       pg_catalog.pg_get_partkeydef(pr.oid)               AS partition_key,
       cn.nspname                                         AS partition_schema,
       ch.relname                                         AS partition_name,
       format('%I.%I', cn.nspname, ch.relname)            AS partition_qualified_name,
       pg_catalog.pg_get_expr(ch.relpartbound, ch.oid)    AS partition_bound
FROM pg_catalog.pg_inherits i
JOIN pg_catalog.pg_class ch ON ch.oid = i.inhrelid
JOIN pg_catalog.pg_class pr ON pr.oid = i.inhparent
JOIN pg_catalog.pg_namespace cn ON cn.oid = ch.relnamespace
JOIN pg_catalog.pg_namespace pn ON pn.oid = pr.relnamespace
WHERE pr.relkind = 'p'
  AND pn.nspname = ANY($1::text[])
  AND ch.relpersistence <> 't'
ORDER BY pn.nspname, pr.relname, ch.relname
"""

_FUNCTIONS_SQL = """
SELECT n.nspname                                         AS schema,
       p.proname                                         AS name,
       pg_catalog.pg_get_function_identity_arguments(p.oid) AS arguments,
       p.prokind                                         AS kind,
       pg_catalog.pg_get_functiondef(p.oid)              AS definition
FROM pg_catalog.pg_proc p
JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = ANY($1::text[])
ORDER BY n.nspname, p.proname,
         pg_catalog.pg_get_function_identity_arguments(p.oid)
"""

_TRIGGERS_SQL = """
SELECT n.nspname                                    AS schema,
       c.relname                                    AS table_name,
       t.tgname                                     AS trigger_name,
       t.tgenabled                                  AS enabled,
       pg_catalog.pg_get_triggerdef(t.oid, true)    AS definition
FROM pg_catalog.pg_trigger t
JOIN pg_catalog.pg_class c ON c.oid = t.tgrelid
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = ANY($1::text[])
  AND NOT t.tgisinternal
ORDER BY n.nspname, c.relname, t.tgname
"""

_POLICIES_SQL = """
SELECT schemaname   AS schema,
       tablename    AS table_name,
       policyname   AS policy_name,
       permissive   AS permissive,
       roles        AS roles,
       cmd          AS command,
       qual         AS using_expression,
       with_check   AS with_check_expression
FROM pg_catalog.pg_policies
WHERE schemaname = ANY($1::text[])
ORDER BY schemaname, tablename, policyname
"""

_VIEWS_SQL = """
SELECT n.nspname                               AS schema,
       c.relname                               AS name,
       c.relkind                               AS relkind,
       pg_catalog.pg_get_viewdef(c.oid, true)  AS definition
FROM pg_catalog.pg_class c
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = ANY($1::text[])
  AND c.relkind IN ('v', 'm')
ORDER BY n.nspname, c.relname
"""

_EXTENSIONS_SQL = """
SELECT e.extname   AS name,
       e.extversion AS version,
       n.nspname   AS schema
FROM pg_catalog.pg_extension e
JOIN pg_catalog.pg_namespace n ON n.oid = e.extnamespace
ORDER BY e.extname
"""

#: Safe role metadata only — ``rolpassword`` is **never** selected.
_ROLES_SQL = """
SELECT r.rolname        AS name,
       r.rolcanlogin    AS can_login,
       r.rolsuper       AS is_superuser,
       r.rolcreaterole  AS can_create_role,
       r.rolcreatedb    AS can_create_db,
       r.rolbypassrls   AS bypasses_rls,
       r.rolconnlimit   AS connection_limit
FROM pg_catalog.pg_roles r
WHERE r.rolname NOT LIKE 'pg\\_%'
ORDER BY r.rolname
"""

_IDENTITY_SQL = """
SELECT current_database()                 AS database,
       current_setting('server_version')  AS server_version,
       current_setting('server_encoding') AS server_encoding
"""



@dataclass
class CatalogSnapshot:
    """Structured catalog extraction for the requested schemas."""

    identity: dict[str, Any] = field(default_factory=dict)
    schemas: list[str] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    columns: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[dict[str, Any]] = field(default_factory=list)
    indexes: list[dict[str, Any]] = field(default_factory=list)
    sequences: list[dict[str, Any]] = field(default_factory=list)
    functions: list[dict[str, Any]] = field(default_factory=list)
    triggers: list[dict[str, Any]] = field(default_factory=list)
    policies: list[dict[str, Any]] = field(default_factory=list)
    views: list[dict[str, Any]] = field(default_factory=list)
    extensions: list[dict[str, Any]] = field(default_factory=list)
    roles: list[dict[str, Any]] = field(default_factory=list)
    partitions: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "schemas": self.schemas,
            "tables": self.tables,
            "columns": self.columns,
            "constraints": self.constraints,
            "indexes": self.indexes,
            "sequences": self.sequences,
            "functions": self.functions,
            "triggers": self.triggers,
            "policies": self.policies,
            "views": self.views,
            "extensions": self.extensions,
            "roles": self.roles,
            "partitions": self.partitions,
        }

    def columns_for(self, schema: str, table: str) -> list[dict[str, Any]]:
        """Return the columns of one table in ordinal order."""
        return [
            column
            for column in self.columns
            if column["schema"] == schema and column["table_name"] == table
        ]

    def primary_key_columns(self, schema: str, table: str) -> list[str]:
        """Return the column names of the table's primary key (may be empty)."""
        for constraint in self.constraints:
            if (
                constraint["schema"] == schema
                and constraint["table_name"] == table
                and constraint["constraint_type"] == "p"
            ):
                definition = str(constraint["definition"])
                inner = definition[definition.find("(") + 1: definition.rfind(")")]
                return [part.strip().strip('"') for part in inner.split(",") if part.strip()]
        return []


    def to_ddl_lines(self) -> list[str]:
        """Render a best-effort, **informational** DDL script.

        Deliberately not claimed to be a restorable dump: the authoritative
        record is ``catalog.json`` (see the manifest limitations).
        """
        lines: list[str] = [
            "-- CarbonTally logical backup - best-effort DDL reconstruction",
            "-- INFORMATIONAL: the authoritative catalog record is catalog/catalog.json",
            "",
        ]
        for schema in self.schemas:
            lines.append(f"CREATE SCHEMA IF NOT EXISTS {_quote(schema)};")
        if self.schemas:
            lines.append("")
        for sequence in self.sequences:
            cycle = "CYCLE" if sequence["is_cycled"] else "NO CYCLE"
            lines.append(
                f"CREATE SEQUENCE IF NOT EXISTS {sequence['qualified_name']} "
                f"INCREMENT BY {sequence['increment_by']} MINVALUE {sequence['min_value']} "
                f"MAXVALUE {sequence['max_value']} START WITH {sequence['start_value']} "
                f"CACHE {sequence['cache_size']} {cycle};"
            )
            if sequence.get("owned_by"):
                lines.append(
                    f"ALTER SEQUENCE {sequence['qualified_name']} "
                    f"OWNED BY {sequence['owned_by']};"
                )
        if self.sequences:
            lines.append("")
        for table in self.tables:
            rendered: list[str] = []
            for column in self.columns_for(table["schema"], table["name"]):
                piece = f"    {_quote(column['column_name'])} {column['data_type']}"
                if column.get("collation"):
                    piece += f" COLLATE {column['collation']}"
                if column.get("identity_kind"):
                    piece += f" GENERATED {column['identity_kind']} AS IDENTITY"
                elif column.get("generated_kind"):
                    piece += (
                        f" GENERATED ALWAYS AS ({column.get('generation_expression')}) "
                        f"{column['generated_kind']}"
                    )
                elif column["default_expression"]:
                    piece += f" DEFAULT {column['default_expression']}"
                if column["not_null"] and not column.get("identity_kind"):
                    piece += " NOT NULL"
                rendered.append(piece)
            if not rendered:
                continue
            keyword = "UNLOGGED TABLE" if table.get("persistence") == "u" else "TABLE"
            lines.append(
                f"CREATE {keyword} IF NOT EXISTS {table['qualified_name']} (\n"
                + ",\n".join(rendered)
                + "\n);"
            )
            if table.get("comment"):
                lines.append(
                    f"COMMENT ON TABLE {table['qualified_name']} IS "
                    f"{_sql_literal(str(table['comment']))};"
                )
            for column in self.columns_for(table["schema"], table["name"]):
                if column.get("comment"):
                    lines.append(
                        f"COMMENT ON COLUMN {table['qualified_name']}."
                        f"{_quote(column['column_name'])} IS "
                        f"{_sql_literal(str(column['comment']))};"
                    )
        if self.tables:
            lines.append("")
        if self.partitions:
            lines.append(
                "-- Partition metadata (key definitions, leaf relationships and bounds) is"
            )
            lines.append("-- recorded authoritatively in catalog/catalog.json -> partitions.")
            for partition in self.partitions:
                lines.append(
                    f"-- partition: {partition['partition_qualified_name']} OF "
                    f"{partition['parent_qualified_name']} "
                    f"({partition['partition_key']}) {partition['partition_bound']}"
                )
            lines.append("")
        for constraint in self.constraints:
            lines.append(
                f"ALTER TABLE {_qualify(constraint['schema'], constraint['table_name'])} "
                f"ADD CONSTRAINT {_quote(constraint['constraint_name'])} "
                f"{constraint['definition']};"
            )
        if self.constraints:
            lines.append("")
        for index in self.indexes:
            if index["is_primary"]:
                continue
            lines.append(f"{index['definition']};")
        if self.indexes:
            lines.append("")
        for view in self.views:
            keyword = "MATERIALIZED VIEW" if view["relkind"] == "m" else "VIEW"
            lines.append(
                f"CREATE OR REPLACE {keyword} {_qualify(view['schema'], view['name'])} AS\n"
                f"{view['definition']}"
            )
        if self.views:
            lines.append("")
        for function in self.functions:
            lines.append(function["definition"])
            lines.append("")
        for trigger in self.triggers:
            lines.append(f"{trigger['definition']};")
        if self.triggers:
            lines.append("")
        for policy in self.policies:
            roles = policy["roles"]
            rendered_roles = ", ".join(roles) if isinstance(roles, list) else str(roles)
            statement = (
                f"CREATE POLICY {_quote(policy['policy_name'])} ON "
                f"{_qualify(policy['schema'], policy['table_name'])} "
                f"AS {policy['permissive']} FOR {policy['command']} TO {rendered_roles}"
            )
            if policy["using_expression"]:
                statement += f" USING ({policy['using_expression']})"
            if policy["with_check_expression"]:
                statement += f" WITH CHECK ({policy['with_check_expression']})"
            lines.append(statement + ";")
        return lines



def _quote(identifier: str) -> str:
    """Quote a single identifier (informational rendering only)."""
    return '"' + str(identifier).replace('"', '""') + '"'


def _sql_literal(text: str) -> str:
    """Render a string literal for the informational DDL script.

    Doubling ``'`` is sufficient under PostgreSQL's default
    ``standard_conforming_strings = on`` (backslashes are literal), which is the
    only mode this script is informational for.
    """
    return "'" + str(text).replace("'", "''") + "'"


def _qualify(schema: str, name: str) -> str:
    """Quote a schema-qualified identifier (informational rendering only)."""
    return f"{_quote(schema)}.{_quote(name)}"


#: Raw PostgreSQL ``attidentity`` / ``attgenerated`` codes mapped to explicit labels
#: (F3/F4). Anything else becomes ``None`` so a consumer never sees a bare flag byte.
_IDENTITY_LABELS = {"a": "ALWAYS", "d": "BY DEFAULT"}
_GENERATED_LABELS = {"s": "STORED"}


def _normalize_columns(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map raw catalog flags into explicit, unambiguous column metadata (F3–F5).

    * ``identity_kind`` — ``"ALWAYS"`` / ``"BY DEFAULT"`` / ``None``;
    * ``generated_kind`` — ``"STORED"`` / ``None``;
    * ``generation_expression`` — the expression of a generated column;
    * ``default_expression`` — a **genuine** DEFAULT only (never a generation
      expression), so a generated column can never be mistaken for an ordinary
      default;
    * ``collation`` — a non-default collation name, else ``None``;
    * ``comment`` — the object comment, else ``None``.
    """
    normalized: list[dict[str, Any]] = []
    for row in rows:
        entry = dict(row)
        raw_identity = str(entry.pop("identity_kind", None) or "")
        raw_generated = str(entry.pop("generated_kind", None) or "")
        entry["identity_kind"] = _IDENTITY_LABELS.get(raw_identity)
        entry["generated_kind"] = _GENERATED_LABELS.get(raw_generated)
        expression = entry.get("default_expression")
        if entry["generated_kind"]:
            entry["generation_expression"] = expression
            entry["default_expression"] = None
        else:
            entry["generation_expression"] = None
        for key in ("collation", "comment"):
            if not entry.get(key):
                entry[key] = None
        normalized.append(entry)
    return normalized


async def collect_catalog(connection: Any, schemas: Sequence[str]) -> CatalogSnapshot:
    """Collect the catalog snapshot using an existing (read-only) connection.

    Args:
        connection: an ``asyncpg`` connection inside the export transaction.
        schemas: schema names to export.

    Returns:
        A :class:`CatalogSnapshot`.

    Raises:
        BackupExportError: when a catalog query fails.
    """
    wanted = list(schemas)
    snapshot = CatalogSnapshot()
    try:
        identity_row = await connection.fetchrow(_IDENTITY_SQL)
        snapshot.identity = _jsonable(dict(identity_row)) if identity_row else {}
        snapshot.schemas = [row["schema"] for row in await connection.fetch(_SCHEMAS_SQL, wanted)]
        snapshot.tables = _rows(await connection.fetch(_TABLES_SQL, wanted, list(_TABLE_KINDS)))
        snapshot.columns = _normalize_columns(
            _rows(await connection.fetch(_COLUMNS_SQL, wanted, list(_TABLE_KINDS)))
        )
        snapshot.constraints = _rows(
            await connection.fetch(_CONSTRAINTS_SQL, wanted, list(_TABLE_KINDS))
        )
        snapshot.indexes = _rows(await connection.fetch(_INDEXES_SQL, wanted, list(_TABLE_KINDS)))
        snapshot.sequences = _rows(await connection.fetch(_SEQUENCES_SQL, wanted))
        snapshot.functions = _rows(await connection.fetch(_FUNCTIONS_SQL, wanted))
        snapshot.triggers = _rows(await connection.fetch(_TRIGGERS_SQL, wanted))
        snapshot.policies = _rows(await connection.fetch(_POLICIES_SQL, wanted))
        snapshot.views = _rows(await connection.fetch(_VIEWS_SQL, wanted))
        snapshot.partitions = _rows(await connection.fetch(_PARTITIONS_SQL, wanted))
        snapshot.extensions = _rows(await connection.fetch(_EXTENSIONS_SQL))
        snapshot.roles = _rows(await connection.fetch(_ROLES_SQL))
    except BackupExportError:
        raise
    except Exception as exc:  # noqa: BLE001 - normalised into a typed error
        raise BackupExportError(
            "catalog introspection failed", details={"reason": exc.__class__.__name__}
        ) from exc
    return snapshot


async def read_sequence_state(connection: Any, qualified_name: str) -> dict[str, Any]:
    """Read a sequence's current state (OID-2).

    ``qualified_name`` must originate from :data:`_SEQUENCES_SQL`, i.e. a string
    the **server** produced with ``format('%I.%I', …)`` — never user input.
    """
    try:
        row = await connection.fetchrow(f"SELECT last_value, is_called FROM {qualified_name}")
    except Exception as exc:  # noqa: BLE001 - normalised into a typed error
        raise BackupExportError(
            "sequence state read failed", details={"sequence": qualified_name}
        ) from exc
    return {
        "last_value": int(row["last_value"]) if row else 0,
        "is_called": bool(row["is_called"]) if row else False,
    }


def _rows(records: Iterable[Any]) -> list[dict[str, Any]]:
    """Convert asyncpg records into plain JSON-serialisable dicts."""
    return [_jsonable(dict(record)) for record in records]


def _jsonable(row: dict[str, Any]) -> dict[str, Any]:
    """Coerce asyncpg scalar types into JSON-serialisable values."""
    import datetime as _dt
    import decimal
    import uuid as _uuid

    converted: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, (_dt.datetime, _dt.date, _dt.time)):
            converted[key] = value.isoformat()
        elif isinstance(value, decimal.Decimal):
            converted[key] = str(value)
        elif isinstance(value, _uuid.UUID):
            converted[key] = str(value)
        elif isinstance(value, (bytes, bytearray, memoryview)):
            # PostgreSQL ``"char"`` columns (e.g. pg_constraint.contype,
            # pg_trigger.tgenabled) arrive from asyncpg as bytes.
            raw = bytes(value)
            try:
                converted[key] = raw.decode("utf-8")
            except UnicodeDecodeError:  # pragma: no cover - defensive
                converted[key] = raw.decode("latin-1")
        elif isinstance(value, (list, tuple)):
            converted[key] = [
                item if isinstance(item, (str, int, float, bool, type(None))) else str(item)
                for item in value
            ]
        else:
            converted[key] = value
    return converted

