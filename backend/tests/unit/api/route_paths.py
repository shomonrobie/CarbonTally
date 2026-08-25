"""Shared route-path enumeration for the V3 API tests.

FastAPI 0.141+ defers ``include_router``: every included sub-router appears in
``router.routes`` / ``app.routes`` as a lazy ``_IncludedRouter`` wrapper that
carries no ``path``. This module is the **single** place that converts a router
(or a FastAPI app) into the set of effective route paths, so route-registration
tests work on any installed FastAPI version.

Mechanism: ``_IncludedRouter`` exposes ``original_router`` (the wrapped
sub-router), whose APIRoutes carry the full path (prefixes are baked in at route
creation). Plain routes simply contribute their ``path``. The recursion handles
arbitrarily nested includes and degrades gracefully on older FastAPI (which
flattens routers eagerly).
"""
from __future__ import annotations

from typing import Any


def flatten_router_paths(router: Any) -> set[str]:
    """Return every effective route path exposed by ``router``.

    ``router`` may be a FastAPI ``APIRouter`` or a ``FastAPI`` app — both expose
    a ``.routes`` sequence.
    """
    paths: set[str] = set()
    for route in router.routes:
        path = getattr(route, "path", None)
        if path:
            paths.add(path)
        original = getattr(route, "original_router", None)
        if original is not None:
            paths |= flatten_router_paths(original)
    return paths
