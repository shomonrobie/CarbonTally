"""Shared CLI plumbing: arguments, env loading, read-only enforcement.

Default mode is READ-ONLY (spec §33). Any future mutation test must declare
itself, use isolated QA-tagged records, clean up only its own records and
verify cleanup; the guard here refuses mutation stages unless explicitly
authorized.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Optional

DEFAULT_READ_ONLY = True

HARNESS_ROOT = Path(__file__).resolve().parent.parent


def load_env_file(env_path: Optional[Path] = None) -> Path:
    """Load ``qa_harness/.env`` (if present) into the process environment.

    The harness never creates this file; operators may provide one locally.
    """
    path = Path(env_path) if env_path else HARNESS_ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())
    return path


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--read-only", action="store_true", default=DEFAULT_READ_ONLY,
        help="Run in read-only mode (default: on). Mutation requires explicit opt-in.",
    )
    parser.add_argument("--role", default="", help="Restrict to a role (e.g. consultant).")
    parser.add_argument("--route", default="", help="Restrict to a route (e.g. /ops).")
    parser.add_argument("--workflow", default="", help="Restrict to a workflow key.")
    parser.add_argument("--no-ai", action="store_true", help="Skip the OpenRouter AI layer.")
    parser.add_argument("--no-visual", action="store_true", help="Skip browser/visual checks.")
    parser.add_argument("--no-security", action="store_true", help="Skip security boundary checks.")
    parser.add_argument("--env", default="", help="Environment name from environments.yaml.")


def require_read_only(args: argparse.Namespace, stage: str) -> None:
    """Refuse to run a mutation stage unless the operator explicitly opts in
    with ``--read-only=false`` semantics. The default is always read-only."""
    if getattr(args, "read_only", True):
        return
    raise SystemExit(
        "BLOCKED — SAFE MUTATION NOT AVAILABLE: mutation stages are disabled in "
        f"this build for stage {stage!r}. Remove --read-only=false and add an "
        "explicit mutation manifest before running mutation tests."
    )
