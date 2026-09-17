"""Step 2C / POD-2 — legacy manual-review compatibility adapter.

The retired pre-V3 `queue_for_manual_review()` targeted a separate manual-review
queue that no longer exists. PO decision C: do not resurrect that architecture —
provide a **thin compatibility adapter** into the current V3 manual-review
workflow, preserving tenant/organisation authorization, auditability and existing
queue semantics, without creating a second queue.

These tests exercise the translation contract directly (the registration step is
injected, so no storage/DB is touched).
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from api.v3_documents import (
    LegacyManualReviewError,
    legacy_queue_for_manual_review,
)


class _FakeManualExtraction:
    def __init__(self, item=None, raises=False):
        self._item = item
        self._raises = raises
        self.calls = 0

    async def get_item_by_file_id(self, file_id):
        self.calls += 1
        if self._raises:
            raise RuntimeError("lookup unavailable")
        return self._item


def _repos(manual_extraction=None):
    return SimpleNamespace(manual_extraction=manual_extraction or _FakeManualExtraction())


def _record():
    return SimpleNamespace(id="doc-1")


@pytest.mark.asyncio
async def test_adapter_translates_the_legacy_request_into_the_v3_pipeline():
    calls = {}

    async def fake_register(**kwargs):
        calls.update(kwargs)
        return _record()

    result = await legacy_queue_for_manual_review(
        organization_id="org-1",
        filename="messy_fuel_card.csv",
        content=b"Transaction Date,Fuel Type,Volume (L)\n01/10/2023,Diesel,53.8\n",
        content_type="text/csv",
        data_type="fuel",
        uploaded_by="user-9",
        repos=_repos(_FakeManualExtraction(SimpleNamespace(id="item-7"))),
        auto_result={"status": "error", "confidence": 0.1, "missing_fields": ["quantity"]},
        register=fake_register,
    )

    # the legacy request reaches the CURRENT pipeline with tenant context intact
    assert calls["organization_id"] == "org-1"
    assert calls["uploaded_by"] == "user-9"
    assert calls["data_type"] == "fuel"
    assert calls["file_type"] == "SPREADSHEET"
    assert calls["mime_type"] == "text/csv"
    assert calls["content"].startswith(b"Transaction Date")
    # compatibility mapping is returned, not fabricated
    assert result["review_id"] == "doc-1"
    assert result["document_id"] == "doc-1"
    assert result["item_id"] == "item-7"
    assert result["workflow"] == "v3_manual_review"
    assert isinstance(result["issues"], list)
    assert isinstance(result["summary"], dict)


@pytest.mark.asyncio
async def test_adapter_returns_a_truthful_error_when_the_legacy_request_is_unsafe():
    async def must_not_run(**kwargs):  # pragma: no cover - asserted below
        raise AssertionError("the pipeline must not run for an unsafe legacy request")

    with pytest.raises(LegacyManualReviewError) as missing_org:
        await legacy_queue_for_manual_review(
            organization_id=None,
            filename="a.csv",
            content=b"x",
            content_type="text/csv",
            uploaded_by="u",
            repos=_repos(),
            register=must_not_run,
        )
    assert "organisation" in str(missing_org.value)

    with pytest.raises(LegacyManualReviewError) as missing_bytes:
        await legacy_queue_for_manual_review(
            organization_id="org-1",
            filename="a.csv",
            content=None,
            content_type="text/csv",
            uploaded_by="u",
            repos=_repos(),
            register=must_not_run,
        )
    assert "bytes" in str(missing_bytes.value)

    with pytest.raises(LegacyManualReviewError) as missing_name:
        await legacy_queue_for_manual_review(
            organization_id="org-1",
            filename="",
            content=b"x",
            content_type="text/csv",
            uploaded_by="u",
            repos=_repos(),
            register=must_not_run,
        )
    assert "file name" in str(missing_name.value)


@pytest.mark.asyncio
async def test_item_lookup_failure_does_not_fail_the_translation():
    async def fake_register(**_kwargs):
        return _record()

    result = await legacy_queue_for_manual_review(
        organization_id="org-1",
        filename="a.csv",
        content=b"x",
        content_type="text/csv",
        uploaded_by="u",
        repos=_repos(_FakeManualExtraction(raises=True)),
        register=fake_register,
    )

    assert result["item_id"] is None      # unresolved, never invented
    assert result["review_id"] == "doc-1"


@pytest.mark.asyncio
async def test_adapter_sends_one_registration_per_request():
    """Legacy call semantics are preserved: one review record per request."""
    count = {"n": 0}

    async def fake_register(**_kwargs):
        count["n"] += 1
        return _record()

    for _ in range(3):
        await legacy_queue_for_manual_review(
            organization_id="org-1",
            filename="a.csv",
            content=b"x",
            content_type="text/csv",
            uploaded_by="u",
            repos=_repos(),
            register=fake_register,
        )
    assert count["n"] == 3
