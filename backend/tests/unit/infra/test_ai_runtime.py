"""Unit tests for infra.ai_runtime attribution facts (WS4 Gate 5, task T2).

Covers the host-derived :func:`provider_label` helper and the secret-free
:func:`configured_ai_attribution` facts. No database, no network, no secrets.
"""
from __future__ import annotations

from collections.abc import Iterator

import pytest

from infra.ai_runtime import configured_ai_attribution, provider_label

#: AI-extraction identity env vars, neutralised (blank = unset) per test.
_AI_ENV_KEYS = (
    "CARBONTALLY_AI_BASE_URL",
    "CARBONTALLY_AI_API_KEY",
    "CARBONTALLY_AI_MODEL",
)

_ALL_NONE = {"provider": None, "model": None, "model_version": None}


@pytest.fixture(autouse=True)
def _neutral_ai_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Blank every AI-extraction env var before each test."""
    for key in _AI_ENV_KEYS:
        monkeypatch.setenv(key, "")
    yield


class TestProviderLabel:
    def test_none_and_blank_return_none(self) -> None:
        assert provider_label(None) is None
        assert provider_label("") is None
        assert provider_label("   ") is None

    def test_known_openai_host(self) -> None:
        assert provider_label("https://api.openai.com/v1") == "openai"

    def test_known_anthropic_host(self) -> None:
        assert provider_label("https://api.anthropic.com/v1") == "anthropic"

    def test_known_openrouter_host(self) -> None:
        assert provider_label("https://openrouter.ai/api/v1") == "openrouter"

    def test_subdomain_of_known_domain(self) -> None:
        assert provider_label("https://eu.openai.com/v1") == "openai"

    def test_scheme_less_input_is_accepted(self) -> None:
        assert provider_label("api.anthropic.com/v1") == "anthropic"

    def test_port_is_ignored(self) -> None:
        assert provider_label("https://api.openai.com:8443/v1") == "openai"

    def test_unknown_host_falls_back_to_hostname(self) -> None:
        # Truthful host-derived fallback, never a fabricated canonical name.
        assert (
            provider_label("https://llm-gw.example.test/v1")
            == "llm-gw.example.test"
        )


class TestConfiguredAiAttribution:
    def test_not_configured_returns_all_none(self) -> None:
        assert configured_ai_attribution() == _ALL_NONE

    def test_model_only_is_not_attribution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "gpt-test")
        assert configured_ai_attribution() == _ALL_NONE

    def test_base_url_only_is_not_attribution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.openai.com/v1")
        assert configured_ai_attribution() == _ALL_NONE

    def test_configured_returns_identity_without_secret(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "gpt-test-1")
        monkeypatch.setenv("CARBONTALLY_AI_API_KEY", "sk-super-secret-value")
        facts = configured_ai_attribution()
        assert facts == {
            "provider": "openai",
            "model": "gpt-test-1",
            "model_version": None,
        }
        serialized = str(facts)
        assert "sk-super-secret-value" not in serialized
        assert "api_key" not in facts

    def test_unknown_gateway_provider_label_is_hostname(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(
            "CARBONTALLY_AI_BASE_URL", "https://llm-gw.carbontally.test/v1"
        )
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "local-model")
        facts = configured_ai_attribution()
        assert facts["provider"] == "llm-gw.carbontally.test"
        assert facts["model"] == "local-model"
        assert facts["model_version"] is None

    def test_explicit_truthfully_known_model_version(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://api.anthropic.com/v1")
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "claude-test")
        facts = configured_ai_attribution(model_version="2026-09-05")
        assert facts["provider"] == "anthropic"
        assert facts["model"] == "claude-test"
        assert facts["model_version"] == "2026-09-05"

    def test_blank_model_version_is_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CARBONTALLY_AI_BASE_URL", "https://openrouter.ai/api/v1")
        monkeypatch.setenv("CARBONTALLY_AI_MODEL", "openrouter-test")
        facts = configured_ai_attribution(model_version="   ")
        assert facts["provider"] == "openrouter"
        assert facts["model_version"] is None
