#!/usr/bin/env python3
"""DEMO-T1 — provision the local Demo Lab's synthetic, role-bearing identities.

Idempotent by construction:

* entity ids are deterministic (UUIDv5 from the manifest key), so re-running
  updates the same rows instead of inserting duplicates;
* authentication users are matched by e-mail through the local GoTrue admin API,
  so the same auth user id is reused on every run;
* every write is ``INSERT … ON CONFLICT (id) DO UPDATE`` or an equivalent
  upsert keyed on a natural key.

Credentials (the generated lab password and the JWT secret) are stored **outside
the repository** by :mod:`lab`; nothing secret is ever written into the release
tree.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402

DEMO_MARKER = {"demo_lab": True, "namespace": lab.LAB_NAMESPACE}


# --- helpers --------------------------------------------------------------


def has_column(table: str, column: str) -> bool:
    value = lab.psql_scalar(
        "SELECT count(*) FROM information_schema.columns "
        f"WHERE table_schema='public' AND table_name='{table}' AND column_name='{column}'")
    return int(value or 0) > 0


def go(value) -> str:
    """SQL literal for a python value (dict/list → jsonb, None → NULL)."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return "'" + json.dumps(value).replace("'", "''") + "'::jsonb" \
            if isinstance(value, dict) else \
            "'{" + ",".join(str(item) for item in value) + "}'::uuid[]"
    text = str(value).replace("'", "''")
    return f"'{text}'"


def sql(statement: str, *, label: str, failures: list) -> None:
    result = lab.psql(statement)
    if result.returncode != 0 or "ERROR" in result.stderr:
        failures.append({"step": label, "error": result.stderr.strip()[:300]})


# --- authentication users (local GoTrue only) -----------------------------


def gotrue_headers() -> dict:
    return {"apikey": lab.service_key(), "Authorization": f"Bearer {lab.service_key()}"}


def list_users() -> dict[str, dict]:
    """Map e-mail → auth user record from the LAB's GoTrue (never the shared stack)."""
    base = f"http://127.0.0.1:{lab.GATEWAY_PORT}/auth/v1/admin/users?per_page=1000"
    status, payload, raw = lab.http_json(base, headers=gotrue_headers())
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(f"could not list lab auth users (status={status}): {raw[:200]}")
    users = payload.get("users") or []
    return {str(user.get("email", "")).lower(): user for user in users}


def ensure_user(actor: dict, password: str, existing: dict[str, dict]) -> dict:
    email = actor["email"].lower()
    base = f"http://127.0.0.1:{lab.GATEWAY_PORT}/auth/v1/admin/users"
    if email in existing:
        user_id = existing[email]["id"]
        status, payload, raw = lab.http_json(
            f"{base}/{user_id}", method="PUT", headers=gotrue_headers(),
            body={"password": password, "email_confirm": True})
        if status not in (200, 201):
            raise RuntimeError(f"could not update {email} (status={status}): {raw[:200]}")
        return {"user_id": user_id, "created": False}
    status, payload, raw = lab.http_json(
        base, method="POST", headers=gotrue_headers(),
        body={"email": actor["email"], "password": password, "email_confirm": True,
              "user_metadata": DEMO_MARKER})
    if status not in (200, 201) or not isinstance(payload, dict):
        raise RuntimeError(f"could not create {email} (status={status}): {raw[:200]}")
    return {"user_id": payload["id"], "created": True}


# --- entities and relationships ------------------------------------------


