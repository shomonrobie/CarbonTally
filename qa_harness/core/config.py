"""Resolved QA Harness configuration (dataclasses).

Raw YAML (config/*.yaml) is loaded by :mod:`qa_harness.config.loader` and
mapped onto these typed objects. Everything here is plain data — no
application contact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ToolSpec:
    name: str
    available: bool = False
    reason: str = ""


@dataclass
class TargetEnv:
    name: str
    frontend_url: str = ""
    api_url: str = ""
    api_prefix: str = "/api/v3"
    supabase_auth_url: str = ""
    supabase_rest_url: str = ""
    postgres_dsn_env: str = "DATABASE_URL"
    postgres_host: str = ""
    postgres_port: int = 0
    postgres_db: str = ""
    notes: str = ""

    @property
    def frontend_base_url(self) -> str:
        """Alias used by run scripts."""
        return self.frontend_url

    @property
    def api_base_url(self) -> str:
        """Alias used by run scripts."""
        return self.api_url


@dataclass
class RoleSpec:
    key: str
    label: str
    workspace: str
    landing_route: str
    capabilities: List[str] = field(default_factory=list)
    boundaries: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class RouteSpec:
    path: str
    workspace: str
    label: str = ""
    auth: str = "public"          # public | authenticated
    roles: List[str] = field(default_factory=list)
    expected_title: str = ""


@dataclass
class WorkflowStep:
    action: str
    expected_status: str = ""
    verify_persisted: bool = True


@dataclass
class WorkflowSpec:
    key: str
    label: str
    personas: List[str] = field(default_factory=list)
    steps: List[WorkflowStep] = field(default_factory=list)
    description: str = ""


@dataclass
class TableRule:
    table: str
    operational: bool = True
    min_rows_for_pagination: int = 20
    require_pagination: bool = True
    require_page_size: bool = True
    require_sorting: bool = True
    require_filtering: bool = True
    require_search: bool = False
    require_context_columns: bool = True   # org/client/entity identification
    notes: str = ""


@dataclass
class UxRule:
    key: str
    label: str
    description: str = ""
    severity: str = "P2"


@dataclass
class SeverityDef:
    level: str
    label: str
    examples: List[str] = field(default_factory=list)


@dataclass
class Exclusion:
    kind: str                 # route | table | finding | console_error | endpoint
    pattern: str
    reason: str = ""
    global_exclusion: bool = False


@dataclass
class QaConfig:
    harness_name: str
    harness_version: str
    mode: str                              # read-only (default)
    target: TargetEnv = field(default_factory=TargetEnv)
    environments: Dict[str, TargetEnv] = field(default_factory=dict)
    roles: Dict[str, RoleSpec] = field(default_factory=dict)
    routes: List[RouteSpec] = field(default_factory=list)
    workflows: Dict[str, WorkflowSpec] = field(default_factory=dict)
    table_rules: Dict[str, TableRule] = field(default_factory=dict)
    ux_rules: List[UxRule] = field(default_factory=list)
    severities: Dict[str, SeverityDef] = field(default_factory=dict)
    exclusions: List[Exclusion] = field(default_factory=list)
    viewports: List[Dict[str, int]] = field(default_factory=list)
    tools: Dict[str, ToolSpec] = field(default_factory=dict)
    identity: Dict[str, Any] = field(default_factory=dict)
    ai: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)
    config_dir: Path = field(default_factory=Path)

    @property
    def read_only(self) -> bool:
        return self.mode.lower() in ("read-only", "readonly", "read_only")

    @property
    def default_environment(self) -> str:
        return "local" if "local" in self.environments else (
            next(iter(self.environments), "local")
        )

    @property
    def identities(self) -> Dict[str, Any]:
        """Alias for the identity manifest config (scripts use ``config.identities``)."""
        return self.identity

    def environment(self, name: str) -> TargetEnv:
        env = self.environments.get(name)
        if env is not None:
            return env
        if name == "local":
            return self.target
        raise KeyError(f"unknown environment {name!r} (available: {sorted(self.environments)})")

    def tool(self, name: str) -> ToolSpec:
        return self.tools.get(name, ToolSpec(name=name))

    def route_paths(self, workspace: Optional[str] = None) -> List[str]:
        if workspace is None:
            return [r.path for r in self.routes]
        return [r.path for r in self.routes if r.workspace == workspace]


def load_config(config_dir: Optional[Path] = None) -> "QaConfig":
    """Load the typed harness configuration (delegates to config.loader).

    Imported lazily to avoid a circular import: the loader imports the typed
    dataclasses from this module.
    """
    from qa_harness.config.loader import load_config as _load

    return _load(config_dir)
