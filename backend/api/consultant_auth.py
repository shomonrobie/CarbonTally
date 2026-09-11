"""V3 consultant authorization (Phase 7).

The consultant→firm→client authorization chain implemented server-side. It
mirrors the authoritative RLS helper ``public.is_org_consultant(org)``:

    authenticated user
        → consultant profile (active)
        → consultant firm membership (active)
        → client grant for the target organisation
            (firm member's ``client_access`` contains the org id
             OR the firm has a ``consultant_clients`` row for the org)

Every consultant-facing endpoint must pass ``require_consultant()`` and then
``ensure_consultant_org_access`` for any organisation the consultant touches —
the browser-supplied ``organization_id``/``client_id`` is never trusted
without this server-side re-authorization.

Consultant action permissions use the real ``consultant_firm_members``
``can_manage_clients`` / ``can_upload_documents`` / ``can_generate_reports`` /
``can_manage_team`` columns (no invented permission matrix).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException

from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, get_current_user
from domain.partners import ConsultantFirmMember, ConsultantProfile

#: The consultant role names the schema/seed uses (informational only — the
#: ``can_*`` flag columns are the actual authorization surface).
CONSULTANT_ROLES: tuple[str, ...] = ("owner", "manager", "consultant", "viewer")

#: WS6 / SEC-0003 — roles authorised to REVOKE a consultant-client
#: relationship (approved product decision: Owner/Admin/Manager may revoke;
#: Member/Viewer may not). This is deliberately role-based, not capability
#: based, per the approved decision.
CONSULTANT_REVOKER_ROLES: tuple[str, ...] = ("owner", "admin", "manager")

#: The real permission columns on ``consultant_firm_members``.
CONSULTANT_PERMISSIONS: dict[str, str] = {
    "manage_clients": "can_manage_clients",
    "upload_documents": "can_upload_documents",
    "generate_reports": "can_generate_reports",
    "manage_team": "can_manage_team",
    # P6-2A — consultant processing capabilities (D1).
    "extract": "can_extract",
    "map": "can_map",
    "validate": "can_validate",
    "calculate": "can_calculate",
    "confirm_automation": "can_confirm_automation",
    "submit": "can_submit",
}

#: ``consultant_clients.status`` values used by the existing repository surface.
#: D19/P6-1C lifecycle vocabulary: only ``active`` grants access (D15);
#: ``pending`` / ``rejected`` / ``suspended`` / ``ended`` carry no access;
#: ``inactive`` is the legacy soft-deactivate.
CLIENT_STATUSES: tuple[str, ...] = (
    "active", "pending", "rejected", "suspended", "ended", "inactive",
)


@dataclass(frozen=True, slots=True)
class ConsultantContext:
    """The authenticated consultant's identity (profile + firm membership)."""

    profile: ConsultantProfile
    firm_member: ConsultantFirmMember


async def _resolve_context(
    current_user: AuthUser, repos: RepositoryBundle
) -> Optional[ConsultantContext]:
    """Canonical Layer-2 consultant context resolution (P6-1B).

    The authenticated user's Consultant workspace identity is derived from
    AUTHORITATIVE server-side membership state only:

    1. the user's ACTIVE ``consultant_firm_members`` rows
       (``get_active_memberships_by_user`` — mirroring the RLS helper
       ``is_org_consultant``, which is firm_id-based);
    2. the single distinct firm those rows point at (the operating firm —
       for an owner-self consultant this is their own ``consultant_profiles``
       row, exactly as before; for a team member it is the firm whose profile
       owns the membership row);
    3. that firm's ``consultant_profiles`` row must exist and be active.

    Zero active memberships -> not a consultant. More than one DISTINCT active
    firm -> ambiguous under the single-firm assumption and therefore DENIED
    (never silently picked). Inactive/revoked membership never resolves.
    """
    memberships = await repos.consultants.get_active_memberships_by_user(
        current_user.user_id
    )
    if not memberships:
        return None
    firm_ids = {m.firm_id for m in memberships}
    if len(firm_ids) != 1:
        # Ambiguous (multiple active firms) or no membership — deny rather than
        # guess. Single-firm is the current model; RLS stays unaffected.
        return None
    # Most recent active membership row for the single firm.
    member = max(
        memberships,
        key=lambda m: (
            m.joined_at or m.invited_at
            or datetime.min.replace(tzinfo=timezone.utc)
        ),
    )
    profile = await repos.consultants.get_profile_by_id(member.firm_id)
    if profile is None or not profile.is_active:
        return None
    return ConsultantContext(profile=profile, firm_member=member)


