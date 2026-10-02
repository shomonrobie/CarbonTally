"""Storage Management Step 1B — the single authoritative upload authorization gate.

Every supported document-upload ingress (V3 organisation upload, consultant
client upload, and the two legacy upload routes) authorizes through this module
**before** any storage object is written and before any signed upload URL is
issued.  It adds no new authorization model: it composes the machinery the
platform already ratified —

* ``require_org_member()`` / ``ensure_org_access`` — authentication,
  organisation isolation, internal-staff operational scope, Processing-Entity
  denial (D20);
* the CL-42 viewer read-only rule;
* the consultant chain ``require_consultant`` → active ``consultant_clients``
  grant (D15/P6-1C) → the firm member's real ``can_upload_documents`` flag.

Ratified consultant/client rules enforced here:

* the **client organisation** is the tenancy owner — the gate returns the client
  organisation id and the upload is written under it;
* the consultant grant must be **active**; an ended/suspended grant is denied
  immediately (no data is moved, copied or archived);
* the consultant's configured capability applies consistently across its clients
  (the existing ``can_upload_documents`` flag — no per-client permission matrix
  is invented).

The module also owns the shared audit emission for significant document events
(Step 1I).  Audit writes are best-effort and never break an upload; a signed URL
is never itself stored as a secret.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException, status

from auth import AuthUser

#: Actor classes recorded on upload audit entries (canonical audit vocabulary).
ACTOR_ORG_USER_PROVENANCE = "org_user"
ACTOR_CONSULTANT_PROVENANCE = "consultant"

#: Significant document audit actions (Step 1I).
ACTION_UPLOAD_INITIATED = "document.upload_initiated"
ACTION_UPLOAD_COMPLETED = "document.upload_completed"
ACTION_SECURITY_SCAN_STARTED = "document.security_scan_started"
ACTION_SECURITY_SCAN_COMPLETED = "document.security_scan_completed"
ACTION_SECURITY_REJECTED = "document.security_rejected"
ACTION_ACCEPTED = "document.accepted"
ACTION_SIGNED_URL_ISSUED = "document.signed_url_issued"
ACTION_DOWNLOAD = "document.download"
ACTION_DELETED = "document.deleted"
ACTION_UPLOAD_DENIED = "document.upload_denied"
#: Step 2F — an abandoned upload authorisation was reaped (idempotent cleanup).
ACTION_UPLOAD_EXPIRED = "document.upload_authorisation_expired"
#: Step 2F — the cleanup pass itself (audit of the operational action).
ACTION_CLEANUP = "document.cleanup"
#: Step 2D — a required external malware scan could not be obtained (fail-closed).
ACTION_SCAN_UNAVAILABLE = "document.security_scan_unavailable"
#: Step 2P — a derived artefact (repair/OCR render) was created alongside the
#: customer's original; the original is never replaced by it.
ACTION_DERIVED_ARTEFACT = "document.derived_artefact_created"

#: Entity type used for document audit entries.
DOCUMENT_ENTITY = "organization_files"


@dataclass(frozen=True, slots=True)
class UploadActor:
    """The authorized uploader, as resolved by the gate.

    ``organization_id`` is always the **client organisation** that owns the
    stored bytes — for a consultant upload this is the client's organisation,
    never the firm's.
    """

    user_id: str
    organization_id: str
    actor_type: str
    organization_role: str = ""
    consultant_firm_id: Optional[str] = None
    consultant_membership_role: Optional[str] = None
    consultant_permission: Optional[str] = None

    @property
    def is_consultant(self) -> bool:
        return self.actor_type == ACTOR_CONSULTANT_PROVENANCE

    def provenance(self) -> dict:
        """Provenance recorded on the document row and in the audit trail.

        Consultant provenance lives in application metadata only — never in the
        storage path and never as a second tenancy.
        """
        data: dict[str, Any] = {
            "upload_actor_type": self.actor_type,
            "uploaded_by_user_id": self.user_id,
            "organization_id": self.organization_id,
        }
        if self.organization_role:
            data["uploaded_by_org_role"] = self.organization_role
        if self.is_consultant:
            data["uploaded_by_consultant_firm_id"] = self.consultant_firm_id
            data["uploaded_by_consultant_role"] = self.consultant_membership_role
            data["consultant_originated"] = True
        return data



async def record_document_event(
    *,
    repos: Any,
    action: str,
    actor: Optional[UploadActor],
    organization_id: str,
    entity_id: str,
    changed_fields: Optional[dict] = None,
    reason: Optional[str] = None,
    outcome: str = "success",
    correlation_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    actor_type: Optional[str] = None,
) -> None:
    """Append one significant document event to the audit ledger (best-effort).

    Never raises: an audit sink outage must not fail a customer upload, and the
    audit payload never contains object bytes or signed URLs.

    ``actor`` is the gate's resolved identity where one exists; internal pipeline
    stages that only carry provenance pass ``actor_id``/``actor_type`` instead.
    """
    sink = getattr(repos, "audit", None)
    record = getattr(sink, "record", None)
    if not callable(record):
        return
    resolved_actor = actor.user_id if actor is not None else (actor_id or "system")
    resolved_type = (
        actor.actor_type if actor is not None else actor_type
    )
    try:
        from domain.audit import AuditEntry

        await record(
            AuditEntry(
                id=str(uuid4()),
                correlation_id=correlation_id or entity_id or str(uuid4()),
                entity_type=DOCUMENT_ENTITY,
                entity_id=entity_id or "",
                action=action,
                actor=resolved_actor,
                occurred_at=datetime.now(timezone.utc),
                changed_fields=dict(changed_fields or {}),
                reason=reason,
                outcome=outcome,
                organization_id=organization_id or None,
                actor_type=resolved_type,
                actor_organization_id=(
                    actor.organization_id if actor is not None else None
                ),
                acting_for_organization_id=(
                    actor.organization_id
                    if actor is not None and actor.is_consultant
                    else None
                ),
            )
        )
    except Exception as exc:  # noqa: BLE001 - audit must never break the path
        print(f"audit write failed for {action}: {exc!r}")



async def _deny(
    *,
    repos: Any,
    status_code: int,
    detail: str,
    organization_id: str,
    user_id: str,
    action_reason: str,
) -> None:
    """Record the denial, then raise the HTTP error."""
    await record_document_event(
        repos=repos,
        action=ACTION_UPLOAD_DENIED,
        actor=None,
        organization_id=organization_id,
        entity_id="",
        changed_fields={"user_id": user_id, "required_permission": "upload_documents"},
        reason=action_reason,
        outcome="failure",
    )
    raise HTTPException(status_code=status_code, detail=detail)



async def authorize_organization_upload(
    *,
    current_user: AuthUser,
    organization_id: str,
    repos: Any,
) -> UploadActor:
    """Authorize an organisation-member (direct customer) document upload.

    Enforces, in order: authenticated principal → organisation membership →
    tenant isolation (``ensure_org_access``, which denies Processing Entity staff
    and foreign tenants while preserving internal-staff oversight) → the CL-42
    viewer read-only rule.
    """
    from api.dependencies import ensure_org_access

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="organization_id is required",
        )
    if not (current_user.is_org_member or current_user.is_internal_staff):
        await _deny(
            repos=repos,
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization member access required",
            organization_id=str(organization_id),
            user_id=current_user.user_id,
            action_reason="caller is not an organisation member",
        )

    role_name = getattr(current_user, "role_name", "") or ""
    role = getattr(current_user, "role", "") or ""
    if "org_viewer" in (role_name, role) and not current_user.is_internal_staff:
        await _deny(
            repos=repos,
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewers are read-only and cannot upload documents",
            organization_id=str(organization_id),
            user_id=current_user.user_id,
            action_reason="viewer is read-only (CL-42)",
        )

    try:
        ensure_org_access(current_user, organization_id)
    except HTTPException as exc:
        await _deny(
            repos=repos,
            status_code=exc.status_code,
            detail=str(exc.detail),
            organization_id=str(organization_id),
            user_id=current_user.user_id,
            action_reason="organisation scope check failed",
        )

    return UploadActor(
        user_id=current_user.user_id,
        organization_id=str(organization_id),
        actor_type=(
            "internal_staff" if current_user.is_internal_staff else ACTOR_ORG_USER_PROVENANCE
        ),
        organization_role=role_name or role,
    )



async def authorize_consultant_upload(
    *,
    current_user: AuthUser,
    consultant_context: Any,
    client_id: str,
    repos: Any,
) -> UploadActor:
    """Authorize a consultant upload **for** an active, authorized client.

    The active ``consultant_clients`` grant plus firm ownership is resolved by the
    existing consultant surface (404 cross-firm, 403 when the grant is not
    active), and the firm member's real ``can_upload_documents`` flag is then
    required.  The returned organisation is the client's, so the bytes are stored
    in the client organisation's namespace.
    """
    if current_user is None or consultant_context is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Consultant access required",
        )

    from api.consultant_auth import ensure_consultant_permission
    from api.v3_consultants import _authorized_client_org

    try:
        organization_id = await _authorized_client_org(
            client_id, current_user, consultant_context, repos
        )
    except HTTPException as exc:
        await _deny(
            repos=repos,
            status_code=exc.status_code,
            detail=str(exc.detail),
            organization_id="",
            user_id=current_user.user_id,
            action_reason="consultant client grant is not active or not owned by the firm",
        )

    firm_member = getattr(consultant_context, "firm_member", None)
    try:
        ensure_consultant_permission(consultant_context, "upload_documents")
    except HTTPException as exc:
        await _deny(
            repos=repos,
            status_code=exc.status_code,
            detail=str(exc.detail),
            organization_id=str(organization_id),
            user_id=current_user.user_id,
            action_reason="consultant lacks the upload_documents capability",
        )

    return UploadActor(
        user_id=current_user.user_id,
        organization_id=str(organization_id),
        actor_type=ACTOR_CONSULTANT_PROVENANCE,
        organization_role="consultant",
        consultant_firm_id=str(getattr(firm_member, "firm_id", "") or "") or None,
        consultant_membership_role=str(getattr(firm_member, "role", "") or "") or None,
        consultant_permission="upload_documents",
    )

