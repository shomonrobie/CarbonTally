#!/usr/bin/env python3
"""CT-MP-SUB-004 / PD-5 — deterministic, resettable Demo Lab QA fixture.

The independent verification of CT-MP-SUB-004 could not browser-verify the
POSITIVE Manual Processing coverage states (finding **F-5**, NV-1…NV-4, NV-8):
no consultant firm in the Demo Lab reported ``enabled:true``, no plan carried
``features.consultant_manual_processing``, no organisation carried a Manual
Processing subscription, and ``capacity`` was ``null``.

The Product Owner authorised a purpose-built QA fixture
(``docs/architecture/CT-MP-SUB-004-PO-decision-record.md`` §7, **PD-5**) to make
those already-implemented states reachable for browser verification. PD-5
authorises **QA-fixture work only**: no application code, no product behaviour,
no schema/migration/RLS change, no production access, no deployment.

This module EXTENDS the existing DEMO-T1 pattern (:mod:`lab`, :mod:`provision`)
rather than inventing a parallel mechanism:

* it reuses ``lab`` (names, ports, deterministic UUIDs, psql/HTTP helpers,
  local-only credentials) and ``provision`` (the GoTrue user upsert + SQL
  literal helpers);
* every fixture row has a **deterministic id** (``lab.deterministic_uuid``) and
  every write is an ``INSERT … ON CONFLICT (id) DO UPDATE`` upsert, so re-running
  is idempotent and never accumulates duplicates;
* every fixture row is **clearly labelled** (organisation ``metadata.fixture``
  = ``ct-mp-sub-004-pd5``, names prefixed ``MP-FX``, plan codes prefixed
  ``MP-FX-``, lab e-mail local-parts prefixed ``mp.``) and ``--reset`` removes
  exactly those rows and those local GoTrue users;
* it writes ONLY to the local Demo Lab database and the local lab gateway — it
  never contacts production, Render, a hosted Supabase project, or the investor
  demo dataset.

What it deliberately does NOT do:

* it does not change any application code, capability rule, workflow or
  authorization boundary — the fixture creates REAL rows through the SAME
  tables the application reads, and every endpoint re-checks them server-side;
* it does not apply any migration (the CT-MP-SUB-003 coverage table and the
  FIN-06 governance/processor tables are already present in the lab schema);
* it does not weaken RLS: writes go through the lab's superuser psql session in
  the same way DEMO-T1 provisioning does, and the application still connects as
  the service role behind its own API-boundary authorization.

Usage::

    python3 tools/demo_lab/fixture_mp_coverage.py            # apply (idempotent)
    python3 tools/demo_lab/fixture_mp_coverage.py --verify   # server-side checks
    python3 tools/demo_lab/fixture_mp_coverage.py --reset    # remove the fixture
    python3 tools/demo_lab/fixture_mp_coverage.py --json     # machine-readable
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402
import provision  # noqa: E402

BACKEND = f"http://127.0.0.1:{lab.BACKEND_PORT}"
GATEWAY = f"http://127.0.0.1:{lab.GATEWAY_PORT}"

#: Stable fixture identity — used in row labels and evidence file names.
FIXTURE_ID = "ct-mp-sub-004-pd5"
FIXTURE_MARKER = {
    "demo_lab": True,
    "namespace": lab.LAB_NAMESPACE,
    "fixture": FIXTURE_ID,
}

PLAN_DIRECT = "MP-FX-DIRECT"
PLAN_FIRM_SELECTED = "MP-FX-FIRM-SELECTED"
PLAN_FIRM_ALL = "MP-FX-FIRM-ALL"
FIXTURE_PLAN_CODES = (PLAN_DIRECT, PLAN_FIRM_SELECTED, PLAN_FIRM_ALL)

#: SELECTED_CLIENTS purchased capacity for the fixture firm (one client is
#: pre-allocated, so the meter renders a partially-consumed state and one
#: eligible client remains available for the allocate/release demonstration).
SELECTED_CAPACITY = 3


def fid(key: str) -> str:
    """Stable UUID for one fixture row (idempotent by construction)."""
    return lab.deterministic_uuid(f"mpfix:{key}")


def sql(statement: str, *, label: str, failures: list) -> None:
    """Run one fixture statement, recording (never raising) a failure."""
    result = lab.psql(statement)
    if result.returncode != 0 or "ERROR" in result.stderr:
        failures.append({"step": label, "error": result.stderr.strip()[:300]})


# ---------------------------------------------------------------------------
# The states this fixture represents (declarative — one source of truth)
# ---------------------------------------------------------------------------
#
# Commercial coverage is expressed ONLY through the existing D37 org-scoped
# commercial model (``customer_subscriptions`` -> ``billing_plans.features``):
#
#   direct customer  : features.manual_processing.enabled
#   consultant firm  : features.consultant_manual_processing = {enabled, mode,
#                      selected_capacity} read from the FIRM's OWN organisation
#                      subscription (``consultant_profiles.organization_id``)
#
# Eligibility is the existing ``consultant_clients`` relationship. No parallel
# subscription, coverage, consultant or PE model is introduced.

PLANS = (
    {
        "code": PLAN_DIRECT,
        "key": "plan_direct",
        "name": "MP-FX Direct Manual Processing (QA fixture)",
        "features": {"manual_processing": {"enabled": True}},
    },
    {
        "code": PLAN_FIRM_SELECTED,
        "key": "plan_firm_selected",
        "name": "MP-FX Consultancy — Selected Clients coverage (QA fixture)",
        "features": {
            "consultant_manual_processing": {
                "enabled": True,
                "mode": "SELECTED_CLIENTS",
                "selected_capacity": SELECTED_CAPACITY,
            }
        },
    },
    {
        "code": PLAN_FIRM_ALL,
        "key": "plan_firm_all",
        "name": "MP-FX Consultancy — All Eligible Clients coverage (QA fixture)",
        "features": {
            "consultant_manual_processing": {
                "enabled": True,
                "mode": "ALL_ELIGIBLE_CLIENTS",
                "selected_capacity": None,
            }
        },
    },
)

ORGS = (
    {"key": "org_firm_selected", "name": "MP-FX Consultancy — Selected Coverage"},
    {"key": "org_firm_all", "name": "MP-FX Consultancy — All-Eligible Coverage"},
    {"key": "org_client_direct", "name": "MP-FX Client — Direct Only"},
    {"key": "org_client_dual", "name": "MP-FX Client — Direct + Sponsored"},
    {"key": "org_client_sponsored", "name": "MP-FX Client — Sponsored"},
    {"key": "org_client_unallocated", "name": "MP-FX Client — Eligible (Unallocated)"},
)

#: Fixture client organisations (the ones a browser can log into / be covered).
CLIENT_ORGS = (
    "org_client_direct",
    "org_client_dual",
    "org_client_sponsored",
    "org_client_unallocated",
)

#: Fixture actors. ``entity`` decides which identifier table is written; the
#: local part becomes ``<local_part>@demo-lab.carbontally.local``.
ACTORS = (
    {"key": "u_consultant_selected", "local_part": "mp.consultant.selected",
     "entity": "consultant", "firm": "firm_selected"},
    {"key": "u_consultant_allel", "local_part": "mp.consultant.allel",
     "entity": "consultant", "firm": "firm_all"},
    {"key": "u_owner_direct", "local_part": "mp.owner.direct",
     "entity": "customer", "org": "org_client_direct"},
    {"key": "u_owner_dual", "local_part": "mp.owner.dual",
     "entity": "customer", "org": "org_client_dual"},
    {"key": "u_owner_sponsored", "local_part": "mp.owner.sponsored",
     "entity": "customer", "org": "org_client_sponsored"},
)

FIRMS = (
    {
        "key": "firm_selected",
        "name": "MP-FX Consultancy — Selected Coverage",
        "org": "org_firm_selected",
        "owner": "u_consultant_selected",
        "plan": PLAN_FIRM_SELECTED,
        "mode": "SELECTED_CLIENTS",
        "clients": ("org_client_dual", "org_client_unallocated"),
        "allocated": ("org_client_dual",),
    },
    {
        "key": "firm_all",
        "name": "MP-FX Consultancy — All-Eligible Coverage",
        "org": "org_firm_all",
        "owner": "u_consultant_allel",
        "plan": PLAN_FIRM_ALL,
        "mode": "ALL_ELIGIBLE_CLIENTS",
        "clients": ("org_client_sponsored",),
        "allocated": (),
    },
)

SUBSCRIPTIONS = (
    {"key": "sub_client_direct", "org": "org_client_direct", "plan": PLAN_DIRECT},
    {"key": "sub_client_dual", "org": "org_client_dual", "plan": PLAN_DIRECT},
    {"key": "sub_firm_selected", "org": "org_firm_selected", "plan": PLAN_FIRM_SELECTED},
    {"key": "sub_firm_all", "org": "org_firm_all", "plan": PLAN_FIRM_ALL},
)

#: FIN-06 governance + processor rows. Configured ONLY for the Direct+Sponsored
#: client so the customer surface can show the fully-operational state
#: (``operational_status=configured``, governance Active, PE configured) while
#: the sponsored-only client stays ``not_yet_configured`` (the F-5/F1 state).
PE_ALPHA_KEY = "pe:pe_alpha"
GOVERNANCE_TARGETS = ("org_client_dual",)
PROCESSOR_TARGETS = ("org_client_dual",)

FIXTURE_EMAILS = tuple(f"{a['local_part']}@{lab.EMAIL_DOMAIN}" for a in ACTORS)


# ---------------------------------------------------------------------------
# Apply (idempotent)
# ---------------------------------------------------------------------------


def org_ids() -> dict[str, str]:
    return {org["key"]: fid(f"org:{org['key']}") for org in ORGS}


def apply_plans(failures: list) -> None:
    """Upsert the three fixture plans as their CURRENT version (idempotent)."""
    for plan in PLANS:
        columns = ("(id, plan_code, name, description, price, currency, "
                   "billing_interval, features, billing_mode, "
                   "assisted_processing_available, is_active, version)")
        values = (
            f"({provision.go(fid(f'plan:{plan['key']}'))}, "
            f"{provision.go(plan['code'])}, {provision.go(plan['name'])}, "
            f"{provision.go('CT-MP-SUB-004 PD-5 QA fixture — not a commercial plan')}, "
            f"0, 'GBP', 'month', {provision.go(plan['features'])}, "
            f"'STANDARD', false, true, 1)"
        )
        sql(f"INSERT INTO billing_plans {columns} VALUES {values} "
            "ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, "
            "description = EXCLUDED.description, features = EXCLUDED.features, "
            "billing_mode = EXCLUDED.billing_mode, is_active = true, "
            "version = EXCLUDED.version, effective_to = NULL",
            label=f"plan:{plan['code']}", failures=failures)


def apply_orgs(failures: list) -> None:
    """Upsert the fixture organisations, labelled with the fixture marker."""
    marker_supported = provision.has_column("organizations", "metadata")
    for org in ORGS:
        columns = "(id, name, is_active" + (", metadata" if marker_supported else "") + ")"
        values = (f"({provision.go(fid(f'org:{org['key']}'))}, "
                  f"{provision.go(org['name'])}, true"
                  + (f", {provision.go({**FIXTURE_MARKER, 'key': org['key']})}::jsonb"
                     if marker_supported else "") + ")")
        sql(f"INSERT INTO organizations {columns} VALUES {values} "
            "ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, is_active = true",
            label=f"org:{org['key']}", failures=failures)


def apply_users(failures: list) -> dict[str, dict]:
    """Create/reuse the fixture GoTrue users (lab domain, lab password)."""
    password = lab.demo_password()
    existing = provision.list_users()
    users: dict[str, dict] = {}
    for actor in ACTORS:
        record = {"email": f"{actor['local_part']}@{lab.EMAIL_DOMAIN}"}
        try:
            created = provision.ensure_user(record, password, existing)
        except Exception as exc:  # noqa: BLE001 — report, do not crash
            failures.append({"step": f"auth_user:{actor['key']}", "error": str(exc)[:300]})
            continue
        users[actor["key"]] = {"user_id": created["user_id"], "email": record["email"]}
    return users


def mirror_users(users: dict[str, dict], failures: list) -> None:
    """Mirror the fixture auth ids into the lab DB's ``auth.users``.

    The release's foreign keys (``organization_members``, ``consultant_profiles``,
    ``consultant_firm_members``) reference ``public.users``; the lab's
    ``sync_auth_user_to_public_users`` trigger populates it from ``auth.users``.
    Only ``id``/``email`` are written — no credentials, hashes or sessions.
    """
    for key, record in users.items():
        sql("INSERT INTO auth.users (id, email) VALUES "
            f"({provision.go(record['user_id'])}, {provision.go(record['email'])}) "
            "ON CONFLICT (id) DO NOTHING",
            label=f"auth_user_mirror:{key}", failures=failures)


def apply_relationships(entities: dict[str, str], users: dict[str, dict],
                        failures: list) -> None:
    """Upsert consultant profiles, firm memberships, org members and client grants."""
    for firm in FIRMS:
        owner_key = firm["owner"]
        if owner_key not in users:
            failures.append({"step": f"firm:{firm['key']}",
                             "error": f"owner user {owner_key} was not created"})
            continue
        sql("INSERT INTO consultant_profiles "
            "(id, user_id, company_name, is_active, organization_id) VALUES "
            f"({provision.go(fid(f'firm:{firm['key']}'))}, "
            f"{provision.go(users[owner_key]['user_id'])}, "
            f"{provision.go(firm['name'])}, true, "
            f"{provision.go(entities[firm['org']])}) "
            "ON CONFLICT (id) DO UPDATE SET user_id = EXCLUDED.user_id, "
            "company_name = EXCLUDED.company_name, is_active = true, "
            "organization_id = EXCLUDED.organization_id",
            label=f"consultant_profile:{firm['key']}", failures=failures)

        client_access = [entities[org_key] for org_key in firm["clients"]]
        sql("INSERT INTO consultant_firm_members "
            "(id, firm_id, user_id, role, can_manage_clients, client_access, "
            "is_active, joined_at) VALUES "
            f"({provision.go(fid(f'firm_member:{firm['key']}'))}, "
            f"{provision.go(fid(f'firm:{firm['key']}'))}, "
            f"{provision.go(users[owner_key]['user_id'])}, 'owner', true, "
            f"{provision.go(client_access)}, true, NOW()) "
            "ON CONFLICT (id) DO UPDATE SET user_id = EXCLUDED.user_id, "
            "role = EXCLUDED.role, can_manage_clients = true, "
            "client_access = EXCLUDED.client_access, is_active = true",
            label=f"firm_member:{firm['key']}", failures=failures)

        for org_key in firm["clients"]:
            name = next(o["name"] for o in ORGS if o["key"] == org_key)
            sql("INSERT INTO consultant_clients "
                "(id, consultant_id, organization_id, client_name, status, "
                "relationship_origin, created_by) VALUES "
                f"({provision.go(fid(f'client:{firm['key']}:{org_key}'))}, "
                f"{provision.go(fid(f'firm:{firm['key']}'))}, "
                f"{provision.go(entities[org_key])}, {provision.go(name)}, "
                f"'active', 'legacy', {provision.go(users[owner_key]['user_id'])}) "
                "ON CONFLICT (id) DO UPDATE SET consultant_id = EXCLUDED.consultant_id, "
                "organization_id = EXCLUDED.organization_id, "
                "client_name = EXCLUDED.client_name, status = 'active'",
                label=f"consultant_client:{firm['key']}:{org_key}", failures=failures)

    for actor in ACTORS:
        if actor["entity"] != "customer" or actor["key"] not in users:
            continue
        sql("INSERT INTO organization_members "
            "(id, organization_id, user_id, role, is_active) VALUES "
            f"({provision.go(fid(f'org_member:{actor['key']}'))}, "
            f"{provision.go(entities[actor['org']])}, "
            f"{provision.go(users[actor['key']]['user_id'])}, 'owner', true) "
            "ON CONFLICT (id) DO UPDATE SET organization_id = EXCLUDED.organization_id, "
            "user_id = EXCLUDED.user_id, role = 'owner', is_active = true",
            label=f"organization_member:{actor['key']}", failures=failures)


def apply_subscriptions(entities: dict[str, str], failures: list) -> None:
    """Upsert the fixture subscriptions (existing D37 org-scoped model)."""
    for sub in SUBSCRIPTIONS:
        sql("INSERT INTO customer_subscriptions "
            "(id, organization_id, plan, plan_code, plan_version, billing_mode, "
            "lifecycle_status, status, current_period_start, current_period_end, "
            "activated_at) VALUES "
            f"({provision.go(fid(f'sub:{sub['key']}'))}, "
            f"{provision.go(entities[sub['org']])}, {provision.go(sub['plan'])}, "
            f"{provision.go(sub['plan'])}, 1, 'STANDARD', 'active', 'active', "
            "NOW(), NOW() + INTERVAL '1 year', NOW()) "
            "ON CONFLICT (id) DO UPDATE SET organization_id = EXCLUDED.organization_id, "
            "plan = EXCLUDED.plan, plan_code = EXCLUDED.plan_code, "
            "plan_version = EXCLUDED.plan_version, billing_mode = 'STANDARD', "
            "lifecycle_status = 'active', status = 'active'",
            label=f"subscription:{sub['key']}", failures=failures)


def apply_allocations(entities: dict[str, str], users: dict[str, dict],
                      failures: list) -> None:
    """Upsert the pre-placed SELECTED_CLIENTS allocations."""
    for firm in FIRMS:
        actor_id = (users.get(firm["owner"], {}).get("user_id")
                    or fid(f"firm:{firm['key']}"))
        for org_key in firm["allocated"]:
            sql("INSERT INTO consultant_mp_allocations "
                "(id, consultant_id, consultant_client_id, organization_id, state, "
                "reason, allocated_by) VALUES "
                f"({provision.go(fid(f'alloc:{firm['key']}:{org_key}'))}, "
                f"{provision.go(fid(f'firm:{firm['key']}'))}, "
                f"{provision.go(fid(f'client:{firm['key']}:{org_key}'))}, "
                f"{provision.go(entities[org_key])}, 'active', "
                f"{provision.go('CT-MP-SUB-004 PD-5 QA fixture')}, "
                f"{provision.go(actor_id)}) "
                "ON CONFLICT (id) DO UPDATE SET consultant_id = EXCLUDED.consultant_id, "
                "consultant_client_id = EXCLUDED.consultant_client_id, "
                "organization_id = EXCLUDED.organization_id, state = 'active', "
                "released_by = NULL, released_at = NULL, updated_at = NOW()",
                label=f"allocation:{firm['key']}:{org_key}", failures=failures)


def normalise_allocations(failures: list) -> None:
    """Remove any allocation the fixture does not declare (convergence).

    A browser (or admin) allocate creates an extra row with a random id; this
    step drops such rows so the next ``apply`` converges to the declared baseline
    and re-running the fixture never accumulates conflicting allocation state.
    """
    declared = [fid(f"alloc:{firm['key']}:{org_key}")
                for firm in FIRMS for org_key in firm["allocated"]]
    keep = "(" + ",".join(f"'{value}'" for value in declared) + ")"
    sql(f"DELETE FROM public.consultant_mp_allocations "
        f"WHERE consultant_id IN {_FIRM_IDS} AND id NOT IN {keep}",
        label="normalise_allocations", failures=failures)


def apply_governance(entities: dict[str, str], users: dict[str, dict],
                     failures: list) -> None:
    """Upsert the FIN-06 governance + processor rows for the configured client."""
    setup_actor = (users.get("u_owner_dual", {}).get("user_id") or fid("u_owner_dual"))
    pe_alpha = lab.deterministic_uuid(PE_ALPHA_KEY)
    for org_key in GOVERNANCE_TARGETS:
        sql("INSERT INTO manual_processing_grants "
            "(id, scope_type, scope_id, enabled, reason, set_by) VALUES "
            f"({provision.go(fid(f'grant:{org_key}'))}, 'organization', "
            f"{provision.go(entities[org_key])}, true, "
            f"{provision.go('CT-MP-SUB-004 PD-5 QA fixture')}, "
            f"{provision.go(setup_actor)}) "
            "ON CONFLICT (id) DO UPDATE SET scope_type = 'organization', "
            "scope_id = EXCLUDED.scope_id, enabled = true",
            label=f"governance_grant:{org_key}", failures=failures)
    for org_key in PROCESSOR_TARGETS:
        sql("INSERT INTO manual_processing_processors "
            "(id, scope_type, scope_id, processing_entity_id, active, reason, set_by) "
            "VALUES "
            f"({provision.go(fid(f'processor:{org_key}'))}, 'organization', "
            f"{provision.go(entities[org_key])}, {provision.go(pe_alpha)}, true, "
            f"{provision.go('CT-MP-SUB-004 PD-5 QA fixture')}, "
            f"{provision.go(setup_actor)}) "
            "ON CONFLICT (id) DO UPDATE SET scope_type = 'organization', "
            "scope_id = EXCLUDED.scope_id, "
            "processing_entity_id = EXCLUDED.processing_entity_id, active = true",
            label=f"processor:{org_key}", failures=failures)


# ---------------------------------------------------------------------------
# State snapshot (determinism + reset evidence)
# ---------------------------------------------------------------------------

_FIXTURE_ORG_IDS = "(" + ",".join(f"'{fid(f'org:{o['key']}')}'" for o in ORGS) + ")"
_FIRM_IDS = "(" + ",".join(f"'{fid(f'firm:{f['key']}')}'" for f in FIRMS) + ")"


def counts() -> dict:
    """Row counts of every table the fixture owns (must be stable across runs)."""
    queries = {
        "organizations": "SELECT count(*) FROM public.organizations "
                         f"WHERE id IN {_FIXTURE_ORG_IDS}",
        "billing_plans": "SELECT count(*) FROM public.billing_plans WHERE plan_code IN "
                         "('MP-FX-DIRECT','MP-FX-FIRM-SELECTED','MP-FX-FIRM-ALL')",
        "customer_subscriptions": "SELECT count(*) FROM public.customer_subscriptions "
                                  f"WHERE organization_id IN {_FIXTURE_ORG_IDS}",
        "consultant_profiles": "SELECT count(*) FROM public.consultant_profiles "
                               f"WHERE id IN {_FIRM_IDS}",
        "consultant_firm_members": "SELECT count(*) FROM public.consultant_firm_members "
                                   f"WHERE firm_id IN {_FIRM_IDS}",
        "consultant_clients": "SELECT count(*) FROM public.consultant_clients "
                              f"WHERE consultant_id IN {_FIRM_IDS}",
        "consultant_mp_allocations": "SELECT count(*) FROM public.consultant_mp_allocations "
                                     f"WHERE consultant_id IN {_FIRM_IDS}",
        "manual_processing_grants": "SELECT count(*) FROM public.manual_processing_grants "
                                    f"WHERE scope_id IN {_FIXTURE_ORG_IDS}",
        "manual_processing_processors": "SELECT count(*) FROM public.manual_processing_processors "
                                        f"WHERE scope_id IN {_FIXTURE_ORG_IDS}",
    }
    return {name: int(lab.psql_scalar(query) or 0) for name, query in queries.items()}


# ---------------------------------------------------------------------------
# Reset (removes ONLY what the fixture created)
# ---------------------------------------------------------------------------

#: FK-safe deletion order. Each target clause matches fixture-owned rows only
#: (deterministic ids / fixture plan codes / the ``mp.`` lab users).
RESET_TARGETS: tuple[tuple[str, str, str], ...] = (
    ("consultant_mp_allocations", "public.consultant_mp_allocations",
     f"consultant_id IN {_FIRM_IDS}"),
    ("manual_processing_processors", "public.manual_processing_processors",
     f"scope_id IN {_FIXTURE_ORG_IDS}"),
    ("manual_processing_grants", "public.manual_processing_grants",
     f"scope_id IN {_FIXTURE_ORG_IDS}"),
    ("customer_subscriptions", "public.customer_subscriptions",
     f"organization_id IN {_FIXTURE_ORG_IDS}"),
    ("consultant_clients", "public.consultant_clients",
     f"consultant_id IN {_FIRM_IDS}"),
    ("consultant_firm_members", "public.consultant_firm_members",
     f"firm_id IN {_FIRM_IDS}"),
    ("organization_members", "public.organization_members",
     f"organization_id IN {_FIXTURE_ORG_IDS}"),
    ("consultant_profiles", "public.consultant_profiles", f"id IN {_FIRM_IDS}"),
    ("organizations", "public.organizations", f"id IN {_FIXTURE_ORG_IDS}"),
    ("billing_plans", "public.billing_plans",
     "plan_code IN ('MP-FX-DIRECT','MP-FX-FIRM-SELECTED','MP-FX-FIRM-ALL')"),
)


def _fixture_auth_ids() -> list[str]:
    """The lab auth user ids currently held by the fixture's e-mail addresses."""
    emails = ",".join(f"'{email}'" for email in FIXTURE_EMAILS)
    value = lab.psql_scalar(
        f"SELECT coalesce(string_agg(id::text, ','), '') FROM auth.users "
        f"WHERE lower(email) IN ({emails})")
    return [token for token in (value or "").split(",") if token]


