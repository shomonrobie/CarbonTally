"""V3 health / readiness surface.

Phase 3 — ``GET /api/v3/health/realtime`` verifies that the configured
Supabase API gateway actually routes to the Realtime upstream using the SAME
path the frontend websocket client uses (``/realtime/v1``). It exists because
a gateway returning ``503`` for that route silently disables every Realtime
feature (message delivery, presence, notification bells) while auth/REST keep
working. It is a readiness probe only — it never weakens messaging
authorization.
"""

from __future__ import annotations

import http.client
import os
from urllib.parse import urlsplit

from fastapi import APIRouter

router = APIRouter(prefix="/api/v3", tags=["Health"])

#: Probe timeout for the realtime readiness check (seconds).
_PROBE_TIMEOUT_S = 3


def _realtime_probe_url() -> str:
    """Derive the realtime websocket path exactly as the frontend does.

    ``supabase-js`` derives its realtime URL from ``SUPABASE_URL`` by keeping
    host/port and using the ``/realtime/v1`` path (websocket scheme). We probe
    the same route over plain HTTP with an Upgrade request.
    """
    base = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    if not base:
        return ""
    return base + "/realtime/v1/websocket"


def _probe_realtime() -> dict:
    url = _realtime_probe_url()
    if not url:
        return {
            "status": "unconfigured",
            "url": "",
            "http_status": None,
            "note": "SUPABASE_URL is not configured; realtime readiness cannot be verified.",
        }
    parts = urlsplit(url)
    host = parts.hostname or ""
    port = parts.port or (443 if parts.scheme == "https" else 80)
    secure = parts.scheme == "https"
    path = parts.path or "/"
    connection_cls = http.client.HTTPSConnection if secure else http.client.HTTPConnection
    try:
        conn = connection_cls(host, port, timeout=_PROBE_TIMEOUT_S)
        try:
            conn.request(
                "GET",
                path,
                headers={
                    "Upgrade": "websocket",
                    "Connection": "Upgrade",
                    "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
                    "Sec-WebSocket-Version": "13",
                },
            )
            response = conn.getresponse()
            code = response.status
            response.read()
        finally:
            conn.close()
    except Exception as exc:  # connection refused / reset / timeout
        return {
            "status": "down",
            "url": url,
            "http_status": None,
            "note": f"Realtime gateway unreachable: {type(exc).__name__}",
        }
    if code == 503:
        return {
            "status": "down",
            "url": url,
            "http_status": code,
            "note": (
                "The API gateway returned 503 for /realtime/v1 — the Realtime "
                "upstream is not reachable through the gateway. Local stack: "
                "verify the Kong upstream host/port for the realtime service "
                "(config.toml [api].port + a running realtime container)."
            ),
        }
    if code == 101:
        return {
            "status": "up",
            "url": url,
            "http_status": code,
            "note": "Realtime websocket handshake completed through the API gateway.",
        }
    # Any other gateway answer means the upstream is reachable but the
    # websocket endpoint did not complete a handshake (404/400/426...).
    return {
        "status": "degraded",
        "url": url,
        "http_status": code,
        "note": (
            "The API gateway answered but the Realtime websocket endpoint did "
            "not complete a handshake. Realtime features are unavailable."
        ),
    }


@router.get("/health/realtime")
async def realtime_health() -> dict:
    """Readiness: is Realtime reachable AND completing websocket handshakes?

    Status semantics:

    * ``up``       — the gateway routed the probe and the websocket handshake
      completed (HTTP 101).
    * ``down``     — the gateway is unreachable or returned 503 (upstream down).
    * ``degraded`` — the gateway answered but the websocket endpoint did not
      complete a handshake (e.g. 404/400). Realtime features are NOT usable
      even though auth/REST work. Local demo stack: the realtime container
      rejects the demo JWT's tenant issuer (``TenantNotFound``) — a local
      provisioning/version mismatch, not a CarbonTally defect.
    """
    return _probe_realtime()
