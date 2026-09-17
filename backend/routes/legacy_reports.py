"""
Step 2C / POD-5 — legacy report-endpoint compatibility layer.

The live legacy report UI (``frontend/src/App.js``) posts to
``{API_URL}/api/generate-enhanced-report`` and
``{API_URL}/api/generate-sustainability-report``, but the only mounted
implementation is ``POST /api/reports/generate-enhanced-report`` — so the legacy
Report menu has been calling two **404s**.

PO decision C: provide a **minimal compatibility layer**, not a new reporting
subsystem and not a resurrected legacy architecture. These two paths therefore
delegate to the single existing implementation
(``routes.reports.generate_enhanced_sustainability_report``); no business logic is
duplicated, and the response body semantics are the ones the live caller already
expects.

Two things the delegating routes add deliberately:

* **tenant isolation** — the legacy handler takes ``organization_id`` from the
  request body and would otherwise serve another organisation's report to any
  authenticated member. The compatibility layer enforces
  ``organization_id == caller's organisation`` (403 otherwise) before delegating;
* **deprecation signalling** — ``Deprecation``/``Link`` headers point callers at
  the current V3 reporting surface (``/api/v3/reports``).

``report_type`` support is unchanged: SECR/CSRD/ISSB are served; anything else
(including the legacy ``AUDITOR_EXCEL`` workbook export, which has no
implementation in this release) keeps the existing truthful 400 rather than
fabricating a file.
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status

from auth import AuthUser, require_org_member
from report_generator import EnhancedReportRequest
from routes import reports as legacy_reports

router = APIRouter(prefix="/api", tags=["legacy-report-compat"])

#: Current V3 reporting surface the compatibility paths point callers to.
V3_REPORTS_PATH = "/api/v3/reports"


def _authorize_tenant(current_user: AuthUser, organization_id: str) -> None:
    """Enforce that the requested report belongs to the caller's organisation."""
    caller_org = getattr(current_user, "organization_id", None)
    if not caller_org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No organisation context for this account.",
        )
    if str(organization_id) != str(caller_org):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to reports for this organisation.",
        )


def _mark_deprecated(response: Response) -> None:
    """Signal deprecation of the legacy compatibility path (RFC 8594/Link)."""
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = f'<{V3_REPORTS_PATH}>; rel="successor-version"'


@router.post("/generate-enhanced-report")
async def compat_generate_enhanced_report(
    request: EnhancedReportRequest,
    response: Response,
    current_user: AuthUser = Depends(require_org_member()),
):
    """Compatibility alias for the legacy ``/api/generate-enhanced-report`` path."""
    _authorize_tenant(current_user, request.organization_id)
    _mark_deprecated(response)
    return await legacy_reports.generate_enhanced_sustainability_report(
        request, current_user
    )


@router.post("/generate-sustainability-report")
async def compat_generate_sustainability_report(
    request: EnhancedReportRequest,
    response: Response,
    current_user: AuthUser = Depends(require_org_member()),
):
    """Compatibility alias for the legacy ``/api/generate-sustainability-report``.

    The live legacy caller uses this path for its ``AUDITOR_EXCEL`` option. No
    auditor-workbook generator exists in this release, so the request is passed to
    the same implementation, which answers with its existing truthful
    ``400 Unsupported report type`` — the compatibility layer never fabricates a
    report file. Reinstating an auditor Excel export is a separate product
    decision, not something this adapter may invent.
    """
    _authorize_tenant(current_user, request.organization_id)
    _mark_deprecated(response)
    return await legacy_reports.generate_enhanced_sustainability_report(
        request, current_user
    )
