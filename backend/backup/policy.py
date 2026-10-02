"""Configurable backup policy (§16, §9) — configuration, never a security control.

The ratified architecture authorises exactly one configurable layer around the
backup capability: the *operational policy* (enablement, retention, frequency,
object-backup inclusion). Everything else is **mandatory and non-configurable**,
and this module says so in code as well as in prose:

============================  =====================================================
Mandatory property            Why it can never be a setting
============================  =====================================================
Application-level encryption  D3: only ciphertext may reach storage
Private, independent storage  D2: a backup on the production account is not off-site
Authorization                 §9: ``require_admin()`` + ``can_manage_backups``
Tenant isolation              the database half is never organisation-scoped (§10)
Integrity verification        §12: an unverified artifact is not a backup
============================  =====================================================

:func:`validate_policy_update` therefore refuses any unknown field *and* any
attempt to express one of those properties as a switch, so "disable encryption
from the dashboard" is not merely discouraged — it is unimplementable.

Scheduling: the architecture's §16 is explicit — *"Do not implement scheduling
yet; the design must merely support it (the ``backup_jobs`` model does)"*. The
frequency is therefore recorded here as durable **intent** and read by the admin
surface, but no automatic schedule-driven job creation is implemented; that
remains the recorded deferred item.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional

from backup.errors import BackupValidationError

#: Recorded intent only — see the module docstring on scheduling.
FREQUENCIES: tuple[str, ...] = ("manual", "daily", "weekly")
DEFAULT_FREQUENCY = "manual"

#: Bounds for the retention setting. ``None`` means "not configured" (no automatic
#: expiry), which is the honest representation the existing retention surface uses.
MIN_RETENTION_DAYS = 1
MAX_RETENTION_DAYS = 3650

#: The fields an administrator may change.
POLICY_FIELDS: tuple[str, ...] = (
    "enabled",
    "retention_days",
    "frequency",
    "object_backup_enabled",
    "object_prefix",
)

#: Properties that are NOT settings, with the reason a caller is refused.
MANDATORY_INVARIANTS: tuple[dict[str, str], ...] = (
    {
        "property": "encryption",
        "rule": "AES-256-GCM is applied in the worker before upload (D3).",
    },
    {
        "property": "private_storage",
        "rule": "The destination is a private bucket in an independent account (D2).",
    },
    {
        "property": "authorization",
        "rule": "require_admin() plus the can_manage_backups capability (§9).",
    },
    {
        "property": "tenant_isolation",
        "rule": "A backup spans tenants; it is never organisation-scoped (§10).",
    },
    {
        "property": "integrity_verification",
        "rule": "Checksums and an authenticated envelope are always recorded (§12).",
    },
)

#: Field names a caller might invent to try to switch an invariant off.
_FORBIDDEN_FIELDS: frozenset[str] = frozenset(
    {
        "encryption",
        "encrypt",
        "disable_encryption",
        "private_storage",
        "public",
        "public_access",
        "authorization",
        "require_authorization",
        "tenant_isolation",
        "verify",
        "verification",
        "integrity",
        "disable_verification",
    }
)


@dataclass(frozen=True)
class BackupPolicy:
    """The effective backup policy (configuration only)."""

    enabled: bool = True
    retention_days: Optional[int] = None
    frequency: str = DEFAULT_FREQUENCY
    object_backup_enabled: bool = True
    object_prefix: str = ""
    mandatory_invariants: tuple[dict[str, str], ...] = field(
        default_factory=lambda: MANDATORY_INVARIANTS
    )

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["mandatory_invariants"] = [
            dict(item) for item in self.mandatory_invariants
        ]
        payload["scheduling"] = (
            "recorded intent only — automatic schedule-driven backups are the "
            "recorded deferred item (§16)"
        )
        return payload


def validate_policy_update(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalise and validate a policy update, or raise.

    Rules (all fail closed):

    * an unknown field is refused, so the dashboard can never widen the surface;
    * a field that names a mandatory invariant is refused with that invariant's
      own reason, so "turn off encryption" is rejected as an *unimplementable*
      request rather than silently ignored;
    * ``retention_days`` must be ``None`` (clear) or an integer in
      :data:`MIN_RETENTION_DAYS`..:data:`MAX_RETENTION_DAYS`;
    * ``frequency`` must be one of :data:`FREQUENCIES`;
    * ``object_prefix`` is a bucket-relative prefix: no leading ``/``, no ``..``.
    """
    unknown = sorted(set(payload) - set(POLICY_FIELDS))
    forbidden = sorted(set(unknown) & _FORBIDDEN_FIELDS)
    if forbidden:
        raise BackupValidationError(
            "encryption, private storage, authorization, tenant isolation and "
            "integrity verification are not configurable",
            details={"fields": forbidden},
        )
    if unknown:
        raise BackupValidationError(
            "unsupported backup policy field", details={"fields": unknown}
        )

    normalized: dict[str, Any] = {}
    if "enabled" in payload:
        if not isinstance(payload["enabled"], bool):
            raise BackupValidationError("enabled must be a boolean")
        normalized["enabled"] = payload["enabled"]
    if "object_backup_enabled" in payload:
        if not isinstance(payload["object_backup_enabled"], bool):
            raise BackupValidationError("object_backup_enabled must be a boolean")
        normalized["object_backup_enabled"] = payload["object_backup_enabled"]
    if "retention_days" in payload:
        value = payload["retention_days"]
        if value is None or value == "":
            normalized["retention_days"] = None
        else:
            try:
                days = int(value)
            except (TypeError, ValueError) as exc:
                raise BackupValidationError("retention_days must be an integer") from exc
            if not MIN_RETENTION_DAYS <= days <= MAX_RETENTION_DAYS:
                raise BackupValidationError(
                    "retention_days is outside the permitted range",
                    details={"min": MIN_RETENTION_DAYS, "max": MAX_RETENTION_DAYS},
                )
            normalized["retention_days"] = days
    if "frequency" in payload:
        value = str(payload["frequency"] or "").strip().lower()
        if value not in FREQUENCIES:
            raise BackupValidationError(
                "frequency must be one of the supported values",
                details={"allowed": list(FREQUENCIES)},
            )
        normalized["frequency"] = value
    if "object_prefix" in payload:
        value = str(payload["object_prefix"] or "").strip()
        if value.startswith("/") or ".." in value:
            raise BackupValidationError(
                "object_prefix must be a bucket-relative prefix without '..'"
            )
        normalized["object_prefix"] = value
    return normalized


