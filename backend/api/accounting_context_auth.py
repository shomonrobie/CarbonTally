"""P17 organization / consultant accounting-context service.

Task: ``P17-IMPLEMENT-02-20260925-API-ACTING-FOR-WRITE-PATHS``.

Answers one question authoritatively, for every persona:

    "Which organisation is this actor operating for, and what entitles them to
     operate for it?"

The answer is derived from **authoritative relationship state only** — an active
``organization_members`` row, the actor's own consultant firm organization, or an
``active`` ``consultant_clients`` grant. It is never derived from the request, and
never inferred merely because a user happens to be a consultant.

Existing resolution is REUSED rather than duplicated:

* ``api.consultant_auth._resolve_context`` — the canonical consultant identity
  chain (active ``consultant_firm_members`` → single firm → active profile);
* ``ConsultantsRepository.get_client_by_org`` / ``list_clients`` — the same grant
  lookup ``ensure_consultant_org_access`` uses, so the D15 "only ``active``
  grants access" rule is honoured in one place;
* ``organization_members`` — the same active-membership predicate the RLS helper
  ``public.is_org_member`` uses;
* ``AuthUser`` — the existing authentication/RBAC model for staff.

**ACTING FOR is context, not authorization.** A resolved context never widens
access: every requested organisation is separately authorised here, and the
data-owning organisation is verified against the actor's authorized set before any
write is attributed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException

from api.dependencies import RepositoryBundle
from auth import AuthUser
from api.consultant_auth import resolve_consultant_context
from core.exceptions import ValidationFailedError
from domain.acting_for import ActingForKind, EntitlementBasis
from domain.cams import CamsPersona

__all__ = [
    "AuthorizedOrganization",
    "AccountingContext",
    "RELATIONSHIP_OWN",
    "RELATIONSHIP_CONSULTANT_CLIENT",
    "RELATIONSHIP_INTERNAL",
    "resolve_persona",
    "list_authorized_organizations",
    "resolve_accounting_context",
    "ensure_record_owner_authorized",
    "resolve_authorized_supplier",
]

RELATIONSHIP_OWN = "OWN"
RELATIONSHIP_CONSULTANT_CLIENT = "CONSULTANT_CLIENT"
RELATIONSHIP_INTERNAL = "CARBONTALLY_INTERNAL"


@dataclass(frozen=True, slots=True)
class AuthorizedOrganization:
    """One organisation the actor may act for, and why.

    Attributes:
        organization_id: The organisation.
        name: Human-readable name, when the row exists.
        relationship: ``OWN`` / ``CONSULTANT_CLIENT`` / ``CARBONTALLY_INTERNAL``.
        entitlement_basis: The authoritative basis (never ``ACTING_FOR``).
        is_own: True when this is the actor's own organisation.
        organization_type: The P17 organisation kind (``CUSTOMER`` by default).
        consolidation_approach: DC-07 value, or ``None`` when undecided.
    """

    organization_id: str
    name: Optional[str]
    relationship: str
    entitlement_basis: str
    is_own: bool
    organization_type: str = "CUSTOMER"
    consolidation_approach: Optional[str] = None

    def as_payload(self) -> dict:
        """Return the API representation."""
        return {
            "organization_id": self.organization_id,
            "name": self.name,
            "relationship": self.relationship,
            "entitlement_basis": self.entitlement_basis,
            "is_own": self.is_own,
            "organization_type": self.organization_type,
            "consolidation_approach": self.consolidation_approach,
            "consolidation_decided": self.consolidation_approach is not None,
        }


@dataclass(frozen=True, slots=True)
class AccountingContext:
    """The resolved accounting context for one request.

    Attributes:
        actor_user_id: The authenticated actor.
        persona: Which operating domain the actor belongs to.
        own_organization_id: The actor's own organisation (firm org for a
            consultant). ``None`` when not yet linked or not applicable.
        data_owning_organization_id: The tenant that OWNS the accounting data.
            This is the authorisation key.
        acting_for_organization_id: The organisation the actor is operating for.
            Equal to the data-owning organisation: acting-for can never point
            somewhere the actor is not entitled to.
        acting_for_organization_name: Human-readable name, when available.
        actor_organization_id: The organisation the actor belongs to, recorded for
            provenance. ``None`` for internal staff.
        is_delegated: True when acting for an organisation other than their own.
        entitlement_basis: The verified basis for the operation.
        acting_for_kind: The recorded acting-for relationship kind.
        consolidation_approach: DC-07 value for the data-owning organisation.
    """

    actor_user_id: str
    persona: str
    own_organization_id: Optional[str]
    data_owning_organization_id: str
    acting_for_organization_id: str
    acting_for_organization_name: Optional[str]
    actor_organization_id: Optional[str]
    is_delegated: bool
    entitlement_basis: str
    acting_for_kind: str
    consolidation_approach: Optional[str] = None

    def provenance_columns(self) -> dict[str, Optional[str]]:
        """The payload persisted on every P17 acting-for carrier.

        Identical shape to ``ActingForContext.as_audit_columns()`` so one writer
        serves all nine ARCH-04 §10.3 paths.
        """
        return {
            "actor_organization_id": self.actor_organization_id,
            "acting_for_organization_id": self.acting_for_organization_id,
        }

    def as_payload(self) -> dict:
        """Return the API representation including the UI-facing acting-for label."""
        return {
            "actor_user_id": self.actor_user_id,
            "persona": self.persona,
            "own_organization_id": self.own_organization_id,
            "data_owning_organization_id": self.data_owning_organization_id,
            "acting_for_organization_id": self.acting_for_organization_id,
            "acting_for_organization_name": self.acting_for_organization_name,
            "actor_organization_id": self.actor_organization_id,
            "is_delegated": self.is_delegated,
            "entitlement_basis": self.entitlement_basis,
            "acting_for_kind": self.acting_for_kind,
            "consolidation_approach": self.consolidation_approach,
            "acting_for_label": (
                "ACTING FOR: "
                f"{self.acting_for_organization_name or self.acting_for_organization_id}"
                if self.is_delegated
                else None
            ),
        }


def resolve_persona(current_user: AuthUser) -> str:
    """Classify the actor into the CAMS operating domain.

    Personas exist for authorisation and presentation, never for accounting: the
    accounting rules are identical for every persona.
    """
    if current_user.is_internal_staff:
        return CamsPersona.STAFF
    if current_user.is_entity_staff:
        return CamsPersona.PROCESSING_ENTITY
    if getattr(current_user, "is_org_member", False):
        return CamsPersona.DIRECT_CUSTOMER
    return CamsPersona.DELEGATED_USER


async def list_authorized_organizations(
    current_user: AuthUser, repos: RepositoryBundle
) -> list[AuthorizedOrganization]:
    """Every organisation the actor may act for, with the reason.

    Built only from authoritative relationship state:

    1. active ``organization_members`` rows → ``OWN`` / ``ORGANIZATION_MEMBERSHIP``;
    2. the actor's own consultant firm organization (``consultant_profiles.
       organization_id``, the P17 HIGH-01 linkage) → ``OWN`` /
       ``CONSULTANT_FIRM_MEMBERSHIP``;
    3. ``consultant_clients`` grants whose status is exactly ``active`` (the D15
       rule) → ``CONSULTANT_CLIENT`` / ``ACTIVE_CONSULTANT_DELEGATION``.

    An organisation reached by more than one route keeps the strongest
    relationship (membership wins over a delegated grant). Being a consultant
    does NOT by itself add any organisation: a consultant with no active grant
    sees only their own firm.
    """
    assert current_user is not None
    found: dict[str, AuthorizedOrganization] = {}

    member_roles = await repos.accounting_context.list_active_member_roles(
        current_user.user_id
    )
    for org_id in member_roles:
        summary = await repos.accounting_context.get_organization_summary(org_id)
        if summary is None or not summary["is_active"]:
            continue
        found[org_id] = AuthorizedOrganization(
            organization_id=org_id,
            name=summary["name"],
            relationship=RELATIONSHIP_OWN,
            entitlement_basis=EntitlementBasis.ORGANIZATION_MEMBERSHIP.value,
            is_own=True,
            organization_type=summary["organization_type"],
            consolidation_approach=summary["consolidation_approach"],
        )

    consultant = await resolve_consultant_context(current_user, repos)
    if consultant is not None:
        firm_org = consultant.profile.organization_id
        if firm_org and firm_org not in found:
            summary = await repos.accounting_context.get_organization_summary(firm_org)
            if summary is not None and summary["is_active"]:
                found[firm_org] = AuthorizedOrganization(
                    organization_id=firm_org,
                    name=summary["name"] or consultant.profile.company_name,
                    relationship=RELATIONSHIP_OWN,
                    entitlement_basis=(
                        EntitlementBasis.CONSULTANT_FIRM_MEMBERSHIP.value
                    ),
                    is_own=True,
                    organization_type=summary["organization_type"],
                    consolidation_approach=summary["consolidation_approach"],
                )
        for client in await repos.consultants.list_clients(consultant.profile.id):
            if client.status != "active":
                # D15: only an ACTIVE grant grants access. pending / rejected /
                # suspended / ended / inactive grant nothing.
                continue
            client_org = str(client.organization_id)
            if client_org in found:
                continue
            summary = await repos.accounting_context.get_organization_summary(client_org)
            if summary is None or not summary["is_active"]:
                continue
            found[client_org] = AuthorizedOrganization(
                organization_id=client_org,
                name=summary["name"] or client.client_name,
                relationship=RELATIONSHIP_CONSULTANT_CLIENT,
                entitlement_basis=EntitlementBasis.ACTIVE_CONSULTANT_DELEGATION.value,
                is_own=False,
                organization_type=summary["organization_type"],
                consolidation_approach=summary["consolidation_approach"],
            )

    return sorted(
        found.values(), key=lambda o: (not o.is_own, o.name or o.organization_id)
    )


async def resolve_accounting_context(
    current_user: AuthUser,
    repos: RepositoryBundle,
    acting_for_organization_id: Optional[str] = None,
) -> AccountingContext:
    """Resolve and AUTHORISE the accounting context for one request.

    ``acting_for_organization_id`` is a REQUEST, never an authority: it must match
    an organisation the actor is entitled to, otherwise the request is refused
    with 403. Changing this value therefore cannot reach another tenant's data.

    Raises:
        HTTPException 401: no authenticated actor.
        HTTPException 403: the actor is not entitled to the requested
            organisation (the fail-closed default).
        HTTPException 404: internal staff requested an organisation that does
            not exist.
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    base_persona = resolve_persona(current_user)
    authorized = await list_authorized_organizations(current_user, repos)
    by_id = {o.organization_id: o for o in authorized}

    requested = acting_for_organization_id or current_user.organization_id
    if requested is None:
        # No explicit selection and no ambient organization: fall back to the
        # actor's OWN organization (their membership organization, or their
        # consultant firm organization). This is the "acts for own organization
        # by default" rule; it is still resolved from the authorized set, never
        # assumed.
        requested = next(
            (o.organization_id for o in authorized if o.is_own), None
        )
    chosen: Optional[AuthorizedOrganization] = None

    if requested is not None and requested in by_id:
        chosen = by_id[requested]
    elif base_persona == CamsPersona.PROCESSING_ENTITY:
        # PE boundary: a Processing Entity operator does not get customer
        # organisation access by default. Fail closed rather than assume.
        raise HTTPException(
            status_code=403,
            detail=(
                "Processing Entity staff may not act for a customer organization "
                "directly; PE access is assignment-scoped"
            ),
        )
    elif base_persona == CamsPersona.STAFF:
        # Internal staff follow the existing CarbonTally staff authorization
        # capability gate on the route is unchanged. This grants no
        # customer-organization authority the staff model does not already have.
        if requested is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "internal staff have no own organization; "
                    "acting_for_organization_id is required"
                ),
            )
        summary = await repos.accounting_context.get_organization_summary(requested)
        if summary is None or not summary["is_active"]:
            raise HTTPException(status_code=404, detail="Organization not found")
        chosen = AuthorizedOrganization(
            organization_id=requested,
            name=summary["name"],
            relationship=RELATIONSHIP_INTERNAL,
            entitlement_basis=EntitlementBasis.CARBONTALLY_INTERNAL_ROLE.value,
            is_own=False,
            organization_type=summary["organization_type"],
            consolidation_approach=summary["consolidation_approach"],
        )

    if chosen is None:
        if requested is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "no own organization is available and no "
                    "acting_for_organization_id was supplied"
                ),
            )
        raise HTTPException(
            status_code=403,
            detail=(
                "not authorized to act for this organization: no active "
                "membership, consultant firm organization or active "
                "consultant-client grant authorizes it"
            ),
        )

    own_org = next((o.organization_id for o in authorized if o.is_own), None)
    is_delegated = chosen.relationship == RELATIONSHIP_CONSULTANT_CLIENT

    # Refine the persona from the RESOLVED relationship. The synchronous
    # classification cannot see consultant state, so a pure consultant (who is
    # not an organisation member) would otherwise be reported as a generic
    # delegated user. The resolved basis is authoritative here.
    if is_delegated:
        persona = CamsPersona.CONSULTANT_CLIENT
    elif chosen.entitlement_basis == EntitlementBasis.CONSULTANT_FIRM_MEMBERSHIP.value:
        persona = CamsPersona.CONSULTANT
    else:
        persona = base_persona

    if chosen.relationship == RELATIONSHIP_INTERNAL:
        kind = ActingForKind.CARBONTALLY_STAFF.value
    elif is_delegated:
        kind = ActingForKind.CONSULTANT_FOR_CLIENT.value
    elif chosen.entitlement_basis == EntitlementBasis.CONSULTANT_FIRM_MEMBERSHIP.value:
        kind = ActingForKind.CONSULTANT_TEAM_FOR_FIRM.value
    else:
        kind = ActingForKind.SELF.value

    return AccountingContext(
        actor_user_id=current_user.user_id,
        persona=persona,
        own_organization_id=own_org,
        data_owning_organization_id=chosen.organization_id,
        acting_for_organization_id=chosen.organization_id,
        acting_for_organization_name=chosen.name,
        actor_organization_id=own_org,
        is_delegated=is_delegated,
        entitlement_basis=chosen.entitlement_basis,
        acting_for_kind=kind,
        consolidation_approach=chosen.consolidation_approach,
    )


