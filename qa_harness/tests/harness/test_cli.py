"""Harness self-tests: CLI plumbing, read-only guard, env loading (spec §34, §35)."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_harness.scripts.common import add_common_args, load_env_file, require_read_only
from qa_harness.scripts.preflight import git_sha, main as preflight_main


def test_common_args_read_only_default() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    add_common_args(parser)
    args = parser.parse_args([])
    assert args.read_only is True


def test_require_read_only_passes_in_default_mode() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    add_common_args(parser)
    args = parser.parse_args(["--read-only"])
    require_read_only(args, "test")  # no raise


def test_require_read_only_blocks_disabled_guard() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    add_common_args(parser)
    parser.set_defaults(read_only=False)
    args = parser.parse_args([])
    with pytest.raises(SystemExit) as exc:
        require_read_only(args, "mutation-stage")
    assert "BLOCKED — SAFE MUTATION NOT AVAILABLE" in str(exc.value)


def test_load_env_file_missing_is_noop(tmp_path: Path) -> None:
    path = load_env_file(tmp_path / "does-not-exist.env")
    assert path == tmp_path / "does-not-exist.env"


def test_load_env_file_sets_only_missing(monkeypatch, tmp_path: Path) -> None:
    env_path = tmp_path / "qa.env"
    env_path.write_text(
        "FOO=bar\n# comment\nEMPTY=\nBAZ=qux\n", encoding="utf-8"
    )
    monkeypatch.setenv("FOO", "already-set")
    load_env_file(env_path)
    assert __import__("os").environ["FOO"] == "already-set"
    assert __import__("os").environ["BAZ"] == "qux"


def test_git_sha_never_raises() -> None:
    sha = git_sha()
    assert sha  # we run inside a git checkout
    assert len(sha) == 40


def test_preflight_exits_zero() -> None:
    assert preflight_main([]) == 0
