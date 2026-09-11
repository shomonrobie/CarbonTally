"""Harness self-tests: configuration loading (spec §35)."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_harness.config.loader import CONFIG_FILES, ConfigLoadError, load_yaml
from qa_harness.core.config import QaConfig, load_config

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_load_real_config() -> None:
    config = load_config()
    assert isinstance(config, QaConfig)
    assert config.harness_name == "CarbonTally QA Harness"
    assert config.read_only is True
    assert "local" in config.environments
    assert len(config.roles) >= 13
    assert len(config.severities) == 4


def test_config_files_all_present() -> None:
    config_dir = Path(__file__).resolve().parent.parent.parent / "config"
    for name in CONFIG_FILES:
        assert (config_dir / name).exists(), f"missing {name}"


def test_missing_config_file_raises() -> None:
    with pytest.raises(ConfigLoadError):
        load_yaml(Path("/nonexistent/qa_config.yaml"))


def test_config_dir_missing_raises() -> None:
    with pytest.raises(ConfigLoadError):
        load_config(Path("/nonexistent"))


def test_environment_resolution() -> None:
    config = load_config()
    env = config.environment("local")
    assert env.api_base_url  # alias property
    assert env.frontend_base_url
    assert env.api_prefix == "/api/v3"
    with pytest.raises(KeyError):
        config.environment("does-not-exist")


def test_viewports_documented() -> None:
    config = load_config()
    assert len(config.viewports) == 8
    widths = {v["width"] for v in config.viewports}
    assert 1920 in widths and 375 in widths and 768 in widths


def test_exclusions_parse() -> None:
    config = load_config()
    kinds = {e.kind for e in config.exclusions}
    assert "console_error" in kinds
