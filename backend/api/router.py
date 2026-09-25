"""Central v2.1 API router + app factory (prep-pack Phase 10.1).

Routing stays thin: this module assembles the single router from the endpoint
modules and maps the existing error hierarchy (``core.exceptions``) onto
consistent HTTP responses. It contains no business logic.

Consistent error contract (Phase 10 scope):

* :class:`core.exceptions.CarbonTallyError` → its declared ``http_status`` with
  the machine-readable ``code`` and optional ``details``.
* ``HTTPException`` (auth/RBAC/404s) → the same envelope with ``code`` derived
  from the status (``UNAUTHORIZED``/``FORBIDDEN``/``NOT_FOUND``/...).
* Pydantic validation errors → ``422 VALIDATION_ERROR`` with field details.
* Unhandled exceptions → ``500 INTERNAL_ERROR`` with a generic message; the full
  traceback is logged server-side and never echoed to the client.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.admin_aliases import router as aliases_router
from api.admin_audit import router as audit_router
from api.admin_entities import router as admin_entities_router
from api.admin_imports import router as imports_router
from api.admin_providers import router as providers_router
from api.business import router as business_router
from api.contracts import ErrorDetail, ErrorResponse, HealthResponse
from services import api_metrics
from api.customer_factors import router as customer_factors_router
from api.issues import router as issues_router
from api.v3_documents import router as v3_documents_router
from api.v3_exports import router as v3_exports_router
from api.v3_notifications import router as v3_notifications_router
from api.v3_organizations import router as v3_organizations_router
from api.v3_commercial import router as v3_commercial_router
from api.v3_billing import router as v3_billing_router
from api.v3_review import router as v3_review_router
from api.v3_verifications import router as v3_verifications_router
from api.v3_consultants import router as v3_consultants_router
from api.v3_manual_extraction import router as v3_manual_extraction_router
from api.v3_operations import router as v3_operations_router
from api.v3_processing import router as v3_processing_router
from api.v3_qc import router as v3_qc_router
from api.v3_accounting_context import router as v3_accounting_context_router
from api.v3_suppliers import router as v3_suppliers_router
from api.v3_scope2 import router as v3_scope2_router
from api.v3_scope3 import router as v3_scope3_router
from api.v3_processing_workflow import router as v3_processing_workflow_router
from api.v3_automatic_processing import router as v3_automatic_processing_router
from api.v3_pe import router as v3_pe_router
from api.v3_search import router as v3_search_router
from api.v3_settings import router as v3_settings_router
from api.v3_emissions import router as v3_emissions_router
from api.v3_reports import router as v3_reports_router
from api.v3_disclosure import router as v3_disclosure_router
from api.v3_discovery import router as v3_discovery_router
from api.v3_messaging import router as v3_messaging_router
from api.manual_processing_admin import router as manual_processing_admin_router
from api.v3_vehicles import router as v3_vehicles_router
from api.v3_whitelabel import router as v3_whitelabel_router
from api.v3_reporting import router as v3_reporting_router
from api.v3_context import router as v3_context_router
from api.v3_health import router as v3_health_router
from api.v3_activity_clarifications import router as v3_activity_clarifications_router
from api.v3_evidence import router as v3_evidence_router
from api.v3_insight import router as v3_insight_router
from api.v3_insight_tools import router as v3_insight_tools_router
from api.v3_insight_interactions import router as v3_insight_interactions_router
from api.middleware import RequestContextMiddleware
from core.exceptions import CarbonTallyError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["CarbonTally v2.1"])


# ---------------------------------------------------------------------------
# Health / liveness (no database access)
# ---------------------------------------------------------------------------


@router.get("/api/v2/health", response_model=HealthResponse, tags=["System"])
async def health(request: Request) -> HealthResponse:
    """Liveness check. Never touches the database or any business engine."""
    context = getattr(request.state, "request_context", None)
    request_id = context.correlation_id if context is not None else ""
    return HealthResponse(request_id=request_id)


# ---------------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------------

_STATUS_CODES_TO_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
    500: "INTERNAL_ERROR",
}


def _request_id(request: Request) -> str:
    context = getattr(request.state, "request_context", None)
    return context.correlation_id if context is not None else ""


async def carbon_tally_error_handler(request: Request, exc: CarbonTallyError) -> JSONResponse:
    """Map every engine/domain error through its declared code + HTTP status."""
    payload = ErrorResponse(
        error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details or {}),
        request_id=_request_id(request),
    )
    return JSONResponse(status_code=exc.http_status, content=payload.model_dump())


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Preserve HTTPException semantics (incl. auth WWW-Authenticate headers).

    RV-1 — forward ``exc.headers`` verbatim so a challenge attached by the auth
    dependency (``auth.get_current_user`` → ``WWW-Authenticate: Bearer``)
    reaches the wire. If the exception carries no headers, keep the previous
    behaviour: emit a standard Bearer challenge for 401, no headers otherwise.
    """
    code = _STATUS_CODES_TO_CODES.get(exc.status_code, f"HTTP_{exc.status_code}")
    payload = ErrorResponse(
        error=ErrorDetail(code=code, message=str(exc.detail), details={}),
        request_id=_request_id(request),
    )
    if exc.headers:
        headers = dict(exc.headers)
    elif exc.status_code == 401:
        headers = {"WWW-Authenticate": "Bearer"}
    else:
        headers = None
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump(), headers=headers)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic 422s become the same envelope with per-field details.

    Error payloads are recursively sanitised because pydantic v2 errors carry
    non-JSON values in ``ctx`` (e.g. a ``ValueError`` raised by a model
    validator); the envelope must never crash on those.
    """
    errors = [_jsonable_error(e) for e in exc.errors()]
    payload = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="request validation failed",
            details={"errors": errors},
        ),
        request_id=_request_id(request),
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


def _jsonable_error(value: Any) -> Any:
    """Recursively convert a pydantic error fragment into JSON-safe primitives."""
    if isinstance(value, dict):
        return {str(key): _jsonable_error(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable_error(item) for item in value]
    if isinstance(value, Exception):
        return str(value)
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    return str(value)


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Never leak stack traces/DB internals; log the real error server-side."""
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    payload = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_ERROR",
            message="Internal server error",
            details={},
        ),
        request_id=_request_id(request),
    )
    return JSONResponse(status_code=500, content=payload.model_dump())


