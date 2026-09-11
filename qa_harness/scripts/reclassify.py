#!/usr/bin/env python3
"""Reclassify persisted findings after a harness defect is fixed (calibration).

Preserves every finding and ALL of its evidence. Only the classification
(and a prefixed calibration note) change, so a previous run whose findings
depended on defective harness behavior is marked ``RE-VERIFY`` instead of
being silently deleted or wrongly trusted.

Example (V1.2 first-run calibration — browser findings were generated from
an unauthenticated /login page because of the full-URL login detection bug)::

    python qa_harness/scripts/reclassify.py \\
        --source run_browser.py \\
        --classification RE-VERIFY \\
        --reason "generated from an unauthenticated /login page (V1.2 full-URL login detection bug); re-verify after the harness fix"

Options:

* ``--dry-run``        report what would change without writing.
* ``--no-reports``     do not regenerate reports/latest after reclassifying.
* ``--findings-dir``   override the findings store directory (tests use this).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

from qa_harness.core.findings import Finding, FindingClassification
from qa_harness.scripts.common import HARNESS_ROOT

FINDINGS_DIR = HARNESS_ROOT / "findings"
NOTE_PREFIX = "[calibration] "


def _load(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _dump(path: Path, rows: List[Dict[str, object]]) -> None:
    tmp = path.with_suffix(".jsonl.tmp")
    tmp.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    tmp.replace(path)


def reclassify_file(path: Path, source: str, classification: str, reason: str,
                    dry_run: bool) -> int:
    rows = _load(path)
    changed = 0
    for row in rows:
        if row.get("source") != source:
            continue
        if row.get("classification") == classification:
            continue
        changed += 1
        if dry_run:
            continue
        row["classification"] = classification
        note = f"{NOTE_PREFIX}{reason}"
        description = str(row.get("description") or "")
        if note not in description:
            row["description"] = (note + "\n\n" + description).strip()
    if not dry_run and changed:
        _dump(path, rows)
    return changed


def reclassify_findings(findings_dir: Path, source: str, classification: str,
                        reason: str, *, dry_run: bool = False,
                        regenerate_reports: bool = True) -> Dict[str, int]:
    """Reclassify findings from ``source`` in normalized + deduplicated stores.

    Returns ``{normalized, deduplicated}`` counts of changed findings.
    """
    from qa_harness.core.findings import normalize_finding, deduplicate_findings  # noqa: F401

    counts: Dict[str, int] = {}
    for name in ("normalized", "deduplicated"):
        counts[name] = reclassify_file(
            findings_dir / name / f"{name}.jsonl", source, classification,
            reason, dry_run=dry_run,
        )
    if not dry_run and regenerate_reports and counts["deduplicated"]:
        _regenerate_reports(findings_dir)
    return counts


def _regenerate_reports(findings_dir: Path) -> None:
    """Regenerate reports/latest from the reclassified deduplicated store.

    Contacts no application; pure local document generation.
    """
    from qa_harness.reports.backlog import ClineBacklogGenerator
    from qa_harness.reports.generator import ReportBundle, ReportGenerator

    path = findings_dir / "deduplicated" / "deduplicated.jsonl"
    findings = [Finding.from_dict(row) for row in _load(path)]
    raw_count = len(_load(findings_dir / "raw" / "raw.jsonl"))
    generator = ReportGenerator()
    bundle = ReportBundle(
        git_sha="",
        environment="local",
        coverage={
            "stages": {},
            "unverified_areas": ["reclassified"],
            "findings_raw": raw_count,
            "findings_deduplicated": len(findings),
            "stage_outcomes": {},
            "checks_executed": 0,
        },
        tests_executed=0,
        tests_skipped=0,
        verdict="UNVERIFIED",
        notes=(
            "Reports regenerated from the reclassified findings store "
            "(calibration reclassification; not a fresh application run)."
        ),
    )
    generator.generate(bundle, findings)
    backlog = ClineBacklogGenerator().generate(findings)
    backlog_path = generator.latest_dir / "CLINE_IMPLEMENTATION_BACKLOG.md"
    ClineBacklogGenerator().write_markdown(backlog, backlog_path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True,
                        help="finding source to reclassify, e.g. run_browser.py")
    parser.add_argument("--classification", required=True,
                        help="target classification, e.g. RE-VERIFY")
    parser.add_argument("--reason", required=True,
                        help="calibration note prepended to the description")
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would change without writing")
    parser.add_argument("--no-reports", action="store_true",
                        help="do not regenerate reports/latest after reclassifying")
    parser.add_argument("--findings-dir", default=str(FINDINGS_DIR),
                        help="findings store directory (default: qa_harness/findings)")
    args = parser.parse_args(argv)

    if args.classification not in FindingClassification.ALL:
        print(f"ERROR: unknown classification {args.classification!r}; "
              f"expected one of {sorted(FindingClassification.ALL)}")
        return 2

    counts = reclassify_findings(
        Path(args.findings_dir), args.source, args.classification, args.reason,
        dry_run=args.dry_run, regenerate_reports=not args.no_reports,
    )
    verb = "would change" if args.dry_run else "changed"
    print(f"{args.source}: normalized {counts['normalized']} {verb}, "
          f"deduplicated {counts['deduplicated']} {verb} -> {args.classification}")
    if args.dry_run:
        print("DRY RUN — no files written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
