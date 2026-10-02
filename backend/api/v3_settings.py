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
from typing import Any, Dict, Mapping, Optional

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    RepositoryBundle,
    get_repositories,
)
from auth import AuthUser, require_admin
from pydantic import BaseModel, ConfigDict

from services.email_provider import (
    ALLOWED_CREDENTIAL_ENVS,
    DEFAULT_CREDENTIAL_ENV,
    DEFAULT_PROVIDER,
    describe_provider_config,
    normalise_provider_config,
    provider_readiness,
)
from services.email_sender import (
    DEFAULT_SENDER,
    describe_email_sender,
    normalise_email_sender,
    resolve_email_sender,
)
from utils.upload_limits import (
    POLICY_FIELDS,
    default_limits,
    effective_policy,
    human_summary,
    platform_limits,
    resolve_configured_policy,
    validate_upload_policy,
)

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


class NotificationSenderUpdate(BaseModel):
    """Platform transactional-email sender configuration.

    The ``actor`` is never provided here: the From address is platform
    configuration, while the actor/acting-for context is recorded by the
    notification producer (``services.email_sender.notification_identity``).
    """

    email_sender: Optional[str] = None


class UploadPolicyUpdate(BaseModel):
    """Upload policy configuration (Admin Panel → Upload Policy).

    Every field is optional: an omitted/``null`` field keeps the currently
    stored value (the same merge semantics as the retention policy).  Values
    are validated by ``utils.upload_limits.validate_upload_policy`` before
    anything is persisted, so an out-of-range limit is refused with 422 rather
    than stored.
    """

    max_file_size_mb: Optional[int] = None
    max_files_per_batch: Optional[int] = None
    max_batch_size_mb: Optional[int] = None


class EmailProviderUpdate(BaseModel):
    """Email delivery provider configuration (CT-FINAL-02 / EMAIL-CONFIG-01).

    Every field is optional: an omitted/``null`` field keeps the currently
    stored value (the same merge semantics as the upload policy), while an
    **empty string** clears it — an SMTP transport that is no longer in use must
    be removable.  No credential is ever accepted here — only the *name* of the
    allow-listed environment variable that holds it.  Unknown fields are refused
    outright (``422``), so a credential sent as an ordinary setting is rejected
    rather than silently dropped or stored.
    """

    model_config = ConfigDict(extra="forbid")

    provider: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    credential_env: Optional[str] = None


#: The persisted provider-configuration fields (one canonical vocabulary).
_PROVIDER_UPDATE_FIELDS = (
    "provider",
    "smtp_host",
    "smtp_port",
    "smtp_username",
    "smtp_use_tls",
    "credential_env",
)


def _merge_provider_update(
    current: Mapping[str, Any], payload: EmailProviderUpdate
) -> Dict[str, Any]:
    """Merge a partial update onto the stored provider configuration.

    A field the administrator did not supply keeps its stored value.  Changing
    the provider without naming a credential variable re-points the credential
    at that provider's default environment variable: a stale variable left over
    from the previous provider would otherwise be read at delivery time, and the
    newly selected provider would fail closed for the wrong reason.
    """
    merged: Dict[str, Any] = {}
    for field in _PROVIDER_UPDATE_FIELDS:
        supplied = getattr(payload, field)
        merged[field] = current.get(field) if supplied is None else supplied

    new_provider = merged.get("provider") or DEFAULT_PROVIDER
    if isinstance(new_provider, str):
        new_provider = new_provider.strip().lower()
    stored_provider = current.get("provider") or DEFAULT_PROVIDER
    if payload.credential_env is None and new_provider != stored_provider:
        merged["credential_env"] = DEFAULT_CREDENTIAL_ENV.get(new_provider)
    return merged


def _describe_email_provider(
    stored: Mapping[str, Any], sender: Optional[str]
) -> Dict[str, Any]:
    """Describe the effective provider configuration — never a credential.

    The description carries the selected provider, the referenced credential
    environment variable and whether that variable is *present* (a boolean), so
    the Admin Dashboard can show what will actually happen without any secret
    crossing the API boundary.  ``readiness`` names any reason delivery would
    fail (no network call is made).
    """
    described = describe_provider_config(stored, stored=stored)
    described["readiness"] = provider_readiness(stored, sender=sender)
    # The allow-listed credential variables are published so the Admin Dashboard
    # can offer exactly the variables the adapter will read — the UI never
    # invents or widens the set (the server re-validates every submission).
    described["credential_options"] = sorted(ALLOWED_CREDENTIAL_ENVS)
    return described


def _describe_upload_policy(configured: dict, stored: dict) -> dict:
    """One canonical description of the upload policy for the admin surface."""
    effective = effective_policy(configured)
    return {
        "effective": effective,
        "configured": {field: configured.get(field) for field in POLICY_FIELDS},
        "defaults": default_limits(),
        "platform_caps": platform_limits(),
        "summary": human_summary(configured),
        "updated_at": stored.get("updated_at"),
        "updated_by": stored.get("updated_by"),
    }


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


