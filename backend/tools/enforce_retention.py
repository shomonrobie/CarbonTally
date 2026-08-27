"""N3 — retention enforcement CLI (deployment scheduler entry point).

Usage:
    python -m tools.enforce_retention            # dry run (report only)
    python -m tools.enforce_retention --apply    # apply configured policy

Audit and evidence tables are never purged (security invariant). No retention
duration is invented — only configured values are enforced.
"""
from __future__ import annotations

import asyncio
import sys

from api.dependencies import get_repositories
from services.retention import enforce_retention


async def _main(apply: bool) -> int:
    repos = await get_repositories()
    report = await enforce_retention(repos, dry_run=not apply)
    print(f"dry_run={report['dry_run']} policy={report['policy']}")
    for domain, detail in report["domains"].items():
        print(f"  {domain}: {detail}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main(apply="--apply" in sys.argv)))
