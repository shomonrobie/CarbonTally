"""CT-IMPLEMENT-01 (2026-09-27) — remediation regression tests.

Covers the engineering remediations implemented in this task that are
deterministic and database-free:

1. **CT-AUDIT-01 §11.1 A** — ``utils.audit_logger`` must never swallow an audit
   write failure silently: failures are counted, described and logged, and can
   be escalated to a hard failure (``strict=True`` or
   ``AUDIT_LOG_FAILURE_MODE=raise``).
2. **CT-AUDIT-01 §11.1 B** — the literal ``/api/admin/audit/activity/*`` routes
   must be declared before the parameterised ``/activity/{log_id}`` route so the
   literal paths can no longer be shadowed.
3. **CT-SCHEMA-03 F-03/F-04** — ``utils.emissions.get_emission_factor`` resolves
   through the canonical governed chain (approved customer factor → CarbonTally
   factor via ``factor_aliases`` → controlled unresolved), never through the
   retired ``defra_conversion_factors`` table, and records the factor provenance
   that produced the number.
4. **CT-SCHEMA-03 F-05/F-09 (CT-IMPLEMENT-04, 2026-09-28)** — every remaining
   *non-decision-gated* read site of the retired ``defra_conversion_factors``
   table is repointed onto the canonical ``emission_factors`` table (enhanced
   report generation, the emissions listing, the organisation
   data/dashboard/export routes) and both legacy frontend factor embeds are
   removed.  New references are confined by an explicit allowlist to the
   surfaces still awaiting a PO decision (PD-3 admin factor management, PD-5
   manual-entry factor lookup).

The tests use an in-memory fake Supabase client, so they assert the *queries and
the decision* rather than a live database.  Live schema compatibility of the
canonical column set is established separately against the disposable canonical
rebuild (see the CT-IMPLEMENT-01 report).
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# fake Supabase client
# ---------------------------------------------------------------------------


class _Result:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, client, table):
        self._client = client
        self._table = table
        self._filters = []
        self._order = None
        self._limit = None
        self._payload = None

    def select(self, _columns):
        return self

    def eq(self, column, value):
        self._filters.append((column, value))
        return self

    def order(self, column, desc=False):
        self._order = (column, desc)
        return self

    def limit(self, count):
        self._limit = count
        return self

    def maybe_single(self):
        self._limit = 1
        return self

    def insert(self, payload):
        self._payload = payload
        return self

    def execute(self):
        self._client.queries.append(
            {
                "table": self._table,
                "filters": list(self._filters),
                "order": self._order,
                "limit": self._limit,
            }
        )
        if self._client.raise_on_target == self._table:
            raise RuntimeError("simulated database failure")

        if self._payload is not None:
            row = dict(self._payload)
            row.setdefault("id", "inserted-id")
            self._client.tables.setdefault(self._table, []).append(row)
            return _Result([row])

        rows = [dict(r) for r in self._client.tables.get(self._table, [])]
        for column, value in self._filters:
            rows = [r for r in rows if r.get(column) == value]
        if self._order:
            column, desc = self._order
            rows.sort(key=lambda r: r.get(column), reverse=bool(desc))
        if self._limit is not None:
            rows = rows[: self._limit]
        return _Result(rows)


class FakeSupabase:
    """Minimal PostgREST-shaped fake recording every query it receives."""

    def __init__(self, tables=None, raise_on_target=None):
        self.tables = tables if tables is not None else {}
        self.queries = []
        self.raise_on_target = raise_on_target

    def from_(self, table):
        return _Query(self, table)

    @property
    def tables_queried(self):
        return [q["table"] for q in self.queries]


# ---------------------------------------------------------------------------
# CT-AUDIT-01 §11.1 A — an audit failure is never silent
# ---------------------------------------------------------------------------


def _audit_module():
    from utils import audit_logger

    return audit_logger


async def test_audit_failure_is_observable_and_not_silent(monkeypatch):
    audit = _audit_module()
    audit.reset_audit_failure_state()
    monkeypatch.delenv("AUDIT_LOG_FAILURE_MODE", raising=False)

    client = FakeSupabase(raise_on_target="audit_logs")
    monkeypatch.setattr(audit, "get_supabase_client", lambda: client)
    outcome = await audit.log_audit(
        user_id="u-1",
        organization_id="org-1",
        action_type="document_approved",
        resource_type="document",
        resource_id="doc-1",
        strict=False,
    )

    assert outcome is None
    assert audit.audit_failure_count() == 1
    failure = audit.last_audit_failure()
    assert failure is not None
    assert failure["action_type"] == "document_approved"
    assert failure["resource_type"] == "document"
    assert failure["resource_id"] == "doc-1"
    assert failure["organization_id"] == "org-1"
    assert failure["error_type"] == "RuntimeError"


async def test_audit_strict_mode_fails_closed(monkeypatch):
    audit = _audit_module()
    audit.reset_audit_failure_state()
    monkeypatch.delenv("AUDIT_LOG_FAILURE_MODE", raising=False)

    client = FakeSupabase(raise_on_target="audit_logs")
    monkeypatch.setattr(audit, "get_supabase_client", lambda: client)
    with pytest.raises(audit.AuditWriteError):
        await audit.log_audit(
            action_type="permission_changed",
            resource_type="role",
            strict=True,
        )
    assert audit.audit_failure_count() == 1


async def test_audit_failure_mode_env_raises(monkeypatch):
    audit = _audit_module()
    audit.reset_audit_failure_state()
    monkeypatch.setenv("AUDIT_LOG_FAILURE_MODE", "raise")

    client = FakeSupabase(raise_on_target="audit_logs")
    monkeypatch.setattr(audit, "get_supabase_client", lambda: client)
    with pytest.raises(audit.AuditWriteError):
        await audit.log_audit(action_type="login", resource_type="session")
    assert audit.audit_failure_count() == 1


async def test_audit_success_records_no_failure(monkeypatch):
    audit = _audit_module()
    audit.reset_audit_failure_state()
    monkeypatch.delenv("AUDIT_LOG_FAILURE_MODE", raising=False)

    client = FakeSupabase()
    monkeypatch.setattr(audit, "get_supabase_client", lambda: client)
    row = await audit.log_audit(
        user_id="u-2",
        organization_id="org-2",
        action_type="document_uploaded",
        resource_type="document",
    )

    assert row is not None and row["id"] == "inserted-id"
    assert audit.audit_failure_count() == 0
    assert audit.last_audit_failure() is None
    assert client.tables_queried == ["audit_logs"]


def test_audit_unknown_failure_mode_falls_back_to_log(monkeypatch):
    audit = _audit_module()
    monkeypatch.setenv("AUDIT_LOG_FAILURE_MODE", "explode")
    assert audit._resolve_default_failure_mode() == audit.FAILURE_MODE_LOG


# ---------------------------------------------------------------------------
# CT-AUDIT-01 §11.1 B — literal activity routes are no longer shadowed
# ---------------------------------------------------------------------------


def test_activity_literal_routes_precede_parameterised_route():
    from routes.admin.audit import router

    paths = [getattr(route, "path", "") for route in router.routes]
    export_index = paths.index("/api/admin/audit/activity/export")
    search_index = paths.index("/api/admin/audit/activity/search")
    detail_index = paths.index("/api/admin/audit/activity/{log_id}")

    # Starlette matches in declaration order: every literal path must be
    # considered before the {log_id} wildcard.
    assert export_index < detail_index
    assert search_index < detail_index


# ---------------------------------------------------------------------------
# CT-SCHEMA-03 F-03/F-04 — canonical factor resolution
# ---------------------------------------------------------------------------


def _emissions_module():
    from utils import emissions

    return emissions


def _factor_row(**overrides):
    row = {
        "id": "ef-1",
        # ACTIVITY_TYPE_MAPPING maps the user-facing 'Electricity' label to this
        # canonical activity type.
        "activity_type": "UK Electricity Grid",
        "co2e_multiplier": 0.20705,
        "reporting_year": 2026,
        "unit": "kWh",
        "scope": "Scope 2",
        "country": "GB",
        "factor_source": "DEFRA",
        "factor_set": "2026",
    }
    row.update(overrides)
    return row


def test_canonical_factor_query_never_targets_retired_table():
    emissions = _emissions_module()
    client = FakeSupabase({"emission_factors": [_factor_row()]})

    factor = emissions.get_emission_factor(client, "Electricity", 2026)

    assert factor["factor_id"] == "ef-1"
    assert factor["multiplier"] == pytest.approx(0.20705)
    assert factor["factor_kind"] == "carbontally_factor"
    assert factor["factor_source"] == "DEFRA"
    assert factor["resolution"] == "exact_year"
    assert factor["is_fallback"] is False
    assert "defra_conversion_factors" not in client.tables_queried
    assert "emission_factors" in client.tables_queried


def test_approved_customer_factor_takes_precedence():
    emissions = _emissions_module()
    client = FakeSupabase(
        {
            "customer_factors": [
                {
                    "id": "cf-1",
                    "organization_id": "org-1",
                    "activity_type": "UK Electricity Grid",
                    "co2e_multiplier": 0.19,
                    "reporting_year": 2026,
                    "unit": "kWh",
                    "scope": "Scope 2",
                    "country": "GB",
                    "factor_source": "supplier-specific",
                    "version": 2,
                    "status": "active",
                }
            ],
            "emission_factors": [_factor_row()],
        }
    )

    factor = emissions.get_emission_factor(
        client, "Electricity", 2026, organization_id="org-1"
    )

    assert factor["factor_kind"] == "customer_factor"
    assert factor["customer_factor_id"] == "cf-1"
    assert factor["factor_id"] == "cf-1"
    assert factor["multiplier"] == pytest.approx(0.19)
    assert factor["resolution"] == "customer_factor"
    # Precedence short-circuits: the generic table is never consulted.
    assert "emission_factors" not in client.tables_queried


def test_unapproved_customer_factor_does_not_outrank_canonical():
    emissions = _emissions_module()
    client = FakeSupabase(
        {
            "customer_factors": [
                {
                    "id": "cf-draft",
                    "organization_id": "org-1",
                    "activity_type": "UK Electricity Grid",
                    "co2e_multiplier": 0.19,
                    "reporting_year": 2026,
                    "version": 1,
                    "status": "draft",
                }
            ],
            "emission_factors": [_factor_row()],
        }
    )

    factor = emissions.get_emission_factor(
        client, "Electricity", 2026, organization_id="org-1"
    )

    assert factor["factor_kind"] == "carbontally_factor"
    assert factor["factor_id"] == "ef-1"


def test_governed_alias_resolution_is_recorded():
    emissions = _emissions_module()
    client = FakeSupabase(
        {
            "factor_aliases": [
                {
                    "alias_text": "Site diesel",
                    "target_activity_type": "Diesel (average biofuel blend)",
                    "organization_id": None,
                }
            ],
            "emission_factors": [
                _factor_row(
                    id="ef-diesel",
                    activity_type="Diesel (average biofuel blend)",
                    co2e_multiplier=2.52,
                )
            ],
        }
    )

    factor = emissions.get_emission_factor(client, "Site diesel", 2026)

    assert factor["factor_id"] == "ef-diesel"
    assert factor["alias_used"] == "Diesel (average biofuel blend)"


def test_latest_year_fallback_is_explicit_not_silent():
    emissions = _emissions_module()
    client = FakeSupabase(
        {"emission_factors": [_factor_row(id="ef-2024", reporting_year=2024)]}
    )

    factor = emissions.get_emission_factor(client, "Electricity", 2026)

    assert factor["factor_id"] == "ef-2024"
    assert factor["is_fallback"] is True
    assert factor["resolution"] == "latest_year_fallback"


def test_unresolved_factor_is_a_controlled_state():
    emissions = _emissions_module()
    client = FakeSupabase({"emission_factors": []})

    with pytest.raises(emissions.FactorUnresolved) as excinfo:
        emissions.get_emission_factor(client, "Unobtainium", 2026)

    # Still a ValueError so legacy ``except ValueError`` handlers keep working.
    assert isinstance(excinfo.value, ValueError)
    assert "manual review" in str(excinfo.value)


def test_activity_type_mapping_is_honoured_without_an_alias():
    emissions = _emissions_module()
    client = FakeSupabase(
        {"emission_factors": [_factor_row(activity_type="UK Electricity Grid")]}
    )

    # ACTIVITY_TYPE_MAPPING maps 'Electricity' -> 'UK Electricity Grid'.
    factor = emissions.get_emission_factor(client, "Electricity")

    assert factor["factor_id"] == "ef-1"
    assert factor["alias_used"] is None


# ---------------------------------------------------------------------------
# source-level regression guards
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[3]

_REPOINTED_FILES = (
    "backend/utils/emissions.py",
    "backend/routes/documents_main.py",
    "backend/routes/drafts.py",
    "backend/routes/admin/extraction.py",
    # CT-IMPLEMENT-04 (2026-09-28) — CT-SCHEMA-03 F-05 repoints
    "backend/report_generator.py",
    "backend/routes/emissions.py",
    "backend/routes/organizations/data.py",
    "backend/routes/organizations/dashboard.py",
    "backend/routes/organizations/exports.py",
    # CT-IMPLEMENT-04 (2026-09-28) — CT-SCHEMA-03 F-09 frontend embeds
    "frontend/src/App.js",
    "frontend/App_.js",
)

# These files must *contain* the canonical factor table name, so the guard above
# cannot be satisfied by deleting the factor lookup altogether.
_CANONICAL_FACTOR_READ_FILES = (
    "backend/report_generator.py",
    "backend/routes/emissions.py",
    "backend/routes/organizations/data.py",
    "backend/routes/organizations/dashboard.py",
    "backend/routes/organizations/exports.py",
)

# Live-code files still permitted to name the retired table.  Each entry is a
# surface awaiting a PO decision (PD-3 admin factor management — CT-SCHEMA-03
# F-06/F-07; PD-3/PD-5 factor curation + manual-entry lookup — F-05 residual), a
# deliberate documentation comment, or this guard itself.
_LEGACY_REFERENCE_ALLOWLIST = {
    "backend/routes/admin/defra.py",  # PD-3 / F-06 — 16 reads
    "backend/routes/reports.py",  # PD-3 / PD-5 — 2 reads (F-05 residual)
    "backend/routes/reference.py",  # documentation comment only
    "backend/tests/unit/test_ct_implement_01_remediation.py",  # this guard
    "admin/src/pages/admin/DefraFactors.js",  # PD-3 / F-07
    "admin/src/components/admin/DefraFactorModal.js",  # PD-3 / F-07
    "admin/src/components/admin/ImportDefraModal.js",  # PD-3 / F-07
}

_LEGACY_SCAN_ROOTS = (
    ("backend", "*.py"),
    # F-05-R7 (CT-VERIFY-05 §6): the roots must also cover the ROOT-LEVEL
    # frontend bundles, not just ``frontend/src`` — otherwise a newly added
    # legacy reference in ``frontend/*.js`` would never fail this guard.
    # ``node_modules``/``build``/``dist`` stay excluded via ``_EXCLUDED_DIRS``.
    ("frontend", "*.js"),
    ("frontend", "*.jsx"),
    ("admin", "*.js"),
    ("admin", "*.jsx"),
)

_EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


@pytest.mark.parametrize("relative_path", _REPOINTED_FILES)
def test_no_legacy_factor_table_reference_remains(relative_path):
    text = (_REPO_ROOT / relative_path).read_text(encoding="utf-8", errors="replace")
    assert "defra_conversion_factors" not in text


@pytest.mark.parametrize(
    "relative_path",
    (
        "backend/routes/documents_main.py",
        "backend/routes/drafts.py",
        "backend/routes/admin/extraction.py",
        "backend/routes/emissions.py",
    ),
)
def test_emissions_logs_writes_use_the_canonical_factor_column(relative_path):
    """``emissions_logs.emission_factor_id`` is the canonical column (verified
    against the disposable canonical rebuild); the canonical schema has no
    ``defra_factor_id`` column on ``emissions_logs``."""

    text = (_REPO_ROOT / relative_path).read_text(encoding="utf-8", errors="replace")
    assert "'emission_factor_id'" in text


@pytest.mark.parametrize("relative_path", _CANONICAL_FACTOR_READ_FILES)
def test_repointed_factor_reads_use_the_canonical_table(relative_path):
    """The repoint must *target* ``emission_factors``, not merely delete a read."""

    text = (_REPO_ROOT / relative_path).read_text(encoding="utf-8", errors="replace")
    assert "emission_factors" in text


def test_legacy_factor_table_references_are_confined_to_decided_files():
    """No live-code file may *start* naming the retired table.

    The allowlist is the residual inventory recorded by CT-IMPLEMENT-04 §5: the
    files still naming the retired table are exactly the surfaces awaiting a PO
    decision (PD-3 admin factor management, PD-5 manual-entry factor lookup)
    plus one deliberate documentation comment.  A newly added reference fails
    this test; remediating an allowlisted file merely stops matching, so the
    allowlist never has to grow.
    """

    offenders = []
    for root, pattern in _LEGACY_SCAN_ROOTS:
        base = _REPO_ROOT / root
        if not base.exists():
            continue
        for path in sorted(base.rglob(pattern)):
            relative = path.relative_to(_REPO_ROOT)
            if set(relative.parts[:-1]) & _EXCLUDED_DIRS:
                continue
            recorded = str(relative)
            if recorded in _LEGACY_REFERENCE_ALLOWLIST:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if "defra_conversion_factors" in text:
                offenders.append(recorded)

    assert offenders == []
