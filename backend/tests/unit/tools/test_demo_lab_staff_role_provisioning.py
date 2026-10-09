"""G1 — Demo Lab staff-role provisioning must not destroy release capabilities.

CT-PO-PRODUCT-MODEL-IMPLEMENTATION-01 (G1). The Demo Lab provisioner
(``tools/demo_lab/provision.py::ensure_staff_roles``) used to write
``UPDATE staff_roles SET permissions = <map>`` — a wholesale replacement that
erased every migration-granted capability on each provisioning run:

* ``can_qc`` — ``20260902020000_v1_2_dual_origin_workflow.sql:102-105`` grants it
  by name to ``staff_roles.name IN ('qc_specialist', 'admin')``;
* ``can_manage_billing`` — ``20260824020000_d37_0…:300-304``;
* ``can_manage_backups`` — ``20261026000000_ct_backup_01_backup_jobs.sql:181-185``;
* ``can_review`` / ``can_view_all`` — the migration-seeded ``pe_manager`` row
  (``20260828020000_v3m8_pe_manager_role.sql:22-33``).

The provisioner is not a source of product permissions; ``staff_roles.permissions``
is the release's authoritative catalogue. These tests are **DB-free**: the module
under test is loaded with a stubbed ``lab`` helper whose tiny SQL applier
implements exactly the merge semantics the provisioner must emit, so a regression
back to a wholesale write fails here rather than silently in a provisioned
environment.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
PROVISION_PATH = REPO_ROOT / "tools" / "demo_lab" / "provision.py"
MANIFEST_PATH = REPO_ROOT / "tools" / "demo_lab" / "manifest.json"

#: The provisioner's own merge statement — the ONLY form this test applies.
_MERGE_RE = re.compile(
    r"^UPDATE staff_roles SET permissions = "
    r"COALESCE\(permissions, '\{\}'::jsonb\) \|\| (?P<map>'[^']*')::jsonb(::jsonb)? "
    r"WHERE id = '(?P<id>[^']+)'$",
    re.S,
)
_INSERT_RE = re.compile(
    r"^INSERT INTO staff_roles \(id, name, permissions\) VALUES "
    r"\('(?P<id>[^']+)', '(?P<name>[^']+)', (?P<map>'[^']*')::jsonb(::jsonb)?\)$",
    re.S,
)
_SELECT_RE = re.compile(
    r"^SELECT id FROM staff_roles WHERE name = '(?P<name>[^']+)' LIMIT 1$"
)


def _as_json(literal: str) -> dict:
    return json.loads(literal.strip("'").replace("''", "'"))


class _FakeLab:
    """Minimal stand-in for ``tools/demo_lab/lab`` + an in-memory ``staff_roles``."""

    LAB_NAMESPACE = "demo-lab-test"
    MANIFEST_PATH = MANIFEST_PATH

    def __init__(self, rows: dict[str, dict] | None = None) -> None:
        #: id → {"name": str, "permissions": dict}
        self.rows: dict[str, dict] = {}
        self.statements: list[str] = []
        for role_id, row in (rows or {}).items():
            self.rows[role_id] = {
                "name": row["name"],
                "permissions": dict(row["permissions"]),
            }

    # -- statements the provisioner issues ----------------------------------
    def psql_scalar(self, statement: str) -> str:
        match = _SELECT_RE.match(statement.strip())
        assert match, f"unexpected scalar statement: {statement!r}"
        for role_id, row in self.rows.items():
            if row["name"] == match.group("name"):
                return role_id
        return ""

    def psql(self, statement: str) -> "types.SimpleNamespace":
        text = statement.strip()
        self.statements.append(text)
        merge = _MERGE_RE.match(text)
        if merge:
            target = self.rows[merge.group("id")]
            # `permissions || jsonb` — the right operand wins; nothing is dropped.
            merged = dict(target["permissions"])
            merged.update(_as_json(merge.group("map")))
            target["permissions"] = merged
            return types.SimpleNamespace(returncode=0, stderr="", stdout="")
        insert = _INSERT_RE.match(text)
        if insert:
            self.rows[insert.group("id")] = {
                "name": insert.group("name"),
                "permissions": _as_json(insert.group("map")),
            }
            return types.SimpleNamespace(returncode=0, stderr="", stdout="")
        raise AssertionError(
            "the Demo Lab provisioner must only MERGE staff-role permissions "
            f"(a wholesale write destroys migration grants): {text!r}"
        )

    # -- helpers -------------------------------------------------------------
    def permissions_for(self, name: str) -> dict:
        for row in self.rows.values():
            if row["name"] == name:
                return row["permissions"]
        raise AssertionError(f"role {name!r} was not provisioned")

    def deterministic_uuid(self, key: str) -> str:
        return f"uuid:{key}"


@pytest.fixture()
def provision(monkeypatch: pytest.MonkeyPatch):
    """Load ``provision.py`` against a stub ``lab`` module (no database touched)."""

    def _load(rows: dict[str, dict] | None = None):
        fake = _FakeLab(rows)
        monkeypatch.setitem(sys.modules, "lab", fake)
        spec = importlib.util.spec_from_file_location(
            "ct_demo_lab_provision", PROVISION_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, fake

    yield _load
    # The stub must never leak into another test module.
    sys.modules.pop("lab", None)


def _manifest(*roles: str) -> dict:
    return {"actors": [{"key": f"a{i}", "staff_role": role}
                       for i, role in enumerate(roles)]}


RELEASE_ADMIN_GRANTS = {
    "can_qc": True,
    "can_manage_billing": True,
    "can_manage_backups": True,
}


# ---------------------------------------------------------------------------
# The defect: provisioning must not destroy migration-granted capabilities
# ---------------------------------------------------------------------------


def test_provisioning_preserves_migration_granted_admin_capabilities(provision) -> None:
    """Every capability a migration granted to ``admin`` survives provisioning."""
    module, fake = provision({
        "role-admin": {"name": "admin", "permissions": RELEASE_ADMIN_GRANTS}
    })

    module.ensure_staff_roles(_manifest("admin"), [])

    permissions = fake.permissions_for("admin")
    assert RELEASE_ADMIN_GRANTS.items() <= permissions.items(), permissions
    # ...and the lab's own flags were still applied (merge, not skip).
    assert permissions["demo_lab"] is True
    assert permissions["can_review"] is True
    assert permissions["can_qc"] is True


def test_provisioning_preserves_the_pe_manager_release_vocabulary(provision) -> None:
    """``pe_manager`` keeps the release map plus the lab's meta flag."""
    module, fake = provision({
        "5aaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa": {
            "name": "pe_manager",
            "permissions": {"can_process": True, "can_review": True,
                            "can_view_all": True},
        }
    })

    module.ensure_staff_roles(_manifest("pe_manager"), [])

    permissions = fake.permissions_for("pe_manager")
    assert permissions["can_review"] is True
    assert permissions["can_view_all"] is True
    assert permissions["can_manage_team"] is True
    assert permissions["demo_lab"] is True


