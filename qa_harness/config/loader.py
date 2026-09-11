"""YAML configuration loader with graceful missing-dependency handling.

If PyYAML is not installed the loader raises :class:`ConfigLoadError` with a
clear message — callers report ``SKIPPED — TOOL UNAVAILABLE`` rather than
crashing (spec §36).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml as _yaml  # type: ignore
    _YAML_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised via optional-dep tests
    _yaml = None  # type: ignore
    _YAML_AVAILABLE = False

from qa_harness.core.config import (
    Exclusion,
    QaConfig,
    RoleSpec,
    RouteSpec,
    SeverityDef,
    TableRule,
    TargetEnv,
    ToolSpec,
    UxRule,
    WorkflowSpec,
    WorkflowStep,
)

CONFIG_DIR = Path(__file__).resolve().parent

CONFIG_FILES = [
    "qa_config.yaml",
    "environments.yaml",
    "roles.yaml",
    "routes.yaml",
    "workflows.yaml",
    "table_rules.yaml",
    "ux_rules.yaml",
    "severity.yaml",
    "exclusions.yaml",
]


class ConfigLoadError(RuntimeError):
    """Raised when configuration cannot be loaded."""


def load_yaml(path: Path) -> Dict[str, Any]:
    if not _YAML_AVAILABLE:
        raise ConfigLoadError(
            "PyYAML is not installed; install requirements.txt "
            "(SKIPPED — TOOL UNAVAILABLE for config loading)"
        )
    path = Path(path)
    if not path.exists():
        raise ConfigLoadError(f"config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = _yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigLoadError(f"config file must map to a YAML mapping: {path}")
    return data


def _target_env(name: str, data: Dict[str, Any]) -> TargetEnv:
    return TargetEnv(
        name=name,
        frontend_url=data.get("frontend_url", ""),
        api_url=data.get("api_url", ""),
        api_prefix=data.get("api_prefix", "/api/v3"),
        supabase_auth_url=data.get("supabase_auth_url", ""),
        supabase_rest_url=data.get("supabase_rest_url", ""),
        postgres_dsn_env=data.get("postgres_dsn_env", "DATABASE_URL"),
        postgres_host=data.get("postgres_host", ""),
        postgres_port=int(data.get("postgres_port", 0) or 0),
        postgres_db=data.get("postgres_db", ""),
        notes=data.get("notes", ""),
    )


def load_config(config_dir: Optional[Path] = None) -> QaConfig:
    """Load every YAML file in the config directory into a typed :class:`QaConfig`."""
    config_dir = Path(config_dir) if config_dir else CONFIG_DIR
    if not config_dir.exists():
        raise ConfigLoadError(f"config directory not found: {config_dir}")

    raw_all: Dict[str, Dict[str, Any]] = {}
    for name in CONFIG_FILES:
        raw_all[name] = load_yaml(config_dir / name)

    main = raw_all["qa_config.yaml"]
    harness = main.get("harness", {})
    tools_raw = main.get("tools", {})
    target_raw = main.get("target", {})
    viewports = main.get("viewports", [])
    identity = main.get("identity", {})
    ai = main.get("ai", {})

    environments_raw = raw_all["environments.yaml"].get("environments", {})
    environments = {name: _target_env(name, data) for name, data in environments_raw.items()}

    target = _target_env("local", target_raw)
    if "local" in environments:
        local = environments["local"]
        # YAML target wins; fall back to environments.local for blank fields.
        for field_name in (
            "frontend_url", "api_url", "api_prefix", "supabase_auth_url",
            "supabase_rest_url", "postgres_dsn_env", "postgres_host",
            "postgres_port", "postgres_db",
        ):
            if not getattr(target, field_name):
                setattr(target, field_name, getattr(local, field_name))

    roles_raw = raw_all["roles.yaml"].get("roles", {})
    roles = {
        key: RoleSpec(
            key=key,
            label=data.get("label", key),
            workspace=data.get("workspace", ""),
            landing_route=data.get("landing_route", ""),
            capabilities=list(data.get("capabilities", [])),
            boundaries=list(data.get("boundaries", [])),
            description=data.get("description", ""),
        )
        for key, data in roles_raw.items()
    }

    routes = [
        RouteSpec(
            path=entry.get("path", ""),
            workspace=entry.get("workspace", ""),
            label=entry.get("label", ""),
            auth=entry.get("auth", "public"),
            roles=list(entry.get("roles", [])),
            expected_title=entry.get("expected_title", ""),
        )
        for entry in raw_all["routes.yaml"].get("routes", [])
    ]

    workflows = {}
    for key, data in raw_all["workflows.yaml"].get("workflows", {}).items():
        steps = [
            WorkflowStep(
                action=step.get("action", ""),
                expected_status=step.get("expected_status", ""),
                verify_persisted=step.get("verify_persisted", True),
            )
            for step in data.get("steps", [])
        ]
        workflows[key] = WorkflowSpec(
            key=key,
            label=data.get("label", key),
            personas=list(data.get("personas", [])),
            steps=steps,
            description=data.get("description", ""),
        )

    table_rules = {
        key: TableRule(
            table=key,
            operational=data.get("operational", True),
            min_rows_for_pagination=int(data.get("min_rows_for_pagination", 20)),
            require_pagination=data.get("require_pagination", True),
            require_page_size=data.get("require_page_size", True),
            require_sorting=data.get("require_sorting", True),
            require_filtering=data.get("require_filtering", True),
            require_search=data.get("require_search", False),
            require_context_columns=data.get("require_context_columns", True),
            notes=data.get("notes", ""),
        )
        for key, data in raw_all["table_rules.yaml"].get("tables", {}).items()
    }

    ux_rules = [
        UxRule(
            key=entry.get("key", ""),
            label=entry.get("label", ""),
            description=entry.get("description", ""),
            severity=entry.get("severity", "P2"),
        )
        for entry in raw_all["ux_rules.yaml"].get("rules", [])
    ]

    severities = {
        level: SeverityDef(level=level, label=data.get("label", level), examples=list(data.get("examples", [])))
        for level, data in raw_all["severity.yaml"].get("severities", {}).items()
    }

    exclusions = [
        Exclusion(
            kind=entry.get("kind", ""),
            pattern=entry.get("pattern", ""),
            reason=entry.get("reason", ""),
            global_exclusion=entry.get("global", False),
        )
        for entry in raw_all["exclusions.yaml"].get("exclusions", [])
    ]

    tools = {
        name: ToolSpec(
            name=name,
            available=bool(data.get("available", False)),
            reason=data.get("reason", ""),
        )
        for name, data in tools_raw.items()
    }

    return QaConfig(
        harness_name=harness.get("name", "CarbonTally QA Harness"),
        harness_version=harness.get("version", "1.0.0"),
        mode=harness.get("mode", "read-only"),
        target=target,
        environments=environments,
        roles=roles,
        routes=routes,
        workflows=workflows,
        table_rules=table_rules,
        ux_rules=ux_rules,
        severities=severities,
        exclusions=exclusions,
        viewports=viewports,
        tools=tools,
        identity=identity,
        ai=ai,
        raw=raw_all,
        config_dir=config_dir,
    )
