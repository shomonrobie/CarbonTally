"""V3 platform settings surface (N3 retention + Analytics & Integrations).

Retention is a CONFIGURABLE platform capability. The settings below are the
platform-wide retention policy (the RC2 ``system_settings`` columns). Only
CarbonTally internal staff with admin authority may read/write them.

No retention duration is invented here: unset values are returned as ``None``
and the UI renders "Not configured". Enforcement is a server-side concern —
this surface is configuration only.

Analytics & Integrations is additive: only Google Analytics 4 (GA4) is
implemented. The browser needs the (non-secret) GA4 configuration before a
visitor signs in, so the read is deliberately public while every write stays
behind ``require_admin()``.
"""
from __future__ import annotations

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    RepositoryBundle,
    get_repositories,
)
from auth import AuthUser, require_admin
from pydantic import BaseModel

router = APIRouter(prefix="/api/v3/settings", tags=["V3 — Platform Settings"])

#: GA4 measurement IDs are ``G-`` followed by uppercase alphanumerics
#: (``G-XXXXXXXXXX``). Universal Analytics (``UA-…``) and Google Tag Manager
#: (``GTM-…``) identifiers are not GA4 measurement IDs and are rejected: the
#: loader must never be handed an identifier it cannot configure.
_GA4_MEASUREMENT_ID_RE = re.compile(r"^G-[A-Z0-9]{4,20}$")


def normalise_ga4_measurement_id(raw: Optional[str]) -> Optional[str]:
    """Return the canonical GA4 measurement ID, or ``None`` when unset.

    Raises ``ValueError`` for a supplied value that is not a GA4 measurement ID.
    """
    if raw is None:
        return None
    candidate = str(raw).strip().upper()
    if not candidate:
        return None
    if not _GA4_MEASUREMENT_ID_RE.match(candidate):
        raise ValueError(
            "ga4_measurement_id must be a GA4 measurement ID of the form "
            "G-XXXXXXXXXX (Google Tag Manager GTM-… and Universal Analytics "
            "UA-… identifiers are not accepted)"
        )
    return candidate


class RetentionUpdate(BaseModel):
    audit_log_retention_days: Optional[int] = None
    data_retention_days: Optional[int] = None
    document_retention_days: Optional[int] = None
    backup_retention_days: Optional[int] = None


class AnalyticsSettingsUpdate(BaseModel):
    """Analytics & Integrations configuration (GA4 only)."""

    enabled: bool = False
    ga4_measurement_id: Optional[str] = None


@router.get("/retention")
async def get_retention_settings(
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Return the configured platform retention policy (N3). Unset values are
    ``None`` — the UI must not invent durations."""
    return {"settings": await repos.settings.get_retention()}


@router.put("/retention")
async def update_retention_settings(
    payload: RetentionUpdate,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Persist the configurable retention policy (server-side enforcement
    remains the platform's responsibility)."""
    for field in ("audit_log_retention_days", "data_retention_days",
                  "document_retention_days", "backup_retention_days"):
        value = getattr(payload, field)
        if value is not None and value < 0:
            raise HTTPException(
                status_code=422,
                detail=f"{field} must be a non-negative number of days",
            )
    return {
        "settings": await repos.settings.update_retention(
            audit_log_retention_days=payload.audit_log_retention_days,
            data_retention_days=payload.data_retention_days,
            document_retention_days=payload.document_retention_days,
            backup_retention_days=payload.backup_retention_days,
            updated_by=current_user.user_id,
        )
    }


@router.get("/analytics")
async def get_analytics_settings(
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Public read of the browser-side analytics bootstrap configuration.

    This read is intentionally unauthenticated: CarbonTally's public marketing
    surface must be able to decide whether to load GA4 before a visitor has
    signed in. The response is trimmed to the two non-secret provider fields
    that the browser already exposes when GA4 is loaded — the enabled flag and
    the measurement ID. It never returns retention values, internal actor
    identifiers or any tenant data.
    """
    config = await repos.settings.get_analytics()
    return {
        "settings": {
            "enabled": config["enabled"],
            "ga4_measurement_id": config["ga4_measurement_id"],
        }
    }


@router.put("/analytics")
async def update_analytics_settings(
    payload: AnalyticsSettingsUpdate,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Persist the Analytics & Integrations configuration (GA4 only).

    Enabled analytics requires a valid measurement ID: a half-configured
    provider is rejected here rather than persisted, so the runtime loader is
    never asked to configure GA4 with an identifier it cannot use.
    """
    try:
        measurement_id = normalise_ga4_measurement_id(payload.ga4_measurement_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if payload.enabled and measurement_id is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "A GA4 measurement ID (G-XXXXXXXXXX) is required before Google "
                "Analytics can be enabled"
            ),
        )

    return {
        "settings": await repos.settings.update_analytics(
            enabled=payload.enabled,
            ga4_measurement_id=measurement_id,
            updated_by=current_user.user_id,
        )
    }
