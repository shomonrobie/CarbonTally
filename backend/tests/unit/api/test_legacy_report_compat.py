"""Step 2C / POD-5 — legacy report-endpoint compatibility layer.

Evidence (current release): the live legacy report UI in `frontend/src/App.js`
posts to `/api/generate-enhanced-report` and `/api/generate-sustainability-report`,
while only `/api/reports/generate-enhanced-report` is mounted — the live UI was
therefore calling two 404s. PO decision C: a minimal compatibility layer that
delegates to the existing implementation, preserves authorization/tenant
isolation and response semantics, and documents deprecation — no new report
subsystem, no duplicated business logic.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from routes import legacy_reports
from report_generator import EnhancedReportRequest


def _request(organization_id: str, report_type: str = "SECR") -> EnhancedReportRequest:
    return EnhancedReportRequest(
        organization_id=organization_id,
        reporting_year=2024,
        report_type=report_type,
        include_narratives=True,
    )


def _response():
    return SimpleNamespace(headers={})


@pytest.mark.asyncio
async def test_both_legacy_paths_delegate_to_the_existing_implementation(monkeypatch):
    calls = []

    async def fake_impl(request, current_user):
        calls.append((request.organization_id, request.report_type, current_user.user_id))
        return {"status": "ok", "report": "secr"}

    monkeypatch.setattr(legacy_reports.legacy_reports, "generate_enhanced_sustainability_report", fake_impl)
    user = SimpleNamespace(user_id="u-1", organization_id="org-1")

    for handler in (
        legacy_reports.compat_generate_enhanced_report,
        legacy_reports.compat_generate_sustainability_report,
    ):
        response = _response()
        result = await handler(_request("org-1"), response, user)
        assert result == {"status": "ok", "report": "secr"}
        # deprecation signalling is added without changing the body semantics
        assert response.headers["Deprecation"] == "true"
        assert "/api/v3/reports" in response.headers["Link"]

    assert calls == [("org-1", "SECR", "u-1"), ("org-1", "SECR", "u-1")]


@pytest.mark.asyncio
async def test_cross_tenant_report_requests_are_denied(monkeypatch):
    called = []

    async def fake_impl(request, current_user):  # pragma: no cover - must not run
        called.append(request.organization_id)
        return {"status": "ok"}

    monkeypatch.setattr(legacy_reports.legacy_reports, "generate_enhanced_sustainability_report", fake_impl)
    user = SimpleNamespace(user_id="u-1", organization_id="org-1")

    with pytest.raises(HTTPException) as denied:
        await legacy_reports.compat_generate_enhanced_report(
            _request("org-other"), _response(), user
        )
    assert denied.value.status_code == 403
    assert "access" in str(denied.value.detail).lower()
    assert called == []  # the generator was never reached


@pytest.mark.asyncio
async def test_a_caller_without_an_organisation_is_refused(monkeypatch):
    monkeypatch.setattr(
        legacy_reports.legacy_reports,
        "generate_enhanced_sustainability_report",
        lambda *a, **k: None,
    )
    user = SimpleNamespace(user_id="u-1", organization_id=None)

    with pytest.raises(HTTPException) as denied:
        await legacy_reports.compat_generate_sustainability_report(
            _request("org-1"), _response(), user
        )
    assert denied.value.status_code == 403


@pytest.mark.asyncio
async def test_unsupported_report_types_keep_the_existing_truthful_error(monkeypatch):
    """The auditor-Excel option has no implementation: it must not be faked."""
    async def raising_impl(request, current_user):
        raise HTTPException(status_code=400, detail=f"Unsupported report type: {request.report_type}")

    monkeypatch.setattr(legacy_reports.legacy_reports, "generate_enhanced_sustainability_report", raising_impl)
    user = SimpleNamespace(user_id="u-1", organization_id="org-1")

    with pytest.raises(HTTPException) as unsupported:
        await legacy_reports.compat_generate_sustainability_report(
            _request("org-1", "AUDITOR_EXCEL"), _response(), user
        )
    assert unsupported.value.status_code == 400
    assert "AUDITOR_EXCEL" in unsupported.value.detail