def test_no_row_is_ever_written_with_a_wholesale_permission_map() -> None:
    """The source itself must never assign the column without the merge operator."""
    source = PROVISION_PATH.read_text(encoding="utf-8")
    # The merge expression (Python-escaped braces in the f-string) ...
    assert "COALESCE(permissions, '{{}}'::jsonb) || " in source
    # ... and no bare, unmerged assignment of the column anywhere.
    assert "SET permissions = '" not in source


# ---------------------------------------------------------------------------
# The capability the lab needs: CarbonTally QC (can_qc)
# ---------------------------------------------------------------------------


def test_admin_role_is_created_with_can_qc_and_is_idempotent(provision) -> None:
    """A fresh lab role gets ``can_qc``; a second run changes nothing."""
    module, fake = provision()

    module.ensure_staff_roles(_manifest("admin"), [])
    first = dict(fake.permissions_for("admin"))
    assert first["can_qc"] is True
    assert first["is_staff_admin"] is True
    assert first["demo_lab"] is True

    fake.statements.clear()
    module.ensure_staff_roles(_manifest("admin"), [])
    assert fake.permissions_for("admin") == first
    # Idempotent: the second run re-applies the same merge (no lost keys).
    assert fake.statements and all("|| " in s for s in fake.statements)


def test_unknown_role_gets_no_product_capability(provision) -> None:
    """The provisioner never invents capabilities for a role it does not define."""
    module, fake = provision()

    module.ensure_staff_roles(_manifest("reviewer"), [])

    assert fake.permissions_for("reviewer") == {"demo_lab": True}


def test_real_manifest_roles_are_all_provisioned(provision) -> None:
    """The shipped manifest's role vocabulary resolves to provisioned rows."""
    module, fake = provision()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    role_ids = module.ensure_staff_roles(manifest, [])

    assert {"admin", "operator", "pe_manager"} <= set(role_ids)
    assert fake.permissions_for("operator")["can_process"] is True
    assert fake.permissions_for("pe_manager")["can_process"] is True
    assert fake.permissions_for("admin")["can_qc"] is True