async def ensure_record_owner_authorized(
    current_user: AuthUser,
    repos: RepositoryBundle,
    owner_organization_id: str,
) -> AccountingContext:
    """Authorise the actor for a RECORD's data-owning organisation.

    This is the guard that makes "the data-owning organization cannot be
    overridden by an unauthorized actor" true: the RECORD's owner is the authority
    the actor must satisfy, so a caller cannot attribute a write to a tenant it has
    no relationship with merely by naming a different acting-for value.
    """
    return await resolve_accounting_context(
        current_user, repos, acting_for_organization_id=owner_organization_id
    )


async def resolve_authorized_supplier(
    repos: RepositoryBundle,
    supplier_id: Optional[str],
    data_owner: str,
) -> Optional[str]:
    """Resolve a supplier CLAIM against the authorized data-owning organization.

    A ``supplier_id`` in a request body is a claim, never an authority. The row is
    loaded server-side and accepted only when it belongs to the **resolved**
    data-owning organization, so a calculation cannot attribute an emission to
    another tenant's supplier. A supplier that belongs to another organization is
    deliberately indistinguishable from one that does not exist, so the response
    confirms nothing about another tenant's master data.

    ``emissions_logs.supplier_id`` carries no foreign key, so an unvalidated id
    would be stored silently — that is exactly why the check is here and not left
    to the database.

    Args:
        repos: The request's repository bundle (``suppliers`` is always bound).
        supplier_id: The claimed supplier, or ``None`` for "no supplier claimed".
        data_owner: The RESOLVED data-owning organization (the authorization key).

    Returns:
        The validated supplier id, or ``None`` when no supplier was claimed.

    Raises:
        ValidationFailedError 422: the claim cannot be honoured — the supplier does
            not exist or is not available to this organization. Nothing is
            persisted, and the supplier is never guessed.
    """
    if supplier_id is None:
        return None
    supplier = await repos.suppliers.get(supplier_id)
    if supplier is None or str(supplier.organization_id) != str(data_owner):
        raise ValidationFailedError(
            "no supplier with that id is available to this organization",
            details={"field": "supplier_id", "supplier_id": supplier_id},
        )
    return supplier_id

