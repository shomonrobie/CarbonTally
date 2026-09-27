# backend/utils/audit_logger.py
"""Legacy audit writer for the ``audit_logs`` table.

CT-AUDIT-01 (§11.1 A) — audit failures must never be swallowed silently.

This module historically caught every persistence error, printed a warning and
returned ``None`` — an audit write could fail on an authentication, approval or
permission-change path with no observable trace (F-3 in the CT-AUDIT-01 report).

The failure policy is now explicit:

* ``AUDIT_LOG_FAILURE_MODE=log`` (default) — keep the write non-fatal for
  operational continuity, but record the failure at ERROR level, retain the
  last failure and count every failure so it is observable (§77 observability).
* ``AUDIT_LOG_FAILURE_MODE=raise`` — fail closed: raise :class:`AuditWriteError`.

Callers on security/compliance-critical paths (authentication, approval,
permission changes) should pass ``strict=True`` so a lost audit record cannot
pass unnoticed, independent of the process-wide default.
"""
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import os

from database import get_supabase_client

logger = logging.getLogger("carbontally.audit")

FAILURE_MODE_LOG = "log"
FAILURE_MODE_RAISE = "raise"

_FAILURE_MODE_ENV = "AUDIT_LOG_FAILURE_MODE"


def _resolve_default_failure_mode() -> str:
    """Return the process-wide audit failure policy ("log" or "raise")."""
    mode = (os.getenv(_FAILURE_MODE_ENV) or FAILURE_MODE_LOG).strip().lower()
    if mode not in (FAILURE_MODE_LOG, FAILURE_MODE_RAISE):
        logger.warning(
            "%s=%r is not a recognised audit failure mode; falling back to %r",
            _FAILURE_MODE_ENV,
            mode,
            FAILURE_MODE_LOG,
        )
        return FAILURE_MODE_LOG
    return mode


class AuditWriteError(RuntimeError):
    """Raised when an audit record could not be persisted (strict mode)."""


_failure_count = 0
_last_failure: Optional[Dict[str, Any]] = None


def audit_failure_count() -> int:
    """Number of audit-write failures observed in this process."""
    return _failure_count


def last_audit_failure() -> Optional[Dict[str, Any]]:
    """Describe the most recent audit-write failure (no secrets, no payload)."""
    return dict(_last_failure) if _last_failure else None


def reset_audit_failure_state() -> None:
    """Clear the observability counters (used by tests)."""
    global _failure_count, _last_failure
    _failure_count = 0
    _last_failure = None


def _record_failure(
    exc: BaseException,
    *,
    action_type: Optional[str],
    resource_type: Optional[str],
    resource_id: Optional[str],
    organization_id: Optional[str],
) -> None:
    """Record an audit-write failure observably (never silently)."""
    global _failure_count, _last_failure
    _failure_count += 1
    _last_failure = {
        "action_type": action_type,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "organization_id": organization_id,
        "error_type": type(exc).__name__,
        "error": str(exc),
        "at": datetime.now().isoformat(),
    }
    logger.error(
        "audit write failed (count=%s, action_type=%s, resource_type=%s, "
        "resource_id=%s, organization_id=%s): %s",
        _failure_count,
        action_type,
        resource_type,
        resource_id,
        organization_id,
        exc,
    )

async def log_audit(
    user_id: Optional[str] = None,
    staff_id: Optional[str] = None,
    organization_member_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    action_type: str = None,
    resource_type: str = None,
    resource_id: Optional[str] = None,
    action: str = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    old_data: Optional[Dict] = None,
    new_data: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
    strict: Optional[bool] = None
):
    """Log an audit event."""
    try:
        supabase = get_supabase_client()
        
        # Calculate changes if both old and new data provided
        changes = None
        if old_data and new_data:
            changes = {}
            for key in set(old_data.keys()) | set(new_data.keys()):
                if key in old_data and key in new_data and old_data[key] != new_data[key]:
                    changes[key] = {
                        'old': old_data.get(key),
                        'new': new_data.get(key)
                    }
        
        audit_data = {
            'user_id': user_id,
            'staff_id': staff_id,
            'organization_member_id': organization_member_id,
            'organization_id': organization_id,
            'action_type': action_type,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'action': action,
            'description': description,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'old_data': old_data,
            'new_data': new_data,
            'changes': changes,
            'metadata': metadata,
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.from_('audit_logs') \
            .insert(audit_data) \
            .execute()
        
        return result.data[0] if result.data else None
        
    except Exception as e:
        # CT-AUDIT-01 F-3: never swallow an audit failure silently.  The failure
        # is counted and logged; in strict mode (or under
        # AUDIT_LOG_FAILURE_MODE=raise) it is surfaced to the caller instead.
        _record_failure(
            e,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            organization_id=organization_id,
        )
        effective_strict = (
            _resolve_default_failure_mode() == FAILURE_MODE_RAISE
            if strict is None
            else bool(strict)
        )
        if effective_strict:
            raise AuditWriteError(
                f"audit write failed for action_type={action_type!r} "
                f"resource_type={resource_type!r}: {e}"
            ) from e
        return None

# Logging helpers for specific actions
async def log_document_action(
    document_id: str,
    organization_id: str,
    user_id: str,
    action: str,
    old_data: Optional[Dict] = None,
    new_data: Optional[Dict] = None,
    **kwargs
):
    """Log document-related actions."""
    return await log_audit(
        user_id=user_id,
        organization_id=organization_id,
        action_type='document_uploaded' if action == 'uploaded' else 'document_updated',
        resource_type='document',
        resource_id=document_id,
        action=action,
        old_data=old_data,
        new_data=new_data,
        **kwargs
    )

async def log_verification_action(
    verification_id: str,
    organization_id: str,
    user_id: str,
    action: str,
    status: str,
    **kwargs
):
    """Log verification actions."""
    action_type_map = {
        'submitted': 'verification_submitted',
        'verified': 'verification_approved',
        'rejected': 'verification_rejected',
        'needs_revision': 'verification_needs_revision'
    }
    
    return await log_audit(
        user_id=user_id,
        organization_id=organization_id,
        action_type=action_type_map.get(action, 'verification_submitted'),
        resource_type='verification',
        resource_id=verification_id,
        action=action,
        metadata={'status': status},
        **kwargs
    )

async def log_message_action(
    message_id: str,
    conversation_id: str,
    user_id: str,
    action: str,
    **kwargs
):
    """Log message actions."""
    return await log_audit(
        user_id=user_id,
        action_type='message_sent' if action == 'sent' else 'message_read',
        resource_type='message',
        resource_id=message_id,
        action=action,
        metadata={'conversation_id': conversation_id},
        **kwargs
    )

async def log_notification_action(
    notification_id: str,
    user_id: str,
    action: str,
    **kwargs
):
    """Log notification actions."""
    return await log_audit(
        user_id=user_id,
        action_type='notification_sent' if action == 'sent' else 'notification_read',
        resource_type='notification',
        resource_id=notification_id,
        action=action,
        **kwargs
    )