"""Harness self-tests: report generation, verdict, Cline backlog (spec §31–§32)."""

from __future__ import annotations

from pathlib import Path

from qa_harness.core.findings import (
    Finding,
    FindingClassification,
)
from qa_harness.reports.backlog import ClineBacklogGenerator
from qa_harness.reports.generator import (
    REPORT_FILENAMES,
    ReportBundle,
    ReportGenerator,
    _partition_findings,
    acceptance_verdict,
)


def _finding(category: str, severity: str, title: str, id: str = "") -> Finding:
    return Finding(category=category, severity=severity, title=title, id=id)


def test_verdict_not_accepted_on_p0() -> None:
    findings = [_finding("SEC", "P0", "cross-tenant leak"), _finding("UI", "P3", "typo")]
    assert acceptance_verdict(findings) == "NOT ACCEPTED"


def test_verdict_not_accepted_on_p1() -> None:
    findings = [_finding("WF", "P1", "consultant cannot operate")]
    assert acceptance_verdict(findings) == "NOT ACCEPTED"


def test_verdict_conditions_on_p2_only() -> None:
    findings = [_finding("UX", "P2", "queue workspace buried")]
    assert acceptance_verdict(findings) == "ACCEPTED WITH CONDITIONS"


def test_verdict_unverified_when_areas_untested() -> None:
    assert acceptance_verdict([], unverified_areas=["browser"]) == "UNVERIFIED"
    assert acceptance_verdict([]) == "ACCEPTED"


def test_generator_writes_bundle(tmp_path: Path) -> None:
    generator = ReportGenerator(base_dir=tmp_path)
    bundle = ReportBundle(git_sha="abc123", environment="local",
                          coverage={"stages": {"db": 0}})
    findings = [_finding("DB", "P2", "duplicate memberships", "QA-DB-001")]
    paths = generator.generate(bundle, findings)
    assert paths["master"].exists()
    assert paths["executive"].exists()
    assert paths["findings"].exists()
    master_text = paths["master"].read_text(encoding="utf-8")
    assert "abc123" in master_text
    assert "- P2: 1" in master_text
    findings_text = paths["findings"].read_text(encoding="utf-8")
    assert "QA-DB-001" in findings_text
    assert "duplicate memberships" in findings_text


def test_generator_archives_previous(tmp_path: Path) -> None:
    generator = ReportGenerator(base_dir=tmp_path)
    bundle = ReportBundle(git_sha="one", environment="local")
    generator.generate(bundle, [])
    second = ReportGenerator(base_dir=tmp_path)
    second.generate(ReportBundle(git_sha="two", environment="local"), [])
    archived = list((tmp_path / "archive").glob("*CARBONTALLY_QA_MASTER_REPORT.md"))
    assert len(archived) == 1


def test_generator_does_not_claim_acceptance_from_incomplete_tests(tmp_path: Path) -> None:
    generator = ReportGenerator(base_dir=tmp_path)
    bundle = ReportBundle(git_sha="sha", environment="local",
                          coverage={"unverified_areas": ["api", "browser"]},
                          verdict="")
    generator.generate(bundle, [])
    master = (tmp_path / "latest" / "CARBONTALLY_QA_MASTER_REPORT.md").read_text(encoding="utf-8")
    assert "UNVERIFIED" in master


def test_report_filenames_include_backlog() -> None:
    assert "CLINE_IMPLEMENTATION_BACKLOG.md" in REPORT_FILENAMES


def test_backlog_generation() -> None:
    finding = _finding("RLS", "P1", "viewer can upload", "QA-RLS-001")
    finding.role = "viewer"
    finding.route = "/documents"
    finding.workflow = "customer"
    finding.actual = "upload succeeded"
    finding.expected = "403 denied"
    entries = ClineBacklogGenerator().generate([finding])
    assert len(entries) == 1
    entry = entries[0]
    assert entry.finding_id == "QA-RLS-001"
    assert entry.priority == "P1"
    assert entry.affected_layer == "database (RLS)"
    assert entry.security_implications
    assert entry.acceptance_criteria


