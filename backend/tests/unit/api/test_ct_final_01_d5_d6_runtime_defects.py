"""CT-FINAL-01 — CT-VERIFY-06 D-5 and D-6 regression tests (the last two 500s).

**D-5** — ``POST /api/documents/{org_id}/{file_id}/review`` embedded
``customer_documents`` from ``organization_files`` even though **no foreign key
links those tables**, so PostgREST answered ``PGRST200 … Could not find a
relationship`` and the handler converted it into HTTP 500.  The same handler also
read ``.get('customer_documents', {})`` and then called ``.get()`` on a ``NULL``
relation (``AttributeError`` → the same 500).  The review route is now reachable
for valid same-tenant data, without fabricating a ``customer_documents`` object
and without an interaction between ``organization_files`` and
``customer_documents`` being invented.

**D-6** — ``GET /api/admin/defra/factors/{deleted_id}`` returned 500 instead of
404: ``maybe_single().execute()`` returns ``None`` (not a response object) when
no row matches, and ``None.data`` is an ``AttributeError``.  A missing factor is
a 404 — for read, update and delete alike.

Everything here is DB-free: the service-role client is faked to PostgREST
semantics, including the PGRST200 relationship error and the ``None`` return.
"""
from __future__ import annotations

import asyncio
import pathlib

import pytest
from fastapi import HTTPException

from auth import AuthUser
from utils.emissions import FactorUnresolvedBlocked

BACKEND = pathlib.Path(__file__).resolve().parents[3]

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

