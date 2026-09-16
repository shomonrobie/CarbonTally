"""P6-2D — D7 durable firm + processing-mode provenance (CP1 regression suite).

Ratified decisions under test:

* ``PO-PHASE6-D7-R-20260910`` — durable, SERVER-DERIVED consultant firm
  provenance captured at action time, plus the item's processing-mode
  provenance preserved separately; actor / firm / mode / origin stay distinct;
  firm provenance is never actor-supplied and never rewritten.
* ``PO-PHASE6-D7b-R-20260910`` — no ``CONSULTANT`` ``processing_origin`` value
  (origin vocabulary stays exactly internal / PE).
* ``PO-PHASE6-D7c-R-20260910`` — no historical backfill: unrecorded rows stay
  unrecorded (``NULL``), nothing is fabricated.

What is covered:

* a consultant processing action records the firm resolved from the active
  membership/engagement relationship and the item's canonical processing mode;
* client-supplied firm / organization / actor / mode claims cannot influence
  what is recorded (actor injection, parameter tampering);
* a second firm and a later membership change can never rewrite recorded
  provenance (write-once, historical stability);
* denied actions (cross-firm, cross-organisation) record NO provenance;
* non-consultant actors (organisation member, internal staff) record no
  consultant firm provenance — the consultant path is the only source;
* automatic work acted on by a consultant records ``automatic`` (automatic vs
  manual is actor-agnostic);
* every consultant action route in the workflow surface records provenance;
* the migration is additive/nullable, has no backfill and changes no origin.
"""
from __future__ import annotations

import asyncio
import datetime as _dt
import pathlib
import uuid

from domain.billing import BillingPlan, Subscription
from tests.unit.api.fakes import admin_user, consultant_user, member_user
from tests.unit.api.test_v3_operations import _seed_batch_with_item, _seed_ops_world

PROC = "/api/v3/processing"

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
_MIGRATION = (
    _REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260910120000_p6_2d_consultant_provenance.sql"
)
_WORKFLOW_SRC = _REPO_ROOT / "backend" / "api" / "v3_processing_workflow.py"
_ORIGIN_MIGRATION = (
    _REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260902020000_v1_2_dual_origin_workflow.sql"
)