def test_backlog_po_decision_flag() -> None:
    finding = _finding("WF", "P2", "self-approval unresolved", "QA-WF-001")
    finding.actual = "PO DECISION REQUIRED: single-owner self-approval policy unclear"
    entries = ClineBacklogGenerator().generate([finding])
    assert entries[0].po_decision_required is True


# --- V1.2 calibration: verdict must ignore harness artifacts ---------------


def test_verdict_ignores_harness_contract_defects() -> None:
    finding = _finding("API", "P1", "missing required param", "QA-API-001")
    finding.classification = FindingClassification.HARNESS_CONTRACT_DEFECT
    assert acceptance_verdict([finding]) == "ACCEPTED"


def test_verdict_ignores_inconclusive() -> None:
    finding = _finding("SEC", "P3", "gate inconclusive", "QA-SEC-001")
    finding.classification = FindingClassification.INCONCLUSIVE
    assert acceptance_verdict([finding]) == "ACCEPTED"


def test_verdict_counts_reverify_as_candidate() -> None:
    finding = _finding("WF", "P1", "consultant reporting 403", "QA-WF-001")
    finding.classification = FindingClassification.REVERIFY
    assert acceptance_verdict([finding]) == "NOT ACCEPTED"


def test_verdict_mixed_real_and_harness_defects() -> None:
    harness = _finding("API", "P1", "missing param", "QA-API-001")
    harness.classification = FindingClassification.HARNESS_CONTRACT_DEFECT
    real = _finding("SEC", "P0", "cross-tenant leak", "QA-SEC-001")
    assert acceptance_verdict([harness, real]) == "NOT ACCEPTED"


def test_partition_findings_splits_classifications() -> None:
    real = _finding("DB", "P1", "real defect", "QA-DB-001")
    reverify = _finding("WF", "P1", "candidate", "QA-WF-001")
    reverify.classification = FindingClassification.REVERIFY
    harness = _finding("API", "P1", "harness bug", "QA-API-001")
    harness.classification = FindingClassification.HARNESS_CONTRACT_DEFECT
    inconclusive = _finding("SEC", "P3", "inconclusive", "QA-SEC-001")
    inconclusive.classification = FindingClassification.INCONCLUSIVE
    counted, calibration, inconclusive_out = _partition_findings(
        [real, reverify, harness, inconclusive]
    )
    assert {f.id for f in counted} == {"QA-DB-001", "QA-WF-001"}
    assert {f.id for f in calibration} == {"QA-API-001"}
    assert {f.id for f in inconclusive_out} == {"QA-SEC-001"}


def test_backlog_excludes_harness_artifacts() -> None:
    real = _finding("WF", "P1", "consultant blocked", "QA-WF-001")
    inconclusive = _finding("SEC", "P3", "gate inconclusive", "QA-SEC-001")
    inconclusive.classification = FindingClassification.INCONCLUSIVE
    harness = _finding("API", "P1", "missing param", "QA-API-001")
    harness.classification = FindingClassification.HARNESS_CONTRACT_DEFECT
    entries = ClineBacklogGenerator().generate([real, inconclusive, harness])
    assert [e.finding_id for e in entries] == ["QA-WF-001"]


def test_master_report_lists_calibration_defects(tmp_path: Path) -> None:
    generator = ReportGenerator(base_dir=tmp_path)
    harness = _finding("API", "P1", "missing required param", "QA-API-001")
    harness.classification = FindingClassification.HARNESS_CONTRACT_DEFECT
    harness.actual = "HTTP 422 — Field required"
    real = _finding("WF", "P1", "consultant blocked", "QA-WF-001")
    bundle = ReportBundle(git_sha="sha", environment="local",
                          tests_executed=42, verdict="NOT ACCEPTED")
    generator.generate(bundle, [real, harness])
    master = (tmp_path / "latest" / "CARBONTALLY_QA_MASTER_REPORT.md").read_text(encoding="utf-8")
    assert "Harness calibration defects" in master
    assert "QA-API-001" in master
    assert "not CarbonTally defects" in master
    assert "Tests executed: 42" in master