def ensure_staff_roles(manifest: dict, failures: list) -> dict[str, str]:
    """Ensure every staff role named by the manifest exists in the LAB database.

    ``operator`` and ``pe_manager`` are produced by the release migrations; the
    internal ``admin`` role is **demo-lab data** (created here, never in a
    migration) because the release's seeded vocabulary does not include it.
    """
    defaults = {
        # `can_manage_organizations` is the release's own admin permission key
        # (api/manual_processing_admin.py: ADMIN_PERMISSION).
        # P12 Step-2 completion: `can_manage_staff` is the release's own
        # staff-admin key used by the N1 support-messaging counterparty
        # (api/v3_messaging.py + migrations/20260902040000_phase5_pe_operational_messaging.sql
        # §88-102: "INTERNAL staff (entity_id NULL) whose staff role grants
        # can_manage_staff"). It is NOT a new permission — the Demo Lab simply
        # did not grant it, so the support counterparty answered 409. Granting it
        # to the lab's `admin` role mirrors the production staff-admin intent and
        # exercises the real authorization path (no RLS change, no bypass).
        # P16-REMEDIATION-02 RD-1: `can_review` is the release's own review gate
        # (api/v3_processing_workflow.py / ops validate route require it). The
        # Demo Lab's `admin` role is the internal staff-admin/QC authority
        # (it already holds can_qc + is_staff_admin) but was never granted
        # can_review, so no internal actor could execute `mapped -> validated`
        # and the reviewer half of the state machine was unreachable. Granting it
        # to `admin` only preserves the intended separation:
        #     operator -> map        (can_process)
        #     admin    -> validate   (can_review)   <-- this grant
        #     operator -> calculate  (can_process)
        # No new permission name is invented and no other role is broadened.
        "admin": {"is_superuser": True, "is_staff_admin": True,
                  "can_manage_organizations": True, "can_manage_staff": True,
                  "can_review": True,
                  "demo_lab": True},
        "operator": {"can_process": True, "demo_lab": True},
        "pe_manager": {"can_process": True, "can_manage_team": True, "demo_lab": True},
    }
    wanted: list[str] = []
    for actor in manifest["actors"]:
        name = actor.get("staff_role")
        if name and name not in wanted:
            wanted.append(name)

    role_ids: dict[str, str] = {}
    for name in wanted:
        existing = lab.psql_scalar(
            f"SELECT id FROM staff_roles WHERE name = {go(name)} LIMIT 1")
        permissions = defaults.get(name, {"demo_lab": True})
        if existing:
            role_ids[name] = existing
            sql(f"UPDATE staff_roles SET permissions = {go(permissions)}::jsonb "
                f"WHERE id = {go(existing)}", label=f"staff_role:{name}:update",
                failures=failures)
        else:
            role_id = lab.deterministic_uuid(f"staff_role:{name}")
            role_ids[name] = role_id
            sql("INSERT INTO staff_roles (id, name, permissions) VALUES "
                f"({go(role_id)}, {go(name)}, {go(permissions)}::jsonb)",
                label=f"staff_role:{name}:insert", failures=failures)
    return role_ids


def ensure_entity_rows(manifest: dict, state: dict, failures: list) -> dict:
    """Upsert organizations, the processing entity, the firm and its engagements."""
    entities: dict[str, dict] = {}

    marker_supported = has_column("organizations", "metadata")
    for org in manifest["organizations"]:
        org_id = lab.deterministic_uuid(f"org:{org['key']}")
        columns = "(id, name, is_active" + (", metadata" if marker_supported else "") + ")"
        values = (f"({go(org_id)}, {go(org['name'])}, true"
                  + (f", {go({**DEMO_MARKER, 'key': org['key'], 'kind': org['kind']})}::jsonb"
                     if marker_supported else "") + ")")
        sql(f"INSERT INTO organizations {columns} VALUES {values} "
            "ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, is_active = true",
            label=f"organization:{org['key']}", failures=failures)
        entities[org["key"]] = {"id": org_id, "name": org["name"], "kind": org["kind"]}

    for entity in manifest.get("processing_entities", []):
        entity_id = lab.deterministic_uuid(f"pe:{entity['key']}")
        sql("INSERT INTO processing_entities (id, name, status, metadata) VALUES "
            f"({go(entity_id)}, {go(entity['name'])}, 'active', "
            f"{go({**DEMO_MARKER, 'key': entity['key']})}::jsonb) "
            "ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, status = 'active'",
            label=f"processing_entity:{entity['key']}", failures=failures)
        entities[entity["key"]] = {"id": entity_id, "name": entity["name"],
                                   "kind": "processing_entity"}

    firm = manifest.get("consultant_firm")
    if firm:
        firm_id = lab.deterministic_uuid(f"firm:{firm['key']}")
        entities[firm["key"]] = {"id": firm_id, "name": firm["company_name"],
                                 "kind": "consultant_firm"}
    return entities