ALL_PROC_FLAGS = {
    "can_extract": True,
    "can_map": True,
    "can_validate": True,
    "can_calculate": True,
    "can_confirm_automation": True,
    "can_submit": True,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_consultant(
    world,
    *,
    user_id="u-c1",
    firm_id="firm-c1",
    org_id="org-a",
    client_id="cc-1",
    is_active=True,
    engagement_status="active",
    caps=None,
):
    """Seed one consulting firm (profile + active member) with a client grant."""
    # FIN-06 precondition: the consultant manual work under test requires the
    # organisation to have Manual Processing enabled (OFF by default).
    world.manual_processing.seed_grant("organization", org_id)
    world.consultants.seed_profile(firm_id, user_id, "C1 Advisory", is_active=is_active)
    world.consultants.seed_firm_member(
        firm_id,
        user_id,
        role="manager",
        is_active=is_active,
        can_manage_clients=True,
        **(caps or {}),
    )
    world.consultants.seed_client(
        client_id, firm_id, org_id, "Client Org", status=engagement_status
    )
    return consultant_user(user_id, f"{user_id}@example.test")


def _prov(world, item_id):
    """Read the durable D7 provenance straight from the repository surface."""
    return asyncio.run(
        world.manual_extraction.get_item_consultant_provenance(item_id)
    )


def _seed_entitlement(world, org_id="org-a", *, key="sub-p62d-1") -> None:
    asyncio.run(
        world.billing_plans.create(
            BillingPlan(
                id=str(uuid.uuid4()),
                plan_code="professional",
                name="Professional",
                price=149,
                currency="GBP",
                included_credits=500,
                version=1,
                is_active=True,
                features={},
                effective_from=_dt.datetime.now(_dt.timezone.utc),
            ),
            created_by="admin-1",
        )
    )
    asyncio.run(
        world.billing_subscriptions.upsert_active(
            Subscription(
                id=str(uuid.uuid4()),
                organization_id=org_id,
                plan_code="professional",
                plan_version=1,
                billing_mode="CREDIT",
                lifecycle_status="active",
                current_period_start=_dt.datetime.now(_dt.timezone.utc),
                current_period_end=_dt.datetime.now(_dt.timezone.utc),
                idempotency_key=key,
            ),
            created_by="admin-1",
        )
    )


class _FakeJob:
    def __init__(self, item_id, automation_extracted_data):
        self.source_item_id = item_id
        self.automation_extracted_data = automation_extracted_data


class _FakeProcessing:
    def __init__(self, by_item):
        self._by_item = by_item

    async def get_by_item(self, item_id):
        return self._by_item.get(item_id)


def _install_automatic_job(world, item) -> None:
    """Durable automatic-processing job WITH machine output → item is automatic."""
    job = _FakeJob(item.id, {"activity": "Electricity", "quantity": 1, "unit": "kWh"})
    world.processing = _FakeProcessing({item.id: job})


def _extract(client, item, data=None, **extra):
    payload = {
        "extracted_data": data
        or {"supplier": "ACME", "quantity": 100, "unit": "kWh"}
    }
    payload.update(extra)
    return client.post(f"{PROC}/items/{item.id}/extract", json=payload)


# ---------------------------------------------------------------------------
# D7 — positive: the authorised firm and the canonical mode are recorded
# ---------------------------------------------------------------------------


def test_extract_records_server_derived_firm_and_mode(
    client, world, user_provider
) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(_seed_consultant(world, caps=ALL_PROC_FLAGS))

    assert _prov(world, item.id) is None  # nothing recorded before any action

    response = _extract(client, item)
    assert response.status_code == 200, response.text

    prov = _prov(world, item.id)
    assert prov is not None, "a consultant processing action must record provenance"
    assert prov["consultant_firm_id"] == "firm-c1"
    assert prov["processing_mode"] == "manual"
    assert prov["consultant_provenance_at"] is not None


def test_repeated_consultant_actions_keep_write_once_provenance(
    client, world, user_provider
) -> None:
    """extract → map → validate: recorded once, then immutable."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(_seed_consultant(world, caps=ALL_PROC_FLAGS))

    assert _extract(client, item).status_code == 200
    first = _prov(world, item.id)

    mapped = client.post(
        f"{PROC}/items/{item.id}/map",
        json={
            "mapped_data": {"activity_type": "Natural gas"},
            "emission_factor_used": "factor-defra-gas",
        },
    )
    assert mapped.status_code == 200, mapped.text
    assert client.post(f"{PROC}/items/{item.id}/validate").status_code == 200

    assert _prov(world, item.id) == first, "provenance must never be rewritten"


def test_stage_claim_records_provenance(client, world, user_provider) -> None:
    """The stage-claim route is also a consultant action boundary."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(_seed_consultant(world, caps=ALL_PROC_FLAGS))

    claimed = client.post(f"{PROC}/items/{item.id}/start", json={"stage": "extraction"})
    assert claimed.status_code == 200, claimed.text
    prov = _prov(world, item.id)
    assert prov is not None and prov["consultant_firm_id"] == "firm-c1"


def test_consultant_review_records_provenance(client, world, user_provider) -> None:
    world.manual_extraction.seed_item(
        "item-rev-1", "org-a", "invoice.pdf", status="calculated"
    )
    user_provider.set_user(_seed_consultant(world))
    response = client.post(
        f"{PROC}/items/item-rev-1/consultant-review", json={"passed": True}
    )
    assert response.status_code == 200, response.text
    prov = _prov(world, "item-rev-1")
    assert prov is not None and prov["consultant_firm_id"] == "firm-c1"


def test_consultant_submission_records_provenance(client, world, user_provider) -> None:
    world.manual_extraction.seed_item(
        "item-sub-1", "org-a", "invoice.pdf", status="consultant_reviewed"
    )
    _seed_entitlement(world)
    user_provider.set_user(_seed_consultant(world, caps={"can_submit": True}))
    response = client.post(f"{PROC}/items/item-sub-1/consultant-submit")
    assert response.status_code == 200, response.text
    prov = _prov(world, "item-sub-1")
    assert prov is not None and prov["consultant_firm_id"] == "firm-c1"


def test_automatic_work_records_automatic_mode(client, world, user_provider) -> None:
    """Actor-agnostic mode: a CONSULTANT action on automatic work records
    ``automatic`` — the actor never determines the mode."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    _install_automatic_job(world, item)
    user_provider.set_user(_seed_consultant(world, caps=ALL_PROC_FLAGS))

    assert _extract(client, item).status_code == 200
    prov = _prov(world, item.id)
    assert prov["processing_mode"] == "automatic"
    assert prov["consultant_firm_id"] == "firm-c1"


# ---------------------------------------------------------------------------
# D7 — server-derived only: client input can never choose the provenance
# ---------------------------------------------------------------------------


def test_client_supplied_firm_org_and_actor_cannot_influence_provenance(
    client, world, user_provider
) -> None:
    """Actor injection: a request claiming another firm / organization / actor
    cannot cause those values to be recorded — the server derives the firm."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(_seed_consultant(world, caps=ALL_PROC_FLAGS))

    response = _extract(
        client,
        item,
        consultant_firm_id="firm-evil",
        firm_id="firm-evil",
        organization_id="org-b",
        processing_mode="automatic",
        extracted_by="someone-else",
        actor="someone-else",
    )
    assert response.status_code == 200, response.text

    prov = _prov(world, item.id)
    assert prov["consultant_firm_id"] == "firm-c1"
    assert prov["consultant_firm_id"] != "firm-evil"


def test_client_cannot_claim_processing_mode(client, world, user_provider) -> None:
    """The mode is the item's server-derived classification, never a claim."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(_seed_consultant(world, caps=ALL_PROC_FLAGS))

    response = _extract(client, item, processing_mode="automatic", mode="automatic")
    assert response.status_code == 200, response.text
    assert _prov(world, item.id)["processing_mode"] == "manual"


def test_second_firm_cannot_rewrite_established_provenance(
    client, world, user_provider
) -> None:
    """Cross-firm: firm B (legitimately engaged for the same client) acting
    later must NOT overwrite the firm A provenance already recorded."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)

    user_c1 = _seed_consultant(world, caps=ALL_PROC_FLAGS)
    user_provider.set_user(user_c1)
    assert _extract(client, item).status_code == 200
    assert _prov(world, item.id)["consultant_firm_id"] == "firm-c1"

    _seed_consultant(
        world,
        user_id="u-c2",
        firm_id="firm-c2",
        client_id="cc-2",
        caps=ALL_PROC_FLAGS,
    )
    user_provider.set_user(consultant_user("u-c2", "u-c2@example.test"))
    mapped = client.post(
        f"{PROC}/items/{item.id}/map",
        json={"mapped_data": {"activity_type": "Electricity"}, "emission_factor_used": "f-x"},
    )
    assert mapped.status_code == 200, mapped.text
    assert _prov(world, item.id)["consultant_firm_id"] == "firm-c1"


def test_membership_change_does_not_rewrite_recorded_provenance(
    client, world, user_provider
) -> None:
    """Historical stability: a later membership change cannot alter what an
    earlier action recorded (and an unresolvable context denies, not rewrites)."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user = _seed_consultant(world, caps=ALL_PROC_FLAGS)
    user_provider.set_user(user)
    assert _extract(client, item).status_code == 200
    recorded = _prov(world, item.id)

    # The same user acquires a second active firm membership → the consultant
    # context becomes ambiguous and is denied (fail-closed).
    world.consultants.seed_firm_member(
        "firm-other", "u-c1", role="manager", is_active=True, can_manage_clients=True
    )
    denied = client.post(f"{PROC}/items/{item.id}/validate")
    assert denied.status_code == 403, denied.text
    assert _prov(world, item.id) == recorded


def test_cross_firm_consultant_denied_and_records_no_provenance(
    client, world, user_provider
) -> None:
    """A firm engaged elsewhere cannot act on this client's item at all."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    _seed_consultant(
        world,
        user_id="u-cx",
        firm_id="firm-cx",
        org_id="org-b",
        client_id="cc-x",
        caps=ALL_PROC_FLAGS,
    )
    user_provider.set_user(consultant_user("u-cx", "u-cx@example.test"))

    response = _extract(client, item)
    assert response.status_code == 403, response.text
    assert _prov(world, item.id) is None


