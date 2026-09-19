#!/usr/bin/env python3
"""DEMO-T1 — server-side verification of the local Demo Lab identities.

For every actor in the manifest the script:

1. **authenticates** against the LAB's GoTrue (password grant);
2. calls the server-authoritative ``GET /api/v3/me/context`` and checks the
   resolved actor type, workspace destination, organisation and role;
3. exercises a probe matrix (expected allow / expected deny) against the release
   API, using only the real server-side gates;
4. checks tenant/entity isolation (Org A↔B, Client A↔B, consultant→unrelated
   organisation, customer→admin plane, customer→PE plane);
5. writes machine-readable evidence outside the repository.

It never trusts frontend routing: every expectation is a server response.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402

BACKEND = f"http://127.0.0.1:{lab.BACKEND_PORT}"
GATEWAY = f"http://127.0.0.1:{lab.GATEWAY_PORT}"

#: The release's server-authoritative workspace mapping (/api/v3/me/context).
DESTINATIONS = {
    "staff": "/ops",
    "entity_staff": "/pe",
    "consultant": "/consultant",
    "customer": "/home",
    "new_user": "/onboarding",
}


def login(actor: dict, state: dict) -> tuple[str, str]:
    """Password login via the lab GoTrue; documented fallback to a lab-signed token."""
    password = state.get("demo_password")
    status, payload, _raw = lab.http_json(
        f"{GATEWAY}/auth/v1/token?grant_type=password", method="POST",
        headers={"apikey": lab.anon_key()},
        body={"email": actor["email"], "password": password})
    if status == 200 and isinstance(payload, dict) and payload.get("access_token"):
        return payload["access_token"], "password_grant"
    record = state.get("actors", {}).get(actor["key"], {})
    token = lab.mint_token(record.get("user_id", ""), actor["email"], state["jwt_secret"])
    return token, f"minted_token (password grant status={status})"


def api_get(path: str, token: str) -> tuple[int, dict | list | None, str]:
    return lab.http_json(f"{BACKEND}{path}",
                         headers={"Authorization": f"Bearer {token}"})


def check(name: str, ok: bool, detail: str) -> dict:
    return {"check": name, "ok": bool(ok), "detail": detail}


def contexts(manifest: dict, state: dict) -> tuple[dict, dict, list]:
    tokens, context, checks = {}, {}, []
    for actor in manifest["actors"]:
        token, method = login(actor, state)
        tokens[actor["key"]] = token
        status, payload, raw = api_get("/api/v3/me/context", token)
        context[actor["key"]] = {"status": status, "payload": payload,
                                 "auth_method": method}
        expect = actor["expect"]
        if status != 200 or not isinstance(payload, dict):
            checks.append(check(f"context:{actor['key']}", False,
                                f"status={status} raw={str(raw)[:120]}"))
            continue
        problems = []
        if payload.get("actor_type") != expect["actor_type"]:
            problems.append(f"actor_type={payload.get('actor_type')}!={expect['actor_type']}")
        if payload.get("destination") != expect["destination"]:
            problems.append(f"destination={payload.get('destination')}!={expect['destination']}")
        if payload.get("destination") != DESTINATIONS.get(payload.get("actor_type")):
            problems.append("destination does not match the server mapping")
        if expect.get("role"):
            actual = (payload.get("staff") or payload.get("organization") or
                      payload.get("consultant") or {}).get("role")
            if actual != expect["role"]:
                problems.append(f"role={actual}!={expect['role']}")
        if expect.get("organization"):
            org = payload.get("organization") or {}
            if org.get("name") != state["entities"][expect["organization"]]["name"]:
                problems.append(f"organization={org.get('name')}")
        checks.append(check(f"context:{actor['key']}", not problems,
                            "ok" if not problems else "; ".join(problems)))
    return tokens, context, checks


def probe_specs(state: dict) -> list[dict]:
    """The authorization matrix, expressed against real release endpoints.

    Expectations follow the release's own gates:

    * ``GET /api/v3/organizations/{id}``              → ``require_org_member``
    * ``GET /api/v3/reporting/audit-activity``        → ``ensure_org_audit_access`` (owner/admin)
    * ``GET /api/v3/consultants/me``                  → ``require_consultant``
    * ``GET /api/v3/consultants/clients/{id}/context``→ consultant client grant
    * ``GET /api/v3/pe/me``                           → ``require_pe_member``
    * ``GET /api/v3/admin/manual-processing/grants``  → internal staff + admin authority
    """
    ent = state["entities"]
    org_a, org_b = ent["org_a"]["id"], ent["org_b"]["id"]
    # `client_id` on /consultants/clients/{client_id}/... is the engagement row
    # (consultant_clients.id), not the client organisation id.
    client_a = lab.deterministic_uuid("engagement:client_a")
    client_b = lab.deterministic_uuid("engagement:client_b")
    client_a_org, client_b_org = ent["client_a"]["id"], ent["client_b"]["id"]
    return [
        {"name": "org_a_owner reads Org A", "actor": "org_a_owner",
         "path": f"/api/v3/organizations/{org_a}", "expect": (200,)},
        {"name": "org_a_owner reads Org B (DENY)", "actor": "org_a_owner",
         "path": f"/api/v3/organizations/{org_b}", "expect": (403, 404),
         "isolation": "Org A → Org B"},
        {"name": "org_b_owner reads Org B", "actor": "org_b_owner",
         "path": f"/api/v3/organizations/{org_b}", "expect": (200,)},
        {"name": "org_b_owner reads Org A (DENY)", "actor": "org_b_owner",
         "path": f"/api/v3/organizations/{org_a}", "expect": (403, 404),
         "isolation": "Org B → Org A"},
        {"name": "org_a_viewer reads Org A (read allowed)", "actor": "org_a_viewer",
         "path": f"/api/v3/organizations/{org_a}", "expect": (200,)},
        {"name": "org_a_owner audit activity", "actor": "org_a_owner",
         "path": f"/api/v3/reporting/audit-activity?organization_id={org_a}",
         "expect": (200,),
         "defect": "F-T1-001: endpoint raises 500 (asyncpg: operator does not exist: uuid = text) "
                   "for a correctly-authorized owner — product defect, outside T1 identity scope"},
        {"name": "org_a_viewer audit activity (DENY)", "actor": "org_a_viewer",
         "path": f"/api/v3/reporting/audit-activity?organization_id={org_a}",
         "expect": (403,), "isolation": "viewer → owner/admin surface"},
        {"name": "org_a_member audit activity (DENY)", "actor": "org_a_member",
         "path": f"/api/v3/reporting/audit-activity?organization_id={org_a}",
         "expect": (403,), "isolation": "member → owner/admin surface"},
        {"name": "org_a_owner audit on Org B (DENY)", "actor": "org_a_owner",
         "path": f"/api/v3/reporting/audit-activity?organization_id={org_b}",
         "expect": (403, 404), "isolation": "Org A → Org B audit"},
        {"name": "consultant owner /consultants/me", "actor": "consultant_owner",
         "path": "/api/v3/consultants/me", "expect": (200,)},
        {"name": "consultant member /consultants/me", "actor": "consultant_member",
         "path": "/api/v3/consultants/me", "expect": (200,)},
        {"name": "org_a_owner /consultants/me (DENY)", "actor": "org_a_owner",
         "path": "/api/v3/consultants/me", "expect": (403,),
         "isolation": "customer → consultant plane"},
        {"name": "consultant owner enters Client A", "actor": "consultant_owner",
         "path": f"/api/v3/consultants/clients/{client_a}/context", "expect": (200,)},
        {"name": "consultant owner enters Client B", "actor": "consultant_owner",
         "path": f"/api/v3/consultants/clients/{client_b}/context", "expect": (200,)},
        {"name": "consultant owner enters unrelated Org B (DENY)", "actor": "consultant_owner",
         "path": f"/api/v3/consultants/clients/{org_b}/context", "expect": (403, 404),
         "isolation": "consultant → unrelated organisation"},
        {"name": "client_a_owner /consultants/me (DENY)", "actor": "client_a_owner",
         "path": "/api/v3/consultants/me", "expect": (403,),
         "isolation": "client → consultant plane"},
        {"name": "client_a_owner reads Client A", "actor": "client_a_owner",
         "path": f"/api/v3/organizations/{client_a_org}", "expect": (200,)},
        {"name": "client_a_owner reads Client B (DENY)", "actor": "client_a_owner",
         "path": f"/api/v3/organizations/{client_b_org}", "expect": (403, 404),
         "isolation": "Client A → Client B"},
        {"name": "client_b_owner reads Client B", "actor": "client_b_owner",
         "path": f"/api/v3/organizations/{client_b_org}", "expect": (200,)},
        {"name": "client_b_owner reads Client A (DENY)", "actor": "client_b_owner",
         "path": f"/api/v3/organizations/{client_a_org}", "expect": (403, 404),
         "isolation": "Client B → Client A"},
    ]



def remaining_probes(state: dict) -> list[dict]:
    """PE plane, admin control plane and cross-plane denials."""
    ent = state["entities"]
    org_b = ent["org_b"]["id"]
    client_b = ent["client_b"]["id"]
    return [
        {"name": "pe_manager /pe/me", "actor": "pe_manager",
         "path": "/api/v3/pe/me", "expect": (200,)},
        {"name": "org_a_owner /pe/me (DENY)", "actor": "org_a_owner",
         "path": "/api/v3/pe/me", "expect": (403,), "isolation": "customer → PE plane"},
        {"name": "internal operator /pe/me (DENY)", "actor": "internal_operator",
         "path": "/api/v3/pe/me", "expect": (403,), "isolation": "internal staff → PE plane"},
        {"name": "platform admin reads MPG grants", "actor": "platform_admin",
         "path": "/api/v3/admin/manual-processing/grants", "expect": (200,)},
        {"name": "internal operator grants (DENY: no admin authority)",
         "actor": "internal_operator", "path": "/api/v3/admin/manual-processing/grants",
         "expect": (403,), "isolation": "staff operator → admin authority"},
        {"name": "org_a_owner grants (DENY)", "actor": "org_a_owner",
         "path": "/api/v3/admin/manual-processing/grants", "expect": (403,),
         "isolation": "customer → admin plane"},
        {"name": "consultant owner grants (DENY)", "actor": "consultant_owner",
         "path": "/api/v3/admin/manual-processing/grants", "expect": (403,),
         "isolation": "consultant → admin plane"},
        {"name": "pe_manager grants (DENY)", "actor": "pe_manager",
         "path": "/api/v3/admin/manual-processing/grants", "expect": (403,),
         "isolation": "PE → admin plane"},
        {"name": "org_a_owner reads Org B members (DENY)", "actor": "org_a_owner",
         "path": f"/api/v3/organizations/{org_b}/members", "expect": (403, 404),
         "isolation": "Org A → Org B members"},
        {"name": "client_a_owner reads Client B members (DENY)", "actor": "client_a_owner",
         "path": f"/api/v3/organizations/{client_b}/members", "expect": (403, 404),
         "isolation": "Client A → Client B members"},
    ]


def run_probes(specs: list[dict], tokens: dict) -> list[dict]:
    results = []
    for spec in specs:
        status, payload, _raw = api_get(spec["path"], tokens[spec["actor"]])
        detail = f"status={status} expected={list(spec['expect'])}"
        if status in (403, 404) and isinstance(payload, dict) and payload.get("detail"):
            detail += f" reason={str(payload['detail'])[:70]}"
        results.append({"probe": spec["name"], "actor": spec["actor"], "path": spec["path"],
                        "status": status, "expected": list(spec["expect"]),
                        "ok": status in spec["expect"], "isolation": spec.get("isolation"),
                        "defect": spec.get("defect"), "detail": detail})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the local Demo Lab identities")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(lab.MANIFEST_PATH.read_text())
    state = lab.load_state()
    if not state.get("actors"):
        raise SystemExit("nothing provisioned yet — run "
                         "`python3 tools/demo_lab/provision.py` first")
    for actor in manifest["actors"]:
        actor["email"] = state["actors"][actor["key"]]["email"]

    tokens, context, checks = contexts(manifest, state)
    probes = run_probes(probe_specs(state) + remaining_probes(state), tokens)

    isolation = []
    for probe in probes:
        if probe["isolation"]:
            isolation.append({"rule": probe["isolation"], "probe": probe["probe"],
                              "status": probe["status"], "ok": probe["ok"]})

    routing = [check(f"routing:{actor['key']}",
                     (context[actor["key"]]["payload"] or {}).get("destination")
                     == actor["expect"]["destination"],
                     f"{(context[actor['key']]['payload'] or {}).get('actor_type')} → "
                     f"{(context[actor['key']]['payload'] or {}).get('destination')}")
               for actor in manifest["actors"]]

    failed = [c for c in checks + routing if not c["ok"]] + \
        [p for p in probes if not p["ok"] and not p.get("defect")]
    defects = [p for p in probes if not p["ok"] and p.get("defect")]
    evidence = {
        "lab": lab.LAB_ID, "namespace": lab.LAB_NAMESPACE, "database": lab.LAB_DB,
        "gateway": GATEWAY, "backend": BACKEND,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "contexts": {key: {"status": value["status"], "auth_method": value["auth_method"],
                           "actor_type": (value["payload"] or {}).get("actor_type"),
                           "destination": (value["payload"] or {}).get("destination"),
                           "organization": (value["payload"] or {}).get("organization"),
                           "staff": (value["payload"] or {}).get("staff"),
                           "consultant": (value["payload"] or {}).get("consultant")}
                     for key, value in context.items()},
        "context_checks": checks, "routing_checks": routing, "probes": probes,
        "isolation": isolation,
        "summary": {
            "contexts": len(checks), "contexts_failed": len([c for c in checks if not c["ok"]]),
            "probes": len(probes), "probes_failed": len([p for p in probes if not p["ok"]]),
            "probes_failed_identity": len([p for p in probes
                                           if not p["ok"] and not p.get("defect")]),
            "known_product_defects": [p["probe"] for p in probes
                                      if not p["ok"] and p.get("defect")],
            "isolation_rules": len(isolation),
            "isolation_rules_failed": len([i for i in isolation if not i["ok"]]),
            "auth_methods": sorted({v["auth_method"].split(" ")[0] for v in context.values()}),
        },
    }
    lab.ensure_dirs()
    out = lab.EVIDENCE_DIR / f"verify_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    out.write_text(json.dumps(evidence, indent=1, default=str))

    if args.json:
        print(json.dumps(evidence, indent=1, default=str))
    else:
        print(f"── actor contexts: {len(checks) - evidence['summary']['contexts_failed']}"
              f"/{len(checks)} correct  (auth: {', '.join(evidence['summary']['auth_methods'])})")
        for item in checks + routing:
            print(f"  [{'PASS' if item['ok'] else 'FAIL'}] {item['check']}: {item['detail']}")
        print(f"── authorization / isolation probes: "
              f"{len(probes) - evidence['summary']['probes_failed']}/{len(probes)} as expected")
        for probe in probes:
            print(f"  [{'PASS' if probe['ok'] else 'FAIL'}] {probe['probe']}: {probe['detail']}")
        print(f"── isolation rules enforced: "
              f"{len(isolation) - evidence['summary']['isolation_rules_failed']}/{len(isolation)}")
        for defect in defects:
            print(f"── KNOWN PRODUCT DEFECT (outside T1 scope): {defect['probe']} — "
                  f"{defect['detail']}\n   {defect['defect']}")
        print(f"evidence: {out}")
        if failed:
            print(f"RESULT: FAILED ({len(failed)} checks)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
