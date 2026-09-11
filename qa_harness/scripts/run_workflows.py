#!/usr/bin/env python3
"""Workflow QA runner — spec §13–§18, §34.

Executes the executable workflows (customer, consultant, client, PE,
operations, admin, messaging) against live identities when the stack is
reachable; otherwise reports SKIPPED. Persisted-state verification is
performed by the DB layer; this runner drives API steps and records expected
vs actual statuses.
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional

from qa_harness.core.config import load_config
from qa_harness.core.status import ToolUnavailable
from qa_harness.identities.loader import resolve_manifest_path
from qa_harness.identities.resolver import IdentityResolver
from qa_harness.scripts.common import HARNESS_ROOT, add_common_args, load_env_file
from qa_harness.scripts.preflight import git_sha

EXIT_OK = 0
EXIT_SKIPPED = 3
EXIT_FAIL = 1


def _build_discovery(config: Any, env: Any) -> Any:
    """Optional read-only ResourceDiscovery for workflow probes.

    Returns ``None`` when the DB is unreachable, discovery is disabled in
    qa_config.yaml, or the driver is missing — the workflow executor then
    SKIPs resource-bound steps with an explicit reason. Never raises.
    """
    try:
        main = config.raw.get("qa_config.yaml", {})
        if not main.get("database", {}).get("resource_discovery", True):
            return None
        from qa_harness.db.discovery import ResourceDiscovery
        from qa_harness.scripts.run_db import _resolve_connection

        dsn, _source = _resolve_connection(env, config)
        return ResourceDiscovery(dsn)
    except Exception:
        return None


def run_workflows(args: argparse.Namespace, ctx: Any = None) -> int:
    config = load_config(HARNESS_ROOT / "config")
    env_name = args.env or config.default_environment
    env = config.environment(env_name)
    print(f"Workflow QA — environment: {env_name}")
    owned_ctx = ctx is None
    if ctx is None:
        from qa_harness.core.run_context import RunContext
        ctx = RunContext(env=env, env_name=env_name, git_sha=git_sha(),
                         read_only=args.read_only)

    from qa_harness.identities.loader import IdentityLoader

    manifest = config.identities.get("manifest")
    manifest_path = resolve_manifest_path(manifest) if manifest else None
    loader = IdentityLoader(manifest_path=manifest_path if manifest_path.exists() else None)
    resolver = IdentityResolver(loader=loader)
    count = len(resolver.all())
    if count == 0:
        print("SKIPPED — NO IDENTITIES (identity manifest not configured)")
        if owned_ctx:
            ctx.emit_skipped("WF", "Workflow QA unavailable",
                             reason="no identity population", source="run_workflows.py")
            ctx.finish()
        return EXIT_SKIPPED
    print(f"  identity population loaded: {count}")

    try:
        password = ctx.demo_password()
    except ToolUnavailable as exc:
        print(f"SKIPPED — {exc}")
        if owned_ctx:
            ctx.emit_skipped("WF", "Workflow QA unavailable",
                             reason=str(exc), source="run_workflows.py")
            ctx.finish()
        return EXIT_SKIPPED

    from qa_harness.api.session import ApiSessionPool
    from qa_harness.workflows import ALL_WORKFLOWS
    from qa_harness.workflows.executor import WorkflowExecutor

    selected = [args.workflow] if args.workflow else [w.key for w in ALL_WORKFLOWS]
    workflows = [w for w in ALL_WORKFLOWS if w.key in selected]

    pool = ApiSessionPool(env=env, password=password)
    discovery = _build_discovery(config, env)
    try:
        executor = WorkflowExecutor(ctx, resolver, pool, discovery=discovery)
        executor.run_all(workflows, source="run_workflows.py", role_filter=args.role)
    finally:
        if discovery is not None:
            discovery.close()

    summary = executor.summary()
    ctx.record_checks(sum(summary.values()) - summary.get("SKIPPED", 0))
    print(f"  steps executed: {sum(summary.values())} "
          f"[PASS={summary.get('PASS', 0)} FAIL={summary.get('FAIL', 0)} "
          f"WARNING={summary.get('WARNING', 0)} SKIPPED={summary.get('SKIPPED', 0)}]")
    for outcome in executor.outcomes:
        if outcome.outcome in ("FAIL", "WARNING"):
            print(f"    {outcome.workflow}.{outcome.action:22s} {outcome.outcome:8s} "
                  f"expected={outcome.expected} actual={outcome.actual_status} — {outcome.detail[:80]}")

    pool.close()
    if owned_ctx:
        ctx.finish()
    if summary.get("FAIL", 0):
        print("RESULT: FAIL")
        return EXIT_FAIL
    print("RESULT: PASS (read-only workflow steps executed; mutation steps SKIPPED)")
    return EXIT_OK


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="CarbonTally QA — workflows")
    add_common_args(parser)
    args = parser.parse_args(argv)
    load_env_file()
    return run_workflows(args)


if __name__ == "__main__":
    raise SystemExit(main())
