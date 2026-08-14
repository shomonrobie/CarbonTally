"""Request context middleware (prep-pack Phase 10.1, §19 Security Model).

Only the middleware required by the approved Phase 10 architecture is added:

* **request/correlation ID** — accept ``X-Request-ID``/``X-Correlation-ID`` or
  generate one; echo it back on both headers and attach it to
  ``request.state.request_context`` so every downstream dependency (engines,
  audit, logs) shares the same correlation id (prep-pack R15).
* **request timing** — ``X-Response-Time-Ms`` header + structured access log.
* **structured request context** — client IP, method, path, status and the
  correlation id are logged together.

No rate limiting, billing, external integrations or other future middleware is
added (explicit Phase 10 scope boundary).
"""
from __future__ import annotations

import time
import uuid
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from core.logging import get_logger

logger = get_logger(__name__)

#: Headers accepted/propagated as the request/correlation id.
_REQUEST_ID_HEADERS = ("X-Request-ID", "X-Correlation-ID")

#: Header echoed back to callers for correlation.
_RESPONSE_ID_HEADERS = ("X-Request-ID", "X-Correlation-ID")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a correlation id + timing context to every request.

    The context is available on ``request.state.request_context``
    (:class:`api.dependencies.RequestContext`) to all route handlers and
    dependencies after the middleware runs.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = self._resolve_correlation_id(request)
        client_ip = self._resolve_client_ip(request)
        started_ns = time.perf_counter_ns()

        # Attach the structured request context before the handler runs so
        # dependencies (audit context, engine audit entries) can reuse it.
        from api.dependencies import RequestContext

        request.state.request_context = RequestContext(
            correlation_id=correlation_id,
            client_ip=client_ip,
            started_at=_utc_now(),
        )

        try:
            response = await call_next(request)
        except Exception:
            self._log("error", request, correlation_id, 500, started_ns)
            raise

        elapsed_ms = (time.perf_counter_ns() - started_ns) / 1_000_000
        for header in _RESPONSE_ID_HEADERS:
            response.headers[header] = correlation_id
        response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.1f}"
        self._log("info", request, correlation_id, response.status_code, started_ns)
        return response

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_correlation_id(request: Request) -> str:
        for header in _REQUEST_ID_HEADERS:
            value = request.headers.get(header)
            if value and value.strip():
                return value.strip()[:128]
        return uuid.uuid4().hex

    @staticmethod
    def _resolve_client_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client is not None:
            return request.client.host or ""
        return ""

    @staticmethod
    def _log(
        level: str,
        request: Request,
        correlation_id: str,
        status_code: int,
        started_ns: int,
    ) -> None:
        elapsed_ms = (time.perf_counter_ns() - started_ns) / 1_000_000
        message = (
            f"{request.method} {request.url.path} -> {status_code} "
            f"[{elapsed_ms:.1f}ms] correlation_id={correlation_id}"
        )
        if level == "error":
            logger.error(message)
        else:
            logger.info(message)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


__all__ = ["RequestContextMiddleware", "_REQUEST_ID_HEADERS"]