async def resolve_consultant_context(
    current_user: AuthUser, repos: RepositoryBundle
) -> Optional[ConsultantContext]:
    """Non-raising consultant identity resolution (D21 brand-context use).

    Returns ``None`` for any non-consultant caller (customer, Processing
    Entity staff, internal staff without a consultant profile). Never raises —
    used by surfaces that fall back to CarbonTally branding instead of
    rejecting the request.
    """
    if current_user is None:
        return None
    return await _resolve_context(current_user, repos)


async def require_consultant(
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> ConsultantContext:
    """Dependency: the caller must be an active consultant firm member."""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    context = await _resolve_context(current_user, repos)
    if context is None:
        raise HTTPException(
            status_code=403,
            detail="Consultant access required (active consultant firm membership)",
        )
    return context


def ensure_consultant_permission(
    context: ConsultantContext, permission: str
) -> None:
    """Reject an action the firm member's real permission flags do not allow."""
    column = CONSULTANT_PERMISSIONS.get(permission)
    if column is None:
        raise HTTPException(status_code=422, detail=f"unknown consultant permission {permission!r}")
    if not getattr(context.firm_member, column, False):
        raise HTTPException(
            status_code=403,
            detail=f"consultant lacks permission: {permission}",
        )


def ensure_consultant_revocation_authority(context: ConsultantContext) -> None:
    """WS6 / SEC-0003 — only Owner/Admin/Manager may revoke a relationship.

    Approved product decision: Consultant Owner/Admin/Manager may revoke a
    consultant-client relationship; Consultant Member/Viewer may not. This
    check is role-based (not capability-based) per the decision.
    """
    role = (context.firm_member.role or "").lower()
    if role not in CONSULTANT_REVOKER_ROLES:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only a consultant Owner, Admin or Manager may revoke a "
                "consultant-client relationship"
            ),
        )


async def resolve_consultant_firm_id(
    current_user: AuthUser, repos: RepositoryBundle
) -> Optional[str]:
    """P6-2D (D7) — authoritative server-side consultant FIRM id for a caller.

    Returns the firm id the caller's Consultant context resolves to — the single
    active ``consultant_firm_members`` membership's firm (the same firm the
    authorization chain and the ``consultant_clients`` grant lookup use) — or
    ``None`` when the caller is not acting in the Consultant capacity
    (organisation member, internal CarbonTally staff, Processing Entity staff) or
    has no unambiguous active firm context.

    Callers MUST use this value — never a request-supplied firm/organization id —
    as the D7 firm-provenance source (``PO-PHASE6-D7-R-20260910``). It is derived
    from authoritative membership state only; no client input is consulted.
    """
    if (
        getattr(current_user, "is_internal_staff", False)
        or getattr(current_user, "is_entity_staff", False)
        or getattr(current_user, "is_org_member", False)
    ):
        return None
    context = await _resolve_context(current_user, repos)
    if context is None:
        return None
    return str(context.firm_member.firm_id)