def test_cross_organisation_access_denied_and_records_no_provenance(
    client, world, user_provider
) -> None:
    _seed_ops_world(world)
    world.manual_extraction.seed_item("item-b-1", "org-b", "other.pdf", status="pending")
    user_provider.set_user(_seed_consultant(world, caps=ALL_PROC_FLAGS))

    response = client.post(
        f"{PROC}/items/item-b-1/extract", json={"extracted_data": {"quantity": 1}}
    )
    assert response.status_code == 403, response.text
    assert _prov(world, "item-b-1") is None


# ---------------------------------------------------------------------------
# D7 — non-consultant actors record NO consultant firm provenance
# ---------------------------------------------------------------------------


def test_org_member_action_records_no_consultant_firm_provenance(
    client, world, user_provider
) -> None:
    _seed_ops_world(world)
    # FIN-06 precondition: an organisation member performing manual extraction
    # requires the enable (the assertion under test is about provenance only).
    world.manual_processing.seed_grant("organization", "org-a")
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(member_user("org-a", "user-a", "a@example.test"))
    response = _extract(client, item)
    assert response.status_code == 200, response.text
    assert _prov(world, item.id) is None


def test_internal_staff_action_records_no_consultant_firm_provenance(
    client, world, user_provider
) -> None:
    _seed_ops_world(world)
    # FIN-06 precondition: the actor here is not resolved as a platform operator
    # by the fixture world (no seeded staff profile), so the organisation is
    # explicitly enabled; the assertion under test is about provenance only.
    world.manual_processing.seed_grant("organization", "org-a")
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(admin_user())
    response = _extract(client, item)
    assert response.status_code == 200, response.text
    assert _prov(world, item.id) is None


