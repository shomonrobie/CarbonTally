"""Analytics & Integrations settings (GA4) — API, authorization and fail-closed
behaviour.

Only Google Analytics 4 is implemented. The configuration is an enabled flag
plus a non-secret measurement ID; the browser read is deliberately public, every
write requires CarbonTally internal admin authority, and a half-configured or
malformed provider must be rejected rather than persisted.
"""
from __future__ import annotations

import pytest

from tests.unit.api.route_paths import flatten_router_paths

ANALYTICS_PATH = "/api/v3/settings/analytics"


def _route_dependencies(router, path_fragment: str) -> list:
    """Return ``(methods, dependency_call)`` pairs for the matching routes.

    The aggregated V3 router exposes included sub-routers lazily, so the
    recursion mirrors ``route_paths.flatten_router_paths``.
    """
    found: list = []
    for route in getattr(router, "routes", []):
        path = getattr(route, "path", None)
        if path and path_fragment in path:
            dependant = getattr(route, "dependant", None)
            if dependant is not None:
                methods = tuple(sorted(getattr(route, "methods", []) or []))
                for dep in dependant.dependencies:
                    found.append((methods, dep.call))
        original = getattr(route, "original_router", None)
        if original is not None:
            found.extend(_route_dependencies(original, path_fragment))
    return found


# ---------------------------------------------------------------------------
# Route registration + authorization posture
# ---------------------------------------------------------------------------


def test_analytics_settings_routes_registered() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    assert any(ANALYTICS_PATH in path for path in paths), "analytics settings route missing"


def test_analytics_settings_write_requires_internal_admin() -> None:
    from api.v3_settings import router as settings_router

    put_deps = {
        getattr(call, "__name__", "")
        for methods, call in _route_dependencies(settings_router, ANALYTICS_PATH)
        if "PUT" in methods
    }
    # require_admin() -> admin_checker: only CarbonTally internal admin authority
    # may change analytics configuration.
    assert "admin_checker" in put_deps


def test_analytics_settings_read_is_deliberately_public() -> None:
    """The public marketing surface must know whether to load GA4 before a
    visitor signs in, so the read carries no authentication dependency. The
    response is trimmed to the two non-secret provider fields."""
    from api.v3_settings import router as settings_router

    get_deps = {
        getattr(call, "__name__", "")
        for methods, call in _route_dependencies(settings_router, ANALYTICS_PATH)
        if "GET" in methods
    }
    assert "admin_checker" not in get_deps
    assert "auth_checker" not in get_deps


# ---------------------------------------------------------------------------
# Measurement-ID validation
# ---------------------------------------------------------------------------


def test_measurement_id_is_trimmed_and_uppercased() -> None:
    from api.v3_settings import normalise_ga4_measurement_id

    assert normalise_ga4_measurement_id("  g-abc1234567 ") == "G-ABC1234567"


def test_unset_measurement_id_is_none() -> None:
    from api.v3_settings import normalise_ga4_measurement_id

    assert normalise_ga4_measurement_id(None) is None
    assert normalise_ga4_measurement_id("") is None
    assert normalise_ga4_measurement_id("   ") is None


@pytest.mark.parametrize(
    "bad_id",
    [
        "UA-123456-1",  # Universal Analytics, not GA4
        "GTM-ABCDEF",  # Google Tag Manager container
        "G-",  # no body
        "G-AB",  # too short to be a measurement ID
        "ABC1234567",  # missing the G- prefix
        "G-AB C123456",  # whitespace inside the ID
        "<script>alert(1)</script>",
        "G-ABCDEFGHIJ-EXTRA",  # a second hyphen is not valid
    ],
)
def test_invalid_measurement_id_is_rejected(bad_id: str) -> None:
    from api.v3_settings import normalise_ga4_measurement_id

    with pytest.raises(ValueError):
        normalise_ga4_measurement_id(bad_id)