def _flag(stored: Mapping[str, Any], key: str, default: bool) -> bool:
    """Read a stored boolean flag, treating an explicit ``None`` as unset.

    ``system_settings`` surfaces *every* allow-listed key, using ``None`` for one
    nobody has set. A plain ``stored.get(key, default)`` would therefore read
    "not configured" as ``False`` and report the whole platform as "backup
    disabled" — the opposite of the documented default.
    """
    value = stored.get(key)
    return default if value is None else bool(value)


def policy_from_stored(
    stored: Optional[Mapping[str, Any]] = None,
    *,
    retention_days: Optional[int] = None,
) -> BackupPolicy:
    """Build the effective policy from the stored row plus the retention setting.

    A missing/malformed stored row yields the documented defaults; it never
    fabricates a duration (``retention_days`` stays ``None`` = "not configured"),
    which keeps N3's "never invent a policy value" rule intact.
    """
    stored = dict(stored or {})
    effective_retention = (
        stored.get("retention_days")
        if stored.get("retention_days") is not None
        else retention_days
    )
    frequency = str(stored.get("frequency") or DEFAULT_FREQUENCY).strip().lower()
    if frequency not in FREQUENCIES:
        frequency = DEFAULT_FREQUENCY
    prefix = stored.get("object_prefix")
    return BackupPolicy(
        enabled=_flag(stored, "enabled", True),
        retention_days=(
            int(effective_retention) if effective_retention is not None else None
        ),
        frequency=frequency,
        object_backup_enabled=_flag(stored, "object_backup_enabled", True),
        object_prefix=str(prefix) if isinstance(prefix, str) else "",
    )


__all__ = [
    "BackupPolicy",
    "DEFAULT_FREQUENCY",
    "FREQUENCIES",
    "MANDATORY_INVARIANTS",
    "MAX_RETENTION_DAYS",
    "MIN_RETENTION_DAYS",
    "POLICY_FIELDS",
    "policy_from_stored",
    "validate_policy_update",
]