def remove_auth_users() -> dict:
    """Delete the fixture GoTrue users (lab domain) and their mirrored rows."""
    removed_gotrue = 0
    try:
        headers = provision.gotrue_headers()
        status, payload, _raw = lab.http_json(
            f"{GATEWAY}/auth/v1/admin/users?per_page=1000", headers=headers)
        if status == 200 and isinstance(payload, dict):
            wanted = {email.lower() for email in FIXTURE_EMAILS}
            for user in payload.get("users", []):
                if str(user.get("email", "")).lower() in wanted:
                    code, _p, _r = lab.http_json(
                        f"{GATEWAY}/auth/v1/admin/users/{user['id']}",
                        method="DELETE", headers=headers)
                    removed_gotrue += int(code in (200, 204))
    except Exception as exc:  # noqa: BLE001 — reset must report, not crash
        return {"gotrue_removed": removed_gotrue, "error": str(exc)[:200]}

    ids = _fixture_auth_ids()
    mirrored = 0
    if ids:
        id_list = ",".join(f"'{value}'" for value in ids)
        for table in ("auth.users", "public.users"):
            sql(f"DELETE FROM {table} WHERE id IN ({id_list})",
                label=f"reset:{table}", failures=[])
        mirrored = len(ids)
    return {"gotrue_removed": removed_gotrue, "mirror_rows_removed": mirrored}


