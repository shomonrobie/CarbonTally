"""Harness self-tests: secret redaction (spec §37, §35)."""

from __future__ import annotations

import json

from qa_harness.core.secrets import Redactor, default_redactor, describe_available_secrets, redact

JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0In0.signature1234567890"


def test_redacts_jwt() -> None:
    text = f"Authorization: Bearer {JWT}"
    out = redact(text)
    assert JWT not in out
    assert "[REDACTED]" in out


def test_redacts_api_key_shape() -> None:
    out = redact("api_key = sk-abcdefghijklmnopqrstuvwxyz123456")
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in out
    assert "[REDACTED]" in out


def test_redacts_signed_url_token() -> None:
    out = redact("https://storage.local/file.pdf?token=abcdefgh12345678&x=1")
    assert "abcdefgh12345678" not in out


def test_redacts_env_value(monkeypatch) -> None:
    monkeypatch.setenv("CARBON_TALLY_DEMO_PASSWORD", "S3cr3t-Demo-Pass!-long-enough")
    redactor = Redactor()
    out = redactor.redact("password is S3cr3t-Demo-Pass!-long-enough here")
    assert "S3cr3t-Demo-Pass!-long-enough" not in out


def test_redact_json_safe() -> None:
    payload = {
        "url": f"https://x?a=1&signature=deadbeefdeadbeef",
        "nested": {"token": JWT},
        "list": ["ok", f"Bearer {JWT}"],
        "number": 42,
    }
    safe = default_redactor.redact_json_safe(payload)
    dumped = json.dumps(safe)
    assert JWT not in dumped
    assert "deadbeefdeadbeef" not in dumped
    assert "ok" in dumped


def test_describe_available_secrets_returns_names_only(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "sb_secret_super_secret_value_123")
    names = describe_available_secrets()
    assert "SUPABASE_SERVICE_KEY" in names
    assert all("secret" not in n.lower() or n == "SUPABASE_SERVICE_KEY" for n in names)
    joined = " ".join(names)
    assert "sb_secret_super_secret_value_123" not in joined


def test_no_short_value_mangling() -> None:
    # Ordinary prose must survive redaction.
    out = redact("the customer id is 42 and the org name is Quayside")
    assert "Quayside" in out
