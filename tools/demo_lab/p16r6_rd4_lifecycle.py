#!/usr/bin/env python3
"""P16-R6 / RD-4 (R9) — live accounting-result reportability lifecycle (A–J).

Actor: a CarbonTally internal staff reviewer (``platform_admin``, ``can_review``),
the same model the reviewer surfaces use.
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
REASON = ("single-gas CH4 component factor used as a Scope 3 total; superseded by "
          "the corrected multi-line calculation")


def sq(sql: str) -> str:
    return (lab.psql(sql).stdout or "").strip()


def census(org: str, label: str) -> None:
    out = sq(
        "SELECT reportability_status||' n='||count(*)::text||' sum='||coalesce(sum(co2e_kg),0)::text"
        f" FROM calculation_snapshots WHERE organization_id='{org}' GROUP BY 1 ORDER BY 1;")
    print(f"   [{label}] {out.replace(chr(10), ' | ')}")


def main() -> int:
    org = sq(f"SELECT organization_id FROM calculation_snapshots WHERE id='{INVALID_SNAP}';")
    start = sq(f"SELECT min(start_date) FROM emissions_logs WHERE organization_id='{org}';")
    print(f"[setup] org={org} period_start={start}")

    reviewer, _ = login("platform_admin")
    breakdown = (f"/api/v3/emissions/scope-breakdown?organization_id={org}"
                 f"&start_date={start}&end_date=2026-12-31")

    print("\n== A: historical invalid result exists ==")
    print(sq("SELECT 'snapshot '||id||' co2e='||co2e_kg||' status='||reportability_status"
             f" FROM calculation_snapshots WHERE id='{INVALID_SNAP}';\n"
             "SELECT 'log '||id||' co2e='||calculated_kg_co2e||' status='||reportability_status"
             f" FROM emissions_logs WHERE id='{INVALID_LOG}';"))

    print("\n== F-before: reportable aggregate (API) ==")
    _s, before = call(breakdown, reviewer, label="before")
    before_total = (before or {}).get("total_co2e_kg")
    print(f"   before.total={before_total} by_scope={json.dumps((before or {}).get('by_scope'))}")
    census(org, "census-before")

    print("\n== B/C/D: authorized reviewer invalidates with supersession ==")
    st, body = call(f"/api/v3/emissions/calculations/{INVALID_SNAP}/invalidate", reviewer,
                    method="POST",
                    body={"reason": REASON, "status": "not_for_reporting",
                          "superseded_by_snapshot_id": VALID_SNAP},
                    label="invalidate")
    print(f"   [{st}] {json.dumps(body)[:260]}")

    print("\n== I-denied: unauthorised actor (org owner, no staff profile) ==")
    try:
        owner, _ = login("org_a_owner")
        st2, b2 = call(f"/api/v3/emissions/calculations/{VALID_SNAP}/invalidate", owner,
                       method="POST", body={"reason": "unauthorised"}, label="unauthorised")
        print(f"   [{st2}] {json.dumps(b2)[:180]}")
    except Exception as exc:
        print(f"   [skip] {type(exc).__name__}")

    print("\n== J: repeat invalidation is safely rejected ==")
    st3, b3 = call(f"/api/v3/emissions/calculations/{INVALID_SNAP}/invalidate", reviewer,
                   method="POST", body={"reason": "repeat"}, label="repeat")
    print(f"   [{st3}] {json.dumps(b3)[:180]}")

    print("\n== b'': reason is mandatory ==")
    st4, b4 = call(f"/api/v3/emissions/calculations/{VALID_SNAP}/invalidate", reviewer,
                   method="POST", body={"reason": "   "}, label="blank reason")
    print(f"   [{st4}] {json.dumps(b4)[:180]}")

    print("\n== E/C/D: persisted lifecycle state ==")
    print(sq(
        "SELECT 'snapshot '||id||' co2e='||co2e_kg||' status='||reportability_status"
        "||' reason_len='||coalesce(length(invalidated_reason),0)||' by='||coalesce(invalidated_by::text,'NULL')"
        "||' at='||coalesce(invalidated_at::text,'NULL')||' superseded_by='||coalesce(superseded_by_snapshot_id::text,'NULL')"
        f" FROM calculation_snapshots WHERE id='{INVALID_SNAP}';\n"
        "SELECT 'log '||id||' co2e='||calculated_kg_co2e||' status='||reportability_status"
        "||' by='||coalesce(invalidated_by::text,'NULL')||' superseded_by_log='||coalesce(superseded_by_log_id::text,'NULL')"
        f" FROM emissions_logs WHERE id='{INVALID_LOG}';\n"
        "SELECT 'replacement '||id||' co2e='||co2e_kg||' status='||reportability_status"
        f" FROM calculation_snapshots WHERE id='{VALID_SNAP}';"))

    print("\n== F-after: reportable aggregate (API) ==")
    _s, after = call(breakdown, reviewer, label="after")
    after_total = (after or {}).get("total_co2e_kg")
    print(f"   after.total={after_total} by_scope={json.dumps((after or {}).get('by_scope'))}")
    census(org, "census-after")
    if before_total and after_total:
        print(f"   CHANGED={before_total != after_total} "
              f"delta={float(before_total) - float(after_total):.6f}")

    print("\n== G/H: exclusion + inspectability ==")
    print(sq("SELECT count(*)::text||' reportable emission rows' FROM emissions_logs"
             f" WHERE organization_id='{org}' AND reportability_status='reportable';"))
    print(sq("SELECT 'invalid log still inspectable '||id||' co2e='||calculated_kg_co2e"
             f" FROM emissions_logs WHERE id='{INVALID_LOG}';"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