def ensure_user_mirror(users: dict[str, dict], failures: list) -> None:
    """Mirror the lab auth user ids into the lab database's ``auth.users``.

    The release schema keeps foreign keys from ``organization_members``,
    ``staff_profiles`` and ``consultant_profiles`` to ``auth.users``. The lab
    authenticates against the local stack's GoTrue (so the authoritative user rows
    live in the stack database), which means the lab database needs the same ids
    present locally for those constraints. Only ``id``/``email`` are written — no
    credentials, hashes or sessions — and the rows are clearly namespaced by the
    lab e-mail domain.
    """
    for actor_key, record in users.items():
        sql("INSERT INTO auth.users (id, email) VALUES "
            f"({go(record['user_id'])}, {go(record['email'])}) "
            "ON CONFLICT (id) DO NOTHING",
            label=f"auth_user_mirror:{actor_key}", failures=failures)


def ensure_actor_relationships(manifest: dict, entities: dict, role_ids: dict,
                               users: dict[str, dict], failures: list) -> None:
    """Upsert memberships, staff profiles, firm membership and client engagements."""
    firm = manifest.get("consultant_firm") or {}
    firm_id = entities.get(firm.get("key", ""), {}).get("id")
    clients = [org for org in manifest["organizations"] if org["kind"] == "consultant_client"]

    # The firm's OWN profile row first: ``consultant_profiles`` IS the firm in this
    # model, and ``consultant_firm_members.firm_id`` / ``consultant_clients.consultant_id``
    # both reference it.
    owner_key = next((actor["key"] for actor in manifest["actors"]
                      if actor.get("firm_owner")), None)
    if firm_id and owner_key:
        sql("INSERT INTO consultant_profiles (id, user_id, company_name, is_active) VALUES "
            f"({go(firm_id)}, {go(users[owner_key]['user_id'])}, "
            f"{go(firm['company_name'])}, true) "
            "ON CONFLICT (id) DO UPDATE SET user_id = EXCLUDED.user_id, "
            "company_name = EXCLUDED.company_name, is_active = true",
            label="consultant_profile:firm", failures=failures)

    for actor in manifest["actors"]:
        key, user_id = actor["key"], users[actor["key"]]["user_id"]
        entity_kind = actor["entity"]

        if entity_kind == "customer":
            org = entities[actor["organization"]]
            sql("INSERT INTO organization_members "
                "(id, organization_id, user_id, role, is_active) VALUES "
                f"({go(lab.deterministic_uuid(f'member:{key}'))}, {go(org['id'])}, "
                f"{go(user_id)}, {go(actor['org_role'])}, true) "
                "ON CONFLICT (id) DO UPDATE SET organization_id = EXCLUDED.organization_id, "
                "user_id = EXCLUDED.user_id, role = EXCLUDED.role, is_active = true",
                label=f"organization_member:{key}", failures=failures)

        if entity_kind in ("platform", "internal_staff", "processing_entity"):
            entity_id = (None if entity_kind != "processing_entity"
                         else entities[actor["processing_entity"]]["id"])
            role_id = role_ids.get(actor["staff_role"])
            sql("INSERT INTO staff_profiles "
                "(id, user_id, first_name, last_name, email, role_id, is_active, entity_id) "
                "VALUES "
                f"({go(lab.deterministic_uuid(f'staff:{key}'))}, {go(user_id)}, "
                f"{go(actor['local_part'].split('.')[0].title())}, 'Demo', "
                f"{go(actor['email'])}, {go(role_id)}, true, {go(entity_id)}) "
                "ON CONFLICT (id) DO UPDATE SET user_id = EXCLUDED.user_id, "
                "email = EXCLUDED.email, role_id = EXCLUDED.role_id, "
                "entity_id = EXCLUDED.entity_id, is_active = true",
                label=f"staff_profile:{key}", failures=failures)

        if entity_kind == "consultant":
            capabilities = actor.get("capabilities") or {}
            flags = {
                "can_manage_clients": capabilities.get("can_manage_clients", True),
                "can_upload_documents": capabilities.get("can_upload_documents", True),
                "can_generate_reports": capabilities.get("can_generate_reports", True),
                "can_manage_team": capabilities.get("can_manage_team", True),
                "can_extract": capabilities.get("can_extract", True),
                "can_map": capabilities.get("can_map", True),
                "can_validate": capabilities.get("can_validate", True),
                "can_calculate": capabilities.get("can_calculate", True),
                "can_confirm_automation": capabilities.get("can_confirm_automation", True),
                "can_submit": capabilities.get("can_submit", True),
            }
            column_names = ["id", "firm_id", "user_id", "role", "client_access", "is_active",
                            "joined_at", *flags]
            values = [go(lab.deterministic_uuid(f"firm_member:{key}")), go(firm_id), go(user_id),
                      go(actor["firm_role"]),
                      "'{" + ",".join(entities[org["key"]]["id"] for org in clients
                                      if actor.get("firm_owner") or org["key"] == "client_a")
                      + "}'::uuid[]",
                      "true", "now()", *[go(value) for value in flags.values()]]
            updates = ", ".join(f"{name} = EXCLUDED.{name}"
                                for name in ("firm_id", "user_id", "role", "client_access",
                                             "is_active", *flags))
            sql(f"INSERT INTO consultant_firm_members ({', '.join(column_names)}) VALUES "
                f"({', '.join(values)}) ON CONFLICT (id) DO UPDATE SET {updates}",
                label=f"consultant_firm_member:{key}", failures=failures)

    # Active engagements: only ``status='active'`` grants consultant access.
    for org in clients:
        sql("INSERT INTO consultant_clients "
            "(id, consultant_id, organization_id, client_name, status) VALUES "
            f"({go(lab.deterministic_uuid(f'engagement:{org['key']}'))}, {go(firm_id)}, "
            f"{go(entities[org['key']]['id'])}, {go(org['name'])}, 'active') "
            "ON CONFLICT (id) DO UPDATE SET consultant_id = EXCLUDED.consultant_id, "
            "organization_id = EXCLUDED.organization_id, status = 'active'",
            label=f"consultant_client:{org['key']}", failures=failures)



