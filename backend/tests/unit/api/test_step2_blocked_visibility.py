"""Step 2 / WS-H (F-11) — blocked-job visibility on the customer payload.

The customer processing surface must be able to distinguish a job that is
*blocked awaiting human review* from one that completed, and must receive the
truthful block reason. These tests lock that contract on the payload builder
used by `GET /api/v3/processing/jobs` (the org-scoped customer surface).
"""
from __future__ import annotations

from api.v3_automatic_processing import _job_payload
from domain.automatic_processing import AutomaticProcessingJob

_REASON = (
    "extraction completeness 0.33 below 0.50 threshold — unresolved: quantity, unit"
)


def _job(**overrides):
    base = dict(
        id="job-1",
        organization_id="11111111-1111-4111-8111-111111111111",
        file_name="color_07_water.pdf",
        file_url="uploads/org-1/color_07_water.pdf",
        file_type="PDF",
        stage="blocked",
        status="manual_review",
        manual_review_reason=_REASON,
        attempt_count=0,
    )
    base.update(overrides)
    return AutomaticProcessingJob(**base)


def test_blocked_job_payload_exposes_the_reason_and_a_human_label():
    payload = _job_payload(_job())

    assert payload["stage"] == "blocked"
    assert payload["status"] == "manual_review"
    assert payload["manual_review_reason"] == _REASON
    # `unresolved: quantity, unit` is the truthful, customer-safe diagnostic
    assert "unresolved: quantity, unit" in payload["manual_review_reason"]
    # the customer receives a label, not a raw status code
    assert payload["stage_label"]
    assert payload["stage_label"] != payload["stage"]


def test_completed_job_payload_is_distinguishable_from_blocked():
    payload = _job_payload(
        _job(stage="completed", status="completed", manual_review_reason=None)
    )

    assert payload["stage"] == "completed"
    assert payload["manual_review_reason"] is None
