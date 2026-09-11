"""Harness self-tests: finding model, normalization, deduplication (spec §28–§30)."""

from __future__ import annotations

import pytest

from qa_harness.core.findings import (
    CATEGORIES,
    Deduplicator,
    Finding,
    FindingClassification,
    FindingIdAllocator,
    FindingNormalizer,
    deduplicate_findings,
    filter_by,
    normalize_finding,
    normalize_text,
    renumber,
)


def test_finding_defaults() -> None:
    finding = Finding(category="DB", severity="P2", title="orphan rows")
    assert finding.status == "OPEN"
    assert finding.timestamp
    assert finding.normalized_key  # auto-computed
    assert finding.id is None


def test_finding_invalid_category() -> None:
    with pytest.raises(ValueError):
        Finding(category="NOPE", severity="P2", title="x")


def test_finding_invalid_severity() -> None:
    with pytest.raises(ValueError):
        Finding(category="DB", severity="P9", title="x")


def test_finding_classification_defaults_to_real() -> None:
    finding = Finding(category="DB", severity="P2", title="orphan rows")
    assert finding.classification == FindingClassification.REAL


def test_finding_invalid_classification_raises() -> None:
    with pytest.raises(ValueError):
        Finding(category="DB", severity="P2", title="x",
                classification="MAYBE")


def test_classification_roundtrip() -> None:
    finding = Finding(category="SEC", severity="P3", title="gate inconclusive",
                      classification=FindingClassification.INCONCLUSIVE)
    restored = Finding.from_dict(finding.to_dict())
    assert restored.classification == FindingClassification.INCONCLUSIVE


def test_verdict_counted_vocabulary() -> None:
    assert FindingClassification.VERDICT_COUNTED == {
        FindingClassification.REAL,
        FindingClassification.APPLICATION_DEFECT,
        FindingClassification.REVERIFY,
    }
    assert FindingClassification.HARNESS_CONTRACT_DEFECT not in FindingClassification.VERDICT_COUNTED
    assert FindingClassification.HARNESS_RUNTIME_ERROR not in FindingClassification.VERDICT_COUNTED
    assert FindingClassification.AUTHENTICATION_FAILURE not in FindingClassification.VERDICT_COUNTED
    assert FindingClassification.INCONCLUSIVE not in FindingClassification.VERDICT_COUNTED


def test_classification_harness_runtime_error_vocabulary() -> None:
    assert FindingClassification.HARNESS_RUNTIME_ERROR == "HARNESS_RUNTIME_ERROR"
    assert FindingClassification.AUTHENTICATION_FAILURE == "AUTHENTICATION_FAILURE"
    assert FindingClassification.APPLICATION_DEFECT == "APPLICATION_DEFECT"
    for value in FindingClassification.ALL:
        assert value in FindingClassification.ALL


def test_id_allocator() -> None:
    allocator = FindingIdAllocator()
    assert allocator.allocate("DB") == "QA-DB-001"
    assert allocator.allocate("DB") == "QA-DB-002"
    assert allocator.allocate("UI") == "QA-UI-001"


def test_normalize_text_paraphrase_collapse() -> None:
    a = normalize_text("No pagination in document table")
    b = normalize_text("Documents table lacks pagination")
    assert a == b


def test_normalize_text_stopwords() -> None:
    # Stopwords are dropped; the negation token is meaningful and kept.
    assert normalize_text("the table has no pagination") == normalize_text("table no pagination")
    assert normalize_text("the table has no pagination") != normalize_text("pagination table")


def test_serialization_roundtrip() -> None:
    finding = Finding(category="API", severity="P1", title="500 on create",
                      route="/api/v3/orgs", evidence=["resp.json"])
    data = finding.to_dict()
    restored = Finding.from_dict(data)
    assert restored.title == finding.title
    assert restored.evidence == ["resp.json"]


def test_deduplicator_merges_evidence() -> None:
    dedup = Deduplicator()
    f1 = Finding(category="UX", severity="P2", title="No pagination in document table",
                 evidence=["shot1.png"])
    f2 = Finding(category="UX", severity="P2", title="Documents table lacks pagination",
                 evidence=["shot2.png"])
    canonical = dedup.add(f1)
    dedup.add(f2)
    result = dedup.deduplicated()
    assert len(result) == 1
    assert result[0].dedup_group_size == 2
    assert set(result[0].evidence) == {"shot1.png", "shot2.png"}


def test_deduplicate_findings_renumbers() -> None:
    findings = [
        Finding(category="UX", severity="P2", title="No pagination in document table"),
        Finding(category="UX", severity="P2", title="Documents table lacks pagination"),
        Finding(category="DB", severity="P1", title="orphan rows"),
    ]
    deduplicated = deduplicate_findings(findings)
    assert len(deduplicated) == 2
    ids = [f.id for f in deduplicated]
    assert ids[0].startswith("QA-DB-") and ids[1].startswith("QA-UX-")


def test_normalize_finding_attaches_key() -> None:
    finding = Finding(category="UI", severity="P3", title="Button misaligned")
    assert normalize_finding(finding).normalized_key


def test_renumber_deterministic() -> None:
    findings = [
        Finding(category="DB", severity="P2", title="z"),
        Finding(category="DB", severity="P2", title="a"),
    ]
    first = renumber([Finding(**f.to_dict()) for f in findings])
    second = renumber([Finding(**f.to_dict()) for f in findings])
    assert [f.id for f in first] == [f.id for f in second]


def test_filter_by() -> None:
    findings = [
        Finding(category="DB", severity="P1", title="a", role="consultant"),
        Finding(category="DB", severity="P2", title="b", role="operator"),
    ]
    result = filter_by(findings, severity="P1")
    assert len(result) == 1 and result[0].title == "a"
    assert len(filter_by(findings)) == 2


def test_all_categories_have_prefixes() -> None:
    for key in CATEGORIES:
        assert key in ("DB", "RLS", "API", "AUTH", "WF", "UI", "UX", "SEC", "A11Y")
