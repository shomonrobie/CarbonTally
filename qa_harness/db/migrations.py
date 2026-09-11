"""Migration-state audit (read-only).

Compares the migrations present in the repo (``supabase/migrations/``) against
the migrations recorded as applied in the database. A migration file that is
not applied means the schema does not match the code (historical MD-2:
``vehicles`` migration existed in the repo but was not applied).

The repo-side listing is deterministic; the DB-side check uses
``supabase_migrations.schema_migrations`` when present and falls back to a
schema diff when it is not.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

_MIGRATION_FILE = re.compile(r"^(\d{14})_(.+)\.sql$")


@dataclass
class MigrationRecord:
    version: str          # e.g. "20260810000000"
    name: str             # e.g. "v3m1_processing_entities"
    filename: str
    applied: Optional[bool] = None   # None = unknown

    @property
    def key(self) -> str:
        return self.version


class MigrationAudit:
    def __init__(self, migrations_dir: Optional[Path] = None) -> None:
        self.migrations_dir = Path(migrations_dir) if migrations_dir else (
            Path(__file__).resolve().parent.parent.parent / "supabase" / "migrations"
        )
        self._repo_records: Optional[List[MigrationRecord]] = None

    def repo_migrations(self) -> List[MigrationRecord]:
        if self._repo_records is not None:
            return self._repo_records
        records: List[MigrationRecord] = []
        if self.migrations_dir.exists():
            for path in sorted(self.migrations_dir.glob("*.sql")):
                match = _MIGRATION_FILE.match(path.name)
                if match:
                    records.append(MigrationRecord(
                        version=match.group(1),
                        name=match.group(2),
                        filename=path.name,
                    ))
        self._repo_records = records
        return records

    def applied_versions(self, connection: Optional[Any] = None) -> List[str]:
        """Return versions recorded as applied, or [] when unknown/unreachable."""
        if connection is None:
            return []
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "SELECT version FROM supabase_migrations.schema_migrations ORDER BY version;"
                )
                return [str(row[0]) for row in cursor.fetchall()]
            finally:
                cursor.close()
        except Exception:
            return []

    def not_applied(self, applied: List[str]) -> List[MigrationRecord]:
        applied_set = set(applied)
        return [r for r in self.repo_migrations() if r.version not in applied_set]

    def summary(self, applied: Optional[List[str]] = None,
                connection: Optional[Any] = None) -> Dict[str, object]:
        if applied is None and connection is not None:
            applied = self.applied_versions(connection)
        applied = applied if applied is not None else []
        pending = self.not_applied(applied)
        return {
            "repo_migrations": len(self.repo_migrations()),
            "applied_versions": len(applied),
            "pending": [r.filename for r in pending],
            "pending_count": len(pending),
        }
