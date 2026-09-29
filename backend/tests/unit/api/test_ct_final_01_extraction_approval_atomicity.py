"""CT-FINAL-01 D-3 — the admin extraction approval must be atomic.

CT-VERIFY-06 §19 D-3 reproduced this at runtime::

    POST /api/admin/extraction/approve   (resolvable factor)
      → emissions_logs row WRITTEN
      → PGRST204 "Could not find the 'approved_at' column of 'manual_review_queue'"
      → HTTP 500 after a committed write

Two defects, both fixed in ``routes/admin/extraction.py``:

* **data model** — ``manual_review_queue`` has no ``approved_at`` /
  ``approved_by`` / ``emission_log_id`` column, so the work-item update could
  never succeed.  The approval now writes only canonical columns
  (``status`` / ``completed_at`` / ``completed_by``) and records the approval
  provenance inside the existing ``data_entry`` JSONB column.
* **atomicity** — the work item is marked complete *before* the emissions row is
  written, and any failure afterwards is compensated for, so an approval either
  completes completely or leaves no side effect (AGENTS.md #17/#74).

Everything here is DB-free: the service-role client is replaced by a fake that
mirrors PostgREST semantics (``maybe_single`` → row or ``None``;
``Prefer: return=representation`` → the affected rows), and the column set the
handler writes is checked against the migration that defines the table.
"""
from __future__ import annotations

import asyncio
import pathlib
import re

import pytest
from fastapi import HTTPException

from auth import AuthUser
from utils.emissions import FACTOR_BLOCKED_CODE, FactorUnresolvedBlocked

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
INIT_MIGRATION = REPO_ROOT / "supabase" / "migrations" / "00000000000000_init_schema.sql"
ENTITY_MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260810010000_v3m2_entity_relationships.sql"
)

_RESOLVED_FACTOR = {
    "multiplier": 2.5,
    "reporting_year": 2025,
    "factor_id": "factor-1",
    "is_fallback": False,
    "factor_kind": "carbontally_factor",
    "factor_source": "DEFRA-DESNZ",
    "resolution": "canonical_factor",
    "customer_factor_id": None,
}


def _canonical_review_columns() -> set[str]:
    """The real ``manual_review_queue`` column set, read from the migrations."""
    sql = INIT_MIGRATION.read_text(encoding="utf-8")
    match = re.search(
        r"CREATE TABLE public\.manual_review_queue \((.*?)\n\);", sql, re.DOTALL
    )
    assert match, "manual_review_queue definition not found in the init migration"
    columns = set()
    for line in match.group(1).splitlines():
        line = line.strip().rstrip(",")
        if not line or line.upper().startswith(("CONSTRAINT", "PRIMARY KEY", "FOREIGN KEY")):
            continue
        columns.add(line.split()[0].lower())
    # Later migrations may add columns (v3m2 adds entity_id).
    alt = ENTITY_MIGRATION.read_text(encoding="utf-8")
    for added in re.findall(
        r"ALTER TABLE public\.manual_review_queue\s+ADD COLUMN IF NOT EXISTS (\w+)", alt
    ):
        columns.add(added.lower())
    return columns


# ---------------------------------------------------------------------------
# PostgREST-shaped fake with injectable failures
# ---------------------------------------------------------------------------


class _Result:
    def __init__(self, data, count=None):
        self.data = data
        self.count = count


class _Query:
    def __init__(self, client, table):
        self._client = client
        self._table = table
        self._filters = []
        self._payload = None
        self._op = "select"
        self._single = False

    def select(self, _columns="*"):
        return self

    def eq(self, column, value):
        self._filters.append((column, value))
        return self

    def maybe_single(self):
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

    def _matching_rows(self):
        rows = self._client.tables.get(self._table, [])
        for column, value in self._filters:
            rows = [r for r in rows if r.get(column) == value]
        return rows

    def execute(self):
        if self._op == "insert":
            self._client.inserts.append((self._table, dict(self._payload)))
            if self._table in self._client.fail_inserts:
                raise self._client.fail_inserts[self._table]
            row = dict(self._payload)
            row.setdefault("id", f"{self._table}-1")
            self._client.tables.setdefault(self._table, []).append(row)
            return _Result([row])

        if self._op == "update":
            self._client.update_calls += 1
            self._client.updates.append((self._table, dict(self._payload)))
            if self._client.update_calls in self._client.fail_update_calls:
                raise RuntimeError("simulated update failure")
            matched = []
            for row in self._matching_rows():
                row.update(self._payload)
                matched.append(dict(row))
            # supabase-py sends ``Prefer: return=representation`` on writes, so
            # an empty result genuinely means "no row matched".
            return _Result(matched)

        if self._op == "delete":
            self._client.deletes.append(self._table)
            matched = self._matching_rows()
            remaining = [
                r for r in self._client.tables.get(self._table, []) if r not in matched
            ]
            self._client.tables[self._table] = remaining
            return _Result(matched)

        rows = [dict(r) for r in self._matching_rows()]
        if self._single:
            return _Result(rows[0] if rows else None)
        return _Result(rows)


