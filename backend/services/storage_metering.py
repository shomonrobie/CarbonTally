"""Storage Management Step 2N — integrate document storage with the EXISTING entitlement model.

The ratified commercial model already exists in this repository; Step 2 does not
add a second entitlement system.  What already exists and is reused verbatim:

* ``billing_plans.included_storage_bytes`` — the **admin-configurable** capacity
  per plan (CarbonTally Admin publishes plans through ``api.v3_commercial``);
* ``billing_storage_usage`` + ``BillingService.meter_storage()`` — the
  server-authoritative metering snapshot derived from ``organization_files``;
* ``BillingService.get_entitlement()`` — the read-only entitlement view
  (``storage.usage_bytes`` / ``included_bytes`` / ``additional_bytes``).

Two deliberate design decisions, both taken from the ratified model rather than
invented here:

1. **Consumption is metered, not refused.**  The ratified model computes
   ``additional_bytes = max(0, usage - included)`` — i.e. storage beyond the
   included allowance is *measured and billable*, not a hard upload block.
   Turning capacity into an upload refusal would be a new commercial policy, so
   this module never blocks an upload on capacity.
2. **Fail-open on missing commercial wiring.**  If the billing surface (or a
   plan) is unavailable, the upload path is not affected: the integration
   reports ``recorded: false`` with the reason.  Commercial configuration is an
   administrative concern; it must never make document intake impossible.

The remaining gap (per-consultant managed-client capacity) is reported by
:func:`capacity_integration_status` instead of being silently expanded into this
task — the consultant subscription/plan model is unchanged.
"""
from __future__ import annotations

from typing import Any, Optional

from core.logging import get_logger

logger = get_logger(__name__)


async def record_storage_usage(repos: Any, organization_id: str) -> dict[str, Any]:
    """Refresh the existing storage metering snapshot for ``organization_id``.

    Best-effort and read-only with respect to the document: it never changes a
    document row, never blocks an upload and never charges anything by itself.
    Returns a JSON-safe outcome that the caller can record on the audit entry.
    """
    outcome: dict[str, Any] = {
        "integration": "billing_storage_usage",
        "organization_id": organization_id,
        "recorded": False,
    }
    if not organization_id:
        outcome["reason"] = "no organisation to meter"
        return outcome
    try:
        from services.billing import BillingService
    except Exception as exc:  # pragma: no cover - import boundary
        outcome["reason"] = f"billing service unavailable: {exc}"
        return outcome

    storage_repo = getattr(repos, "billing_storage", None)
    if storage_repo is None:
        outcome["reason"] = (
            "repos.billing_storage is not wired; storage usage is not metered"
        )
        return outcome

    try:
        usage = await BillingService(repos).meter_storage(organization_id)
    except Exception as exc:  # noqa: BLE001 - metering must never fail an upload
        logger.warning(
            "storage metering failed for organisation %s: %s", organization_id, exc
        )
        outcome["reason"] = f"metering failed: {str(exc)[:200]}"
        return outcome

    outcome.update(
        recorded=True,
        usage_bytes=int(getattr(usage, "usage_bytes", 0) or 0),
        included_bytes=int(getattr(usage, "included_bytes", 0) or 0),
        additional_bytes=int(getattr(usage, "additional_bytes", 0) or 0),
        source=str(getattr(usage, "source", "") or ""),
    )
    return outcome


async def capacity_snapshot(repos: Any, organization_id: str) -> Optional[dict]:
    """Read-only entitlement snapshot (``None`` when the commercial surface is absent)."""
    if not organization_id:
        return None
    try:
        from services.billing import BillingService
    except Exception:  # pragma: no cover - import boundary
        return None
    if getattr(repos, "billing_storage", None) is None:
        return None
    try:
        entitlement = await BillingService(repos).get_entitlement(organization_id)
    except Exception as exc:  # noqa: BLE001 - a missing plan is not an error here
        logger.warning(
            "entitlement lookup failed for organisation %s: %s", organization_id, exc
        )
        return None
    return entitlement.get("storage") if isinstance(entitlement, dict) else None


def capacity_integration_status() -> dict:
    """Exactly what was integrated, and what deliberately remains separate."""
    return {
        "integrated": {
            "included_storage_bytes": "billing_plans (admin-configurable)",
            "metering": "billing_storage_usage via BillingService.meter_storage",
            "entitlement_view": "BillingService.get_entitlement -> storage.*",
            "trigger": (
                "a security-accepted direct upload refreshes the metering snapshot "
                "(best-effort; never blocks the upload)"
            ),
        },
        "not_integrated": {
            "upload_refusal_on_capacity": (
                "not implemented: the ratified model meters and bills storage "
                "beyond the included allowance (additional_bytes); refusing "
                "uploads on capacity would be a new commercial policy"
            ),
            "consultant_managed_client_capacity": (
                "unchanged: a consultant subscription covering managed clients is "
                "already expressed by the existing plan/subscription model; Step 2 "
                "makes no change to it"
            ),
            "second_entitlement_system": "not created (explicitly out of scope)",
        },
        "ratified_boundary": (
            "Consultants are direct CarbonTally customers; their subscription covers "
            "managed clients; CarbonTally Admin configures capacity through plans. "
            "Storage is metered per organisation, including consultant-originated "
            "documents, which are stored in the client organisation's namespace."
        ),
    }
