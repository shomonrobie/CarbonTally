"""Unit tests for infra.config."""
from __future__ import annotations

from collections.abc import Iterator

import pytest

from infra.config import (
    AppConfig,
    ConfigError,
    get_config,
    load_config,
    parse_bool,
    parse_int,
    parse_log_level,
    reset_config,
)

#: Every config-relevant env var, neutralised (blank = unset) before each test.
_CONFIG_ENV_KEYS = [
    "APP_ENV",
    "ENV",
    "SUPABASE_URL",
    "NEXT_PUBLIC_SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "DATABASE_URL",
    "SUPABASE_DB_URL",
    "LOG_LEVEL",
    "EVENT_BUS_MAX_HANDLERS",
    "SEARCH_INDEX_DEFAULT_LIMIT",
    "AUDIT_DEFAULT_ACTOR",
    "AUDIT_BATCH_SIZE",
    "CACHE_DEFAULT_TTL_SECONDS",
]


@pytest.fixture(autouse=True)
def _neutral_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Blank every config env var and drop any cached snapshot."""
    reset_config()
    for key in _CONFIG_ENV_KEYS:
        monkeypatch.setenv(key, "")
    yield
    reset_config()


class TestParsers:
    def test_parse_int_default_when_blank(self) -> None:
        assert parse_int("X", None, 5) == 5
        assert parse_int("X", "", 5) == 5

    def test_parse_int_accepts_value(self) -> None:
        assert parse_int("X", "7", 5) == 7

    def test_parse_int_rejects_non_numeric(self) -> None:
        with pytest.raises(ConfigError, match="must be an integer"):
            parse_int("X", "abc", 5)

    def test_parse_int_enforces_bounds(self) -> None:
        with pytest.raises(ConfigError, match=">= 1"):
            parse_int("X", "0", 5, minimum=1)
        with pytest.raises(ConfigError, match="<= 10"):
            parse_int("X", "11", 5, maximum=10)

    def test_parse_bool(self) -> None:
        assert parse_bool("X", None, True) is True
        assert parse_bool("X", "", False) is False
        assert parse_bool("X", "true", False) is True
        assert parse_bool("X", "off", True) is False
        with pytest.raises(ConfigError, match="must be a boolean"):
            parse_bool("X", "maybe", False)

    def test_parse_log_level(self) -> None:
        assert parse_log_level("X", None, "INFO") == "INFO"
        assert parse_log_level("X", "debug", "INFO") == "DEBUG"
        with pytest.raises(ConfigError, match="LOG"):
            parse_log_level("LOG_LEVEL", "verbose", "INFO")


class TestLoadConfig:
    def test_defaults(self) -> None:
        config = load_config()
        assert config.env == "development"
        assert config.supabase_url == ""
        assert config.database_url == ""
        assert config.log_level == "INFO"
        assert config.event_bus_max_handlers == 100
        assert config.search_index_default_limit == 10
        assert config.audit_default_actor == "system"
        assert config.audit_batch_size == 100
        assert config.cache_default_ttl_seconds == 300

    def test_env_overrides(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("SUPABASE_URL", "http://supabase.test")
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@127.0.0.1:54326/db")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("EVENT_BUS_MAX_HANDLERS", "50")
        monkeypatch.setenv("SEARCH_INDEX_DEFAULT_LIMIT", "25")
        monkeypatch.setenv("AUDIT_DEFAULT_ACTOR", "import-svc")
        monkeypatch.setenv("CACHE_DEFAULT_TTL_SECONDS", "60")
        config = load_config()
        assert config.env == "test"
        assert config.supabase_url == "http://supabase.test"
        assert config.database_url == "postgresql://test:test@127.0.0.1:54326/db"
        assert config.log_level == "DEBUG"
        assert config.event_bus_max_handlers == 50
        assert config.search_index_default_limit == 25
        assert config.audit_default_actor == "import-svc"
        assert config.cache_default_ttl_seconds == 60

    def test_invalid_numeric_value_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("EVENT_BUS_MAX_HANDLERS", "not-a-number")
        with pytest.raises(ConfigError):
            load_config()

    def test_log_level_int(self) -> None:
        config = load_config()
        assert config.log_level == "INFO"
        assert config.log_level_int == 20

    def test_app_config_is_immutable(self) -> None:
        config = AppConfig(
            env="test",
            supabase_url="",
            supabase_service_key="",
            database_url="",
            log_level="INFO",
            event_bus_max_handlers=100,
            search_index_default_limit=10,
            audit_default_actor="system",
            audit_batch_size=100,
            cache_default_ttl_seconds=300,
        )
        with pytest.raises(Exception):
            config.env = "prod"  # type: ignore[misc]


class TestSingleton:
    def test_get_config_caches(self) -> None:
        assert get_config() is get_config()

    def test_reset_config_forces_reload(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        first = get_config()
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        reset_config()
        second = get_config()
        assert second.log_level == "WARNING"
        assert first is not second
