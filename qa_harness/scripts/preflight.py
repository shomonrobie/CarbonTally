#!/usr/bin/env python3
"""Preflight: validate the harness environment (spec §34).

Checks Python version, required imports, optional tool availability, secret
env presence (never values), the QA workspace layout, and records the Git SHA
of the CarbonTally checkout. Does NOT contact the application.
"""

from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from qa_harness.scripts.common import HARNESS_ROOT, add_common_args, load_env_file

REQUIRED_MODULES = [
    "yaml",
    "requests",
]

OPTIONAL_MODULES: Dict[str, str] = {
    "playwright": "pip install playwright && playwright install chromium",
    "schemathesis": "pip install schemathesis",
    "axe": "npm/axe-core injection (browser layer)",
    "pgtap": "PostgreSQL extension",
    "zap": "OWASP ZAP daemon",
}

SECRET_ENV_VARS = [
    "CARBON_TALLY_DEMO_PASSWORD",
    "OPENROUTER_AGEN_SWARM_V1_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
    "SUPABASE_JWT_SECRET",
]

# Reported presence only — values are never printed.
SECRET_REDACTION = ["SUPABASE_SERVICE_KEY", "SUPABASE_JWT_SECRET", "GITHUB_TOKEN"]


def git_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=HARNESS_ROOT.parent,
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def check_imports(module_names: List[str]) -> List[Tuple[str, bool, str]]:
    results = []
    for name in module_names:
        try:
            importlib.import_module(name)
            results.append((name, True, ""))
        except ImportError:
            results.append((name, False, f"pip install {name}"))
    return results


def optional_tool_status() -> Dict[str, bool]:
    status: Dict[str, bool] = {}
    try:
        importlib.import_module("playwright")
        status["playwright"] = True
    except ImportError:
        status["playwright"] = False
    try:
        importlib.import_module("schemathesis")
        status["schemathesis"] = True
    except ImportError:
        status["schemathesis"] = False
    return status


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="CarbonTally QA Harness — preflight")
    add_common_args(parser)
    args = parser.parse_args(argv)
    load_env_file()

    print("CarbonTally QA Harness — preflight")
    print("=" * 50)
    print(f"Python: {sys.version.split()[0]}")
    print(f"Git SHA (CarbonTally checkout): {git_sha()}")

    print("\nRequired modules:")
    ok = True
    for name, present, hint in check_imports(REQUIRED_MODULES):
        print(f"  {name}: {'OK' if present else f'MISSING ({hint})'}")
        ok = ok and present

    print("\nOptional tools (SKIPPED — TOOL UNAVAILABLE is reported per run):")
    for name, present in optional_tool_status().items():
        print(f"  {name}: {'available' if present else 'UNAVAILABLE'}")

    print("\nSecret env vars (presence only — values are never printed):")
    for var in SECRET_ENV_VARS:
        present = bool(os.environ.get(var))
        print(f"  {var}: {'set' if present else 'NOT SET (ok for build-only runs)'}")

    print("\nDemo credentials (values are never printed):")
    try:
        from qa_harness.core.credentials import demo_credentials_summary
        summary = demo_credentials_summary()
        print(f"  source: {summary['source']}")
        print(f"  password: {summary['password']}")
    except Exception as exc:  # never crash preflight on credential issues
        print(f"  error: {type(exc).__name__}: {exc}")
        ok = False

    print("\nIdentity population (generated model — no secrets):")
    try:
        from qa_harness.core.config import load_config
        from qa_harness.identities.loader import (
            DEMO_DOMAIN,
            IdentityLoader,
            generate_full_population,
            resolve_manifest_path,
        )
        from collections import Counter

        config = load_config()
        generated = generate_full_population()
        counts = Counter(i.persona for i in generated)
        demo = [i for i in generated if i.is_demo]
        non_demo = [i for i in generated if not i.is_demo]
        manifest_cfg = config.identities.get("manifest")
        manifest_path = resolve_manifest_path(manifest_cfg) if manifest_cfg else None
        loader = IdentityLoader(manifest_path=manifest_path if manifest_path and manifest_path.exists() else None)
        merged = loader.load()
        print(f"  generated model: {len(generated)} identities total "
              f"({len(demo)} demo @{DEMO_DOMAIN}, {len(non_demo)} non-demo audit/fixture)")
        print(f"  demo total: {len(demo)} "
              f"(documented seeder total: {config.identities.get('total_demo_identities', 'n/a')})")
        print("  breakdown: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        print(f"  representative (manifest {manifest_path.name if manifest_path else 'none'}): "
              f"{sum(1 for i in merged.values() if i.representative)}")
    except Exception as exc:  # pragma: no cover
        print(f"  SKIPPED — identity model unavailable ({exc})")

    print("\nWorkspace layout:")
    expected_dirs = [
        "config", "identities", "db", "api", "browser", "visual", "workflows",
        "rules", "agents", "evidence", "findings", "reports", "scripts", "tests",
    ]
    for name in expected_dirs:
        present = (HARNESS_ROOT / name).is_dir()
        print(f"  {name}/: {'OK' if present else 'MISSING'}")
        ok = ok and present

    print("\nRead-only guard:", "ENFORCED (default)" if args.read_only else "DISABLED")
    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
