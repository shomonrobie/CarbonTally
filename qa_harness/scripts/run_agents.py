#!/usr/bin/env python3
"""Agent swarm runner — spec §27, §34.

Runs the optional OpenRouter analysis layer over deduplicated findings. With
``--no-ai`` (or without the API key) it computes only the deterministic
verdict. Never runs tests; never touches the application.
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional

from qa_harness.agents.base import openrouter_available
from qa_harness.agents.swarm import AgentSwarm
from qa_harness.findings import FindingStore
from qa_harness.reports.generator import (
    ReportBundle,
    ReportGenerator,
    acceptance_verdict,
)
from qa_harness.scripts.common import HARNESS_ROOT, add_common_args, load_env_file

EXIT_OK = 0
EXIT_SKIPPED = 3
EXIT_FAIL = 1


def run_agents(args: argparse.Namespace) -> int:
    store = FindingStore()
    findings = store.load_jsonl("deduplicated", "deduplicated.jsonl")
    print(f"Agent analysis — deduplicated findings loaded: {len(findings)}")

    if args.no_ai or not openrouter_available():
        verdict = acceptance_verdict(findings)
        print("SKIPPED — AI SWARM (deterministic verdict only)" if not openrouter_available()
              else "AI swarm disabled by --no-ai")
        print(f"Deterministic verdict: {verdict}")
        return EXIT_SKIPPED if not openrouter_available() else EXIT_OK

    swarm = AgentSwarm()
    result = swarm.run(findings)
    print(f"Swarm status: {result.status.value}")
    if result.verdict:
        print(f"Verdict: {result.verdict.recommended}")
        print(f"Reasoning: {result.verdict.reasoning[:500]}")
    return EXIT_OK


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="CarbonTally QA — agent swarm (optional AI)")
    add_common_args(parser)
    args = parser.parse_args(argv)
    load_env_file()
    return run_agents(args)


if __name__ == "__main__":
    raise SystemExit(main())
