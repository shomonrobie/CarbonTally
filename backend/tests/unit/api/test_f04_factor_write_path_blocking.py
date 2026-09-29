"""CT-FINAL-01 — F-04 (blocking factor validation on WRITE paths) regression tests.

Ratified scope: an emission factor must never be *silently absent* on a write
path.  Before this change-set each of the three write paths could persist an
emissions row with ``emission_factor_id = NULL`` and a fabricated ``2.68``
multiplier whenever no governed factor resolved.  Under F-04 an unresolved
factor is a **blocking validation state**: the write is refused (HTTP 409)
with the machine-detectable code ``FACTOR_UNRESOLVED_BLOCKED`` and nothing is
mutated (AGENTS.md #17 provenance, #25 server-authoritative calculation,
#26/#47 blocked state, #74 no false completion).

Covered write paths (one HTTP-shaped case each, plus a success case proving the
factor provenance actually reaches the persisted row):

* ``POST /api/drafts/{draft_id}/submit``            → ``routes.drafts.submit_draft``
* ``POST /api/documents/{org_id}/{file_id}/review`` → ``routes.documents_main.customer_review_document``
* ``POST /api/admin/extraction/approve``            → ``routes.admin.extraction.approve_extraction``

The tests call the real endpoint coroutines over an in-memory fake Supabase
client (the established DB-free unit pattern) and monkeypatch **only** the
factor-resolution result, so the blocking decision and the persisted payload are
the production code paths.  No database is contacted.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi import HTTPException

from auth import AuthUser
from utils.emissions import (
    FACTOR_BLOCKED_CODE,
    FactorUnresolved,
    FactorUnresolvedBlocked,
    factor_blocked_detail,
    require_emission_factor,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]

#: The three ratified F-04 write paths.
_WRITE_PATH_FILES = (
    "backend/routes/drafts.py",
    "backend/routes/documents_main.py",
    "backend/routes/admin/extraction.py",
)

#: A resolved-factor mapping with the full canonical provenance contract.
_RESOLVED_FACTOR = {
    "multiplier": 2.5,
    "reporting_year": 2025,
    "factor_id": "factor-1",
    "is_fallback": False,
    "factor_kind": "carbontally_factor",
    "factor_source": "DEFRA-DESNZ",
    "factor_set": "DEFRA-2025",
    "unit": "kWh",
    "scope": "Scope 2",
    "country": "GB",
    "customer_factor_id": None,
    "alias_used": "UK Electricity Grid",
    "resolution": "canonical_factor",
}


# ---------------------------------------------------------------------------
# in-memory PostgREST-shaped fake (records every query it receives)
# ---------------------------------------------------------------------------


class _Result:
    def __init__(self, data=None):
        self.data = data if data is not None else []


class _Query:
    def __init__(self, client, table):
        self._client = client
        self._table = table
        self._filters = []
        self._payload = None
        self._limit = None
        self._single = False
        self._op = "select"

    def select(self, _columns="*"):
        return self

    def eq(self, column, value):
        self._filters.append((column, value))
        return self

    def maybe_single(self):
        self._limit = 1
        self._single = True
        return self

    def insert(self, payload):
        self._op = "insert"
        self._payload = payload
        return self

    def update(self, payload):
        self._op = "update"
        self._payload = payload
        return self

    def delete(self):
        self._op = "delete"
        return self

    def execute(self):
        self._client.queries.append((self._table, self._op))
        if self._op == "insert":
            row = dict(self._payload)
            row.setdefault("id", f"{self._table}-inserted")
            self._client.tables.setdefault(self._table, []).append(row)
            return _Result([row])
        if self._op == "update":
            self._client.updates.append((self._table, self._payload))
            # PostgREST parity: supabase-py sends ``Prefer: return=representation``
            # for writes, so an update returns the affected rows — and an empty
            # result genuinely means "no row matched".
            matched = []
            for row in self._client.tables.get(self._table, []):
                if all(row.get(column) == value for column, value in self._filters):
                    row.update(self._payload)
                    matched.append(dict(row))
            return _Result(matched)
        if self._op == "delete":
            self._client.deletes.append(self._table)
            return _Result([])
        rows = [dict(r) for r in self._client.tables.get(self._table, [])]
        for column, value in self._filters:
            rows = [r for r in rows if r.get(column) == value]
        if self._limit is not None:
            rows = rows[: self._limit]
        # PostgREST ``maybe_single()`` returns an object (or null), never a list.
        if self._single:
            return _Result(rows[0] if rows else None)
        return _Result(rows)


class FakeSupabase:
    """Minimal fake recording inserts/updates/deletes per table."""

    def __init__(self, tables=None):
        self.tables = dict(tables or {})
        self.queries = []
        self.updates = []
        self.deletes = []

    def from_(self, table):
        return _Query(self, table)

    def inserted(self, table):
        return [q for q in self.queries if q == (table, "insert")]

    def updated_tables(self):
        return [table for table, _payload in self.updates]


def _run(coro):
    return asyncio.run(coro)


def _member_user(org_id="org-a"):
    return AuthUser(
        user_id="user-1",
        email="member@carbontally.test",
        role="user",
        role_name="user",
        organization_id=org_id,
        is_org_member=True,
    )


def _admin_user():
    return AuthUser(
        user_id="admin-1",
        email="admin@carbontally.test",
        role="admin",
        role_name="admin",
        is_staff=True,
        is_admin=True,
    )


# ---------------------------------------------------------------------------
# F-04 primitive contract
# ---------------------------------------------------------------------------


def test_blocked_code_is_frozen_and_recognisable() -> None:
    """The 409 detail must carry a stable, machine-detectable code."""
    assert FACTOR_BLOCKED_CODE == "FACTOR_UNRESOLVED_BLOCKED"
    detail = factor_blocked_detail("Electricity", 2025)
    assert detail.startswith(FACTOR_BLOCKED_CODE)
    assert "Electricity" in detail and "2025" in detail
    assert "No emissions record was written" in detail


def test_blocked_is_a_subclass_of_unresolved() -> None:
    """Legacy ``except FactorUnresolved`` handlers keep working."""
    assert issubclass(FactorUnresolvedBlocked, FactorUnresolved)


def test_require_emission_factor_raises_when_nothing_resolves(monkeypatch) -> None:
    def _raise(*_args, **_kwargs):
        raise FactorUnresolved("no factor")

    monkeypatch.setattr("utils.emissions.get_emission_factor", _raise)
    with pytest.raises(FactorUnresolvedBlocked):
        require_emission_factor(object(), "Electricity", 2025)


def test_require_emission_factor_raises_when_factor_has_no_id(monkeypatch) -> None:
    """A resolved row without ``factor_id`` is still a provenance failure."""
    monkeypatch.setattr(
        "utils.emissions.get_emission_factor",
        lambda *_a, **_k: dict(_RESOLVED_FACTOR, factor_id=None),
    )
    with pytest.raises(FactorUnresolvedBlocked) as excinfo:
        require_emission_factor(object(), "Electricity", 2025)
    assert "provenance is mandatory" in str(excinfo.value)


def test_require_emission_factor_returns_resolved_factor(monkeypatch) -> None:
    monkeypatch.setattr(
        "utils.emissions.get_emission_factor",
        lambda *_a, **_k: dict(_RESOLVED_FACTOR),
    )
    factor = require_emission_factor(object(), "Electricity", 2025)
    assert factor["factor_id"] == "factor-1"
    assert factor["multiplier"] == 2.5
    assert factor["resolution"] == "canonical_factor"


# ---------------------------------------------------------------------------
# path 1 — draft submit
# ---------------------------------------------------------------------------


def _draft_world():
    return FakeSupabase(
        {
            "draft_entries": [
                {
                    "id": "draft-1",
                    "user_id": "user-1",
                    "organization_id": "org-a",
                    "file_id": "file-1",
                    "data": {
                        "fuel_utility_type": "Electricity",
                        "consumption": "1000",
                        "billing_start": "2025-03-31",
                        "reporting_year": 2025,
                        "asset_name": "Main Office",
                    },
                    "progress": 100,
                }
            ],
            "organization_files": [{"id": "file-1", "status": "ready_for_review"}],
            "assets": [{"id": "asset-1", "name": "Main Office"}],
        }
    )


def test_f04_draft_submit_is_blocked_without_a_factor(monkeypatch) -> None:
    from routes import drafts

    client = _draft_world()
    monkeypatch.setattr(drafts, "get_supabase_client", lambda: client)

    def _blocked(*_args, **_kwargs):
        raise FactorUnresolvedBlocked("no factor")

    monkeypatch.setattr(drafts, "require_emission_factor", _blocked)

    with pytest.raises(HTTPException) as excinfo:
        _run(drafts.submit_draft("draft-1", {}, _member_user()))

    assert excinfo.value.status_code == 409
    assert FACTOR_BLOCKED_CODE in str(excinfo.value.detail)
    # Nothing was written or destroyed: no emissions row, no approval, and the
    # draft survives so the operator can fix the mapping and re-submit.
    assert client.inserted("emissions_logs") == []
    assert client.updated_tables() == []
    assert client.deletes == []
    assert len(client.tables["draft_entries"]) == 1


def test_f04_draft_submit_records_resolved_factor_provenance(monkeypatch) -> None:
    from routes import drafts

    client = _draft_world()
    monkeypatch.setattr(drafts, "get_supabase_client", lambda: client)
    monkeypatch.setattr(
        drafts, "require_emission_factor", lambda *_a, **_k: dict(_RESOLVED_FACTOR)
    )

    result = _run(drafts.submit_draft("draft-1", {}, _member_user()))
    assert result["success"] is True

    rows = list(client.tables["emissions_logs"])
    assert len(rows) == 1
    row = rows[0]
    assert row["emission_factor_id"] == "factor-1"
    # 1000 kWh × the RESOLVED multiplier — never the removed 2.68 default.
    assert row["calculated_kg_co2e"] == 2500.0
    metadata = row["metadata"]
    assert metadata["multiplier_used"] == 2.5
    assert metadata["reporting_year"] == 2025
    assert metadata["factor_resolution"] == "canonical_factor"
    assert metadata["factor_kind"] == "carbontally_factor"
    assert metadata["factor_source"] == "DEFRA-DESNZ"


# ---------------------------------------------------------------------------
# path 2 — customer document review/approve
# ---------------------------------------------------------------------------


def _document_world():
    return FakeSupabase(
        {
            "organization_members": [
                {"id": "member-1", "organization_id": "org-a", "user_id": "user-1"}
            ],
            "organization_files": [
                {
                    "id": "file-1",
                    "organization_id": "org-a",
                    "status": "ready_for_review",
                    "customer_documents": {"id": "cdoc-1", "asset_id": "asset-1"},
                    "metadata": {
                        "extraction_result": {
                            "fuel_utility_type": "Electricity",
                            "consumption": "1000",
                            "billing_start": "2025-03-31",
                            "reporting_year": 2025,
                        }
                    },
                }
            ],
            "assets": [{"id": "asset-1", "name": "Main Office"}],
        }
    )


def _review_request(action="approve"):
    from routes.documents_main import CustomerReviewRequest

    return CustomerReviewRequest(action=action, notes="looks right")


def test_f04_document_approval_is_blocked_without_a_factor(monkeypatch) -> None:
    from routes import documents_main

    client = _document_world()
    monkeypatch.setattr(documents_main, "get_supabase_client", lambda: client)

    def _blocked(*_args, **_kwargs):
        raise FactorUnresolvedBlocked("no factor")

    monkeypatch.setattr(documents_main, "require_emission_factor", _blocked)

    with pytest.raises(HTTPException) as excinfo:
        _run(
            documents_main.customer_review_document(
                "org-a", "file-1", _review_request(), _member_user()
            )
        )

    assert excinfo.value.status_code == 409
    assert FACTOR_BLOCKED_CODE in str(excinfo.value.detail)
    # The document was NOT marked approved and no emissions row exists.
    assert client.updated_tables() == []
    assert client.inserted("emissions_logs") == []


def test_f04_document_approval_records_resolved_factor_provenance(monkeypatch) -> None:
    from routes import documents_main

    client = _document_world()
    monkeypatch.setattr(documents_main, "get_supabase_client", lambda: client)
    monkeypatch.setattr(
        documents_main,
        "require_emission_factor",
        lambda *_a, **_k: dict(_RESOLVED_FACTOR),
    )

    result = _run(
        documents_main.customer_review_document(
            "org-a", "file-1", _review_request(), _member_user()
        )
    )
    assert result["success"] is True
    assert result["status"] == "approved"

    rows = list(client.tables["emissions_logs"])
    assert len(rows) == 1
    row = rows[0]
    assert row["emission_factor_id"] == "factor-1"
    assert row["calculated_kg_co2e"] == 2500.0
    assert row["metadata"]["multiplier_used"] == 2.5
    assert row["metadata"]["factor_resolution"] == "canonical_factor"
    assert row["metadata"]["factor_source"] == "DEFRA-DESNZ"



# ---------------------------------------------------------------------------
# path 3 — admin extraction approval
# ---------------------------------------------------------------------------


def _extraction_client():
    return FakeSupabase(
        {
            "assets": [{"id": "asset-1", "name": "Main Office"}],
            # D-3 (CT-FINAL-01): the approval now reads the work item it is
            # approving (the queue row is the approval subject) before it writes
            # anything, so the world must contain the referenced review item.
            "manual_review_queue": [
                {
                    "id": "review-1",
                    "organization_id": "org-a",
                    "status": "pending",
                    "completed_at": None,
                    "completed_by": None,
                    "data_entry": {"note": "reviewer draft"},
                }
            ],
        }
    )


def _approval_request():
    from routes.admin.extraction import ExtractionApprovalRequest

    return ExtractionApprovalRequest(
        review_id="review-1",
        organization_id="org-a",
        extraction_result={
            "billing_start": "2025-03-31",
            "consumption": 1000,
            "fuel_utility_type": "Electricity",
            "asset_name": "Main Office",
        },
    )


def test_f04_admin_extraction_approval_is_blocked_without_a_factor(monkeypatch) -> None:
    from routes.admin import extraction

    client = _extraction_client()
    monkeypatch.setattr(extraction, "get_supabase_client", lambda: client)

    async def _blocked(**_kwargs):
        raise FactorUnresolvedBlocked("no factor")

    monkeypatch.setattr(extraction, "calculate_emissions_with_defra", _blocked)

    with pytest.raises(HTTPException) as excinfo:
        _run(extraction.approve_extraction(_approval_request(), _admin_user()))

    assert excinfo.value.status_code == 409
    assert FACTOR_BLOCKED_CODE in str(excinfo.value.detail)
    assert client.inserted("emissions_logs") == []
    assert client.updated_tables() == []


def test_f04_admin_extraction_approval_records_resolved_factor_provenance(
    monkeypatch,
) -> None:
    from routes.admin import extraction

    client = _extraction_client()
    monkeypatch.setattr(extraction, "get_supabase_client", lambda: client)

    async def _calculated(**_kwargs):
        return {
            "reporting_year": 2025,
            "multiplier_used": 2.5,
            "calculated_kg_co2e": 2500.0,
            "is_fallback": False,
            "factor_id": "factor-1",
        }

    monkeypatch.setattr(extraction, "calculate_emissions_with_defra", _calculated)
    monkeypatch.setattr(
        extraction, "require_emission_factor", lambda *_a, **_k: dict(_RESOLVED_FACTOR)
    )

    result = _run(extraction.approve_extraction(_approval_request(), _admin_user()))
    assert result.success is True

    rows = list(client.tables["emissions_logs"])
    assert len(rows) == 1
    metadata = rows[0]["metadata"]
    assert rows[0]["emission_factor_id"] == "factor-1"
    assert metadata["multiplier_used"] == 2.5
    assert metadata["factor_resolution"] == "canonical_factor"
    assert metadata["factor_source"] == "DEFRA-DESNZ"
    assert metadata["factor_kind"] == "carbontally_factor"


# ---------------------------------------------------------------------------
# source-level guarantees (the fabricated default must never come back)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", _WRITE_PATH_FILES)
def test_write_paths_use_the_blocking_resolver(relative_path: str) -> None:
    text = (_REPO_ROOT / relative_path).read_text(encoding="utf-8")
    assert "require_emission_factor" in text
    assert "FactorUnresolved" in text


@pytest.mark.parametrize("relative_path", _WRITE_PATH_FILES)
def test_write_paths_contain_no_fabricated_multiplier(relative_path: str) -> None:
    """The removed ``2.68`` fallback must not be reintroduced as CODE (F-04).

    The number may still appear in an explanatory comment recording why it was
    removed; a literal in executable code (or a string constant) is a failure.
    """
    import ast

    text = (_REPO_ROOT / relative_path).read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, float) and abs(node.value - 2.68) < 1e-9:
                raise AssertionError(f"{relative_path} still contains the 2.68 literal")
            if isinstance(node.value, str) and "2.68" in node.value:
                raise AssertionError(
                    f"{relative_path} embeds 2.68 in a string constant"
                )
    for line in text.splitlines():
        if "2.68" in line and not line.lstrip().startswith("#"):
            raise AssertionError(f"{relative_path} mentions 2.68 outside a comment")


@pytest.mark.parametrize("relative_path", _WRITE_PATH_FILES)
def test_write_paths_never_persist_a_null_factor_reference(relative_path: str) -> None:
    text = (_REPO_ROOT / relative_path).read_text(encoding="utf-8")
    assert "'emission_factor_id': None" not in text
    assert '"emission_factor_id": None' not in text
