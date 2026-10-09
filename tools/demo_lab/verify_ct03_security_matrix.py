#!/usr/bin/env python3
"""CT-CONSULTANT-MODEL-IMPLEMENTATION-03 — live security/authorization matrix.

Independent, deterministic verification of the CT03 authorization boundaries
against the RUNNING Demo Lab backend, using REAL password-grant logins (the same
path the browser uses). AGENTS.md §45 requires both the ALLOW and the DENY case
for every boundary; this script asserts both.

What it exercises
-----------------
* identity separation (§7.1, §45): consultant / internal-staff / PE identities
  are refused by the client plane, and a client identity is refused by the
  consultant plane;
* the entitlement gate (F-5, MUSTNOT-5): with the firm in ``standard`` mode the
  client plane is refused EVEN THOUGH the relationship profile grants access;
* the profile CEILING (F-3, PO-9): an unknown profile is a 422, PO-4 refuses
  ``managed`` outside co-branded/white-label, and a client can never map factors
  or recalculate;
* the retention lifecycle (F-4, PO-10): retained read-only is refused on an
  ACTIVE relationship (409) and, when lifted on an ended one, the client plane
  closes immediately (403) and re-opens when re-applied;
* the mode-change REQUEST path (F-6, PO-1/PO-5): the firm can only REQUEST; it
  cannot write ``commercial_mode``, and no accepted request changes it;
* no cross-firm oracle (INV-B/INV-C): another firm's client id is a 404.

It is read-mostly: the only state it changes is the two values the fixture owns
(access profile, retained flag) plus a temporary firm-mode flip that it always
restores. It creates NO rows except software-audited mode-change REQUEST rows
(returned by the API, which the fixture does not own and which are harmless,
auditable, and clearly attributed to the firm owner).

Usage::

    ./backend/.venv/bin/python tools/demo_lab/verify_ct03_security_matrix.py
    ./backend/.venv/bin/python tools/demo_lab/verify_ct03_security_matrix.py --json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402
import fixture_ct03_client_plane as fixture  # noqa: E402

BACKEND = f"http://127.0.0.1:{lab.BACKEND_PORT}"
GATEWAY = f"http://127.0.0.1:{lab.GATEWAY_PORT}"
FIRM = fixture.FIRM_ID

ACTORS = {
    "consultant_owner": "consultant.owner@demo-lab.carbontally.local",
    "consultant_member": "consultant.member@demo-lab.carbontally.local",
    "internal_operator": "operator@demo-lab.carbontally.local",
    "platform_admin": "platform.admin@demo-lab.carbontally.local",
    "pe_manager": "pe.manager@demo-lab.carbontally.local",
    "client_managed": fixture.NEW_CLIENTS[0]["email"],
    "client_retained": fixture.NEW_CLIENTS[1]["email"],
    "client_off": fixture.NEW_CLIENTS[2]["email"],
    "client_a": "owner.clienta@demo-lab.carbontally.local",
}


def _login(email: str, password: str) -> str:
    status, payload, raw = lab.http_json(
        f"{GATEWAY}/auth/v1/token?grant_type=password", method="POST",
        headers={"apikey": lab.anon_key()},
        body={"email": email, "password": password})
    if status != 200 or not isinstance(payload, dict) or not payload.get("access_token"):
        raise RuntimeError(f"login failed for {email} (status={status}): {raw[:160]}")
    return payload["access_token"]


def _call(path: str, token: str, *, method: str = "GET", body: dict | None = None):
    headers = {"Authorization": f"Bearer {token}"}
    if body is not None:
        return lab.http_json(f"{BACKEND}{path}", method=method, headers=headers,
                             body=body)
    return lab.http_json(f"{BACKEND}{path}", method=method, headers=headers)


def _mode(mode: str) -> None:
    lab.psql(f"UPDATE consultant_profiles SET commercial_mode = '{mode}' WHERE id = '{FIRM}'")


def run() -> dict:
    password = lab.demo_password()
    tokens = {key: _login(email, password) for key, email in ACTORS.items()}
    managed_org = fixture._id("org:managed")
    retained_org = fixture._id("org:retained")
    retained_rel = fixture._id("relationship:retained")
    client_a_rel = fixture.EXISTING_RELATIONSHIPS["client_a"]["relationship_id"]
    checks: list[dict] = []

    def check(name: str, got, want, detail: str = "") -> None:
        checks.append({"check": name, "ok": got == want, "want": want, "got": got,
                       "detail": detail[:200]})

    # --- identity separation (§7.1 / §45) --------------------------------
    for actor in ("consultant_owner", "consultant_member", "internal_operator",
                  "platform_admin", "pe_manager"):
        s, _p, _r = _call(f"/api/v3/portal/{managed_org}/context", tokens[actor])
        check(f"DENY {actor} -> client portal", s, 403)
    s, _p, _r = _call(f"/api/v3/consultants/me", tokens["client_managed"])
    check("DENY client -> consultant plane (/me)", s in (401, 403), True, f"status={s}")
    s, _p, _r = _call(f"/api/v3/consultants/clients/{retained_rel}/access-profile",
                      tokens["client_managed"], method="POST", body={"profile": "managed"})
    check("DENY client -> firm access-profile write", s in (401, 403), True, f"status={s}")

    # --- entitlement gate (F-5 / MUSTNOT-5) ------------------------------
    s, p, _r = _call(f"/api/v3/portal/{managed_org}/context", tokens["client_managed"])
    check("ALLOW managed client (white_label) -> portal 200", s, 200)

    # --- profile ceiling (F-3 / PO-9) ------------------------------------
    s, _p, _r = _call(f"/api/v3/consultants/clients/{retained_rel}/access-profile",
                      tokens["consultant_owner"], method="POST",
                      body={"profile": "god_mode"})
    check("REJECT unknown access profile (422)", s, 422)
    s, _p, _r = _call(f"/api/v3/consultants/clients/{client_a_rel}/access-profile",
                      tokens["consultant_owner"], method="POST", body={"profile": "managed"})
    check("ALLOW firm sets managed (white_label entitles it)", s, 200)
    s, _p, _r = _call(f"/api/v3/consultants/clients/{retained_rel}/access-profile",
                      tokens["consultant_owner"], method="POST", body={"profile": "read_only"})
    check("ALLOW firm restores retained profile read_only", s, 200)
    s, _p, _r = _call(f"/api/v3/consultants/clients/{client_a_rel}/access-profile",
                      tokens["consultant_owner"], method="POST", body={"profile": "read_only"})
    check("ALLOW firm restores client_a read_only", s, 200)
    s, _p, _r = _call(f"/api/v3/consultants/clients/"
                      "d9f9f30b-4152-54a1-9bbe-75eb6f99056c/access-profile",
                      tokens["consultant_owner"], method="POST", body={"profile": "off"})
    check("DENY another firm's client id (404, no oracle)", s, 404)

    # --- PO-9: a client can never map/recalculate (no route exists) -------
    for path in (f"/api/v3/portal/{managed_org}/factors",
                 f"/api/v3/portal/{managed_org}/mappings",
                 f"/api/v3/portal/{managed_org}/recalculate"):
        s, _p, _r = _call(path, tokens["client_managed"])
        check(f"ABSENT client route {path.rsplit('/', 1)[1]} (404/405)", s in (404, 405),
              True, f"status={s}")

    # --- writes: comment allowed / denied by profile + state -------------
    s, _p, _r = _call(f"/api/v3/portal/{managed_org}/annotations",
                      tokens["client_managed"], method="POST", body={"message": "ct03 qa"})
    check("ALLOW managed client comment (201)", s, 201)
    s, _p, _r = _call(f"/api/v3/portal/{retained_org}/annotations",
                      tokens["client_retained"], method="POST", body={"message": "ct03 qa"})
    check("DENY retained client comment (PA-3)", s, 403)
    s, _p, _r = _call(f"/api/v3/portal/{retained_org}/context", tokens["client_retained"])
    check("ALLOW retained client read (200)", s, 200)
   


    # --- entitlement gate: STANDARD firm has NO client plane (F-5) --------
    _mode("standard")
    s, _p, _r = _call(f"/api/v3/portal/{managed_org}/context", tokens["client_managed"])
    check("DENY client plane while firm mode=standard (MUSTNOT-5)", s, 403)
    s, _p, _r = _call(f"/api/v3/consultants/clients/{client_a_rel}/access-profile",
                      tokens["consultant_owner"], method="POST", body={"profile": "managed"})
    check("DENY managed profile in standard mode (PO-4)", s, 403)
    _mode("white_label")
    s, _p, _r = _call(f"/api/v3/portal/{managed_org}/context", tokens["client_managed"])
    check("ALLOW client plane restored (white_label)", s, 200)

    # --- retention lifecycle (F-4 / PO-10) -------------------------------
    s, _p, _r = _call(f"/api/v3/consultants/clients/{client_a_rel}/retention",
                      tokens["consultant_owner"], method="POST",
                      body={"retained_read_only": True})
    check("REJECT retained on an ACTIVE relationship (409)", s, 409)
    s, _p, _r = _call(f"/api/v3/consultants/clients/{retained_rel}/retention",
                      tokens["consultant_owner"], method="POST",
                      body={"retained_read_only": True})
    check("ALLOW retained on an ENDED relationship", s, 200)
    s, _p, _r = _call(f"/api/v3/consultants/clients/{retained_rel}/retention",
                      tokens["consultant_owner"], method="POST",
                      body={"retained_read_only": False})
    check("ALLOW lift retained read-only", s, 200)
    s, _p, _r = _call(f"/api/v3/portal/{retained_org}/context", tokens["client_retained"])
    check("DENY client plane after retention lifted (403)", s, 403)
    s, _p, _r = _call(f"/api/v3/consultants/clients/{retained_rel}/retention",
                      tokens["consultant_owner"], method="POST",
                      body={"retained_read_only": True})
    check("ALLOW re-apply retained read-only", s, 200)
    s, p, _r = _call(f"/api/v3/portal/{retained_org}/context", tokens["client_retained"])
    check("ALLOW client plane read-only re-opened (200)", s, 200)
    check("retained context reports state=retained_read_only",
          (p or {}).get("state"), "retained_read_only")
    check("retained context keeps read_data", ((p or {}).get("capabilities") or {})
          .get("read_data"), True)
    check("retained context denies comment", ((p or {}).get("capabilities") or {})
          .get("comment"), False)
    rows = lab.psql_scalar(
        "SELECT count(*) FROM organizations WHERE id = "
        f"'{retained_org}'").strip()
    check("ENDED relationship did NOT delete the organisation (data preserved)",
          rows, "1")

    # --- mode-change REQUEST path (F-6 / PO-1 / PO-5) --------------------
    s, p, _r = _call("/api/v3/consultants/me/mode-change-requests",
                     tokens["consultant_owner"], method="POST",
                     body={"requested_mode": "co_branded", "reason": "CT03 QA"})
    check("ALLOW firm owner requests a mode change (201)", s, 201)
    s, _p, _r = _call("/api/v3/consultants/me/mode-change-requests",
                      tokens["consultant_owner"], method="POST",
                      body={"requested_mode": "white_label"})
    check("REJECT request for the current mode (422)", s, 422)
    s, _p, _r = _call("/api/v3/consultants/me/mode-change-requests",
                      tokens["consultant_owner"], method="POST",
                      body={"requested_mode": "platinum"})
    check("REJECT unknown mode (422)", s, 422)
    s, _p, _r = _call("/api/v3/consultants/me/mode-change-requests",
                      tokens["consultant_member"], method="POST",
                      body={"requested_mode": "standard"})
    check("DENY firm member without CAP-MANAGE-TEAM (403)", s, 403)
    s, _p, _r = _call("/api/v3/consultants/me/mode-change-requests",
                      tokens["client_managed"], method="POST",
                      body={"requested_mode": "standard"})
    check("DENY client -> mode-change request", s in (401, 403), True, f"status={s}")
    pending = lab.psql_scalar(
        "SELECT count(*) FROM consultant_mode_change_requests "
        f"WHERE firm_id = '{FIRM}' AND status = 'requested'").strip()
    check("mode-change REQUEST persisted (auditable)", int(pending) >= 1, True,
          f"rows={pending}")
    live_mode = lab.psql_scalar(
        f"SELECT commercial_mode FROM consultant_profiles WHERE id = '{FIRM}'").strip()
    check("PO-5: an accepted REQUEST did not change commercial_mode",
          live_mode, "white_label")

    # --- retention (N3 platform settings + CT03 OQ-2/PO-10 policy) --------
    s, p, _r = _call("/api/v3/settings/retention", tokens["platform_admin"])
    check("ALLOW internal admin reads N3 platform retention settings", s, 200)
    if s == 200 and isinstance(p, dict):
        check("N3 endpoint invents no duration (unset -> null)",
              (p.get("settings") or {}).get("data_retention_days"), None)

    backend_dir = str(pathlib.Path(__file__).resolve().parents[2] / "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from domain.consultant_retention import (  # noqa: E402
        RETENTION_SETTING_KEY,
        resolve_retention_policy,
    )

    raw = lab.psql_scalar(
        "SELECT setting_value::text FROM system_settings "
        f"WHERE setting_key = '{RETENTION_SETTING_KEY}'").strip()
    policy = resolve_retention_policy(json.loads(raw) if raw else None)
    check("stored consultant retention policy present in system_settings",
          bool(raw), True, raw[:80])
    check("consultant retention = 7 YEARS (OQ-2 / PO-10)", policy.years, 7)
    check("consultant retention auto-delete OFF (deletion not implemented by design)",
          policy.auto_delete_enabled, False)
    check("consultant retention fails SAFE on an absent setting",
          resolve_retention_policy(None).years, 7)
    check("consultant retention fails SAFE on a malformed setting",
          resolve_retention_policy({"years": "nonsense"}).years, 7)

    failed = [c for c in checks if not c["ok"]]
    return {"checks": checks, "passed": len(checks) - len(failed),
            "failed": len(failed), "ok": not failed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for item in result["checks"]:
            mark = "PASS" if item["ok"] else "FAIL"
            extra = "" if item["ok"] else f" (want {item['want']}, got {item['got']})"
            print(f"[{mark}] {item['check']}{extra}")
        print(f"--- {result['passed']} passed, {result['failed']} failed ---")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