# ---------------------------------------------------------------------------
# Repository mapping fails closed
# ---------------------------------------------------------------------------


def test_missing_row_fails_closed() -> None:
    from data.settings import _analytics_from_row

    config = _analytics_from_row(None)
    assert config["enabled"] is False
    assert config["ga4_measurement_id"] is None


def test_unreadable_payload_fails_closed() -> None:
    from data.settings import _analytics_from_row

    for payload in ("not-json", "[]", '"G-ABC1234567"', "{}"):
        config = _analytics_from_row({"setting_value": payload})
        assert config["enabled"] is False
        assert config["ga4_measurement_id"] is None


def test_configured_row_is_returned() -> None:
    from data.settings import _analytics_from_row

    config = _analytics_from_row(
        {"setting_value": '{"enabled": true, "ga4_measurement_id": "G-ABC1234567"}'}
    )
    assert config["enabled"] is True
    assert config["ga4_measurement_id"] == "G-ABC1234567"


def test_blank_measurement_id_normalises_to_none() -> None:
    from data.settings import _analytics_from_row

    config = _analytics_from_row(
        {"setting_value": '{"enabled": true, "ga4_measurement_id": "   "}'}
    )
    assert config["ga4_measurement_id"] is None


# ---------------------------------------------------------------------------
# Endpoint behaviour (direct calls with a local stub — the shared API fakes
# belong to the Phase 8 B2 workstream and are deliberately untouched)
# ---------------------------------------------------------------------------


class _AnalyticsSettingsStub:
    """Stateful stand-in for the real ``SettingsRepository`` analytics surface."""

    def __init__(self) -> None:
        self.config = {
            "enabled": False,
            "ga4_measurement_id": None,
            "updated_at": None,
            "updated_by": None,
        }

    async def get_analytics(self) -> dict:
        return dict(self.config)

    async def update_analytics(self, *, enabled, ga4_measurement_id, updated_by) -> dict:
        self.config = {
            "enabled": bool(enabled),
            "ga4_measurement_id": ga4_measurement_id,
            "updated_at": "2026-09-13T00:00:00+00:00",
            "updated_by": updated_by,
        }
        return dict(self.config)


class _Repos:
    def __init__(self) -> None:
        self.settings = _AnalyticsSettingsStub()


def _admin():
    from auth import AuthUser

    return AuthUser(
        user_id="u-admin",
        email="admin@ct.test",
        role="admin",
        role_name="admin",
        is_staff=True,
    )


async def test_analytics_round_trip_persists_through_the_api_contract() -> None:
    from api.v3_settings import (
        AnalyticsSettingsUpdate,
        get_analytics_settings,
        update_analytics_settings,
    )

    repos = _Repos()
    saved = await update_analytics_settings(
        payload=AnalyticsSettingsUpdate(enabled=True, ga4_measurement_id=" g-abc1234567 "),
        current_user=_admin(),
        repos=repos,
    )
    assert saved["settings"]["enabled"] is True
    assert saved["settings"]["ga4_measurement_id"] == "G-ABC1234567"
    assert saved["settings"]["updated_by"] == "u-admin"

    read = await get_analytics_settings(repos=repos)
    assert read["settings"]["enabled"] is True
    assert read["settings"]["ga4_measurement_id"] == "G-ABC1234567"


async def test_public_read_is_trimmed_to_non_secret_fields() -> None:
    from api.v3_settings import get_analytics_settings

    read = await get_analytics_settings(repos=_Repos())
    assert set(read["settings"].keys()) == {"enabled", "ga4_measurement_id"}


async def test_default_state_is_disabled_and_silent() -> None:
    from api.v3_settings import get_analytics_settings

    read = await get_analytics_settings(repos=_Repos())
    assert read["settings"] == {"enabled": False, "ga4_measurement_id": None}


