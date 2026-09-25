"""P17 acting-for / delegated-user tests (implementation tests).

Pure, no DB. This is the security-critical half of the P17 model, so the tests
are written as ALLOW/DENY pairs rather than happy paths:

* ACTING FOR is context, never authorization (POST-ARCH §35; UIUX-01 §6, §44);
* an actor may only act for an organization they are already entitled to;
* the resolved acting-for organization is the ENTITLED one, so a caller cannot
  attribute an operation to an arbitrary tenant by passing its id;
* a mislabelled "self" operation is recorded truthfully as a delegation.
"""
from __future__ import annotations

import pytest

from core.exceptions import ActingForError
from domain.acting_for import (
    ActingForContext,
    ActingForKind,
    Entitlement,
    EntitlementBasis,
    assert_acting_for_allowed,
    resolve_acting_for,
)

CONSULTANT_ORG = "org-consultant"
CLIENT_ORG = "org-client"
OTHER_ORG = "org-someone-else"
SECOND_CLIENT_ORG = "org-second-client"
CONSULTANT_USER = "user-consultant"

DELEGATED = Entitlement(
    organization_id=CLIENT_ORG,
    basis=EntitlementBasis.ACTIVE_CONSULTANT_DELEGATION,
    actor_organization_id=CONSULTANT_ORG,
)
MEMBERSHIP = Entitlement(
    organization_id=CLIENT_ORG,
    basis=EntitlementBasis.ORGANIZATION_MEMBERSHIP,
    actor_organization_id=CLIENT_ORG,
)


# ---------------------------------------------------------------------------
# ALLOW: an entitled actor may act for the entitled organization
# ---------------------------------------------------------------------------
def test_consultant_may_act_for_an_actively_delegated_client() -> None:
    context = resolve_acting_for(
        actor_user_id=CONSULTANT_USER,
        target_organization_id=CLIENT_ORG,
        entitlements=[DELEGATED],
        kind=ActingForKind.CONSULTANT_FOR_CLIENT,
    )
    assert context.acting_for_organization_id == CLIENT_ORG
    assert context.actor_organization_id == CONSULTANT_ORG
    assert context.basis is EntitlementBasis.ACTIVE_CONSULTANT_DELEGATION
    assert context.is_delegated is True


def test_a_member_operating_their_own_organization_is_not_delegated() -> None:
    context = resolve_acting_for(
        actor_user_id="user-1",
        target_organization_id=CLIENT_ORG,
        entitlements=[MEMBERSHIP],
        kind=ActingForKind.SELF,
    )
    assert context.acting_for_organization_id == CLIENT_ORG
    assert context.actor_organization_id == CLIENT_ORG
    assert context.is_delegated is False


# ---------------------------------------------------------------------------
# DENY: acting-for never creates an entitlement
# ---------------------------------------------------------------------------
def test_actor_with_no_entitlement_cannot_act_for_an_organization() -> None:
    with pytest.raises(ActingForError) as exc:
        resolve_acting_for(
            actor_user_id=CONSULTANT_USER,
            target_organization_id=OTHER_ORG,
            entitlements=[DELEGATED],
        )
    assert exc.value.http_status == 403
    assert exc.value.details["target_organization_id"] == OTHER_ORG


def test_an_entitlement_to_one_client_does_not_permit_acting_for_another() -> None:
    """Cross-boundary isolation: one delegation is not a master key."""
    second_delegation = Entitlement(
        organization_id=SECOND_CLIENT_ORG,
        basis=EntitlementBasis.ACTIVE_CONSULTANT_DELEGATION,
        actor_organization_id=CONSULTANT_ORG,
    )
    # The consultant holds delegations to two clients, but holds none for
    # OTHER_ORG, so acting for OTHER_ORG must still be denied.
    with pytest.raises(ActingForError):
        resolve_acting_for(
            actor_user_id=CONSULTANT_USER,
            target_organization_id=OTHER_ORG,
            entitlements=[DELEGATED, second_delegation],
            actor_organization_id=CONSULTANT_ORG,
        )


def test_empty_entitlements_deny_by_default() -> None:
    with pytest.raises(ActingForError):
        assert_acting_for_allowed(
            actor_user_id=CONSULTANT_USER,
            target_organization_id=CLIENT_ORG,
            entitlements=[],
        )


# ---------------------------------------------------------------------------
# The resolved organization is the ENTITLED one
# ---------------------------------------------------------------------------
def test_resolved_context_always_names_an_entitled_organization() -> None:
    """A caller cannot attribute an operation to an arbitrary tenant."""
    context = resolve_acting_for(
        actor_user_id=CONSULTANT_USER,
        target_organization_id=CLIENT_ORG,
        entitlements=[DELEGATED],
    )
    assert context.acting_for_organization_id == CLIENT_ORG


def test_mislabelled_self_operation_is_recorded_as_a_delegation() -> None:
    """The label must not override the truth about who owns the data."""
    context = resolve_acting_for(
        actor_user_id=CONSULTANT_USER,
        target_organization_id=CLIENT_ORG,
        entitlements=[DELEGATED],
        kind=ActingForKind.SELF,
        actor_organization_id=CONSULTANT_ORG,
    )
    assert context.kind is ActingForKind.DELEGATED_USER
    assert context.is_delegated is True


def test_assert_acting_for_allowed_returns_the_matching_entitlement() -> None:
    entitlement = assert_acting_for_allowed(
        actor_user_id="user-1",
        target_organization_id=CLIENT_ORG,
        entitlements=[
            Entitlement(OTHER_ORG, EntitlementBasis.ORGANIZATION_MEMBERSHIP),
            DELEGATED,
        ],
    )
    assert entitlement.organization_id == CLIENT_ORG


# ---------------------------------------------------------------------------
# Audit payload parity across the ARCH-04 §10.3 paths
# ---------------------------------------------------------------------------
def test_audit_columns_carry_both_actor_and_acting_for_organizations() -> None:
    context = resolve_acting_for(
        actor_user_id=CONSULTANT_USER,
        target_organization_id=CLIENT_ORG,
        entitlements=[DELEGATED],
    )
    assert context.as_audit_columns() == {
        "actor_organization_id": CONSULTANT_ORG,
        "acting_for_organization_id": CLIENT_ORG,
    }


def test_provenance_record_is_frozen_and_self_describing() -> None:
    """The context states who, for whom and on what basis, and cannot be mutated."""
    context = ActingForContext(
        actor_user_id="u",
        actor_organization_id=CONSULTANT_ORG,
        acting_for_organization_id=CLIENT_ORG,
        kind=ActingForKind.CONSULTANT_FOR_CLIENT,
        basis=EntitlementBasis.ACTIVE_CONSULTANT_DELEGATION,
        is_delegated=True,
    )
    with pytest.raises(Exception):
        context.acting_for_organization_id = OTHER_ORG  # type: ignore[misc]