def reset() -> dict:
    """Remove every fixture row and fixture lab user (safe to re-run)."""
    removed: dict[str, int] = {}
    failures: list = []
    for name, table, where in RESET_TARGETS:
        statement = (f"WITH deleted AS (DELETE FROM {table} WHERE {where} RETURNING 1) "
                     "SELECT count(*) FROM deleted")
        value = lab.psql_scalar(statement)
        removed[name] = int(value) if str(value).isdigit() else 0
    removed.update(remove_auth_users())
    return {"removed": removed, "failures": failures}


# ---------------------------------------------------------------------------
# Preconditions — fail closed with the EXACT dependency if a migration is absent
# ---------------------------------------------------------------------------

#: Table -> the source that creates it. If any is absent the fixture STOPS and
#: reports the dependency; it never applies a migration itself (PD-6 gate).
REQUIRED_TABLES = {
    "customer_subscriptions": "D37 commercial model (existing release schema)",
    "billing_plans": "D37 commercial model (existing release schema)",
    "consultant_profiles": "existing consultant model",
    "consultant_clients": "existing consultant model",
    "consultant_firm_members": "existing consultant model",
    "manual_processing_grants":
        "supabase/migrations/20261030000000_manual_processing_routing.sql",
    "manual_processing_processors":
        "supabase/migrations/20261030000000_manual_processing_routing.sql",
    "consultant_mp_allocations":
        "supabase/migrations/20261101000000_ct_mp_sub_003_consultant_coverage.sql",
}


