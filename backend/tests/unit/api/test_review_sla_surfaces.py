"""WS2 / ARCH-0001 — review/SLA surface regression tests.

Verifies the canonical-surface decision: both the canonical ops route family
(``/api/v3/ops/*`` — consumed by the product UI) and the retained admin
legacy-compat family (``/api/v3/admin/*``) stay registered, and that the
canonical ops SLA/review routes expose the expected behaviour.
"""
from __future__ import annotations

from fastapi.routing import APIRoute

from api.router import router


def _paths() -> set[str]:
    return {
        r.path
        for r in router.routes
        if isinstance(r, APIRoute)
    }


def _methods(path: str) -> set[str]:
    return {
        m.lower()
        for r in router.routes
        if isinstance(r, APIRoute) and r.path == path
        for m in r.methods
    }


def test_canonical_ops_sla_surface_registered() -> None:
    assert "/api/v3/ops/sla/settings" in _paths()
    assert _methods("/api/v3/ops/sla/settings") >= {"get", "put"}


def test_canonical_ops_review_assign_registered() -> None:
    assert "/api/v3/ops/review/{review_id}/assign" in _paths()
    assert "post" in _methods("/api/v3/ops/review/{review_id}/assign")


def test_admin_legacy_compat_surface_retained() -> None:
    """The admin-only /api/v3/admin/* review surface is intentionally kept."""
    assert "/api/v3/admin/sla/settings" in _paths()
    assert _methods("/api/v3/admin/sla/settings") >= {"get", "put"}
    assert "/api/v3/admin/review-queue/{review_id}/assign" in _paths()


def test_both_families_are_distinct_urls() -> None:
    """The two families are deliberately separate (no silent route collision)."""
    assert "/api/v3/admin/sla/settings" != "/api/v3/ops/sla/settings"