@router.get("/notification-sender")
async def get_notification_sender_settings(
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Return the effective platform notification sender (admin only).

    The response describes configuration only. The delivery credential
    (``RESEND_API_KEY``) is never read, returned or logged here — an operator
    sees *which address* notifications come from, never the provider secret.
    """
    configured = await repos.settings.get_notification_sender()
    described = describe_email_sender(configured.get("email_sender"))
    return {
        "settings": {
            **described,
            "default_sender": DEFAULT_SENDER,
            "updated_at": configured.get("updated_at"),
            "updated_by": configured.get("updated_by"),
        }
    }


@router.put("/notification-sender")
async def update_notification_sender_settings(
    payload: NotificationSenderUpdate,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Persist the platform notification sender (admin only).

    Only a well-formed single address on a CarbonTally platform domain is
    accepted (D19 §13 — CarbonTally is not an email provider); anything else is
    rejected with 422 rather than stored.  Clearing the value restores the
    platform default.
    """
    try:
        sender = normalise_email_sender(payload.email_sender)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    saved = await repos.settings.update_notification_sender(
        email_sender=sender,
        updated_by=current_user.user_id,
    )
    described = describe_email_sender(saved.get("email_sender"))
    return {
        "settings": {
            **described,
            "default_sender": DEFAULT_SENDER,
            "updated_at": saved.get("updated_at"),
            "updated_by": saved.get("updated_by"),
            # The caller is told explicitly that the platform default is in
            # force when nothing valid is configured.
            "effective": resolve_email_sender(saved.get("email_sender")),
        }
    }


@router.get("/upload-policy")
async def get_upload_policy_settings(
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Return the effective upload policy (admin only).

    ``effective`` is what every upload ingress path enforces right now;
    ``configured`` is what an administrator has stored (``null`` = unset).
    The documented defaults and the ratified platform caps are returned
    alongside so the Admin Panel can show what will happen when a value is
    cleared, and what may never be exceeded.
    """
    stored = await repos.settings.get_upload_policy()
    configured = {
        field: stored.get(field) for field in POLICY_FIELDS
    }
    return {"settings": _describe_upload_policy(configured, stored)}


@router.put("/upload-policy")
async def update_upload_policy_settings(
    payload: UploadPolicyUpdate,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Persist the upload policy (admin only).

    Only positive integers within the ratified platform caps are accepted;
    anything else is refused with 422 and nothing is stored, so a limit
    violation can never be configured into existence.  The change is persisted
    in ``system_settings`` and therefore survives an application restart.
    """
    try:
        validated = validate_upload_policy(
            max_file_size_mb=payload.max_file_size_mb,
            max_files_per_batch=payload.max_files_per_batch,
            max_batch_size_mb=payload.max_batch_size_mb,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    saved = await repos.settings.update_upload_policy(
        max_file_size_mb=validated["max_file_size_mb"],
        max_files_per_batch=validated["max_files_per_batch"],
        max_batch_size_mb=validated["max_batch_size_mb"],
        updated_by=current_user.user_id,
    )
    configured = {
        field: saved.get(field) for field in POLICY_FIELDS
    }
    return {"settings": _describe_upload_policy(configured, saved)}


@router.get("/email-provider")
async def get_email_provider_settings(
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Return the effective email delivery provider configuration (admin only).

    The response describes configuration only and can never contain a
    credential: the settings row stores the *name* of the environment variable
    that holds the provider credential, and this read reports only whether that
    variable is present in the server environment (a boolean).  The provider in
    force is reported even when nothing has been configured — the documented
    default (Resend) applies in that case, so the Admin Dashboard shows what
    will actually happen rather than an empty state.
    """
    stored = await repos.settings.get_email_provider()
    sender_config = await repos.settings.get_notification_sender()
    return {
        "settings": _describe_email_provider(
            stored, resolve_email_sender(sender_config.get("email_sender"))
        )
    }


@router.post("/email-provider/validate")
async def validate_email_provider_settings(
    payload: EmailProviderUpdate,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Validate a candidate provider configuration **without persisting it**.

    ``valid`` is ``false`` for anything the save path would refuse, and
    ``settings.readiness.blocking_issues`` names every remaining reason delivery
    would fail, so an administrator is never told a provider is usable when it
    would fail at the first send.  This performs no network call and sends no
    email; clearing every field simply re-describes the configuration in force.
    """
    stored = await repos.settings.get_email_provider()
    candidate = _merge_provider_update(stored, payload)
    sender_config = await repos.settings.get_notification_sender()
    sender = resolve_email_sender(sender_config.get("email_sender"))

    try:
        validated = normalise_provider_config(candidate)
    except ValueError as exc:
        # Never describe the half-configured candidate as if it were in force.
        return {
            "valid": False,
            "errors": [str(exc)],
            "settings": _describe_email_provider(stored, sender),
        }

    described = _describe_email_provider(validated, sender)
    described["updated_at"] = stored.get("updated_at")
    described["updated_by"] = stored.get("updated_by")
    return {"valid": True, "errors": [], "settings": described}


@router.put("/email-provider")
async def update_email_provider_settings(
    payload: EmailProviderUpdate,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Persist the email delivery provider configuration (admin only).

    The *merged* configuration is validated before anything is written, so an
    unknown provider, a malformed SMTP transport, a credential variable outside
    the environment allow-list, or a credential submitted as an ordinary
    setting is refused with 422 and nothing is stored — the previously stored
    configuration stays in force (fail closed).  Delivery credentials are never
    accepted or returned: only the referenced environment variable name is
    persisted.
    """
    stored = await repos.settings.get_email_provider()
    candidate = _merge_provider_update(stored, payload)
    try:
        validated = normalise_provider_config(candidate)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    saved = await repos.settings.update_email_provider(
        provider=validated["provider"],
        smtp_host=validated["smtp_host"],
        smtp_port=validated["smtp_port"],
        smtp_username=validated["smtp_username"],
        smtp_use_tls=validated["smtp_use_tls"],
        credential_env=validated["credential_env"],
        updated_by=current_user.user_id,
    )
    sender_config = await repos.settings.get_notification_sender()
    return {
        "settings": _describe_email_provider(
            saved, resolve_email_sender(sender_config.get("email_sender"))
        )
    }