def precondition() -> dict:
    """Verify the lab schema + infrastructure the fixture requires (read-only)."""
    missing = {table: source for table, source in REQUIRED_TABLES.items()
               if lab.psql_scalar(f"SELECT to_regclass('public.{table}')") in ("", "None")}
    health = lab.wait_for(f"{GATEWAY}/auth/v1/health", expect_in=(200,),
                          attempts=3, delay=1.0)
    return {"missing_tables": missing, "gateway_health": health}


# ---------------------------------------------------------------------------
# Server-side verification (bounded self-verification, via the live API)
# ---------------------------------------------------------------------------


def login(email: str, password: str) -> str:
    """Password grant against the lab GoTrue (never a minted/forged token)."""
    status, payload, raw = lab.http_json(
        f"{GATEWAY}/auth/v1/token?grant_type=password", method="POST",
        headers={"apikey": lab.anon_key()},
        body={"email": email, "password": password})
    if status == 200 and isinstance(payload, dict) and payload.get("access_token"):
        return payload["access_token"]
    raise RuntimeError(f"login failed for {email} (status={status}): {raw[:160]}")


def api_get(path: str, token: str):
    return lab.http_json(f"{BACKEND}{path}", headers={"Authorization": f"Bearer {token}"})


def _check(name: str, ok: bool, detail: str) -> dict:
    return {"check": name, "ok": bool(ok), "detail": detail}


