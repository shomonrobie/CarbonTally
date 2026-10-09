#!/usr/bin/env python3
"""CT-CONSULTANT-MODEL-IMPLEMENTATION-03 — deterministic Demo Lab QA fixture.

The CT03 increment implements the CLIENT-PLANE state machine (F-3, F-4, F-5,
F-7): the four client access profiles (``off`` / ``read_only`` /
``collaborative`` / ``managed``), the three product modes (``standard`` /
``co_branded`` / ``white_label``) that decide whether a client plane exists at
all, and the PO-10 RETAINED read-only state that survives the end of a
relationship.

None of those states were reachable in the Demo Lab before this fixture: the
one consultant firm was ``standard`` (no client plane at all, MUSTNOT-5) and
both of its client relationships sat at the pre-CT03 default profile ``off``.
The Product Owner therefore authorised a purpose-built, *isolated* QA fixture
so the states can be browser-verified and manually operated.

This module follows the established DEMO-T1 / ``fixture_mp_coverage.py``
pattern rather than inventing a parallel mechanism:

* it reuses :mod:`lab` (names, ports, deterministic UUIDs, psql/HTTP helpers,
  local-only credentials) and :mod:`provision` (the GoTrue user upsert, the
  ``auth.users`` mirror and the SQL literal helpers);
* every fixture row has a **deterministic id** (``lab.deterministic_uuid``) and
  every write is an idempotent ``INSERT … ON CONFLICT (id) DO UPDATE`` upsert;
* every fixture row is **clearly labelled** (organisation
  ``metadata.fixture`` = ``ct-consultant-03-client-plane``, names prefixed
  ``CT03-QA``, lab e-mail local-parts prefixed ``ct03.``) and ``--reset``
  removes exactly those rows, those memberships and those local GoTrue users,
  and restores the two pre-existing rows it touched;
* it writes ONLY to the local Demo Lab database and the local lab gateway — it
  never contacts production, Render, a hosted Supabase project, or the investor
  demo dataset.

Two things are deliberately NOT created, because creating them would weaken the
security property the fixture is meant to demonstrate:

* the fixture does **not** add a second organisation membership to any existing
  demo identity. ``auth.py`` resolves a user's organisation with
  ``maybe_single()``, so a second active membership would break that identity's
  single-organisation resolution (and every other fixture that uses it).
  Instead the fixture provisions three NEW client identities, each with exactly
  one membership in exactly one new organisation;
* the fixture does **not** create a consultant write path for ``commercial_mode``.
  PO-5/§6.3 forbids one, so the fixture performs the mode change the way
  CarbonTally Admin would — directly on ``consultant_profiles.commercial_mode`` —
  and the consultant-facing surface only ever *requests* a change (F-6).

Usage::

    python3 tools/demo_lab/fixture_ct03_client_plane.py            # apply (idempotent)
    python3 tools/demo_lab/fixture_ct03_client_plane.py --verify   # server-side checks
    python3 tools/demo_lab/fixture_ct03_client_plane.py --reset    # remove the fixture
    python3 tools/demo_lab/fixture_ct03_client_plane.py --json     # machine-readable
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402
import provision  # noqa: E402

BACKEND = f"http://127.0.0.1:{lab.BACKEND_PORT}"
GATEWAY = f"http://127.0.0.1:{lab.GATEWAY_PORT}"

#: Stable fixture identity — used in row labels and evidence file names.
FIXTURE_ID = "ct-consultant-03-client-plane"
FIXTURE_MARKER = {"demo_lab": True, "namespace": lab.LAB_NAMESPACE, "fixture": FIXTURE_ID}

#: The ONE consultant firm the Demo Lab provisions (``firm_demo``).
FIRM_ID = "5d37e668-e86a-5e23-8de1-41cf0503a79d"
FIRM_NAME = "Demo Lab Carbon Consultants"

#: The mode the fixture grants the firm. ``white_label`` is the most entitled
#: mode (client plane + managed profile + custom domain), so it makes EVERY
#: profile state reachable — including ``managed``, which PO-4 permits only in
#: co-branded/white-label.
FIXTURE_MODE = "white_label"

#: Pre-existing rows the fixture intentionally touches, with the exact values it
#: must restore on ``--reset`` (verified against the lab DB before the change).
EXISTING_RELATIONSHIPS = {
    "client_a": {
        "relationship_id": "09501808-17e2-5cdc-a128-486f41a997b3",
        "organization_id": "02b38744-27fe-5062-8f36-9af7a726eb4c",
        "profile": "read_only",
        "restore_profile": "off",
    },
    "client_b": {
        "relationship_id": "2bb2a5c8-a5d1-5ec3-808a-f14ff5b1f15b",
        "organization_id": "b4bb08f1-52d5-5155-9572-99026760814c",
        "profile": "collaborative",
        "restore_profile": "off",
    },
}

#: The three NEW client organisations — one per non-default reachable state.
NEW_CLIENTS = (
    {
        "key": "managed",
        "name": "CT03-QA Managed Client",
        "email": f"ct03.owner.managed@{lab.EMAIL_DOMAIN}",
        "contact_name": "CT03 Managed Owner",
        "status": "active",
        "profile": "managed",
        "retained": False,
        "role": "owner",
    },
    {
        "key": "retained",
        "name": "CT03-QA Retained Client",
        "email": f"ct03.owner.retained@{lab.EMAIL_DOMAIN}",
        "contact_name": "CT03 Retained Owner",
        "status": "ended",
        "profile": "read_only",
        "retained": True,
        "role": "owner",
    },
    {
        "key": "off",
        "name": "CT03-QA Off Client",
        "email": f"ct03.owner.off@{lab.EMAIL_DOMAIN}",
        "contact_name": "CT03 Off Owner",
        "status": "active",
        "profile": "off",
        "retained": False,
        "role": "owner",
    },
)


def _id(key: str) -> str:
    """Deterministic id for one fixture row."""
    return lab.deterministic_uuid(f"{FIXTURE_ID}:{key}")


def _evidence_path() -> pathlib.Path:
    lab.ensure_dirs()
    return lab.EVIDENCE_DIR / f"{FIXTURE_ID}.json"

def apply() -> dict:
    """Create/refresh the CT03 client-plane fixture (idempotent)."""
    failures: list = []
    password = lab.demo_password()
    existing = provision.list_users()

    # --- 1. client identities (local GoTrue only) -------------------------
    users: dict[str, dict] = {}
    for client in NEW_CLIENTS:
        created = provision.ensure_user({"email": client["email"]}, password, existing)
        users[client["key"]] = {"user_id": created["user_id"], "email": client["email"]}
        print(f"[user] {client['email']} ({'created' if created['created'] else 'updated'})")

    # ``auth.users`` in the LAB database is the FK target for
    # ``organization_members.user_id``; the local trigger then mirrors the row
    # into ``public.users``.
    provision.ensure_user_mirror(users, failures)

    # --- 2. organisations -------------------------------------------------
    for client in NEW_CLIENTS:
        provision.sql(
            "INSERT INTO organizations (id, name, is_active, metadata) VALUES "
            f"({provision.go(_id('org:' + client['key']))}, {provision.go(client['name'])}, "
            f"true, {provision.go(FIXTURE_MARKER)}) "
            "ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, is_active = true, "
            "metadata = EXCLUDED.metadata",
            label=f"organization:{client['key']}",
            failures=failures,
        )

    # --- 3. memberships (exactly ONE active organisation per new identity) --
    for client in NEW_CLIENTS:
        provision.sql(
            "INSERT INTO organization_members (id, organization_id, user_id, role, is_active) "
            f"VALUES ({provision.go(_id('member:' + client['key']))}, "
            f"{provision.go(_id('org:' + client['key']))}, "
            f"{provision.go(users[client['key']]['user_id'])}, "
            f"{provision.go(client['role'])}, true) "
            "ON CONFLICT (id) DO UPDATE SET organization_id = EXCLUDED.organization_id, "
            "user_id = EXCLUDED.user_id, role = EXCLUDED.role, is_active = true",
            label=f"organization_member:{client['key']}",
            failures=failures,
        )

    # --- 4. consultant relationships (the client-plane states) ------------
    for client in NEW_CLIENTS:
        ended_at = "now()" if client["status"] == "ended" else "NULL"
        provision.sql(
            "INSERT INTO consultant_clients (id, consultant_id, organization_id, "
            "client_name, client_contact_email, client_contact_name, status, ended_at, "
            "client_access_profile, retained_read_only, relationship_origin) VALUES "
            f"({provision.go(_id('relationship:' + client['key']))}, {provision.go(FIRM_ID)}, "
            f"{provision.go(_id('org:' + client['key']))}, {provision.go(client['name'])}, "
            f"{provision.go(client['email'])}, {provision.go(client['contact_name'])}, "
            f"{provision.go(client['status'])}, {ended_at}, "
            f"{provision.go(client['profile'])}, "
            f"{'true' if client['retained'] else 'false'}, "
            "'consultant_created_customer') "
            "ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, "
            "ended_at = EXCLUDED.ended_at, "
            "client_access_profile = EXCLUDED.client_access_profile, "
            "retained_read_only = EXCLUDED.retained_read_only",
            label=f"relationship:{client['key']}",
            failures=failures,
        )

    # --- 5. the firm's product mode (CarbonTally-Admin-owned, PO-5) --------
    provision.sql(
        "UPDATE consultant_profiles SET commercial_mode = "
        f"{provision.go(FIXTURE_MODE)} WHERE id = {provision.go(FIRM_ID)}",
        label="firm:commercial_mode",
        failures=failures,
    )

    # --- 6. the two pre-existing relationships (read_only / collaborative) -
    for key, row in EXISTING_RELATIONSHIPS.items():
        provision.sql(
            "UPDATE consultant_clients SET client_access_profile = "
            f"{provision.go(row['profile'])} WHERE id = {provision.go(row['relationship_id'])}",
            label=f"existing_relationship:{key}",
            failures=failures,
        )

    state = _state(users)
    lab.ensure_dirs()
    _evidence_path().write_text(json.dumps(state, indent=2), encoding="utf-8")
    state["failures"] = failures
    return state



def _state(users: dict[str, dict]) -> dict:
    """Non-secret description of the fixture (safe to write/print)."""
    return {
        "fixture": FIXTURE_ID,
        "firm": {"id": FIRM_ID, "name": FIRM_NAME, "commercial_mode": FIXTURE_MODE},
        "existing_relationships": {
            key: {
                "relationship_id": row["relationship_id"],
                "organization_id": row["organization_id"],
                "client_access_profile": row["profile"],
            }
            for key, row in EXISTING_RELATIONSHIPS.items()
        },
        "clients": [
            {
                "key": client["key"],
                "organization_id": _id("org:" + client["key"]),
                "relationship_id": _id("relationship:" + client["key"]),
                "email": client["email"],
                "user_id": (users.get(client["key"]) or {}).get("user_id"),
                "status": client["status"],
                "client_access_profile": client["profile"],
                "retained_read_only": client["retained"],
            }
            for client in NEW_CLIENTS
        ],
    }


def _login(email: str, password: str) -> tuple[str, str]:
    """Authenticate exactly as the browser does — lab GoTrue password grant.

    The release validates the local stack's signature (``SUPABASE_JWT_SECRET``
    is the stack secret, see ``lab_env.py``), so a locally *minted* token is not
    accepted; the password grant is the authoritative path (the same one
    ``verify.py`` uses).
    """
    status, payload, raw = lab.http_json(
        f"{GATEWAY}/auth/v1/token?grant_type=password",
        method="POST",
        headers={"apikey": lab.anon_key()},
        body={"email": email, "password": password},
    )
    if status != 200 or not isinstance(payload, dict) or not payload.get("access_token"):
        raise RuntimeError(f"password grant failed for {email} (status={status}): {raw[:200]}")
    return payload["access_token"], "password_grant"


def verify() -> dict:
    """Server-side verification: DB state AND the live backend portal gate."""
    checks: list[dict] = []
    password = lab.demo_password()

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    mode = lab.psql_scalar(
        f"SELECT commercial_mode FROM consultant_profiles WHERE id = '{FIRM_ID}'"
    ).strip()
    check("firm.commercial_mode == " + FIXTURE_MODE, mode == FIXTURE_MODE, mode)

    for key, row in EXISTING_RELATIONSHIPS.items():
        got = lab.psql_scalar(
            "SELECT client_access_profile FROM consultant_clients "
            f"WHERE id = '{row['relationship_id']}'"
        ).strip()
        check(f"existing.{key}.profile == {row['profile']}", got == row["profile"], got)

    expected_http = {"managed": 200, "retained": 200, "off": 403}
    for client in NEW_CLIENTS:
        org_id = _id("org:" + client["key"])
        row = lab.psql(
            "SELECT status, client_access_profile, retained_read_only FROM consultant_clients "
            f"WHERE id = '{_id('relationship:' + client['key'])}'"
        ).stdout.strip()
        check(
            f"relationship.{client['key']} (status/profile/retained)",
            row.replace("|", "/") ==
            f"{client['status']}/{client['profile']}/{'t' if client['retained'] else 'f'}",
            row,
        )

        member = lab.psql_scalar(
            f"SELECT count(*) FROM organization_members "
            f"WHERE organization_id = '{org_id}' AND is_active = true"
        ).strip()
        check(f"members.{client['key']} == 1", member == "1", member)
        memberships = lab.psql_scalar(
            "SELECT count(*) FROM organization_members om JOIN users u ON u.id = om.user_id "
            f"WHERE u.email = '{client['email']}' AND om.is_active = true"
        ).strip()
        # ``auth.py`` resolves the organisation with ``maybe_single()``: a second
        # active membership would break this identity's resolution.
        check(f"identity[{client['key']}].active_memberships == 1",
              memberships == "1", memberships)
        token, method = _login(client["email"], password)
        check(f"login[{client['key']}] via {method}", bool(token), method)
        status, payload, raw = lab.http_json(
            f"{BACKEND}/api/v3/portal/{org_id}/context",
            headers={"Authorization": f"Bearer {token}"},
        )
        want = expected_http[client["key"]]
        detail = json.dumps(payload)[:200] if isinstance(payload, dict) else raw[:200]
        check(
            f"portal[{client['key']}] -> HTTP {want}",
            status == want,
            f"got {status}: {detail}",
        )
        if want == 200 and isinstance(payload, dict):
            caps = payload.get("capabilities") or {}
            check(
                f"portal[{client['key']}].profile == {client['profile']}",
                payload.get("profile") == client["profile"],
                str(payload.get("profile")),
            )
            check(
                f"portal[{client['key']}].state == "
                + ("retained_read_only" if client["key"] == "retained" else "active"),
                payload.get("state") ==
                ("retained_read_only" if client["key"] == "retained" else "active"),
                str(payload.get("state")),
            )
            check(f"portal[{client['key']}].map_factors == False (PO-9)",
                  caps.get("map_factors") is False, str(caps.get("map_factors")))
            check(f"portal[{client['key']}].recalculate == False (PO-9)",
                  caps.get("recalculate") is False, str(caps.get("recalculate")))
            check(
                f"portal[{client['key']}].read_data == True",
                caps.get("read_data") is True,
                str(caps.get("read_data")),
            )
            if client["key"] == "retained":
                check("portal[retained].comment == False (PA-3, no write)",
                      caps.get("comment") is False, str(caps.get("comment")))
                check("portal[retained].upload_document == False (PA-3)",
                      caps.get("upload_document") is False, str(caps.get("upload_document")))
            if client["key"] == "managed":
                check("portal[managed].upload_document == False (PO-4 managed)",
                      caps.get("upload_document") is False,
                      str(caps.get("upload_document")))
                check("portal[managed].comment == True",
                      caps.get("comment") is True, str(caps.get("comment")))

    failed = [c for c in checks if not c["ok"]]
    return {"checks": checks, "passed": len(checks) - len(failed),
            "failed": len(failed), "ok": not failed}



def reset() -> dict:
    """Remove exactly this fixture and restore the two rows it touched.

    Never touches any non-fixture organisation, membership or relationship: the
    deletes are keyed on deterministic fixture ids, on the fixture marker, and
    on the two pre-existing relationship ids (whose profile is restored to the
    verified pre-fixture value ``off``).
    """
    failures: list = []
    org_ids = ", ".join(f"'{_id('org:' + c['key'])}'" for c in NEW_CLIENTS)
    rel_ids = ", ".join(f"'{_id('relationship:' + c['key'])}'" for c in NEW_CLIENTS)

    provision.sql(f"DELETE FROM consultant_clients WHERE id IN ({rel_ids})",
                  label="reset:consultant_clients", failures=failures)
    provision.sql(f"DELETE FROM organization_members WHERE organization_id IN ({org_ids})",
                  label="reset:organization_members", failures=failures)
    provision.sql(f"DELETE FROM organizations WHERE id IN ({org_ids})",
                  label="reset:organizations", failures=failures)

    # Local GoTrue identities (and their lab-database mirrors).
    existing = provision.list_users()
    removed_users = []
    for client in NEW_CLIENTS:
        record = existing.get(client["email"].lower())
        if not record:
            continue
        base = f"{GATEWAY}/auth/v1/admin/users/{record['id']}"
        status, _payload, raw = lab.http_json(
            base, method="DELETE", headers=provision.gotrue_headers()
        )
        if status not in (200, 204):
            failures.append({"step": f"reset:gotrue:{client['email']}", "error": raw[:200]})
        removed_users.append(record["id"])
        provision.sql("DELETE FROM organization_members WHERE user_id = "
                      f"'{record['id']}'", label="reset:members_by_user", failures=failures)
        provision.sql(f"DELETE FROM users WHERE id = '{record['id']}'",
                      label="reset:public_users", failures=failures)
        provision.sql(f"DELETE FROM auth.users WHERE id = '{record['id']}'",
                      label="reset:auth_users", failures=failures)

    # Restore the CarbonTally-Admin-owned firm mode and the two pre-existing
    # access profiles to their verified pre-fixture values.
    provision.sql(
        f"UPDATE consultant_profiles SET commercial_mode = 'standard' WHERE id = '{FIRM_ID}'",
        label="reset:firm_mode", failures=failures)
    for key, row in EXISTING_RELATIONSHIPS.items():
        provision.sql(
            "UPDATE consultant_clients SET client_access_profile = "
            f"'{row['restore_profile']}' WHERE id = '{row['relationship_id']}'",
            label=f"reset:existing_relationship:{key}", failures=failures)

    path = _evidence_path()
    if path.exists():
        path.unlink()

    return {"fixture": FIXTURE_ID, "removed_users": removed_users, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verify", action="store_true", help="server-side checks only")
    parser.add_argument("--reset", action="store_true", help="remove the fixture")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    if args.reset:
        result = reset()
        print(json.dumps(result, indent=2) if args.json else
              f"reset {FIXTURE_ID}: removed users={result['removed_users']} "
              f"failures={len(result['failures'])}")
        return 0 if not result["failures"] else 1

    if args.verify:
        result = verify()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            for item in result["checks"]:
                mark = "PASS" if item["ok"] else "FAIL"
                print(f"[{mark}] {item['check']}" + ("" if item["ok"] else f" :: {item['detail']}"))
            print(f"--- {result['passed']} passed, {result['failed']} failed ---")
        return 0 if result["ok"] else 1

    state = apply()
    if args.json:
        print(json.dumps(state, indent=2))
    else:
        print(f"applied {FIXTURE_ID}: firm mode={state['firm']['commercial_mode']}, "
              f"clients={[c['key'] for c in state['clients']]}, "
              f"failures={len(state['failures'])}")
    return 0 if not state["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

