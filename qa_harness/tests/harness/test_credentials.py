"""Credential-loader self-tests (spec V1.2).

All tests use temporary credential files with a FAKE password — the real
local demo password is never used, logged, or committed anywhere.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_harness.core.config import TargetEnv
from qa_harness.core.credentials import (
    CredentialsError,
    DemoCredentials,
    demo_credentials_summary,
    find_credentials_file,
    load_demo_credentials,
    parse_credentials_file,
    password_for,
)
from qa_harness.core.evidence import EvidenceStore
from qa_harness.core.run_context import RunContext
from qa_harness.evidence.registry import EvidenceRegistry
from qa_harness.findings.store import FindingStore

FAKE_PASSWORD = "Test-Local-Demo-Pass-2026!"

SAMPLE_FILE = f"""# Local demo credentials (NEVER COMMIT)

Local-only password (shared): **{FAKE_PASSWORD}**

| Actor | Email | Landing route | Notes |
|---|---|---|---|
| Customer Owner | owner@demo.carbontally.local | /home | Customer |
| Consultant | consultant@demo.carbontally.local | /consultant | Consultant |
"""

ENV = TargetEnv(name="local", api_url="http://localhost:8050")


def _write(tmp_path: Path, text: str = SAMPLE_FILE) -> Path:
    path = tmp_path / ".local-demo-credentials.md"
    path.write_text(text, encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Loading + precedence
# --------------------------------------------------------------------------- #

def test_loaded_from_environment() -> None:
    creds = load_demo_credentials(env={"CARBON_TALLY_DEMO_PASSWORD": "env-secret-123"})
    assert creds.source == "environment"
    assert creds.password == "env-secret-123"
    assert creds.has_password


def test_loaded_from_local_file(tmp_path: Path) -> None:
    path = _write(tmp_path)
    creds = load_demo_credentials(credentials_path=path)
    assert creds.source == "file"
    assert creds.password == FAKE_PASSWORD
    assert creds.file_path == path
    # representative emails parsed (informational only)
    assert "owner@demo.carbontally.local" in creds.representative_emails
    assert "consultant@demo.carbontally.local" in creds.representative_emails


def test_environment_takes_precedence(tmp_path: Path) -> None:
    path = _write(tmp_path)
    creds = load_demo_credentials(
        credentials_path=path,
        env={"CARBON_TALLY_DEMO_PASSWORD": "env-wins-123"},
    )
    assert creds.source == "environment"
    assert creds.password == "env-wins-123"


def test_missing_file_is_not_an_error(tmp_path: Path) -> None:
    creds = load_demo_credentials(
        credentials_path=tmp_path / "does-not-exist.md",
        env={},
    )
    assert creds.source == "none"
    assert not creds.has_password


def test_malformed_file_raises(tmp_path: Path) -> None:
    path = _write(tmp_path, "# no password line here\n| Actor | x |\n")
    with pytest.raises(CredentialsError):
        load_demo_credentials(credentials_path=path, env={})


def test_missing_credential_raises(tmp_path: Path) -> None:
    path = _write(tmp_path, "Local-only password (shared): **  **\n")
    with pytest.raises(CredentialsError):
        load_demo_credentials(credentials_path=path, env={})


def test_short_password_raises(tmp_path: Path) -> None:
    path = _write(tmp_path, "Local-only password (shared): **abc**\n")
    with pytest.raises(CredentialsError):
        load_demo_credentials(credentials_path=path, env={})


def test_no_credential_never_guessed(tmp_path: Path) -> None:
    summary = demo_credentials_summary(credentials_path=tmp_path / "missing.md", env={})
    assert summary == {"source": "NOT SET", "password": "NOT SET"}


# --------------------------------------------------------------------------- #
# No secret leakage
# --------------------------------------------------------------------------- #

def test_password_never_in_representations(tmp_path: Path) -> None:
    creds = DemoCredentials(source="file", password=FAKE_PASSWORD)
    representations = (str(creds), repr(creds), str(creds.to_dict()))
    for representation in representations:
        assert FAKE_PASSWORD not in representation
    # str()/to_dict() state the password is SET without revealing it
    assert "password=SET" in str(creds)
    assert "'password': 'SET'" in str(creds.to_dict())
    summary = demo_credentials_summary(credentials_path=_write(tmp_path), env={})
    assert FAKE_PASSWORD not in str(summary)
    assert summary["password"] == "SET"


def test_parse_never_echoes_password_in_errors(tmp_path: Path) -> None:
    path = _write(tmp_path, "Local-only password (shared): **  **\n")
    try:
        parse_credentials_file(path.read_text(encoding="utf-8"))
    except CredentialsError as exc:
        message = str(exc)
    else:
        pytest.fail("expected CredentialsError")
    assert FAKE_PASSWORD not in message
    assert "password" in message


# --------------------------------------------------------------------------- #
# Structural safeguards (demo-only credential)
# --------------------------------------------------------------------------- #

def test_demo_identity_allowed() -> None:
    password = password_for("owner@demo.carbontally.local",
                            credentials=DemoCredentials(source="file", password=FAKE_PASSWORD))
    assert password == FAKE_PASSWORD


def test_non_demo_identity_rejected() -> None:
    with pytest.raises(ValueError):
        password_for("owner@test.carbontally.local",
                     credentials=DemoCredentials(source="file", password=FAKE_PASSWORD))


def test_audit_fixture_rejected() -> None:
    from qa_harness.identities.loader import generate_full_population
    audit = next(i for i in generate_full_population() if i.persona == "audit")
    assert not audit.is_demo
    with pytest.raises(ValueError):
        password_for(audit, credentials=DemoCredentials(source="file", password=FAKE_PASSWORD))


def test_system_fixture_rejected() -> None:
    from qa_harness.identities.loader import generate_full_population
    fixture = next(i for i in generate_full_population() if i.persona == "fixture")
    assert not fixture.is_demo
    with pytest.raises(ValueError):
        password_for(fixture, credentials=DemoCredentials(source="file", password=FAKE_PASSWORD))


def test_arbitrary_email_rejected() -> None:
    with pytest.raises(ValueError):
        password_for("someone@attacker.example",
                     credentials=DemoCredentials(source="file", password=FAKE_PASSWORD))


# --------------------------------------------------------------------------- #
# Credentials never persist into findings/evidence
# --------------------------------------------------------------------------- #

def _ctx(tmp_path: Path) -> RunContext:
    return RunContext(
        env=ENV,
        env_name="local",
        git_sha="abc1234",
        credentials=DemoCredentials(source="file", password=FAKE_PASSWORD),
        store=FindingStore(tmp_path / "findings"),
        evidence=EvidenceStore(tmp_path / "evidence"),
        registry=EvidenceRegistry(EvidenceStore(tmp_path / "evidence2")),
    )


def test_credentials_not_persisted_into_findings(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    finding = ctx.emit(
        "AUTH", "P1", "login probe",
        description=f"used password {FAKE_PASSWORD} for login attempt",
        actual=f"password={FAKE_PASSWORD}",
    )
    assert FAKE_PASSWORD not in finding.description
    assert FAKE_PASSWORD not in finding.actual
    assert "[REDACTED]" in finding.description
    ctx.finish()
    for store_dir in (tmp_path / "findings").rglob("*.jsonl"):
        assert FAKE_PASSWORD not in store_dir.read_text(encoding="utf-8")


def test_credentials_not_persisted_into_evidence(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    path = ctx.api_evidence("owner", "probe", f"{{'password': '{FAKE_PASSWORD}'}}")
    persisted = path.read_text(encoding="utf-8")
    assert FAKE_PASSWORD not in persisted
    assert "[REDACTED]" in persisted


def test_find_credentials_file_finds_repo_root(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    _write(tmp_path)
    found = find_credentials_file(start=tmp_path)
    assert found == tmp_path / ".local-demo-credentials.md"


# --------------------------------------------------------------------------- #
# Identity model + login-guard regression (unchanged ground truth)
# --------------------------------------------------------------------------- #

def test_identity_model_remains_1192_1183() -> None:
    from qa_harness.identities.loader import generate_full_population
    population = generate_full_population()
    demo = [i for i in population if i.is_demo]
    assert len(population) == 1192
    assert len(demo) == 1183


def test_demo_login_guard_remains_functional() -> None:
    from qa_harness.browser.auth.session import demo_login
    from qa_harness.identities.loader import generate_full_population
    audit = next(i for i in generate_full_population() if i.persona == "audit")
    with pytest.raises(ValueError):
        demo_login("http://127.0.0.1:54325", audit, FAKE_PASSWORD)