def _login_tokens() -> dict:
    """A password-grant token for every actor this verification needs."""
    password = lab.demo_password()
    wanted = {actor["key"]: f"{actor['local_part']}@{lab.EMAIL_DOMAIN}" for actor in ACTORS}
    # Provisioned DEMO-T1 identities used as counterexamples.
    wanted["u_org_b_owner"] = f"owner.b@{lab.EMAIL_DOMAIN}"
    wanted["u_platform_admin"] = f"platform.admin@{lab.EMAIL_DOMAIN}"
    return {key: login(email, password) for key, email in wanted.items()}


def verify() -> list[dict]:
    """Exercise the fixture through the REAL server endpoints (no shortcuts)."""
    org = org_ids()
    tokens = _login_tokens()
    checks: list[dict] = []

    # --- customer states ---------------------------------------------------
    customer_cases = (
        ("org_client_direct", "u_owner_direct",
         {"status": "available", "direct": True, "sponsored": False,
          "sources": ["direct"], "operational": "not_yet_configured"}),
        ("org_client_dual", "u_owner_dual",
         {"status": "available", "direct": True, "sponsored": True,
          "sources": ["direct", "sponsored"], "operational": "configured"}),
        ("org_client_sponsored", "u_owner_sponsored",
         {"status": "available", "direct": False, "sponsored": True,
          "sources": ["sponsored"], "operational": "not_yet_configured"}),
    )
    for org_key, actor_key, want in customer_cases:
        try:
            status, payload, raw = api_get(
                f"/api/v3/organizations/{org[org_key]}/manual-processing",
                tokens[actor_key])
            payload = payload if isinstance(payload, dict) else {}
            ok = (status == 200
                  and payload.get("status") == want["status"]
                  and bool(payload.get("direct_entitled")) == want["direct"]
                  and bool(payload.get("sponsored_entitled")) == want["sponsored"]
                  and sorted(payload.get("coverage_sources") or []) == sorted(want["sources"])
                  and payload.get("operational_status") == want["operational"]
                  and bool(payload.get("effective_entitled")) is True)
            checks.append(_check(
                f"customer:{org_key}", ok,
                f"http={status} status={payload.get('status')} "
                f"sources={payload.get('coverage_sources')} "
                f"direct={payload.get('direct_entitled')} "
                f"sponsored={payload.get('sponsored_entitled')} "
                f"operational={payload.get('operational_status')}"))
        except Exception as exc:  # noqa: BLE001
            checks.append(_check(f"customer:{org_key}", False, str(exc)[:200]))

    # governance Active on the configured client (commercial ≠ operational)
    try:
        status, payload, raw = api_get(
            f"/api/v3/organizations/{org['org_client_dual']}/manual-processing",
            tokens["u_owner_dual"])
        gov = (payload or {}).get("governance") or {}
        checks.append(_check("customer:org_client_dual:governance_active",
                             bool(gov.get("enabled")) is True, f"governance={gov}"))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("customer:org_client_dual:governance_active", False,
                             str(exc)[:200]))

    # --- negative: an existing customer with no entitlement ----------------
    try:
        org_b = lab.deterministic_uuid("org:org_b")
        status, payload, raw = api_get(
            f"/api/v3/organizations/{org_b}/manual-processing", tokens["u_org_b_owner"])
        payload = payload if isinstance(payload, dict) else {}
        ok = (status == 200 and payload.get("status") == "not_included"
              and bool(payload.get("effective_entitled")) is False)
        checks.append(_check("negative:org_b:not_included", ok,
                             f"http={status} status={payload.get('status')}"))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("negative:org_b:not_included", False, str(exc)[:200]))

    # --- consultant states -------------------------------------------------
    consultant_cases = (
        ("u_consultant_selected", "firm_selected",
         {"mode": "SELECTED_CLIENTS", "capacity": SELECTED_CAPACITY,
          "allocated": 1, "available": SELECTED_CAPACITY - 1,
          "eligible": 2, "covered": 1, "unallocated": 1}),
        ("u_consultant_allel", "firm_all",
         {"mode": "ALL_ELIGIBLE_CLIENTS", "capacity": None,
          "allocated": 0, "available": None,
          "eligible": 1, "covered": 0, "unallocated": 1}),
    )
    for actor_key, firm_key, want in consultant_cases:
        try:
            status, payload, raw = api_get(
                "/api/v3/consultants/me/manual-processing/coverage", tokens[actor_key])
            payload = payload if isinstance(payload, dict) else {}
            ok = (status == 200
                  and bool(payload.get("enabled")) is True
                  and payload.get("mode") == want["mode"]
                  and payload.get("capacity") == want["capacity"]
                  and payload.get("allocated") == want["allocated"]
                  and payload.get("available") == want["available"]
                  and len(payload.get("eligible_clients") or []) == want["eligible"]
                  and len(payload.get("covered_clients") or []) == want["covered"]
                  and len(payload.get("unallocated_eligible_clients") or [])
                  == want["unallocated"])
            checks.append(_check(
                f"consultant:{firm_key}", ok,
                f"http={status} enabled={payload.get('enabled')} mode={payload.get('mode')} "
                f"capacity={payload.get('capacity')} allocated={payload.get('allocated')} "
                f"available={payload.get('available')} "
                f"eligible={len(payload.get('eligible_clients') or [])} "
                f"covered={len(payload.get('covered_clients') or [])} "
                f"unallocated={len(payload.get('unallocated_eligible_clients') or [])}"))
        except Exception as exc:  # noqa: BLE001
            checks.append(_check(f"consultant:{firm_key}", False, str(exc)[:200]))

    # --- admin control plane (Commercial Coverage tab data) ----------------
    try:
        status, payload, raw = api_get(
            f"/api/v3/admin/manual-processing/coverage/{fid('firm:firm_selected')}",
            tokens["u_platform_admin"])
        coverage = (payload or {}).get("coverage") or {}
        ok = (status == 200
              and bool(coverage.get("enabled")) is True
              and coverage.get("mode") == "SELECTED_CLIENTS"
              and coverage.get("capacity") == SELECTED_CAPACITY
              and coverage.get("allocated") == 1
              and coverage.get("available") == SELECTED_CAPACITY - 1)
        checks.append(_check(
            "admin:firm_selected_coverage", ok,
            f"http={status} enabled={coverage.get('enabled')} mode={coverage.get('mode')} "
            f"allocated={coverage.get('allocated')}/{coverage.get('capacity')} "
            f"available={coverage.get('available')}"))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("admin:firm_selected_coverage", False, str(exc)[:200]))

    try:
        status, payload, raw = api_get(
            f"/api/v3/admin/manual-processing/coverage/{fid('firm:firm_all')}",
            tokens["u_platform_admin"])
        coverage = (payload or {}).get("coverage") or {}
        ok = (status == 200 and bool(coverage.get("enabled")) is True
              and coverage.get("mode") == "ALL_ELIGIBLE_CLIENTS"
              and coverage.get("capacity") is None
              and len(coverage.get("eligible_clients") or []) == 1)
        checks.append(_check(
            "admin:firm_all_coverage", ok,
            f"http={status} mode={coverage.get('mode')} capacity={coverage.get('capacity')} "
            f"eligible={len(coverage.get('eligible_clients') or [])}"))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("admin:firm_all_coverage", False, str(exc)[:200]))

    try:
        status, payload, raw = api_get(
            f"/api/v3/admin/manual-processing/clients/{org['org_client_dual']}",
            tokens["u_platform_admin"])
        payload = payload if isinstance(payload, dict) else {}
        effective = payload.get("effective_entitlement") or {}
        ok = (status == 200 and bool(effective.get("entitled")) is True
              and effective.get("source") == "direct+sponsored"
              and bool((payload.get("governance") or {}).get("enabled")) is True
              and bool((payload.get("effective") or {}).get("configured")) is True)
        checks.append(_check(
            "admin:client_dual_state", ok,
            f"http={status} source={effective.get('source')} "
            f"gov={(payload.get('governance') or {}).get('enabled')} "
            f"configured={(payload.get('effective') or {}).get('configured')}"))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("admin:client_dual_state", False, str(exc)[:200]))

    # --- negative: eligible-but-unallocated client stays not entitled ------
    try:
        status, payload, raw = api_get(
            f"/api/v3/admin/manual-processing/clients/{org['org_client_unallocated']}",
            tokens["u_platform_admin"])
        payload = payload if isinstance(payload, dict) else {}
        effective = payload.get("effective_entitlement") or {}
        sponsored = payload.get("sponsored") or {}
        ok = (status == 200 and bool(effective.get("entitled")) is False
              and bool(sponsored.get("entitled")) is False
              and sponsored.get("reason") == "not_allocated")
        checks.append(_check(
            "negative:org_client_unallocated:not_allocated", ok,
            f"http={status} entitled={effective.get('entitled')} "
            f"sponsored_reason={sponsored.get('reason')}"))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("negative:org_client_unallocated:not_allocated", False,
                             str(exc)[:200]))

    return checks


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def fixture_ids() -> dict:
    """Every id an operator/verifier needs (never a secret)."""
    return {
        "organizations": org_ids(),
        "firms": {firm["key"]: fid(f"firm:{firm['key']}") for firm in FIRMS},
        "client_grants": {
            f"{firm['key']}:{org_key}": fid(f"client:{firm['key']}:{org_key}")
            for firm in FIRMS for org_key in firm["clients"]
        },
        "allocations": {
            f"{firm['key']}:{org_key}": fid(f"alloc:{firm['key']}:{org_key}")
            for firm in FIRMS for org_key in firm["allocated"]
        },
        "pe_alpha": lab.deterministic_uuid(PE_ALPHA_KEY),
        "existing_negative_org_b": lab.deterministic_uuid("org:org_b"),
    }


