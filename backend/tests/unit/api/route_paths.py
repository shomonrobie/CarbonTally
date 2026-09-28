"""Shared route enumeration for the V3 API tests.

FastAPI 0.141+ defers ``include_router``: every included sub-router appears in
``router.routes`` / ``app.routes`` as a lazy ``_IncludedRouter`` wrapper that
carries no ``path``. This module is the **single** place that converts a router
(or a FastAPI app) into effective route paths, and effective
``(path, endpoint, methods)`` triples, so route-registration tests work on any
installed FastAPI version.

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


def effective_routes(node: Any) -> list[tuple[str, Any, frozenset[str]]]:
    """Return ``(path, endpoint, methods)`` for every route ``node`` serves.

    Registration order is preserved, so callers can assert which handler
    FastAPI will dispatch to: for a given path the first matching route wins.

    ``node`` may be a ``FastAPI`` app, an ``APIRouter``, or one of the lazy
    include wrappers FastAPI >= 0.141 puts in ``.routes``:

    * a lazy ``_IncludedRouter`` carries no ``path`` of its own; its prefixed
      children come from ``effective_candidates()``, whose entries already have
      the parent's include prefix baked into ``path`` (this is the only way to
      read a *prefixed* sub-route path without depending on FastAPI internals);
    * a concrete route (any version) simply contributes ``path``, ``endpoint``
      and ``methods``.

    Anything else — a ``Mount``, a sub-application — is recursed into through
    ``routes`` so its children are reachable too.
    """
    candidates = getattr(node, "effective_candidates", None)
    children = candidates() if callable(candidates) else getattr(node, "routes", ()) or ()

    entries: list[tuple[str, Any, frozenset[str]]] = []
    for child in children:
        path = getattr(child, "path", None)
        if path:
            methods = getattr(child, "methods", None) or ()
            entries.append(
                (path, getattr(child, "endpoint", None), frozenset(str(m).upper() for m in methods))
            )
            continue
        entries.extend(effective_routes(child))
    return entries
