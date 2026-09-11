"""RunContext self-tests: id allocation, redaction, persistence, evidence."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_harness.core.config import TargetEnv
from qa_harness.core.credentials import DemoCredentials
from qa_harness.core.evidence import EvidenceStore
from qa_harness.core.findings import FindingStatus
from qa_harness.core.run_context import RunContext, make_run_id
from qa_harness.evidence.registry import EvidenceRegistry
from qa_harness.findings.store import FindingStore

ENV = TargetEnv(name="local", api_url="http://localhost:8050")


def _ctx(tmp_path: Path, *, git_sha: str = "abc1234",
         credentials: DemoCredentials = DemoCredentials(source="none")) -> RunContext:
    """Hermetic RunContext — never auto-loads the real credential file."""
    return RunContext(
        env=ENV,
        env_name="local",
        git_sha=git_sha,
        credentials=credentials,
        store=FindingStore(tmp_path / "findings"),
        evidence=EvidenceStore(tmp_path / "evidence"),
        registry=EvidenceRegistry(EvidenceStore(tmp_path / "evidence2")),
    )


def test_record_checks_accumulates(tmp_path: Path) -> None:
    ctx = RunContext(env=TargetEnv(name="local", api_url="http://localhost:8050"),
                     env_name="local", git_sha="abc")
    assert ctx.checks_executed == 0
    ctx.record_checks(12)
    ctx.record_checks(30)
    assert ctx.checks_executed == 42


def test_record_checks_ignores_negative(tmp_path: Path) -> None:
    ctx = RunContext(env=TargetEnv(name="local", api_url="http://localhost:8050"),
                     env_name="local", git_sha="abc")
    ctx.record_checks(-5)
    assert ctx.checks_executed == 0


def test_make_run_id(tmp_path: Path) -> None:
    run_id = make_run_id("abcdef1234567890")
    assert run_id.endswith("_abcdef1")


def test_emit_allocates_stable_ids(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    a = ctx.emit("API", "P1", "first api finding")
    b = ctx.emit("API", "P2", "second api finding")
    c = ctx.emit("DB", "P1", "db finding")
    assert a.id == "QA-API-001"
    assert b.id == "QA-API-002"
    assert c.id == "QA-DB-001"
    assert ctx.raw_findings() == [a, b, c]


def test_emit_redacts_secrets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CARBON_TALLY_DEMO_PASSWORD", "super-secret-demo-pass")
    ctx = _ctx(tmp_path)
    finding = ctx.emit("SEC", "P0", "leak", description="password was super-secret-demo-pass")
    assert "super-secret-demo-pass" not in finding.description
    assert "[REDACTED]" in finding.description


def test_emit_redacts_jwt_shape(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    fake_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0MTIzNDEyMzQxMjM0MTIzNCJ9.c2lnbmF0dXJlLWxvbmctZW5vdWdo"
    finding = ctx.emit("AUTH", "P1", "token", actual=fake_jwt)
    assert fake_jwt not in finding.actual
    assert "[REDACTED]" in finding.actual


def test_emit_skipped_uses_not_testable(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    skipped = ctx.emit_skipped("UI", "Browser unavailable", reason="no playwright")
    assert skipped.status == FindingStatus.NOT_TESTABLE
    assert "SKIPPED" in skipped.actual
    assert skipped.severity == "P3"


def test_finish_persists_three_stages(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    ctx.emit("API", "P2", "some api issue")
    ctx.emit("API", "P2", "Some API issue")  # duplicate wording -> dedup
    counts = ctx.finish()
    assert counts["raw"] == 2
    assert counts["normalized"] == 2
    assert counts["deduplicated"] == 1
    assert (tmp_path / "findings" / "raw" / "raw.jsonl").exists()
    assert (tmp_path / "findings" / "normalized" / "normalized.jsonl").exists()
    assert (tmp_path / "findings" / "deduplicated" / "deduplicated.jsonl").exists()


def test_api_evidence_written_and_redacted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://user:supersecretpw@host/db")
    ctx = _ctx(tmp_path)
    path = ctx.api_evidence("customer", "probe", "response token=supersecretpw tail")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "supersecretpw" not in text
    assert "[REDACTED]" in text
    assert len(ctx.registry.items) == 1


def test_demo_password_respects_credentials_source(tmp_path: Path,
                                                   monkeypatch: pytest.MonkeyPatch) -> None:
    from qa_harness.core.status import ToolUnavailable
    monkeypatch.delenv("CARBON_TALLY_DEMO_PASSWORD", raising=False)
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    # no credential -> SKIPPED (never guessed)
    ctx = _ctx(tmp_path)
    with pytest.raises(ToolUnavailable):
        ctx.demo_password()
    assert ctx.demo_credentials_summary()["password"] == "NOT SET"
    # explicit file-backed credentials -> used
    file_ctx = _ctx(tmp_path, credentials=DemoCredentials(
        source="file", password="file-pass-2026!-long"))
    assert file_ctx.demo_password() == "file-pass-2026!-long"
    assert file_ctx.demo_credentials_summary() == {
        "source": "local credentials file", "password": "SET"}
    # environment override wins at the loader level (precedence spec V1.2)
    from qa_harness.core.credentials import load_demo_credentials
    monkeypatch.setenv("CARBON_TALLY_DEMO_PASSWORD", "env-pass-2026!-long")
    creds = load_demo_credentials()
    assert creds.source == "environment"
    assert creds.password == "env-pass-2026!-long"
    env_ctx = _ctx(tmp_path, credentials=creds)
    assert env_ctx.demo_password() == "env-pass-2026!-long"
    assert env_ctx.demo_credentials_summary()["source"] == "environment"
