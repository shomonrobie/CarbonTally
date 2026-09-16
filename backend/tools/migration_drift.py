"""Migration drift prevention gate (WP-8 / FIN-06 phase-2 control).

Deterministic, READ-ONLY comparison between the repository migration set and an
environment's migration ledger, producing a release-evidence artefact and a
hard-fail exit code when the two disagree.

Checks
------
1. repository set: every ``supabase/migrations/*.sql`` file, ordered;
2. ordering anomalies: a filename whose 14-digit version prefix disagrees with
   the lexical position (i.e. the set is not strictly increasing);
3. duplicate migration identities: the same version (or the same filename) twice;
4. naming anomalies: files that do not match ``<14-digit>_<name>.sql``;
5. pending migrations: in the repository, absent from the ledger;
6. unexpected ledger entries: recorded as applied, absent from the repository;
7. applied count / latest applied version (evidence only).

Safety
------
* read-only: a single ``SELECT`` against ``supabase_migrations.schema_migrations``;
* a DSN that looks like a persistent environment (``prod``, ``live``, ``qa``,
  ``demo``, ``investor``) is REFUSED unless ``CARBONTALLY_MIGRATION_DRIFT_ALLOW``
  is set to ``non-production`` (the same guard pattern as the P2 census tool);
* no DSN and no ``--ledger-file`` ⇒ repository-only mode (CI linting).

Emergency override
------------------
``CARBONTALLY_MIGRATION_DRIFT_OVERRIDE=<ticket-id>`` (or ``--override <ticket>``)
downgrades a DRIFT failure to a warning. It is always recorded in the evidence
artefact and printed loudly; it never suppresses the evidence and never changes
the classification.

Usage
-----
    python -m tools.migration_drift --repo-only --out-dir artifacts/migration_drift
    python -m tools.migration_drift --ledger-file ledger.txt
    MIGRATION_DRIFT_DATABASE_URL=postgresql://... python -m tools.migration_drift

Exit codes: 0 = consistent (or overridden), 1 = DRIFT (release-blocking),
2 = environment/usage error.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

MIGRATION_FILE = re.compile(r"^(\d{14})_([A-Za-z0-9_.-]+)\.sql$")

#: DSN substrings that indicate a persistent/authoritative environment.
FORBIDDEN_DSN_MARKERS = ("prod", "live", "qa", "demo", "investor")
ALLOW_ENV = "CARBONTALLY_MIGRATION_DRIFT_ALLOW"
OVERRIDE_ENV = "CARBONTALLY_MIGRATION_DRIFT_OVERRIDE"
DSN_ENV = "MIGRATION_DRIFT_DATABASE_URL"

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_USAGE = 2


@dataclass(frozen=True, slots=True)
class MigrationFile:
    version: str
    name: str
    filename: str


@dataclass
class DriftReport:
    repository: list[str] = field(default_factory=list)
    ledger: list[str] = field(default_factory=list)
    applied: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)
    unexpected: list[str] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)
    ledger_source: str = "none"
    #: False when no ledger was available (repo-only lint mode): repository-side
    #: anomalies still fail the gate, but absent ledger evidence is NOT drift.
    ledger_available: bool = True
    override: Optional[str] = None

    @property
    def drift(self) -> bool:
        repository_side = bool(self.anomalies)
        if not self.ledger_available:
            return repository_side
        return bool(repository_side or self.pending or self.unexpected)

    def as_dict(self, *, generated_at: Optional[str] = None) -> dict:
        return {
            "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
            "repository_count": len(self.repository),
            "ledger_count": len(self.ledger),
            "ledger_available": self.ledger_available,
            "latest_repository_migration": self.repository[-1] if self.repository else None,
            "latest_applied_migration": self.applied[-1] if self.applied else None,
            "pending_count": len(self.pending),
            "unexpected_count": len(self.unexpected),
            "anomaly_count": len(self.anomalies),
            "drift": self.drift,
            "override": self.override,
            "ledger_source": self.ledger_source,
            "pending": self.pending,
            "unexpected": self.unexpected,
            "anomalies": self.anomalies,
        }


def load_repository_migrations(
    root: Path,
) -> tuple[list[MigrationFile], list[str]]:
    """Read ``supabase/migrations`` deterministically; report naming anomalies."""
    migrations_dir = root / "supabase" / "migrations"
    if not migrations_dir.is_dir():
        raise FileNotFoundError(f"no migrations directory at {migrations_dir}")
    files = sorted(p.name for p in migrations_dir.glob("*.sql"))
    parsed: list[MigrationFile] = []
    anomalies: list[str] = []
    seen_versions: set[str] = set()
    for filename in files:
        match = MIGRATION_FILE.match(filename)
        if match is None:
            anomalies.append(f"naming anomaly: {filename} does not match <14 digits>_<name>.sql")
            continue
        version, name = match.group(1), match.group(2)
        if version in seen_versions:
            anomalies.append(f"duplicate migration version {version} (file {filename})")
        seen_versions.add(version)
        parsed.append(MigrationFile(version=version, name=name, filename=filename))
    versions = [m.version for m in parsed]
    if versions != sorted(versions):
        anomalies.append("ordering anomaly: migration versions are not strictly increasing")
    return parsed, anomalies


def parse_ledger(rows: Iterable[str]) -> list[str]:
    """Normalise ledger rows (``<version>`` or ``<version>_<name>``) to versions."""
    versions: list[str] = []
    for row in rows:
        value = str(row).strip()
        if not value:
            continue
        versions.append(value.split("_", 1)[0] if "_" in value else value)
    return versions


def compare(
    migrations: list[MigrationFile],
    ledger_versions: list[str],
    *,
    anomalies: Optional[list[str]] = None,
    ledger_source: str = "none",
    ledger_available: bool = True,
    override: Optional[str] = None,
) -> DriftReport:
    """Classify the repository set against the ledger."""
    repo_versions = [m.version for m in migrations]
    ledger = sorted(set(ledger_versions))
    repo_set = set(repo_versions)
    ledger_set = set(ledger)
    applied = [v for v in repo_versions if v in ledger_set]
    pending = [v for v in repo_versions if v not in ledger_set]
    unexpected = [v for v in ledger if v not in repo_set]
    report = DriftReport(
        repository=repo_versions,
        ledger=ledger,
        applied=applied,
        pending=pending,
        unexpected=unexpected,
        anomalies=list(anomalies or []),
        ledger_source=ledger_source,
        ledger_available=ledger_available,
        override=override,
    )
    if len(ledger) != len(ledger_versions):
        report.anomalies.append("duplicate entries in the migration ledger")
    return report


def assert_safe_dsn(dsn: str) -> None:
    """Refuse persistent/authoritative environments unless explicitly allowed."""
    lowered = dsn.lower()
    if os.environ.get(ALLOW_ENV) == "non-production":
        return
    for marker in FORBIDDEN_DSN_MARKERS:
        if marker in lowered:
            raise SystemExit(
                f"refusing DSN containing {marker!r}: set {ALLOW_ENV}=non-production "
                "to acknowledge a non-production target (production access is a "
                "separate, PO-authorised gate)"
            )


async def fetch_ledger(dsn: str) -> list[str]:
    """Read-only ledger read (``supabase_migrations.schema_migrations``)."""
    assert_safe_dsn(dsn)
    import asyncpg

    conn = await asyncpg.connect(dsn)
    try:
        rows = await conn.fetch(
            "SELECT version FROM supabase_migrations.schema_migrations ORDER BY version"
        )
    finally:
        await conn.close()
    return [str(r["version"]) for r in rows]


def render_markdown(report: DriftReport, *, target: str) -> str:
    payload = report.as_dict()
    lines = [
        "# Migration drift report",
        "",
        f"* target: `{target}`",
        f"* ledger source: `{report.ledger_source}`",
        f"* repository migrations: **{payload['repository_count']}**",
        f"* ledger entries: **{payload['ledger_count']}**",
        f"* latest repository migration: `{payload['latest_repository_migration']}`",
        f"* latest applied migration: `{payload['latest_applied_migration']}`",
        f"* **drift: {'YES' if report.drift else 'NO'}**",
        f"* override: `{report.override or 'none'}`",
        "",
        f"## Pending ({payload['pending_count']})",
        "",
    ]
    lines += [f"* `{v}`" for v in report.pending] or ["* none"]
    lines += ["", f"## Unexpected ledger entries ({payload['unexpected_count']})", ""]
    lines += [f"* `{v}`" for v in report.unexpected] or ["* none"]
    lines += ["", f"## Anomalies ({payload['anomaly_count']})", ""]
    lines += [f"* {a}" for a in report.anomalies] or ["* none"]
    lines += [
        "",
        "## Operator action",
        "",
        "If `drift: YES`, either apply the pending migrations (under the authorised",
        "window) or block the release. The emergency override",
        f"(`{OVERRIDE_ENV}=<ticket-id>`) only downgrades the exit code; it never",
        "suppresses this evidence.",
        "",
    ]
    return "\n".join(lines)


def write_evidence(report: DriftReport, *, target: str, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"migration_drift_{stamp}.json"
    md_path = out_dir / f"migration_drift_{stamp}.md"
    payload = report.as_dict()
    payload["target"] = target
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report, target=target), encoding="utf-8")
    return json_path, md_path


def exit_code(report: DriftReport) -> int:
    """Release gate: drift hard-fails unless an explicit override is recorded."""
    if not report.drift:
        return EXIT_OK
    if report.override:
        return EXIT_OK
    return EXIT_DRIFT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.migration_drift",
        description="Read-only migration drift gate (repository vs ledger).",
    )
    parser.add_argument("--repo-root", default=None, help="repository root (default: auto)")
    parser.add_argument("--repo-only", action="store_true", help="skip the ledger comparison")
    parser.add_argument("--ledger-file", default=None, help="file of applied migration versions")
    parser.add_argument("--dsn", default=None, help=f"ledger DSN (default: ${DSN_ENV})")
    parser.add_argument("--out-dir", default="artifacts/migration_drift")
    parser.add_argument("--override", default=None, help=f"emergency ticket id (or ${OVERRIDE_ENV})")
    return parser


def _repo_root(explicit: Optional[str]) -> Path:
    if explicit:
        return Path(explicit).resolve()
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "supabase" / "migrations").is_dir():
            return parent
    raise SystemExit("could not locate the repository root (supabase/migrations)")


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = _repo_root(args.repo_root)
    override = args.override or os.environ.get(OVERRIDE_ENV) or None

    migrations, anomalies = load_repository_migrations(root)

    ledger_versions: list[str] = []
    ledger_source = "none"
    ledger_available = False
    if args.ledger_file:
        ledger_source = f"file:{args.ledger_file}"
        ledger_available = True
        ledger_versions = parse_ledger(
            Path(args.ledger_file).read_text(encoding="utf-8").splitlines()
        )
    elif not args.repo_only:
        dsn = args.dsn or os.environ.get(DSN_ENV)
        if dsn:
            ledger_source = "database"
            ledger_available = True
            ledger_versions = asyncio.run(fetch_ledger(dsn))
        else:
            ledger_source = "repo-only"

    report = compare(
        migrations,
        ledger_versions,
        anomalies=anomalies,
        ledger_source=ledger_source,
        ledger_available=ledger_available,
        override=override,
    )
    json_path, md_path = write_evidence(
        report, target=f"{root} ({ledger_source})", out_dir=Path(args.out_dir)
    )

    code = exit_code(report)
    print(
        f"migration-drift: repository={len(report.repository)} ledger={len(report.ledger)} "
        f"pending={len(report.pending)} unexpected={len(report.unexpected)} "
        f"anomalies={len(report.anomalies)} drift={report.drift} "
        f"override={report.override or 'none'}"
    )
    print(f"evidence: {json_path} | {md_path}")
    if report.drift and report.override:
        print(
            f"WARNING: migration drift ACCEPTED UNDER OVERRIDE {report.override} — "
            "this must be reviewed and the migrations applied."
        )
    elif code == EXIT_DRIFT:
        print("RELEASE BLOCKED: migration state is inconsistent with the repository.")
    return code


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
