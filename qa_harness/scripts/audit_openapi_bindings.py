#!/usr/bin/env python3
"""Static OpenAPI ↔ probe-binding contract audit (V1.2 calibration).

Reads the live OpenAPI document (read-only GET, no probes are sent) and
cross-checks every ACTION_BINDING, SMOKE probe and probe spec against it:

* paths that do not exist in the spec → HARNESS_CONTRACT_DEFECT candidates
* required query params the harness does not supply → HARNESS_CONTRACT_DEFECT
  candidates (these were the source of false-positive 422s in the first
  read-only sweep)

This is a MAINTENANCE tool. It is NOT part of the QA run and never counts as
an application test. Run it before a QA sweep after the app's API changes:

    python qa_harness/scripts/audit_openapi_bindings.py [openapi_url]

Exit code 0 = every binding matches the contract; 1 = defects found.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from typing import Any, Dict, List, Tuple

HARNESS_ROOT = __import__("qa_harness.scripts.common", fromlist=["HARNESS_ROOT"]).HARNESS_ROOT


def _norm_path(p: str) -> str:
    p = re.sub(r"^/api/v[23]", "", p)
    p = re.sub(r"\{[^}]+\}", "{p}", p)
    return p.split("?")[0]


def _load_spec(url: str) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.load(resp)


def _required_query_params(spec: Dict[str, Any], path: str, method: str) -> List[str]:
    op = spec.get("paths", {}).get(path, {}).get(method)
    if op is None:
        return []
    return [p.get("name", "") for p in op.get("parameters", [])
            if p.get("required") and p.get("in") == "query"]


def audit(url: str = "http://localhost:8050/openapi.json") -> Tuple[List[str], List[str]]:
    """Returns (path_defects, param_defects) as human-readable strings."""
    spec = _load_spec(url)
    spec_norm = {_norm_path(p): p for p in spec.get("paths", {})}

    from qa_harness.api.probe import build_probe_specs, build_smoke_probes
    from qa_harness.workflows.executor import ACTION_BINDINGS

    path_defects: List[str] = []
    param_defects: List[str] = []
    seen: set = set()

    def check(label: str, method: str, endpoint: str) -> None:
        if endpoint in seen:
            return
        seen.add(endpoint)
        raw_path = endpoint.split("?")[0]
        n = _norm_path(raw_path)
        spec_path = spec_norm.get(n)
        if spec_path is None:
            path_defects.append(
                f"{label}: {method.upper()} {endpoint} — path not in OpenAPI"
            )
            return
        supplied = set(re.findall(r"([A-Za-z_]+)=", endpoint.split("?", 1)[1])) \
            if "?" in endpoint else set()
        for req in _required_query_params(spec, spec_path, method.lower()):
            if req not in supplied:
                param_defects.append(
                    f"{label}: {method.upper()} {endpoint} — missing required "
                    f"query param '{req}' (per OpenAPI {spec_path})"
                )

    for action, (method, tpl) in sorted(ACTION_BINDINGS.items()):
        check(f"binding.{action}", method, tpl)
    for probe in build_smoke_probes():
        check(f"smoke.{probe.id}", probe.method, probe.endpoint)
    for probe in build_probe_specs():
        check(f"probe.{probe.id}", probe.method, probe.endpoint)
    return path_defects, param_defects


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8050/openapi.json"
    try:
        path_defects, param_defects = audit(url)
    except Exception as exc:
        print(f"SKIPPED — could not read OpenAPI from {url}: {exc}")
        return 3
    for line in path_defects:
        print(f"PATH  {line}")
    for line in param_defects:
        print(f"PARAM {line}")
    total = len(path_defects) + len(param_defects)
    print(f"\nHARNESS_CONTRACT_DEFECT candidates: {total}")
    print("Classification: HARNESS_CONTRACT_DEFECT (not an app defect).")
    print("RESULT: FAIL" if total else "RESULT: PASS (all bindings match the contract)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