# ---------------------------------------------------------------------------
# Router assembly
# ---------------------------------------------------------------------------

router.include_router(business_router)
router.include_router(imports_router)
router.include_router(providers_router)
router.include_router(audit_router)
router.include_router(aliases_router)
router.include_router(admin_entities_router)
router.include_router(customer_factors_router)
router.include_router(issues_router)
router.include_router(v3_organizations_router)
router.include_router(v3_commercial_router)
router.include_router(v3_billing_router)
router.include_router(v3_documents_router)
router.include_router(v3_review_router)
router.include_router(v3_verifications_router)
router.include_router(v3_notifications_router)
router.include_router(v3_exports_router)
router.include_router(v3_consultants_router)
router.include_router(v3_processing_router)
router.include_router(v3_processing_workflow_router)
router.include_router(v3_automatic_processing_router)
router.include_router(v3_pe_router)
router.include_router(v3_search_router)
router.include_router(v3_settings_router)
router.include_router(v3_emissions_router)
router.include_router(v3_reports_router)
router.include_router(v3_disclosure_router)
router.include_router(v3_manual_extraction_router)
router.include_router(v3_qc_router)
router.include_router(v3_suppliers_router)
router.include_router(v3_scope2_router)
router.include_router(v3_scope3_router)
router.include_router(v3_operations_router)
router.include_router(v3_discovery_router)
router.include_router(v3_messaging_router)
# FIN-06 — CarbonTally Admin Manual Processing governance (admin-gated).
router.include_router(manual_processing_admin_router)
router.include_router(v3_vehicles_router)
router.include_router(v3_whitelabel_router)
router.include_router(v3_reporting_router)
router.include_router(v3_context_router)
# P17-IMPLEMENT-02 — the accounting context surface (acting-for resolution,
# persisted attribution, CAMS dimension validation). Registered after the
# existing context resolver so /me/context behaviour is unchanged.
router.include_router(v3_accounting_context_router)
router.include_router(v3_health_router)
# F-039-1 — authorised activity clarification (F-048-2 / 052).
router.include_router(v3_activity_clarifications_router)
# Phase 8 I1 (CT-P8-I1-INSIGHT-PERSISTENCE-20260921-002) — CarbonTally Insight
# Layer-1 persistent conversation foundation (D2 §24.2). Persistence only: no
# LLM, no tools, no answer generation (I3–I8 remain unauthorized).
router.include_router(v3_evidence_router)
router.include_router(v3_insight_router)
# Phase 8 I3 (PO I3 Tool Catalogue Ratification 2026-09-21) — the four
# ratified controlled read-only tools (registry + deterministic execution).
router.include_router(v3_insight_tools_router)
# Phase 8 I4 — Layer-2 interaction orchestration API (PO I4 authorization).
router.include_router(v3_insight_interactions_router)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Build the v2.1 API application (Uvicorn entry point: ``main_v2.py``)."""
    app = FastAPI(
        title="CarbonTally Backend v2.1 API",
        description=(
            "API boundary around the CarbonTally v2.1 business engines and "
            "repositories. Admin endpoints are staff/admin-only."
        ),
        version="1.0.0",
        docs_url="/api/v2/docs",
        openapi_url="/api/v2/openapi.json",
    )
    app.add_middleware(RequestContextMiddleware)
    # Phase 8-X X7 — API runtime metrics (PO decisions X7-D1..X7-D7). One
    # instrumented-request observation per /api/v3/** call; the accumulated
    # slot map is flushed into the single persisted series row at most every
    # 5 minutes. Best-effort: it can never break a request.
    @app.middleware("http")
    async def api_runtime_metrics(request, call_next):  # type: ignore[no-untyped-def]
        service = api_metrics.get_service() or getattr(
            request.app.state, "api_metrics", None
        )
        if service is None:
            return await call_next(request)
        started = api_metrics.monotonic_ms()
        try:
            response = await call_next(request)
        except Exception:
            # A failed request is still observed (5xx), then re-raised unchanged.
            try:
                await service.observe_request(
                    request,
                    status_code=500,
                    duration_ms=api_metrics.monotonic_ms() - started,
                )
            except Exception:  # noqa: BLE001
                pass
            raise
        try:
            await service.observe_request(
                request,
                status_code=int(getattr(response, "status_code", 500)),
                duration_ms=api_metrics.monotonic_ms() - started,
            )
        except Exception:  # noqa: BLE001
            pass
        return response

    app.include_router(router)

    app.add_exception_handler(CarbonTallyError, carbon_tally_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    return app

