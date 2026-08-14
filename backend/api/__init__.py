"""CarbonTally Backend v2.1 — API layer (prep-pack Phase 10).

The API boundary around the existing business capabilities. Routing stays thin:
every endpoint delegates to the existing domain services, engines and
repositories — it never reimplements matching, calculation, validation,
benchmarking or report-generation logic.

Modules:

* :mod:`api.router` — ``create_app()`` factory, the single v2.1 router and the
  consistent error mapping (``core.exceptions.CarbonTallyError`` → HTTP).
* :mod:`api.dependencies` — composition root (DI wiring, auth reuse, admin
  authorization, request/audit context).
* :mod:`api.middleware` — request/correlation ID + timing middleware.
* :mod:`api.contracts` — stable, serialisable request/response contracts.
* :mod:`api.admin_*` — admin endpoints (imports, providers, audit, aliases).
* :mod:`api.business` — business-processing endpoints (CT-ARCH-012).

The legacy ``backend/main.py`` / ``backend/routes`` application is left
untouched; the v2.1 API is served by ``backend/main_v2.py`` (``create_app``).
"""
from __future__ import annotations

from api.router import create_app, router

__all__ = ["create_app", "router"]
