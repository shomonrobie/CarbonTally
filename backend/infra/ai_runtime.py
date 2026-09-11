"""Optional AI-extraction runtime configuration (Phase 2).

The durable automatic pipeline runs deterministically when no LLM provider is
configured (the default). When all three variables are set the worker builds a
candidate AI extraction engine:

* ``CARBONTALLY_AI_BASE_URL`` — OpenAI/Anthropic-compatible ``…/v1`` root.
* ``CARBONTALLY_AI_API_KEY`` — Bearer token (environment only; never stored in
  the database, never logged, never exposed to the frontend).
* ``CARBONTALLY_AI_MODEL`` — Model identifier sent in the payload.

No credentials are ever written to the database or logs by this module.

WS4 Gate 5 (Automated-Extraction Machine Provenance), task T2 — runtime
attribution facts:

* :func:`provider_label` truthfully derives a provider label from the endpoint
  host (well-known endpoints map to their canonical short label; any other host
  is returned as its hostname — never a fabricated canonical name).
* :func:`configured_ai_attribution` exposes the configured provider/model/version
  facts for durable provenance, reading only the identity environment variables
  (never the API key).
"""
from __future__ import annotations

import os
from typing import Optional
from urllib.parse import urlparse

#: Well-known OpenAI/Anthropic-compatible endpoint domains -> canonical label.
#: Only genuinely well-known domains are mapped; anything else falls back to its
#: hostname so the label stays host-derived and truthful (design risk R1).
_KNOWN_PROVIDER_DOMAINS: tuple[tuple[str, str], ...] = (
    ("openai.com", "openai"),
    ("anthropic.com", "anthropic"),
    ("openrouter.ai", "openrouter"),
)

#: Column length of ``document_processing_queue.automation_provider``.
_MAX_PROVIDER_LABEL_LENGTH = 120


def configured_ai_extraction_engine():
    """Return a candidate AI extraction engine when configured, else ``None``.

    Failures (malformed config, import errors) return ``None`` so the durable
    worker always falls back to the deterministic pipeline.
    """
    base_url = (os.getenv("CARBONTALLY_AI_BASE_URL") or "").strip()
    api_key = os.getenv("CARBONTALLY_AI_API_KEY") or ""
    model = (os.getenv("CARBONTALLY_AI_MODEL") or "").strip()
    if not (base_url and api_key and model):
        return None
    try:
        from infra.llm_client import LLMClient
        from services.ai_document_extraction import AIDocumentExtractionEngine
    except Exception:  # noqa: BLE001 - config failures never break the worker
        return None
    try:
        client = LLMClient(base_url=base_url, api_key=api_key, model=model)
    except ValueError:
        return None
    return AIDocumentExtractionEngine(client)


def _host_of(base_url: Optional[str]) -> Optional[str]:
    """Return the lower-cased hostname of a base URL (or ``None``)."""
    if not base_url:
        return None
    raw = base_url.strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = "https://" + raw
    try:
        host = (urlparse(raw).hostname or "").strip().lower()
    except ValueError:
        return None
    return host or None


def provider_label(base_url: Optional[str]) -> Optional[str]:
    """Truthfully derive a provider label from an endpoint base URL host.

    Well-known OpenAI/Anthropic-compatible endpoints map to their canonical short
    label (e.g. ``https://api.openai.com/v1`` -> ``openai``,
    ``https://api.anthropic.com/v1`` -> ``anthropic``,
    ``https://openrouter.ai/api/v1`` -> ``openrouter``). Any other host — custom
    gateway, proxy, self-hosted endpoint — returns the endpoint hostname itself,
    so the label is always host-derived and never a fabricated canonical name
    (WS4 Gate 5 design, risk R1). Returns ``None`` for missing/blank/malformed
    input. Never reads credentials.
    """
    host = _host_of(base_url)
    if host is None:
        return None
    for domain, label in _KNOWN_PROVIDER_DOMAINS:
        if host == domain or host.endswith("." + domain):
            return label
    return host[:_MAX_PROVIDER_LABEL_LENGTH]


def configured_ai_attribution(
    model_version: Optional[str] = None,
) -> dict[str, Optional[str]]:
    """Return the configured AI-extraction runtime attribution facts.

    Provider and model identity are read from the same environment variables that
    gate the optional AI extraction engine (``CARBONTALLY_AI_BASE_URL`` /
    ``CARBONTALLY_AI_MODEL``). The API key is intentionally never read, so these
    facts cannot leak it. ``model_version`` is ``None`` unless a version is
    truthfully known (providers do not reliably expose one today) — it is never
    fabricated or guessed from the model id (WS4 Gate 5 design, risk R2).

    A non-None result means the runtime is *configured*; it does not by itself
    mean an AI run occurred — the worker decides when an AI pass actually
    contributes to a persisted extraction (task T3).
    """
    base_url = (os.getenv("CARBONTALLY_AI_BASE_URL") or "").strip()
    model = (os.getenv("CARBONTALLY_AI_MODEL") or "").strip()
    if not (base_url and model):
        return {"provider": None, "model": None, "model_version": None}
    return {
        "provider": provider_label(base_url),
        "model": model,
        "model_version": (model_version or "").strip() or None,
    }