# ---------------------------------------------------------------------------
# Route coverage — no consultant action route bypasses the D7 boundary
# ---------------------------------------------------------------------------


def test_every_consultant_action_route_records_provenance() -> None:
    """The provenance boundary is present on every consultant action route:

    start · extract · map · validate · calculate · consultant-review ·
    consultant-submit  →  exactly seven call sites (no alternate-route bypass).
    """
    source = _WORKFLOW_SRC.read_text()
    calls = source.count("await _record_consultant_provenance(")
    assert calls == 7, (
        "expected one D7 provenance call per consultant action route; "
        f"found {calls}"
    )


# ---------------------------------------------------------------------------
# D7b — no CONSULTANT processing_origin (vocabulary frozen)
# ---------------------------------------------------------------------------


def test_d7b_origin_vocabulary_is_unchanged() -> None:
    from domain.processing_origin import (
        ORIGIN_CARBONTALLY_INTERNAL,
        ORIGIN_LABELS,
        ORIGIN_PROCESSING_ENTITY,
    )

    assert {
        ORIGIN_CARBONTALLY_INTERNAL,
        ORIGIN_PROCESSING_ENTITY,
    } == {"CARBONTALLY_INTERNAL", "PROCESSING_ENTITY"}
    assert set(ORIGIN_LABELS) == {"CARBONTALLY_INTERNAL", "PROCESSING_ENTITY"}
    assert "CONSULTANT" not in ORIGIN_LABELS

    origin_migration = _ORIGIN_MIGRATION.read_text()
    assert (
        "processing_origin IN ('CARBONTALLY_INTERNAL', 'PROCESSING_ENTITY')"
        in origin_migration
    )


def test_d7b_new_migration_adds_no_consultant_origin_value() -> None:
    text = _MIGRATION.read_text()
    executable = "\n".join(line.split("--")[0] for line in text.splitlines())
    assert "CONSULTANT" not in executable, (
        "no consultant value may appear in the executable SQL"
    )
    # The origin COLUMN, its CHECK constraint and its vocabulary are untouched:
    # the D7 migration neither alters, drops, re-adds nor constrains them (the
    # name only appears inside descriptive COMMENT string literals).
    assert "ALTER COLUMN processing_origin" not in executable
    assert "ADD COLUMN IF NOT EXISTS processing_origin" not in executable
    assert "processing_origin_check" not in executable


# ---------------------------------------------------------------------------
# D7c — additive/nullable, no historical backfill, nothing fabricated
# ---------------------------------------------------------------------------


def test_d7c_migration_is_additive_nullable_with_no_backfill() -> None:
    text = _MIGRATION.read_text()
    executable = "\n".join(line.split("--")[0] for line in text.splitlines())

    assert "IF NOT EXISTS" in executable  # idempotent
    assert "NOT NULL" not in executable  # nullable only
    assert "DEFAULT" not in executable  # no fabricated values
    assert "UPDATE public.manual_extraction_items" not in executable
    assert "INSERT INTO public.manual_extraction_items" not in executable
    for column in (
        "consultant_firm_id",
        "processing_mode",
        "consultant_provenance_at",
    ):
        assert column in executable
    # the only constraint added is the two-word mode vocabulary on the new column
    assert "processing_mode IN ('automatic', 'manual')" in executable


def test_unrecorded_item_reports_no_provenance(world) -> None:
    """No provenance is invented for an item that never had an action (D7c)."""
    item = world.manual_extraction.seed_item("item-plain-1", "org-a", "plain.pdf")
    assert _prov(world, item.id) is None