async def ensure_consultant_org_access(
    current_user: AuthUser,
    repos: RepositoryBundle,
    organization_id: str,
) -> ConsultantContext:
    """Authorize the consultant to act on ``organization_id``.

    D15 (APPROVED 2026-08-20): consultant access to a client is based on an
    ACTIVE consultant-client authorization (``consultant_clients.status =
    'active'``). When the relationship ends, consultant access to that client
    ends. The active grant row is the single source of the relationship —
    ``client_access`` (a per-member shortcut) does not independently grant
    organisation access.
    """
    if not organization_id:
        raise HTTPException(status_code=422, detail="organization_id is required")
    context = await _resolve_context(current_user, repos)
    if context is None:
        raise HTTPException(status_code=403, detail="Consultant access required")
    client = await repos.consultants.get_client_by_org(
        context.profile.id, organization_id
    )
    if client is None or client.status != "active":
        raise HTTPException(
            status_code=403,
            detail=(
                "Consultant is not authorized for this client organization "
                "(active consultant-client grant required)"
            ),
        )
    return context


async def ensure_consultant_processing_authorized(
    current_user: AuthUser,
    repos: "RepositoryBundle",
    *,
    permission: Optional[str] = None,
    batch: Any = None,
    item: Any = None,
    organization_id: Optional[str] = None,
    requested_organization_id: Optional[str] = None,
) -> None:
    """P6-2A — canonical server-side Consultant processing authorization gate.

    Evaluates, in order, WITHOUT collapsing the axes into one boolean:

        1. actor class     — only the CONSULTANT capacity is gated here. Internal
                             CarbonTally staff (operational bypass) and customer
                             organisation members (P6-2-D10 — preserved) pass
                             through unchanged; PE staff never reach this helper
                             (denied earlier by the org-scope layer).
        2. membership      — the actor must resolve to an active Consultant firm
                             context (``_resolve_context``).
        3. engagement      — the firm must hold an ACTIVE ``consultant_clients``
                             grant for the SERVER-DERIVED batch organization.
        4. capability      — when a permission name is supplied, the member
                             must hold the corresponding processing flag
                             (``ensure_consultant_permission``). ``permission=None``
                             (P6-2B-1 Consultant Review) skips the capability
                             check deliberately: the six-flag model is frozen
                             and Review is a readiness control, not an
                             assurance/QC control; `can_submit` is NOT required
                             for Review.
        5. resource scope  — the requested organization (if any is supplied by
                             the caller) must EQUAL the resource's authoritative
                             organization (``batch.organization_id``, or the
                             server-derived ``organization_id`` for job
                             resources); mismatch → DENY (no silent
                             substitution). When both are supplied they must
                             agree.
        6. D38 conflict    — an open item-level D38 assignment OR a batch-level
                             assignment carrier (``entity_id`` / ``assigned_to``)
                             means the work is held by another processing actor;
                             without an explicitly recognized Operations-
                             controlled handoff (none exists yet — P6-2B
                             deferred) the Consultant action is DENIED
                             (fail-closed, P6-2-D3).

    The org id and item identity are always derived server-side from the loaded
    batch/item — never trusted from a Consultant-supplied value.
    """
    if getattr(current_user, "is_internal_staff", False) or getattr(
        current_user, "is_entity_staff", False
    ):
        return  # staff capacity: not the consultant contract
    if getattr(current_user, "is_org_member", False):
        return  # organisation-member capacity preserved (P6-2-D10)

    context = await _resolve_context(current_user, repos)
    if context is None:
        # Not a consultant context — the org-access layer already denied this
        # caller before this helper ran, so fail closed here as well.
        raise HTTPException(
            status_code=403,
            detail="Consultant processing access requires an active consultant membership",
        )

    authoritative_org = str(organization_id or "")
    if not authoritative_org:
        authoritative_org = str(getattr(batch, "organization_id", "") or "")
    if not authoritative_org:
        raise HTTPException(
            status_code=422, detail="resource has no authoritative organization"
        )
    if requested_organization_id is not None and str(requested_organization_id) != authoritative_org:
        raise HTTPException(
            status_code=403,
            detail="requested organization does not match the resource's organization",
        )
    # Cross-surface guard: when BOTH a job organization and a batch are supplied
    # they must agree (the batch belongs to the authoritative client org).
    if batch is not None and str(getattr(batch, "organization_id", "") or "") not in ("", authoritative_org):
        raise HTTPException(
            status_code=403,
            detail="resource organization conflict (batch does not belong to the job's organization)",
        )

    client = await repos.consultants.get_client_by_org(
        context.profile.id, authoritative_org
    )
    if client is None or client.status != "active":
        raise HTTPException(
            status_code=403,
            detail=(
                "Consultant is not authorized for this client organization "
                "(active consultant-client grant required)"
            ),
        )

    ensure_consultant_permission(context, permission) if permission is not None else None

    # D38 conflict (P6-2-D3): open item assignment or batch-level default
    # assignment carrier => work is held by another processing actor. Jobs
    # without a resolved source item/batch have no D38-held work to gate.
    if item is not None:
        open_assignment = await repos.manual_extraction.work_item_current(
            str(getattr(item, "id", "") or "")
        )
        if open_assignment is not None:
            raise HTTPException(
                status_code=403,
                detail=(
                    "item is currently assigned to another processing actor under D38; "
                    "consultant action denied (no authorized handoff)"
                ),
            )
        if batch is not None and (
            getattr(batch, "entity_id", None) is not None
            or getattr(batch, "assigned_to", None) is not None
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "batch is assigned to a processing actor (entity/internal); "
                    "consultant action denied (no authorized handoff)"
                ),
            )