class FakeSupabase:
    def __init__(self, tables=None, *, fail_inserts=None, fail_update_calls=()):
        self.tables = {
            name: [dict(r) for r in rows] for name, rows in (tables or {}).items()
        }
        self.inserts = []
        self.updates = []
        self.deletes = []
        self.update_calls = 0
        self.fail_inserts = dict(fail_inserts or {})
        self.fail_update_calls = set(fail_update_calls)

    def from_(self, table):
        return _Query(self, table)

    def queue_updates(self):
        return [
            payload for table, payload in self.updates if table == "manual_review_queue"
        ]

    def emissions_rows(self):
        return list(self.tables.get("emissions_logs", []))

    def review_row(self, review_id="review-1"):
        for row in self.tables.get("manual_review_queue", []):
            if row["id"] == review_id:
                return row
        return None



def _run(coro):
    return asyncio.run(coro)


def _admin_user():
    return AuthUser(
        user_id="admin-1",
        email="admin@carbontally.test",
        role="admin",
        role_name="admin",
        is_staff=True,
        is_admin=True,
    )


def _approval_request(review_id="review-1", organization_id="org-a"):
    from routes.admin.extraction import ExtractionApprovalRequest

    return ExtractionApprovalRequest(
        review_id=review_id,
        organization_id=organization_id,
        extraction_result={
            "billing_start": "2025-03-31",
            "consumption": 1000,
            "fuel_utility_type": "Electricity",
            "asset_name": "Main Office",
        },
    )


def _world(**kwargs):
    tables = {
        "assets": [{"id": "asset-1", "name": "Main Office"}],
        "manual_review_queue": [
            {
                "id": "review-1",
                "organization_id": "org-a",
                "status": "pending",
                "completed_at": None,
                "completed_by": None,
                "data_entry": {"reviewer_note": "kept"},
            }
        ],
    }
    return FakeSupabase(tables, **kwargs)


def _wire(monkeypatch, client):
    from routes.admin import extraction

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
    return extraction



# ---------------------------------------------------------------------------
# schema parity — the approval may only write columns that exist
# ---------------------------------------------------------------------------


def test_manual_review_queue_has_no_approved_columns() -> None:
    """The D-3 root cause: these columns do not exist on the work-item table."""
    columns = _canonical_review_columns()
    assert "approved_at" not in columns
    assert "approved_by" not in columns
    assert "emission_log_id" not in columns
    # The columns the corrected handler writes DO exist.
    assert {"status", "completed_at", "completed_by", "data_entry"} <= columns


def test_approval_writes_only_canonical_queue_columns(monkeypatch) -> None:
    client = _world()
    extraction = _wire(monkeypatch, client)

    result = _run(extraction.approve_extraction(_approval_request(), _admin_user()))
    assert result.success is True
    assert result.review_status == "approved"

    payloads = client.queue_updates()
    assert payloads, "the work item must be marked complete"
    canonical = _canonical_review_columns()
    for payload in payloads:
        unknown = set(payload) - canonical
        assert not unknown, f"wrote non-existent column(s): {sorted(unknown)}"


def test_approval_records_provenance_and_preserves_reviewer_data(monkeypatch) -> None:
    client = _world()
    extraction = _wire(monkeypatch, client)

    _run(extraction.approve_extraction(_approval_request(), _admin_user()))

    row = client.review_row()
    assert row["status"] == "approved"
    assert row["completed_by"] == "admin-1"
    assert row["completed_at"]
    # The reviewer's existing data_entry content survives (non-destructive).
    assert row["data_entry"]["reviewer_note"] == "kept"
    approval = row["data_entry"]["approval"]
    assert approval["approved_by"] == "admin-1"
    assert approval["approved_at"]
    assert approval["emission_log_id"] == "emissions_logs-1"

    rows = client.emissions_rows()
    assert len(rows) == 1
    assert rows[0]["emission_factor_id"] == "factor-1"
    assert rows[0]["calculated_kg_co2e"] == 2500.0
    assert rows[0]["metadata"]["review_id"] == "review-1"
    assert rows[0]["metadata"]["factor_resolution"] == "canonical_factor"