# --- duplicate / idempotency audit ---------------------------------------


DUPLICATE_CHECKS = {
    "organization_members (org,user)":
        "SELECT count(*) FROM (SELECT organization_id, user_id FROM organization_members "
        "GROUP BY 1,2 HAVING count(*) > 1) d",
    "staff_profiles (user)":
        "SELECT count(*) FROM (SELECT user_id FROM staff_profiles GROUP BY 1 "
        "HAVING count(*) > 1) d",
    "consultant_firm_members (firm,user)":
        "SELECT count(*) FROM (SELECT firm_id, user_id FROM consultant_firm_members "
        "GROUP BY 1,2 HAVING count(*) > 1) d",
    "consultant_clients (firm,org)":
        "SELECT count(*) FROM (SELECT consultant_id, organization_id FROM consultant_clients "
        "GROUP BY 1,2 HAVING count(*) > 1) d",
    "organizations (name)":
        "SELECT count(*) FROM (SELECT name FROM organizations WHERE name LIKE 'Demo Lab %' "
        "GROUP BY 1 HAVING count(*) > 1) d",
}


def audit_duplicates() -> dict:
    return {label: int(lab.psql_scalar(statement) or 0)
            for label, statement in DUPLICATE_CHECKS.items()}


def counts() -> dict:
    return {
        "organizations": int(lab.psql_scalar("SELECT count(*) FROM organizations") or 0),
        "organization_members": int(lab.psql_scalar(
            "SELECT count(*) FROM organization_members") or 0),
        "staff_profiles": int(lab.psql_scalar("SELECT count(*) FROM staff_profiles") or 0),
        "staff_roles": int(lab.psql_scalar("SELECT count(*) FROM staff_roles") or 0),
        "consultant_profiles": int(lab.psql_scalar(
            "SELECT count(*) FROM consultant_profiles") or 0),
        "consultant_firm_members": int(lab.psql_scalar(
            "SELECT count(*) FROM consultant_firm_members") or 0),
        "consultant_clients": int(lab.psql_scalar(
            "SELECT count(*) FROM consultant_clients") or 0),
        "processing_entities": int(lab.psql_scalar(
            "SELECT count(*) FROM processing_entities") or 0),
        "lab_auth_users": len([email for email in list_users()
                               if email.endswith(lab.EMAIL_DOMAIN)]),
    }


