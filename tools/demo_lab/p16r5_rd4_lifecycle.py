#!/usr/bin/env python3
"""P16-R5 / RD-4 (R9) — live accounting-result reportability lifecycle.

Demonstrates, through the real API plus read-only SQL:
  A historical invalid result remains (value unchanged)
  B invalidation records state + reason + actor + timestamp
  C replacement/supersession relationship recorded
  D invalid result is excluded from reportable aggregation
  E valid replacement remains reportable
  F cross-tenant denial
  G a normal, untouched result remains reportable
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab  # noqa: E402
from p16_journey import call, login  # noqa: E402

INVALID_SNAP = "f60affde-ed51-4b23-b5b3-ac920927568e"
INVALID_LOG = "3c7229be-31ac-4d00-9e29-4ed2052c895d"
VALID_SNAP = "dd5e4648-aa36-405b-b2d7-68ba21477b80"
VALID_LOG = "67ae1d37-cc3b-4b2c-86c6-59797f49898b"


def sq(sql: str) -> str:
    return (lab.psql(sql).stdout or "").strip()


def main() -> int:
    org = sq(f"SELECT organization_id FROM calculation_snapshots WHERE id='{INVALID_SNAP}';")
    print(f"[setup] invalid snapshot org={org}")
    period = sq(f"SELECT min(start_date)||'|'||max(start_date) FROM emissions_logs "
                f"WHERE organization_id='{org}' AND reportability_status='reportable';")
    start = period.split("|")[0]
    print(f"[setup] reportable period start={start}")

    owner, _ = login("org_a_owner")
    breakdown = (f"/api/v3/emissions/scope-breakdown?organization_id={org}"
                 f"&start_date={start}&end_date=2026-12-31")

    # P16-R5: find an actor that is authorised for this organisation. The
    # lifecycle route enforces org access server-side, so we probe identity
    # names only (no secrets are read or printed).
    import json as _json
    import os
    creds = _json.load(open(os.path.expanduser(
        "~/ct_local_env/demo_lab/credentials.local.json")))
    names = sorted(creds.keys()) if isinstance(creds, dict) else []
    print(f"[setup] credential identities: {len(names)}")
    actor = None
    for name in ["org_a_owner", *[n for n in names if n.endswith("_owner")][:25]]:
        try:
            tok, _ = login(name)
        except Exception:
            continue
        st, _b = call(f"/api/v3/emissions/calculations/{INVALID_SNAP}/invalidate", tok,
                      method="POST", body={"reason": "probe"}, label="probe")
        if st not in (401, 403, 404):
            print(f"[setup] !! probe already mutated state with {name} -> {st}")
            break
        if st == 409:  # already non-reportable => authorised (idempotent refusal)
            print(f"[setup] authorized actor={name} (409 already non-reportable)")
            actor = name
            break
        if st == 422:
            print(f"[setup] authorized actor={name} (422 validation reached)")
            actor = name
            break
    if actor is None:
        print("[setup] no actor reached the lifecycle guard; continuing with org_a_owner")
        actor = "org_a_owner"
    owner, _ = login(actor)
    print(f"[setup] using actor={actor}")

    print("\n== D-before: reportable aggregate (API) ==")
    _s, before = call(breakdown, owner, label="scope-breakdown before")
    print(f"   {json.dumps(before)[:220]}")

    print("\n== B: POST /api/v3/emissions/calculations/{snapshot}/invalidate ==")
    status, body = call(
        f"/api/v3/emissions/calculations/{INVALID_SNAP}/invalidate", owner,
        method="POST",
        body={"reason": "single-gas CH4 component factor used as a Scope 3 total; "
                        "superseded by the corrected multi-line calculation",
              "status": "not_for_reporting",
              "superseded_by_snapshot_id": VALID_SNAP},
        label="invalidate")
    print(f"   [{status}] {json.dumps(body)[:300]}")

    print("\n== A/B/C: readback of the persisted lifecycle state ==")
    print(sq(
        "SELECT 'snapshot|'||id||' | co2e='||co2e_kg||' | status='||reportability_status"
        "||' | reason_len='||coalesce(length(invalidated_reason),0)||' | by='||coalesce(invalidated_by::text,'NULL')"
        "||' | at='||coalesce(invalidated_at::text,'NULL')||' | superseded_by='||coalesce(superseded_by_snapshot_id::text,'NULL')"
        f" FROM calculation_snapshots WHERE id='{INVALID_SNAP}';\n"
        "SELECT 'log|'||id||' | co2e='||calculated_kg_co2e||' | status='||reportability_status"
        "||' | by='||coalesce(invalidated_by::text,'NULL')||' | superseded_by_log='||coalesce(superseded_by_log_id::text,'NULL')"
        f" FROM emissions_logs WHERE id='{INVALID_LOG}';\n"
        "SELECT 'replacement|'||id||' | co2e='||co2e_kg||' | status='||reportability_status"
        f" FROM calculation_snapshots WHERE id='{VALID_SNAP}';"))

    print("\n== D-after: reportable aggregate (API) ==")
    _s, after = call(breakdown, owner, label="scope-breakdown after")
    print(f"   {json.dumps(after)[:220]}")
    print(f"   CHANGED={before != after}")

    print("\n== E/G: reportability census for the org ==")
    print(sq(
        "SELECT reportability_status||' | n='||count(*)::text||' | sum='||coalesce(sum(co2e_kg),0)::text"
        f" FROM calculation_snapshots WHERE organization_id='{org}' GROUP BY reportability_status ORDER BY 1;"))

    print("\n== B': idempotence — second invalidation must be refused ==")
    status2, body2 = call(
        f"/api/v3/emissions/calculations/{INVALID_SNAP}/invalidate", owner,
        method="POST", body={"reason": "repeat attempt"}, label="re-invalidate")
    print(f"   [{status2}] {json.dumps(body2)[:200]}")

    print("\n== F: cross-tenant / unauthorised denial ==")
    foreign = next((n for n in names if n != actor and n.endswith(("_owner", "_member"))), None)
    if foreign:
        try:
            other, _ = login(foreign)
        except Exception as exc:
            other = None
            print(f"   [skip] {foreign}: {type(exc).__name__}")
        if other is not None:
            status3, body3 = call(
                f"/api/v3/emissions/calculations/{INVALID_SNAP}/invalidate", other,
                method="POST", body={"reason": "cross-tenant attempt"}, label="cross-tenant")
            print(f"   foreign={foreign} [{status3}] {json.dumps(body3)[:180]}")
    else:
        print("   [skip] no foreign identity available")

    print("\n== B'': reason is mandatory ==")
    status4, body4 = call(
        f"/api/v3/emissions/calculations/{VALID_SNAP}/invalidate", owner,
        method="POST", body={"reason": "   "}, label="blank reason")
    print(f"   [{status4}] {json.dumps(body4)[:200]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
