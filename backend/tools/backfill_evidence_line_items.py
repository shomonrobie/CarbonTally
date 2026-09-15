"""Phase 8 B2 — Class-1 evidence-line backfill CLI (contract §11.4, §22.1).

Usage::

    python -m tools.backfill_evidence_line_items                 # dry run (report only)
    python -m tools.backfill_evidence_line_items --apply         # perform the Class-1 backfill
    python -m tools.backfill_evidence_line_items --apply --batch-size 200 --limit 5000
    python -m tools.backfill_evidence_line_items --json          # machine-readable run report

Boundaries (contract §11.4/§18.4 — enforced by the repository, stated here too):

* The backfill is **not** a migration. It is an explicitly-invoked, offline,
  idempotent, batched, resumable Class-1 operation.
* It **only inserts** missing evidence lines for items whose persisted
  ``extracted_data.line_items[]`` genuinely carries lines. It never re-extracts
  (no PDF/OCR/LLM/parser pass), never updates, never deletes, never renumbers,
  never reads ``mapped_data`` for identity and never infers invoice lines.
* A **dry run writes nothing at all** — including no audit row — so "zero
  writes" is literally true; its counts are identical to the real run's.
* **Execution against any environment is separately authorised.** Production is
  **not** authorised by B2 (G0-D outstanding; 34 + 2 migrations undeployed).
"""
from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import asdict

from api.dependencies import get_repositories
from core.logging import get_logger

logger = get_logger(__name__)


def _parse_args(argv: list[str]) -> tuple[bool, int, int | None, bool]:
    apply = "--apply" in argv
    batch_size = 500
    limit: int | None = None
    as_json = "--json" in argv
    if "--batch-size" in argv:
        batch_size = int(argv[argv.index("--batch-size") + 1])
    if "--limit" in argv:
        limit = int(argv[argv.index("--limit") + 1])
    return apply, batch_size, limit, as_json


async def _main(argv: list[str]) -> int:
    apply, batch_size, limit, as_json = _parse_args(argv)
    repos = await get_repositories()
    repo = repos.evidence_line_items
    report = await repo.backfill(
        dry_run=not apply, batch_size=batch_size, limit=limit
    )
    if as_json:
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print(
            f"B2 Class-1 evidence-line backfill — "
            f"{'APPLY' if apply else 'DRY RUN (no writes)'}"
        )
        print(f"  run_id              : {report.run_id}")
        print(f"  started_at          : {report.started_at}")
        print(f"  finished_at         : {report.finished_at}")
        print(f"  scanned_items       : {report.scanned_items}")
        print(f"  eligible_items      : {report.eligible_items}")
        print(f"  materialised_rows   : {report.materialised_rows}")
        print(f"  skipped_empty       : {report.skipped_empty}")
        print(f"  skipped_malformed   : {report.skipped_malformed}")
        print(f"  skipped_no_lines    : {report.skipped_no_lines}")
        print(f"  divergences         : {report.divergences}")
        print(f"  errors              : {report.errors}")
        print(f"  audit_written       : {report.audit_written}")
        print(
            "  note                : dry runs write nothing (no lines, no audit); "
            "re-running an applied run inserts nothing new (§11.3)."
        )
    return 1 if report.errors else 0


def main() -> int:
    try:
        return asyncio.run(_main(sys.argv[1:]))
    except Exception:  # noqa: BLE001 — an operational CLI reports, never leaks
        logger.exception("B2 evidence-line backfill failed")
        print("B2 evidence-line backfill FAILED — see the developer log.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