# ---------------------------------------------------------------------------
# atomicity — no partial approval side effect may survive
# ---------------------------------------------------------------------------


def test_emissions_write_failure_leaves_no_partial_approval(monkeypatch) -> None:
    """The central D-3 guarantee: a failed approval must not commit anything."""
    client = _world(
        fail_inserts={"emissions_logs": RuntimeError("simulated write failure")}
    )
    extraction = _wire(monkeypatch, client)

    with pytest.raises(HTTPException) as excinfo:
        _run(extraction.approve_extraction(_approval_request(), _admin_user()))

    assert excinfo.value.status_code == 500
    # No emissions row exists ...
    assert client.emissions_rows() == []
    # ... and the work item was rolled back to its pre-approval state.
    row = client.review_row()
    assert row["status"] == "pending"
    assert row["completed_at"] is None
    assert row["completed_by"] is None
    assert row["data_entry"] == {"reviewer_note": "kept"}


def test_committed_emissions_row_is_compensated_when_the_link_fails(
    monkeypatch,
) -> None:
    """Even the post-write linkage step is compensated, not left half-applied."""
    # update call 1 = mark the work item complete; call 2 = link the emissions id.
    client = _world(fail_update_calls={2})
    extraction = _wire(monkeypatch, client)

    with pytest.raises(HTTPException) as excinfo:
        _run(extraction.approve_extraction(_approval_request(), _admin_user()))

    assert excinfo.value.status_code == 500
    assert "rolled back" in str(excinfo.value.detail)
    # The emissions row written moments earlier was removed again.
    assert client.emissions_rows() == []
    assert "emissions_logs" in client.deletes
    row = client.review_row()
    assert row["status"] == "pending"
    assert row["data_entry"] == {"reviewer_note": "kept"}


def test_missing_review_item_is_a_404_and_writes_nothing(monkeypatch) -> None:
    client = _world()
    extraction = _wire(monkeypatch, client)

    with pytest.raises(HTTPException) as excinfo:
        _run(
            extraction.approve_extraction(
                _approval_request(review_id="review-absent"), _admin_user()
            )
        )

    assert excinfo.value.status_code == 404
    assert client.inserts == []
    assert client.queue_updates() == []


def test_review_item_from_another_organization_is_refused(monkeypatch) -> None:
    client = _world()
    client.tables["manual_review_queue"][0]["organization_id"] = "org-b"
    extraction = _wire(monkeypatch, client)

    with pytest.raises(HTTPException) as excinfo:
        _run(extraction.approve_extraction(_approval_request(), _admin_user()))

    assert excinfo.value.status_code == 403
    assert client.inserts == []
    assert client.queue_updates() == []


def test_unresolved_factor_still_blocks_before_any_write(monkeypatch) -> None:
    """F-04 is preserved by the D-3 fix (the approval never became a write-first)."""
    client = _world()
    extraction = _wire(monkeypatch, client)

    def _blocked(*_args, **_kwargs):
        raise FactorUnresolvedBlocked("no factor")

    monkeypatch.setattr(extraction, "require_emission_factor", _blocked)

    with pytest.raises(HTTPException) as excinfo:
        _run(extraction.approve_extraction(_approval_request(), _admin_user()))

    assert excinfo.value.status_code == 409
    assert FACTOR_BLOCKED_CODE in str(excinfo.value.detail)
    assert client.inserts == []
    assert client.updates == []
    row = client.review_row()
    assert row["status"] == "pending"


def test_every_approval_is_tied_to_a_work_item(monkeypatch) -> None:
    """The contract requires ``review_id``, so a 404 is the correct terminal state
    for an unknown work item rather than a silent write (see the 404 test)."""
    from pydantic import ValidationError

    from routes.admin.extraction import ExtractionApprovalRequest

    with pytest.raises(ValidationError):
        ExtractionApprovalRequest(
            organization_id="org-a",
            extraction_result={"billing_start": "2025-03-31", "consumption": 1},
        )

