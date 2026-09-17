"""Step 2C / POD-4 — controlled, tenant-aware P1 rollout.

PO decision C: do NOT globally enable P1. `enabled` must be honoured only for an
explicitly allowlisted organisation, everything else keeps today's `shadow`
behaviour, and the resolution must be deterministic, auditable and reversible.
"""
from __future__ import annotations

from services import extraction_fidelity as p1
from services.automatic_extraction import _apply_p1_fidelity

ENV = {p1.SHAPE_MODE_ENV: "enabled", p1.ROLLOUT_ALLOWLIST_ENV: "org-a, org-b"}


def test_default_is_shadow_with_no_configuration():
    assert p1.shape_mode({}) == p1.MODE_SHADOW
    assert p1.shape_mode({}, organization_id="org-a") == p1.MODE_SHADOW


def test_an_invalid_value_falls_back_to_shadow():
    assert p1.shape_mode({p1.SHAPE_MODE_ENV: "yes-please"}) == p1.MODE_SHADOW
    assert p1.shape_mode({p1.SHAPE_MODE_ENV: "ENABLED  "}) == p1.MODE_SHADOW


def test_enabled_without_an_allowlist_is_downgraded_to_shadow():
    # Fail-safe: misconfiguration must never enable P1 for every tenant.
    assert p1.shape_mode({p1.SHAPE_MODE_ENV: "enabled"}) == p1.MODE_SHADOW
    assert p1.shape_mode({p1.SHAPE_MODE_ENV: "enabled"}, organization_id="org-a") == p1.MODE_SHADOW
    assert p1.shape_mode({p1.SHAPE_MODE_ENV: "enabled", p1.ROLLOUT_ALLOWLIST_ENV: " , "}) == p1.MODE_SHADOW


def test_enabled_is_honoured_only_for_allowlisted_organisations():
    assert p1.shape_mode(ENV, organization_id="org-a") == p1.MODE_ENABLED
    assert p1.shape_mode(ENV, organization_id="org-b") == p1.MODE_ENABLED   # whitespace trimmed
    assert p1.shape_mode(ENV, organization_id="org-c") == p1.MODE_SHADOW
    # No tenant context at all must never be treated as "allowed".
    assert p1.shape_mode(ENV) == p1.MODE_SHADOW


def test_a_global_opt_in_requires_the_explicit_wildcard():
    env = {p1.SHAPE_MODE_ENV: "enabled", p1.ROLLOUT_ALLOWLIST_ENV: "*"}
    assert p1.shape_mode(env, organization_id="anything") == p1.MODE_ENABLED


def test_off_and_shadow_are_never_upgraded_by_the_allowlist():
    off = {p1.SHAPE_MODE_ENV: "off", p1.ROLLOUT_ALLOWLIST_ENV: "org-a"}
    assert p1.shape_mode(off, organization_id="org-a") == p1.MODE_OFF
    shadow = {p1.SHAPE_MODE_ENV: "shadow", p1.ROLLOUT_ALLOWLIST_ENV: "org-a"}
    assert p1.shape_mode(shadow, organization_id="org-a") == p1.MODE_SHADOW


def test_rollout_status_is_an_audit_record_without_secrets():
    status = p1.rollout_status(ENV, organization_id="org-a")
    assert status == {
        "requested_mode": "enabled",
        "effective_mode": "enabled",
        "organization_id": "org-a",
        "in_rollout": True,
        "allowlist_size": 2,
        "allow_all": False,
    }
    outside = p1.rollout_status(ENV, organization_id="org-z")
    assert outside["effective_mode"] == "shadow"
    assert outside["in_rollout"] is False

    # Reversibility: removing the organisation from the allowlist restores the
    # existing safe behaviour, with no restart-time state to unwind.
    reverted = p1.rollout_status(
        {p1.SHAPE_MODE_ENV: "enabled", p1.ROLLOUT_ALLOWLIST_ENV: "org-b"},
        organization_id="org-a",
    )
    assert reverted["effective_mode"] == "shadow"


MULTI_LINE_TEXT = (
    "Invoice INV-1001  Supplier: Acme Fuels Ltd\n"
    "Diesel 1,500 litres 1,800.00\n"
    "Unleaded petrol 900 litres 1,200.00\n"
    "Site: Birmingham Head Office\n"
)


def test_the_hook_keeps_shadow_output_unchanged_outside_the_rollout(monkeypatch):
    monkeypatch.setenv(p1.SHAPE_MODE_ENV, "enabled")
    monkeypatch.setenv(p1.ROLLOUT_ALLOWLIST_ENV, "org-inside")

    outcome = _apply_p1_fidelity(
        MULTI_LINE_TEXT,
        method="pdf",
        page_count=1,
        extracted={"supplier": "Acme Fuels Ltd"},
        unresolved=["quantity", "unit"],
        organization_id="org-outside",
    )

    assert outcome["rollout"]["effective_mode"] == p1.MODE_SHADOW
    assert outcome["block"] is None
    assert outcome["coverage"]["mode"] == p1.MODE_SHADOW
    # shadow never rewrites the extraction
    assert outcome["extracted"] == {"supplier": "Acme Fuels Ltd"}


def test_the_hook_governs_an_allowlisted_organisation(monkeypatch):
    monkeypatch.setenv(p1.SHAPE_MODE_ENV, "enabled")
    monkeypatch.setenv(p1.ROLLOUT_ALLOWLIST_ENV, "org-inside")

    outcome = _apply_p1_fidelity(
        MULTI_LINE_TEXT,
        method="pdf",
        page_count=1,
        extracted={"supplier": "Acme Fuels Ltd"},
        unresolved=["quantity", "unit"],
        organization_id="org-inside",
    )

    assert outcome["rollout"]["effective_mode"] == p1.MODE_ENABLED
    assert outcome["rollout"]["in_rollout"] is True
    assert outcome["coverage"]["mode"] == p1.MODE_ENABLED
