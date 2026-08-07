"""Integration tests for infra.config against the test environment.

Verifies the configuration snapshot agrees with the repository-layer connection
settings that ``infra.supabase`` produces for the test database.
"""
from __future__ import annotations

from collections.abc import Iterator

import pytest

from infra.config import get_config, reset_config
from infra.supabase import get_database_url, get_supabase_url

_LOG_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}


@pytest.fixture(autouse=True)
def _fresh_config() -> Iterator[None]:
    reset_config()
    yield
    reset_config()


def test_config_agrees_with_infra_supabase() -> None:
    config = get_config()
    # The config snapshot must read the exact same values the repository-layer
    # connection helpers resolve (the test host is environment-dependent).
    assert config.database_url == get_database_url()
    assert config.database_url
    assert config.supabase_url == get_supabase_url()


def test_config_is_singleton() -> None:
    assert get_config() is get_config()


def test_config_defaults_are_valid() -> None:
    config = get_config()
    assert config.event_bus_max_handlers >= 1
    assert config.search_index_default_limit >= 1
    assert config.audit_batch_size >= 1
    assert config.cache_default_ttl_seconds >= 0
    assert config.log_level in _LOG_LEVELS
    assert config.log_level_int > 0
    assert config.env