_EMBED_ERROR = (
    "PGRST200: Could not find a relationship between 'organization_files' and "
    "'customer_documents' in the schema cache"
)


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
        self._select_text = "*"

    def select(self, text="*", **_kwargs):
        self._select_text = text
        if "customer_documents (" in text and self._client.reject_embed:
            # A real database without the FK answers exactly this way.
            raise RuntimeError(_EMBED_ERROR)
        return self

    def eq(self, column, value):
        self._filters.append((column, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def range(self, *_args, **_kwargs):
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

    def _matching(self):
        rows = self._client.tables.get(self._table, [])
        for column, value in self._filters:
            rows = [r for r in rows if r.get(column) == value]
        return rows

    def execute(self):
        if self._op == "insert":
            self._client.inserts.append((self._table, dict(self._payload)))
            row = dict(self._payload)
            row.setdefault("id", f"{self._table}-1")
            self._client.tables.setdefault(self._table, []).append(row)
            return _Result([row])
        if self._op == "update":
            self._client.updates.append((self._table, dict(self._payload)))
            matched = []
            for row in self._matching():
                row.update(self._payload)
                matched.append(dict(row))
            return _Result(matched)
        if self._op == "delete":
            self._client.deletes.append(self._table)
            matched = self._matching()
            remaining = [
                r for r in self._client.tables.get(self._table, []) if r not in matched
            ]
            self._client.tables[self._table] = remaining
            return _Result(matched)

        rows = [dict(r) for r in self._matching()]
        if self._single:
            # postgrest: no row -> None (NOT a response object with data=None).
            return _Result(rows[0]) if rows else None
        return _Result(rows)


class FakeSupabase:
    def __init__(self, tables=None, *, reject_embed=False):
        self.tables = {
            name: [dict(r) for r in rows] for name, rows in (tables or {}).items()
        }
        self.reject_embed = reject_embed
        self.inserts = []
        self.updates = []
        self.deletes = []

    def from_(self, table):
        return _Query(self, table)

    def updated_tables(self):
        return [table for table, _payload in self.updates]

    def rows(self, table):
        return list(self.tables.get(table, []))


def _run(coro):
    return asyncio.run(coro)


def _member():
    return AuthUser(
        user_id="user-1",
        email="member@carbontally.test",
        role="user",
        role_name="user",
        organization_id="org-a",
        is_org_member=True,
    )


def _admin():
    return AuthUser(
        user_id="admin-1",
        email="admin@carbontally.test",
        role="admin",
        role_name="admin",
        is_staff=True,
        is_admin=True,
    )


# ---------------------------------------------------------------------------
# D-5 — the document-review route (PGRST200 on the absent embed relation)
# ---------------------------------------------------------------------------


def _document_world(*, reject_embed: bool, linked: dict | None = None):
    file_row = {
        "id": "file-1",
        "organization_id": "org-a",
        "status": "ready_for_review",
        "name": "meter.pdf",
        "file_type": "PDF",
        "metadata": {
            "extraction_result": {
                "fuel_utility_type": "Electricity",
                "consumption": "1000",
                "billing_start": "2025-03-31",
                "asset_name": "Main Office",
            }
        },
    }
    if linked is not None:
        file_row["customer_documents"] = linked
    return FakeSupabase(
        {
            "organization_members": [
                {"id": "member-1", "organization_id": "org-a", "user_id": "user-1"}
            ],
            "organization_files": [file_row],
            "assets": [{"id": "asset-1", "name": "Main Office", "organization_id": "org-a"}],
        },
        reject_embed=reject_embed,
    )


def _wire_documents(monkeypatch, client):
    from routes import documents_main

    monkeypatch.setattr(documents_main, "get_supabase_client", lambda: client)
    monkeypatch.setattr(
        documents_main,
        "require_emission_factor",
        lambda *_a, **_k: dict(_RESOLVED_FACTOR),
    )
    return documents_main


def test_the_original_embed_reproduces_the_runtime_relationship_error() -> None:
    """The defect must stay reproducible in the fake (no silent false pass)."""
    client = _document_world(reject_embed=True)
    with pytest.raises(RuntimeError) as excinfo:
        client.from_("organization_files").select(
            "*, customer_documents (id, asset_id)"
        ).eq("id", "file-1").maybe_single().execute()
    assert "PGRST200" in str(excinfo.value)


def test_document_approval_completes_without_the_embed_relationship(monkeypatch) -> None:
    """D-5: valid same-tenant review data must succeed, not 500."""
    from routes.documents_main import CustomerReviewRequest

    client = _document_world(reject_embed=True)
    documents_main = _wire_documents(monkeypatch, client)

    result = _run(
        documents_main.customer_review_document(
            "org-a",
            "file-1",
            CustomerReviewRequest(action="approve", notes="ok"),
            _member(),
        )
    )

    assert result["success"] is True
    # The work completed: the document is approved and the emissions row exists.
    assert client.rows("organization_files")[0]["status"] == "approved"
    emissions = client.rows("emissions_logs")
    assert len(emissions) == 1
    assert emissions[0]["emission_factor_id"] == "factor-1"
    assert emissions[0]["calculated_kg_co2e"] == 2500.0
    # No customer_documents object was fabricated, so no link was written either.
    assert "customer_documents" not in client.updated_tables()


def test_document_approval_survives_a_null_customer_documents_relation(
    monkeypatch,
) -> None:
    """F-05-R4 on this route: a NULL embed must not raise AttributeError."""
    from routes.documents_main import CustomerReviewRequest

    client = _document_world(reject_embed=False, linked=None)
    client.tables["organization_files"][0]["customer_documents"] = None
    documents_main = _wire_documents(monkeypatch, client)

    result = _run(
        documents_main.customer_review_document(
            "org-a",
            "file-1",
            CustomerReviewRequest(action="approve", notes="ok"),
            _member(),
        )
    )
    assert result["success"] is True
    assert len(client.rows("emissions_logs")) == 1


def test_document_approval_still_uses_a_present_relation(monkeypatch) -> None:
    """A link that does exist keeps its existing semantics (status propagated)."""
    from routes.documents_main import CustomerReviewRequest

    client = _document_world(
        reject_embed=False, linked={"id": "cdoc-1", "asset_id": "asset-1"}
    )
    # The linked customer_documents row exists (as it would in a database that
    # does maintain the relationship), so propagation is observable.
    client.tables["customer_documents"] = [{"id": "cdoc-1", "status": "manual_review"}]
    documents_main = _wire_documents(monkeypatch, client)

    result = _run(
        documents_main.customer_review_document(
            "org-a",
            "file-1",
            CustomerReviewRequest(action="approve", notes="ok"),
            _member(),
        )
    )
    assert result["success"] is True
    assert "customer_documents" in client.updated_tables()
    customer_docs = client.rows("customer_documents")
    assert customer_docs and customer_docs[0]["status"] == "approved"


def test_document_approval_is_still_blocked_without_a_factor(monkeypatch) -> None:
    """F-04 is unaffected by the D-5 change."""
    from routes.documents_main import CustomerReviewRequest

    client = _document_world(reject_embed=True)
    documents_main = _wire_documents(monkeypatch, client)

    def _blocked(*_args, **_kwargs):
        raise FactorUnresolvedBlocked("no factor")

    monkeypatch.setattr(documents_main, "require_emission_factor", _blocked)

    with pytest.raises(HTTPException) as excinfo:
        _run(
            documents_main.customer_review_document(
                "org-a",
                "file-1",
                CustomerReviewRequest(action="approve", notes="ok"),
                _member(),
            )
        )
    assert excinfo.value.status_code == 409
    assert client.rows("emissions_logs") == []
    assert client.updates == []



def test_status_update_route_survives_the_absent_embed(monkeypatch) -> None:
    """The sibling status route had the same embed defect."""
    from routes.documents_main import DocumentStatusUpdateRequest

    client = _document_world(reject_embed=True)
    client.tables["organization_files"][0]["status"] = "uploaded"
    documents_main = _wire_documents(monkeypatch, client)

    result = _run(
        documents_main.update_document_status(
            "org-a",
            "file-1",
            DocumentStatusUpdateRequest(status="staff_review"),
            _admin(),
        )
    )
    assert result["success"] is True
    assert result["new_status"] == "staff_review"
    assert result["customer_document_id"] is None


# ---------------------------------------------------------------------------
# D-6 — admin factor management: a missing factor is a 404, never a 500
# ---------------------------------------------------------------------------


def _factor_world(*, factor_present: bool = True):
    tables = {"emission_factors": []}
    if factor_present:
        tables["emission_factors"] = [
            {
                "id": "factor-1",
                "activity_type": "Electricity (kWh, UK grid)",
                "co2e_multiplier": 0.20707,
                "reporting_year": 2025,
                "unit": "kWh",
                "scope": "Scope 2",
                "country": "GB",
                "factor_source": "DEFRA-DESNZ",
                "factor_set": "DEFRA-2025",
            }
        ]
    return FakeSupabase(tables)


def _wire_defra(monkeypatch, client):
    from routes.admin import defra

    monkeypatch.setattr(defra, "get_supabase_client", lambda: client)
    return defra


def test_unknown_factor_get_returns_404_not_500(monkeypatch) -> None:
    defra = _wire_defra(monkeypatch, _factor_world(factor_present=False))

    with pytest.raises(HTTPException) as excinfo:
        _run(defra.get_admin_defra_factor("deleted-factor", _admin()))

    assert excinfo.value.status_code == 404
    assert "not found" in str(excinfo.value.detail).lower()


def test_known_factor_get_returns_the_factor(monkeypatch) -> None:
    defra = _wire_defra(monkeypatch, _factor_world())

    result = _run(defra.get_admin_defra_factor("factor-1", _admin()))

    assert result.id == "factor-1"
    assert result.co2e_multiplier == 0.20707


def test_unknown_factor_delete_returns_404_not_500(monkeypatch) -> None:
    client = _factor_world(factor_present=False)
    defra = _wire_defra(monkeypatch, client)

    with pytest.raises(HTTPException) as excinfo:
        _run(defra.delete_defra_factor("deleted-factor", _admin(), object()))

    assert excinfo.value.status_code == 404
    assert client.deletes == []


def test_unknown_factor_update_returns_404_not_500(monkeypatch) -> None:
    from routes.admin.defra import DEFRAFactorUpdate

    defra = _wire_defra(monkeypatch, _factor_world(factor_present=False))

    with pytest.raises(HTTPException) as excinfo:
        _run(
            defra.update_defra_factor(
                "deleted-factor", DEFRAFactorUpdate(), _admin(), object()
            )
        )

    assert excinfo.value.status_code == 404