def fixture_logins() -> dict:
    """Fixture identities for the browser verification (no secrets)."""
    return {actor["key"]: f"{actor['local_part']}@{lab.EMAIL_DOMAIN}" for actor in ACTORS}


def _write_evidence(prefix: str, payload: dict) -> str:
    lab.ensure_dirs()
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = lab.EVIDENCE_DIR / f"{prefix}_{stamp}.json"
    out.write_text(json.dumps(payload, indent=1, default=str))
    (lab.EVIDENCE_DIR / f"{prefix}_latest.json").write_text(
        json.dumps(payload, indent=1, default=str))
    return str(out)


def apply() -> dict:
    """Create/recreate the fixture deterministically (idempotent)."""
    pre = precondition()
    if pre["missing_tables"]:
        raise SystemExit(
            "BLOCKED — the Demo Lab schema is missing a prerequisite this task is "
            "not authorised to create (PD-6: no migration may be applied here):\n"
            + "\n".join(f"  - public.{table}  <-  {source}"
                        for table, source in pre["missing_tables"].items()))
    if pre["gateway_health"] != 200:
        raise SystemExit(
            f"lab gateway/auth is not healthy (status={pre['gateway_health']}). "
            "Run `python3 tools/demo_lab/stack.py` first.")

    failures: list = []
    organizations = org_ids()
    apply_plans(failures)
    apply_orgs(failures)
    users = apply_users(failures)
    mirror_users(users, failures)
    apply_relationships(organizations, users, failures)
    apply_subscriptions(organizations, failures)
    apply_allocations(organizations, users, failures)
    normalise_allocations(failures)
    apply_governance(organizations, users, failures)

    state = lab.load_state()
    fixtures = state.setdefault("fixtures", {})
    fixtures[FIXTURE_ID] = {
        "database": lab.LAB_DB,
        "plans": list(FIXTURE_PLAN_CODES),
        "ids": fixture_ids(),
        "logins": fixture_logins(),
    }
    lab.save_state(state)

    summary = {
        "fixture": FIXTURE_ID,
        "database": lab.LAB_DB,
        "gateway": GATEWAY,
        "backend": BACKEND,
        "applied_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "precondition": pre,
        "counts": counts(),
        "ids": fixture_ids(),
        "logins": fixture_logins(),
        "failures": failures,
    }
    summary["evidence"] = _write_evidence("mp_fixture_apply", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CT-MP-SUB-004 PD-5 deterministic Demo Lab QA fixture")
    parser.add_argument("--reset", action="store_true",
                        help="remove every fixture row + fixture lab user")
    parser.add_argument("--verify", action="store_true",
                        help="server-side verification against the live API")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    if args.reset:
        result = reset()
        result["fixture"] = FIXTURE_ID
        result["evidence"] = _write_evidence("mp_fixture_reset", result)
        if args.json:
            print(json.dumps(result, indent=1, default=str))
        else:
            print(f"fixture reset: {FIXTURE_ID}")
            for name, value in result["removed"].items():
                print(f"  removed {name}: {value}")
            for item in result["failures"]:
                print(f"  FAILURE {item['step']}: {item['error']}")
            print(f"evidence: {result['evidence']}")
        return 1 if result["failures"] else 0

    if args.verify:
        checks = verify()
        failed = [c for c in checks if not c["ok"]]
        evidence = {
            "fixture": FIXTURE_ID,
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "backend": BACKEND, "gateway": GATEWAY,
            "checks": checks,
            "summary": {"total": len(checks), "failed": len(failed)},
        }
        evidence["evidence"] = _write_evidence("mp_fixture_verify", evidence)
        if args.json:
            print(json.dumps(evidence, indent=1, default=str))
        else:
            print(f"fixture verification: {len(checks) - len(failed)}/{len(checks)} as expected")
            for item in checks:
                print(f"  [{'PASS' if item['ok'] else 'FAIL'}] {item['check']}: {item['detail']}")
            print(f"evidence: {evidence['evidence']}")
        return 1 if failed else 0

    summary = apply()
    if args.json:
        print(json.dumps(summary, indent=1, default=str))
    else:
        print(f"fixture applied: {FIXTURE_ID} ({lab.LAB_DB})")
        print(f"  counts: {summary['counts']}")
        print("  consultant firms:")
        for firm in FIRMS:
            print(f"    {firm['key']:14s} {fid(f'firm:{firm['key']}')}  "
                  f"[{firm['mode']}]  login={fixture_logins()[firm['owner']]}")
        print("  client organisations:")
        for key, value in org_ids().items():
            print(f"    {key:24s} {value}")
        print("  admin control plane: GET /api/v3/admin/manual-processing/coverage/"
              f"{fid('firm:firm_selected')}")
        print(f"  credentials: lab demo password from {lab.CREDENTIALS_PATH} (never committed)")
        for item in summary["failures"]:
            print(f"  FAILURE {item['step']}: {item['error']}")
        print(f"evidence: {summary['evidence']}")
    return 1 if summary["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
