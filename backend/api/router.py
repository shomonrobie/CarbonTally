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
from api.customer_factors import router as customer_factors_router
from api.issues import router as issues_router
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
    """Preserve HTTPException semantics (incl. auth WWW-Authenticate headers)."""
    code = _STATUS_CODES_TO_CODES.get(exc.status_code, f"HTTP_{exc.status_code}")
    payload = ErrorResponse(
        error=ErrorDetail(code=code, message=str(exc.detail), details={}),
        request_id=_request_id(request),
    )
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
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
    app.include_router(router)

    app.add_exception_handler(CarbonTallyError, carbon_tally_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    return app

