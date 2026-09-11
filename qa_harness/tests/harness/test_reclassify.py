"""Reclassification maintenance tool self-tests.

The tool preserves every finding and all evidence while changing only the
classification + a prefixed calibration note — used to mark a previous run's
findings as needing re-verification after a harness defect is fixed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from qa_harness.core.findings import Finding, FindingClassification
from qa_harness.scripts.reclassify import NOTE_PREFIX, reclassify_findings


def _finding(fid: str, source: str, title: str = "documents table lacks pagination") -> Finding:
    return Finding(
        id=fid, category="UX", severity="P2", title=title,
        source=source, evidence=["screenshots/x.png"],
        description="no pagination in document table",
    )


def _store(tmp_path: Path, findings: List[Finding]) -> Path:
    base = tmp_path / "findings"
    for name in ("normalized", "deduplicated"):
        (base / name).mkdir(parents=True)
        rows = [f.to_dict() for f in findings]
        (base / name / f"{name}.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n"
        )
    return base


def _read(base: Path, name: str) -> List[Dict[str, object]]:
    return [json.loads(l) for l in (base / name / f"{name}.jsonl").read_text().splitlines()]


def test_reclassify_changes_only_target_source_and_preserves_evidence(
        tmp_path: Path) -> None:
    base = _store(tmp_path, [
        _finding("QA-UX-001", "run_browser.py"),
        _finding("QA-UX-002", "run_api.py"),
    ])
    counts = reclassify_findings(
        base, "run_browser.py", FindingClassification.REVERIFY,
        "browser findings generated from an unauthenticated /login page",
        dry_run=False, regenerate_reports=False,
    )
    assert counts["deduplicated"] == 1
    assert counts["normalized"] == 1

    for name in ("normalized", "deduplicated"):
        rows = _read(base, name)
        browser = next(r for r in rows if r["id"] == "QA-UX-001")
        api = next(r for r in rows if r["id"] == "QA-UX-002")
        assert browser["classification"] == FindingClassification.REVERIFY
        assert browser["evidence"] == ["screenshots/x.png"]  # evidence preserved
        assert NOTE_PREFIX in browser["description"]
        assert browser["id"] == "QA-UX-001"  # id/title/timestamp preserved
        assert api["classification"] == FindingClassification.REAL
        assert "calibration" not in api["description"]


def test_reclassify_dry_run_writes_nothing(tmp_path: Path) -> None:
    base = _store(tmp_path, [_finding("QA-UX-001", "run_browser.py")])
    before_normalized = (base / "normalized" / "normalized.jsonl").read_text()
    counts = reclassify_findings(
        base, "run_browser.py", FindingClassification.REVERIFY,
        "dry run reason", dry_run=True, regenerate_reports=False,
    )
    assert counts["deduplicated"] == 1
    assert (base / "normalized" / "normalized.jsonl").read_text() == before_normalized
    assert _read(base, "deduplicated")[0]["classification"] == FindingClassification.REAL


def test_reclassify_rejects_unknown_classification(tmp_path: Path) -> None:
    from qa_harness.scripts import reclassify

    code = reclassify.main([
        "--source", "run_browser.py",
        "--classification", "NOT-A-CLASS",
        "--reason", "x",
        "--findings-dir", str(tmp_path),
        "--no-reports",
    ])
    assert code == 2


def test_reclassify_idempotent(tmp_path: Path) -> None:
    base = _store(tmp_path, [_finding("QA-UX-001", "run_browser.py")])
    reclassify_findings(base, "run_browser.py", FindingClassification.REVERIFY,
                        "once", dry_run=False, regenerate_reports=False)
    counts = reclassify_findings(
        base, "run_browser.py", FindingClassification.REVERIFY,
        "once", dry_run=False, regenerate_reports=False,
    )
    assert counts["deduplicated"] == 0  # already classified; no-op
    assert counts["normalized"] == 0
