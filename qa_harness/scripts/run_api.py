#!/usr/bin/env python3
"""API QA runner — spec §10, §11, §34.

Discovers the OpenAPI document, checks the contract, probes the documented
authorization matrix (expected-allow / expected-deny) and security
boundaries. 4xx responses are contextualized, never blanket-flagged.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, List, Optional

from qa_harness.api.authorization import AuthorizationMatrix
from qa_harness.api.inventory import EndpointInventory
from qa_harness.api.security import ApiSecurityAudit
from qa_harness.core.config import TargetEnv, load_config
from qa_harness.core.status import ToolUnavailable
from qa_harness.scripts.common import HARNESS_ROOT, add_common_args, load_env_file
from qa_harness.scripts.preflight import git_sha

try:
    import requests  # type: ignore
    _REQUESTS = True
except ImportError:  # pragma: no cover
    requests = None  # type: ignore
    _REQUESTS = False

EXIT_OK = 0
EXIT_SKIPPED = 3
EXIT_FAIL = 1


def _fetch_openapi(env: TargetEnv) -> Dict[str, Any]:
    if not _REQUESTS:
        raise ToolUnavailable("requests", "pip install requests")
    url = env.api_base_url.rstrip("/") + "/openapi.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def run_api(args: argparse.Namespace, ctx: Any = None) -> int:
    config = load_config(HARNESS_ROOT / "config")
    env_name = args.env or config.default_environment
    env = config.environment(env_name)
    print(f"API QA — environment: {env_name} ({env.api_base_url})")
    owned_ctx = ctx is None
    if ctx is None:
        from qa_harness.core.run_context import RunContext
        ctx = RunContext(env=env, env_name=env_name, git_sha=git_sha(),
                         read_only=args.read_only)

    try:
        openapi = _fetch_openapi(env)
    except ToolUnavailable as exc:
        print(f"SKIPPED — TOOL UNAVAILABLE ({exc.tool}: {exc.reason})")
        if owned_ctx:
            ctx.emit_skipped("API", "API QA unavailable", reason=str(exc), source="run_api.py")
            ctx.finish()
        return EXIT_SKIPPED
    except Exception as exc:
        print(f"SKIPPED — API UNREACHABLE ({exc})")
        if owned_ctx:
            ctx.emit_skipped("API", "API QA unavailable", reason=str(exc), source="run_api.py")
            ctx.finish()
        return EXIT_SKIPPED

    inventory = EndpointInventory(openapi, api_prefix=env.api_prefix)
    endpoints = inventory.build()
    v3 = inventory.v3_endpoints()
    print(f"  endpoints discovered: {len(endpoints)} (v3: {len(v3)})")
    unexpected = inventory.unexpected()
    print(f"  flagged server-error endpoints: {len(unexpected)}")

    matrix = AuthorizationMatrix()
    security = ApiSecurityAudit()
    print(f"  authorization expectations: {len(matrix.expectations)} "
          f"(PO DECISION REQUIRED: {len(matrix.po_decisions())})")
    print(f"  security boundaries: {len(security.boundaries)}")

    # Authenticated probes require the demo password + identity population.
    try:
        password = ctx.demo_password()
    except ToolUnavailable as exc:
        print(f"SKIPPED — {exc}")
        if owned_ctx:
            ctx.emit_skipped("API", "API probes unavailable",
                             reason=str(exc), source="run_api.py")
            ctx.finish()
        return EXIT_SKIPPED

    probe_cfg = config.raw.get("qa_config.yaml", {}).get("api_probe", {})
    allow_upload = bool(probe_cfg.get("allow_upload_probes", False))
    allow_empty = bool(probe_cfg.get("allow_empty_body_mutation_probes", True))

    from qa_harness.api.probe import (
        ApiProbeEngine,
        build_probe_specs,
        build_smoke_probes,
    )
    from qa_harness.api.session import ApiSessionPool
    from qa_harness.identities.loader import IdentityLoader, resolve_manifest_path
    from qa_harness.identities.resolver import IdentityResolver

    manifest = config.identities.get("manifest")
    manifest_path = resolve_manifest_path(manifest) if manifest else None
    loader = IdentityLoader(manifest_path=manifest_path if manifest_path.exists() else None)
    resolver = IdentityResolver(loader=loader)
    if not resolver.all():
        print("SKIPPED — NO IDENTITIES (identity manifest not configured)")
        if owned_ctx:
            ctx.emit_skipped("API", "API probes unavailable",
                             reason="no identity population", source="run_api.py")
            ctx.finish()
        return EXIT_SKIPPED

    pool = ApiSessionPool(env=env, password=password)
    engine = ApiProbeEngine(
        ctx, resolver, pool,
        allow_empty_body_mutation=allow_empty,
        allow_upload_probes=allow_upload and not args.read_only,
        skip_security=args.no_security,
    )
    specs = build_probe_specs()
    if args.no_security:
        specs = [s for s in specs if s.kind != "security"]
    engine.run(specs, source="run_api.py")
    engine.run(build_smoke_probes(), source="run_api.py")

    summary = engine.summary()
    ctx.record_checks(
        sum(summary.values())
        - summary.get("SKIPPED", 0)
        - summary.get("PO DECISION REQUIRED", 0)
    )
    print(f"  probes executed: {sum(summary.values())} "
          f"[PASS={summary.get('PASS', 0)} FAIL={summary.get('FAIL', 0)} "
          f"WARNING={summary.get('WARNING', 0)} SKIPPED={summary.get('SKIPPED', 0)} "
          f"PO_DECISION_REQUIRED={summary.get('PO DECISION REQUIRED', 0)}]")
    for result in engine.results:
        if result.outcome in ("FAIL", "WARNING", "PO DECISION REQUIRED"):
            print(f"    {result.spec.id:12s} {result.outcome:22s} "
                  f"{result.spec.method} {result.spec.endpoint} "
                  f"→ {result.actual_status or result.error[:60]}")

    pool.close()
    if owned_ctx:
        ctx.finish()
    if summary.get("FAIL", 0):
        print("RESULT: FAIL")
        return EXIT_FAIL
    print("RESULT: PASS (authenticated API probes executed)")
    return EXIT_OK


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="CarbonTally QA — API")
    add_common_args(parser)
    args = parser.parse_args(argv)
    load_env_file()
    return run_api(args)


if __name__ == "__main__":
    raise SystemExit(main())