async def test_disabling_keeps_the_configured_measurement_id() -> None:
    from api.v3_settings import AnalyticsSettingsUpdate, update_analytics_settings

    repos = _Repos()
    await update_analytics_settings(
        payload=AnalyticsSettingsUpdate(enabled=True, ga4_measurement_id="G-ABC1234567"),
        current_user=_admin(),
        repos=repos,
    )
    off = await update_analytics_settings(
        payload=AnalyticsSettingsUpdate(enabled=False, ga4_measurement_id="G-ABC1234567"),
        current_user=_admin(),
        repos=repos,
    )
    assert off["settings"]["enabled"] is False
    assert off["settings"]["ga4_measurement_id"] == "G-ABC1234567"


async def test_enabling_without_a_measurement_id_is_rejected() -> None:
    from api.v3_settings import AnalyticsSettingsUpdate, update_analytics_settings
    from fastapi import HTTPException

    repos = _Repos()
    with pytest.raises(HTTPException) as exc:
        await update_analytics_settings(
            payload=AnalyticsSettingsUpdate(enabled=True, ga4_measurement_id=None),
            current_user=_admin(),
            repos=repos,
        )
    assert exc.value.status_code == 422
    # Nothing was persisted.
    assert repos.settings.config["enabled"] is False


async def test_enabling_with_a_malformed_id_is_rejected() -> None:
    from api.v3_settings import AnalyticsSettingsUpdate, update_analytics_settings
    from fastapi import HTTPException

    repos = _Repos()
    with pytest.raises(HTTPException) as exc:
        await update_analytics_settings(
            payload=AnalyticsSettingsUpdate(enabled=True, ga4_measurement_id="UA-123456-1"),
            current_user=_admin(),
            repos=repos,
        )
    assert exc.value.status_code == 422
    assert repos.settings.config["ga4_measurement_id"] is None


# ---------------------------------------------------------------------------
# HTTP contract: authorization and validation over the real app
# ---------------------------------------------------------------------------


def _set_user(user_provider, user) -> None:
    user_provider.set_user(user)


def test_analytics_write_denied_for_non_admin(client, world, user_provider) -> None:
    """A customer member must not be able to change analytics configuration."""
    from tests.unit.api.fakes import member_user

    _set_user(user_provider, member_user("org-1", "u-member", "member@example.test"))
    response = client.put(
        ANALYTICS_PATH,
        json={"enabled": True, "ga4_measurement_id": "G-ABC1234567"},
    )
    assert response.status_code == 403


def test_analytics_write_denied_for_processing_entity_staff(client, world, user_provider) -> None:
    """Processing Entity staff never hold internal CarbonTally admin authority."""
    from tests.unit.api.fakes import entity_operator_user

    _set_user(user_provider, entity_operator_user("entity-1"))
    response = client.put(
        ANALYTICS_PATH,
        json={"enabled": True, "ga4_measurement_id": "G-ABC1234567"},
    )
    assert response.status_code == 403


def test_analytics_write_requires_authentication(client, world, user_provider) -> None:
    user_provider.set_unauthenticated()
    response = client.put(
        ANALYTICS_PATH,
        json={"enabled": True, "ga4_measurement_id": "G-ABC1234567"},
    )
    assert response.status_code == 401


def test_analytics_write_rejects_invalid_measurement_id(client, world, user_provider) -> None:
    from tests.unit.api.fakes import staff_user

    _set_user(user_provider, staff_user("u-admin", email="admin@example.test", role_name="admin"))
    response = client.put(
        ANALYTICS_PATH,
        json={"enabled": True, "ga4_measurement_id": "GTM-ABCDEF"},
    )
    assert response.status_code == 422


def test_analytics_write_rejects_enabled_without_id(client, world, user_provider) -> None:
    from tests.unit.api.fakes import staff_user

    _set_user(user_provider, staff_user("u-admin", email="admin@example.test", role_name="admin"))
    response = client.put(ANALYTICS_PATH, json={"enabled": True})
    assert response.status_code == 422