async def ensure_consultant_review_authorized(
    current_user: AuthUser,
    repos: "RepositoryBundle",
    *,
    batch: Any,
    item: Any,
) -> None:
    """P6-2B-1 — canonical Consultant Review authorization gate.

    Consultant Review is a CONSULTANT-capacity stage action:

      * organisation members, internal staff and Processing Entity staff are
        NOT Consultant reviewers → DENY (the review stage is not a customer or
        internal-ops control);
      * otherwise the canonical P6-2A resolver is reused with
        ``permission=None`` — active membership → active engagement →
        server-derived resource scope → D38 conflict. No seventh permission
        flag and NO dependency on ``can_submit`` (frozen six-flag model;
        self-review ratified by P6-2B-D1).
    """
    if getattr(current_user, "is_internal_staff", False) or getattr(
        current_user, "is_entity_staff", False
    ):
        raise HTTPException(
            status_code=403,
            detail="Consultant Review requires a Consultant capacity",
        )
    if getattr(current_user, "is_org_member", False):
        raise HTTPException(
            status_code=403,
            detail="Consultant Review requires a Consultant capacity",
        )
    await ensure_consultant_processing_authorized(
        current_user,
        repos,
        batch=batch,
        item=item,
        permission=None,
    )


async def ensure_consultant_submission_authorized(
    current_user: AuthUser,
    repos: "RepositoryBundle",
    *,
    batch: Any,
    item: Any,
) -> None:
    """P6-2B-2 — canonical Consultant submission authorization gate.

    Consultant submission (Consultant Review → CarbonTally QC) is a
    CONSULTANT-capacity action:

      * organisation members, internal staff and Processing Entity staff are
        NOT submitters → DENY (submission is not a customer or internal-ops
        control and never grants QC authority);
      * otherwise the canonical P6-2A resolver is reused with
        ``permission="submit"`` — active membership → active engagement →
        server-derived resource scope → ``can_submit`` capability → D38
        conflict. ``can_submit`` is the ONLY capability that authorizes
        submission (frozen six-flag model, D1); no other capability
        substitutes; submission never grants CarbonTally QC authority.
    """
    if getattr(current_user, "is_internal_staff", False) or getattr(
        current_user, "is_entity_staff", False
    ):
        raise HTTPException(
            status_code=403,
            detail="Consultant submission requires a Consultant capacity",
        )
    if getattr(current_user, "is_org_member", False):
        raise HTTPException(
            status_code=403,
            detail="Consultant submission requires a Consultant capacity",
        )
    await ensure_consultant_processing_authorized(
        current_user,
        repos,
        batch=batch,
        item=item,
        permission="submit",
    )