# --- main -----------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision local Demo Lab identities")
    parser.add_argument("--json", action="store_true", help="machine-readable summary")
    args = parser.parse_args()

    manifest = json.loads(lab.MANIFEST_PATH.read_text())
    for actor in manifest["actors"]:
        actor["email"] = f"{actor['local_part']}@{lab.EMAIL_DOMAIN}"

    health = lab.wait_for(f"http://127.0.0.1:{lab.GATEWAY_PORT}/auth/v1/health",
                          expect_in=(200,), attempts=5, delay=1.0)
    if health != 200:
        raise SystemExit(
            f"lab gateway/auth is not healthy (status={health}). "
            f"Run `python3 tools/demo_lab/stack.py` first.")

    failures: list = []
    password = lab.demo_password()
    role_ids = ensure_staff_roles(manifest, failures)
    entities = ensure_entity_rows(manifest, {}, failures)

    existing = list_users()
    users: dict[str, dict] = {}
    created = updated = 0
    for actor in manifest["actors"]:
        record = ensure_user(actor, password, existing)
        users[actor["key"]] = {"user_id": record["user_id"], "email": actor["email"]}
        created += int(record["created"])
        updated += int(not record["created"])

    ensure_user_mirror(users, failures)
    ensure_actor_relationships(manifest, entities, role_ids, users, failures)

    state = lab.load_state()
    state.update({
        "lab": lab.LAB_ID,
        "namespace": lab.LAB_NAMESPACE,
        "database": lab.LAB_DB,
        "gateway": f"http://127.0.0.1:{lab.GATEWAY_PORT}",
        "jwt_secret": lab.lab_secret(),
        "demo_password": password,
        "emails_domain": lab.EMAIL_DOMAIN,
        "actors": users,
        "entities": entities,
        "staff_roles": role_ids,
    })
    lab.save_state(state)

    summary = {
        "database": lab.LAB_DB,
        "auth_users_created": created,
        "auth_users_updated": updated,
        "entities": {key: value["id"] for key, value in entities.items()},
        "counts": counts(),
        "duplicate_check": audit_duplicates(),
        "failures": failures,
        "credentials_file": str(lab.CREDENTIALS_PATH),
    }
    if args.json:
        print(json.dumps(summary, indent=1, default=str))
    else:
        print(f"provisioned {len(users)} actors into {lab.LAB_DB} "
              f"(created={created}, updated={updated})")
        print(f"counts: {summary['counts']}")
        print(f"duplicate check (all must be 0): {summary['duplicate_check']}")
        for item in failures:
            print(f"  FAILURE {item['step']}: {item['error']}")
        print(f"local credentials: {lab.CREDENTIALS_PATH} (never committed)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
