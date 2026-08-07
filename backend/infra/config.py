"""Application configuration (Backend v2.1 §18 Caching, §19 Security).

Centralised, typed access to every environment variable and tunable the
platform reads. Follows the ``infra/supabase.py`` convention: ``.env`` files are
loaded best-effort once, explicit environment always wins, and the Supabase
values are sourced from the same helpers so this module and the client/pool
module can never disagree.

The layer rules are respected: this module imports only from ``core``
(exceptions) and the sibling ``infra.supabase`` module — no domain logic lives
here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import ClassVar, Optional

from core.exceptions import CarbonTallyError
from infra.supabase import get_database_url, get_service_role_key, get_supabase_url


class ConfigError(CarbonTallyError):
    """Raised when a required or malformed configuration value is supplied."""

    code: ClassVar[str] = "CONFIG_ERROR"
    http_status: ClassVar[int] = 500


# ---------------------------------------------------------------------------
# Primitive parsers (all raise ConfigError on malformed input)
# ---------------------------------------------------------------------------


def parse_int(
    name: str,
    raw: Optional[str],
    default: int,
    *,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
) -> int:
    """Parse ``raw`` as an integer, falling back to ``default`` when blank."""
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc
    if minimum is not None and value < minimum:
        raise ConfigError(f"{name} must be >= {minimum}, got {value}")
    if maximum is not None and value > maximum:
        raise ConfigError(f"{name} must be <= {maximum}, got {value}")
    return value


def parse_bool(name: str, raw: Optional[str], default: bool) -> bool:
    """Parse ``raw`` as a boolean, falling back to ``default`` when blank."""
    if raw is None or raw == "":
        return default
    lowered = raw.strip().lower()
    if lowered in ("1", "true", "yes", "on"):
        return True
    if lowered in ("0", "false", "no", "off"):
        return False
    raise ConfigError(f"{name} must be a boolean, got {raw!r}")


_LOG_LEVELS: dict[str, int] = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
    "NOTSET": 0,
}


def parse_log_level(name: str, raw: Optional[str], default: str) -> str:
    """Return a canonical upper-case logging level name."""
    value = (raw or default).strip().upper()
    if value not in _LOG_LEVELS:
        raise ConfigError(
            f"{name} must be one of {sorted(_LOG_LEVELS)}, got {value!r}"
        )
    return value


# ---------------------------------------------------------------------------
# Configuration snapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Immutable snapshot of the effective runtime configuration."""

    env: str
    supabase_url: str
    supabase_service_key: str
    database_url: str
    log_level: str
    event_bus_max_handlers: int
    search_index_default_limit: int
    audit_default_actor: str
    audit_batch_size: int
    cache_default_ttl_seconds: int

    @property
    def log_level_int(self) -> int:
        """The :mod:`logging` integer level for :attr:`log_level`."""
        return _LOG_LEVELS[self.log_level]


def load_config() -> AppConfig:
    """Read every environment variable and build the configuration snapshot."""
    env = os.getenv("APP_ENV") or os.getenv("ENV") or "development"
    return AppConfig(
        env=env.strip().lower(),
        supabase_url=get_supabase_url(),
        supabase_service_key=get_service_role_key(),
        database_url=get_database_url(),
        log_level=parse_log_level("LOG_LEVEL", os.getenv("LOG_LEVEL"), "INFO"),
        event_bus_max_handlers=parse_int(
            "EVENT_BUS_MAX_HANDLERS", os.getenv("EVENT_BUS_MAX_HANDLERS"),
            100, minimum=1, maximum=10_000,
        ),
        search_index_default_limit=parse_int(
            "SEARCH_INDEX_DEFAULT_LIMIT", os.getenv("SEARCH_INDEX_DEFAULT_LIMIT"),
            10, minimum=1, maximum=1_000,
        ),
        audit_default_actor=os.getenv("AUDIT_DEFAULT_ACTOR") or "system",
        audit_batch_size=parse_int(
            "AUDIT_BATCH_SIZE", os.getenv("AUDIT_BATCH_SIZE"),
            100, minimum=1, maximum=10_000,
        ),
        cache_default_ttl_seconds=parse_int(
            "CACHE_DEFAULT_TTL_SECONDS", os.getenv("CACHE_DEFAULT_TTL_SECONDS"),
            300, minimum=0, maximum=86_400 * 365,
        ),
    )


_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Return the process-wide configuration (built once, cached)."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config() -> None:
    """Drop the cached configuration (used by test suites)."""
    global _config
    _config = None
