#!/usr/bin/env python3
"""Browser QA runner — spec §23–§26, §34.

Route sweeps (authenticated workspaces prioritized), responsive viewports,
table audits and axe accessibility. Without Playwright/Chromium this prints
``SKIPPED — TOOL UNAVAILABLE`` and exits distinct.
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional

from qa_harness.browser.playwright.controller import BrowserController, browser_available
from qa_harness.core.config import load_config
from qa_harness.core.status import ToolUnavailable
from qa_harness.scripts.common import HARNESS_ROOT, add_common_args, load_env_file
from qa_harness.scripts.preflight import git_sha

EXIT_OK = 0
EXIT_SKIPPED = 3
EXIT_FAIL = 1


def run_browser(args: argparse.Namespace, ctx: Any = None) -> int:
    config = load_config(HARNESS_ROOT / "config")
    env_name = args.env or config.default_environment
    env = config.environment(env_name)
    print(f"Browser QA — environment: {env_name} ({env.frontend_base_url})")
    owned_ctx = ctx is None
    if ctx is None:
        from qa_harness.core.run_context import RunContext
        ctx = RunContext(env=env, env_name=env_name, git_sha=git_sha(),
                         read_only=args.read_only)

    if not browser_available():
        print("SKIPPED — TOOL UNAVAILABLE (playwright package not installed)")
        if owned_ctx:
            ctx.emit_skipped("UI", "Browser QA unavailable",
                             reason="playwright package not installed", source="run_browser.py")
            ctx.finish()
        return EXIT_SKIPPED

    try:
        password = ctx.demo_password()
    except ToolUnavailable as exc:
        print(f"SKIPPED — {exc}")
        if owned_ctx:
            ctx.emit_skipped("UI", "Browser QA unavailable",
                             reason=str(exc), source="run_browser.py")
            ctx.finish()
        return EXIT_SKIPPED

    try:
        controller = BrowserController(headless=True, viewport={"width": 1440, "height": 900})
        controller.start()
    except ToolUnavailable as exc:
        print(f"SKIPPED — TOOL UNAVAILABLE ({exc.tool}: {exc.reason})")
        if owned_ctx:
            ctx.emit_skipped("UI", "Browser QA unavailable",
                             reason=str(exc), source="run_browser.py")
            ctx.finish()
        return EXIT_SKIPPED

    from qa_harness.browser.sweep import BrowserSweepEngine
    from qa_harness.identities.loader import IdentityLoader, resolve_manifest_path
    from qa_harness.identities.resolver import IdentityResolver

    manifest = config.identities.get("manifest")
    manifest_path = resolve_manifest_path(manifest) if manifest else None
    loader = IdentityLoader(manifest_path=manifest_path if manifest_path.exists() else None)
    resolver = IdentityResolver(loader=loader)

    engine = BrowserSweepEngine(
        ctx, env, resolver, controller=controller, password=password,
        role_filter=args.role, no_visual=args.no_visual, headless=True,
    )
    try:
        engine.run(source="run_browser.py")
    finally:
        controller.stop()

    summary = engine.summary()
    ctx.record_checks(summary["visits"])
    print(f"  role sweeps: {summary['roles']} (logged in: {summary['logged_in']}); "
          f"route visits: {summary['visits']}; responsive overflows: {summary['responsive_overflows']}; "
          f"a11y violations: {summary['a11y_violations']}; findings: {summary['findings']}")
    for result in engine.results:
        print(f"    {result.role:20s} logged_in={result.logged_in} "
              f"landing={result.landing_path or '-'} "
              f"auth={result.auth_classification or '-'} "
              f"visits={len(result.visits)} "
              f"overflow={len(result.responsive_overflows)} a11y={result.a11y_violations}")
        if result.login_error:
            print(f"      login error: {result.login_error[:160]}")

    if owned_ctx:
        ctx.finish()
    if summary["findings"]:
        print("RESULT: FAIL (browser sweep produced findings)")
        return EXIT_FAIL
    print("RESULT: PASS (browser sweeps executed)")
    return EXIT_OK


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="CarbonTally QA — browser")
    add_common_args(parser)
    args = parser.parse_args(argv)
    load_env_file()
    return run_browser(args)


if __name__ == "__main__":
    raise SystemExit(main())
