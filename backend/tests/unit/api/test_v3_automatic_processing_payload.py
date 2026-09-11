"""WS4 Gate 5 (task T5) — job payload exposes the typed automation block.

Focused unit tests for ``api.v3_automatic_processing._job_payload``: the durable
machine-attribution block (``automation`` = provider/model/model_version) must be
surfaced beside ``ai_extraction`` for job list/detail consumers, with NULL values
for deterministic-only/legacy jobs.
"""
from __future__ import annotations

from domain.automatic_processing import AutomaticProcessingJob


def _job(**overrides: object) -> AutomaticProcessingJob:
    base = dict(
        id="11111111-1111-4111-8111-111111111111",
        organization_id="22222222-2222-4222-8222-222222222222",
        file_name="invoice.pdf",
        file_url="uploads/org-1/invoice.pdf",
        processing_type="utility",
        status="review",
        stage="review",
        source_item_id="item-1",
        pipeline_version="v3-auto-1.0",
        automation_provider="openai",
        automation_model="gpt-test",
        automation_model_version=None,
    )
    base.update(overrides)
    return AutomaticProcessingJob(**base)


def test_payload_includes_typed_automation_block() -> None:
    from api.v3_automatic_processing import _job_payload

    payload = _job_payload(_job())
    assert payload["automation"] == {
        "provider": "openai",
        "model": "gpt-test",
        "model_version": None,
    }
    # The existing AI-extraction (metadata) surface remains alongside it.
    assert "ai_extraction" in payload
    assert payload["ai_extraction"] is None


def test_payload_automation_null_for_deterministic_or_legacy_job() -> None:
    from api.v3_automatic_processing import _job_payload

    payload = _job_payload(
        _job(
            automation_provider=None,
            automation_model=None,
            automation_model_version=None,
        )
    )
    assert payload["automation"] == {
        "provider": None,
        "model": None,
        "model_version": None,
    }


def test_payload_automation_carries_truthful_model_version() -> None:
    from api.v3_automatic_processing import _job_payload

    payload = _job_payload(
        _job(
            automation_provider="anthropic",
            automation_model="claude-test",
            automation_model_version="2026-09-05",
        )
    )
    assert payload["automation"] == {
        "provider": "anthropic",
        "model": "claude-test",
        "model_version": "2026-09-05",
    }
