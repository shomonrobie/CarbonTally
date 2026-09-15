"""Phase 8 B4 — approval/finalisation API (in-memory, no database access).

Locks the PO decision **`B4-D1`** (Amendment 1): only a Customer **Owner/Admin**
may approve or finalise; **consultants and CarbonTally internal staff may never**
do so — enforced server-side, not by UI.

Also locks the **`DM-5`** gate behaviour on finalisation and the S3 atomic
state guard (a concurrent caller receives ``409`` rather than clobbering state).
"""
from __future__ import annotations

from typing import Any, Optional

import pytest
from starlette.testclient import TestClient

from api.dependencies import get_current_user, get_pool, get_repositories
from api.router import create_app
from api.v3_disclosure import get_report_artefact_storage_dep
from auth import AuthUser
from services.report_artefact_storage import InMemoryReportArtefactStorage
from tests.unit.api.fakes import (
    admin_user,
    consultant_user,
    member_user,
    org_admin_user,
    org_owner_user,
)
from tests.unit.api.route_paths import flatten_router_paths

ORG = "org-a"
RV = "rv-1"

CONTRACT_PATHS = {
    "/api/v3/reports/{report_id}/approve",
    "/api/v3/reports/{report_id}/finalise",
    "/api/v3/reports/{report_id}/finalisation-check",
    "/api/v3/reports/{report_id}/frozen-artefact",
    "/api/v3/reports/{report_id}/frozen-artefact/signed-url",
}


def _value(
    requirement_version_id: str,
    effective_class: str,
    value_status: str,
    reason: Optional[str] = None,
) -> dict:
    return {
        "requirement_version_id": requirement_version_id,
        "effective_class": effective_class,
        "value_status": value_status,
        "reason": reason,
    }


def _version_row(status: str) -> dict:
    """Row mapping as ``ReportVersionsRepository.set_status`` materialises it.

    The repository builds its result from ``dict(row)`` over the columns it
    selects, so the fake must return a mapping (not an object).
    """
    return {
        "id": RV,
        "report_id": "rep-1",
        "version_number": 1,
        "content": None,
        "file_url": None,
        "file_name": None,
        "created_by": None,
        "created_at": None,
        "notes": None,
        "change_summary": None,
        "is_current": True,
        "status": status,
    }


class _State(dict):
    pass


class _FakeConn:
    def __init__(self, state: _State) -> None:
        self._s = state
        self.calls: list[tuple[str, tuple]] = []

    async def fetchrow(self, query: str, *args: Any) -> Optional[Any]:
        q = " ".join(query.split())
        if "JOIN public.report_generation_queue" in q:
            ctx = self._s.get("context")
            return ctx
        if q.startswith("UPDATE public.report_versions"):
            self.calls.append(("set_status", args))
            if self._s.get("guard_matches") is False:
                return None
            return _version_row(str(args[2]))
        if "FROM public.report_version_artifacts" in q:
            return self._s.get("artefact")
        if q.startswith("INSERT INTO public.report_version_artifacts"):
            self.calls.append(("artefact_insert", args))
            return self._s.get("artefact_created", _artefact_row())
        if "FROM public.disclosure_values" in q and "WHERE id = $1" in q:
            return self._s.get("value")
        if q.startswith("INSERT INTO public.audit_trail"):
            self.calls.append(("audit", args))
            return _audit_row(str(args[0]))
        raise AssertionError(f"unexpected fetchrow: {q[:90]}")

    async def fetch(self, query: str, *args: Any) -> list[dict]:
        q = " ".join(query.split())
        if "FROM public.disclosure_values" in q:
            return list(self._s.get("values", []))
        raise AssertionError(f"unexpected fetch: {q[:90]}")

    async def execute(self, query: str, *args: Any) -> str:
        return "OK"


class _Acquire:
    def __init__(self, conn: _FakeConn) -> None:
        self._conn = conn

    async def __aenter__(self) -> _FakeConn:
        return self._conn

    async def __aexit__(self, *exc: Any) -> bool:
        return False


class _FakePool:
    def __init__(self, conn: _FakeConn) -> None:
        self._conn = conn

    def acquire(self) -> _Acquire:
        return _Acquire(self._conn)


def _audit_row(action: str) -> dict:
    """Minimal ``audit_trail`` row as ``AuditRepository.record`` materialises it."""
    return {
        "id": "audit-1",
        "action_type": action,
        "table_name": "test",
        "record_id": "11111111-1111-4111-8111-111111111111",
        "performed_by": "11111111-1111-4111-8111-111111111111",
        "performed_at": None,
        "old_data": None,
        "new_data": None,
        "changes": None,
        "ip_address": None,
        "metadata": None,
    }


class _Reports:
    async def get_full(self, report_id: str) -> Optional[dict]:
        return {
            "id": report_id,
            "organization_id": ORG,
            "report_type": "ANNUAL_CARBON",
            "reporting_year": 2025,
            "generated_content": {"sections": [{"title": "Emissions", "value": "2,661.55 kg CO2e"}]},
        }


class _ReportVersions:
    async def get_current(self, report_id: str) -> Optional[dict]:
        return {"id": RV}


class _Repos:
    def __init__(self) -> None:
        self.reports = _Reports()
        self.report_versions = _ReportVersions()


def _pe_staff() -> AuthUser:
    return AuthUser(
        user_id="u-pe", email="pe@carbontally.test", role="pe_staff", role_name="pe_staff",
        is_staff=True, entity_id="entity-1",
    )


def _artefact_row(*, object_key: str = f"{ORG}/rep-1/{RV}.pdf", sha: str = "a" * 64) -> dict:
    return {
        "id": "art-1",
        "organization_id": ORG,
        "report_id": "rep-1",
        "report_version_id": RV,
        "storage_bucket": "report-artifacts",
        "object_key": object_key,
        "content_sha256": sha,
        "byte_size": 1234,
        "content_type": "application/pdf",
        "produced_by": "u-owner",
        "produced_at": None,
        "created_at": None,
    }


@pytest.fixture
def b4_client(monkeypatch):
    """Client with the private-bucket storage swapped for an in-memory double.

    The renderer and brand resolver are the *existing* production ones; they are
    patched here only because unit tests must not render a real PDF.
    """
    state = _State(context={"organization_id": ORG, "report_id": "rep-1", "status": "REVIEWED", "reporting_year": 2025})
    app = create_app()
    holder: dict[str, Any] = {"user": org_owner_user(ORG, "u-owner", "owner@carbontally.test")}
    conn = _FakeConn(state)
    storage = InMemoryReportArtefactStorage()

    async def _brand(repos=None, user=None, organization_id=None):
        return type("Brand", (), {"kind": "carbontally"})()

    monkeypatch.setattr("engines.pdf_render.render_branded_pdf", lambda **kw: b"%PDF-1.7 frozen")
    monkeypatch.setattr("api.consultant_branding.resolve_report_branding", _brand)

    async def _user() -> AuthUser:
        return holder["user"]

    async def _repos() -> _Repos:
        return _Repos()

    async def _pool() -> _FakePool:
        return _FakePool(conn)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_repositories] = _repos
    app.dependency_overrides[get_pool] = _pool
    app.dependency_overrides[get_report_artefact_storage_dep] = lambda: storage
    client = TestClient(app)
    client.b4_state = state  # type: ignore[attr-defined]
    client.b4_holder = holder  # type: ignore[attr-defined]
    client.b4_conn = conn  # type: ignore[attr-defined]
    client.b4_storage = storage  # type: ignore[attr-defined]
    return client


# ---------------------------------------------------------------------------
# Route contract
# ---------------------------------------------------------------------------
def test_b4_routes_are_registered(b4_client: TestClient) -> None:
    missing = CONTRACT_PATHS - flatten_router_paths(b4_client.app)
    assert not missing, f"B4 contract routes missing: {sorted(missing)}"


# ---------------------------------------------------------------------------
# B4-D1 DENY — consultants and internal staff may NEVER approve/finalise
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("endpoint", ["approve", "finalise"])
def test_internal_staff_cannot_transition(b4_client: TestClient, endpoint: str) -> None:
    b4_client.b4_holder["user"] = admin_user()
    response = b4_client.post(f"/api/v3/reports/rep-1/{endpoint}", json={})
    assert response.status_code == 403
    assert b4_client.b4_conn.calls == []  # no transition attempted


@pytest.mark.parametrize("endpoint", ["approve", "finalise"])
def test_consultant_cannot_transition(b4_client: TestClient, endpoint: str) -> None:
    b4_client.b4_holder["user"] = consultant_user("u-cons", "consultant@carbontally.test")
    response = b4_client.post(f"/api/v3/reports/rep-1/{endpoint}", json={})
    assert response.status_code == 403
    assert b4_client.b4_conn.calls == []


@pytest.mark.parametrize("endpoint", ["approve", "finalise"])
def test_processing_entity_staff_cannot_transition(b4_client: TestClient, endpoint: str) -> None:
    b4_client.b4_holder["user"] = _pe_staff()
    response = b4_client.post(f"/api/v3/reports/rep-1/{endpoint}", json={})
    assert response.status_code == 403
    assert b4_client.b4_conn.calls == []


@pytest.mark.parametrize("endpoint", ["approve", "finalise"])
def test_org_member_cannot_transition(b4_client: TestClient, endpoint: str) -> None:
    b4_client.b4_holder["user"] = member_user(ORG, "u-member", "member@carbontally.test")
    response = b4_client.post(f"/api/v3/reports/rep-1/{endpoint}", json={})
    assert response.status_code == 403
    assert b4_client.b4_conn.calls == []


# ---------------------------------------------------------------------------
# B4-D1 ALLOW — Owner and Admin
# ---------------------------------------------------------------------------
def test_owner_can_approve_reviewed_version(b4_client: TestClient) -> None:
    response = b4_client.post("/api/v3/reports/rep-1/approve", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["previous_status"] == "REVIEWED"
    assert body["version_status"] == "APPROVED"
    assert body["actor_role"] == "owner"
    assert b4_client.b4_conn.calls[0][0] == "set_status"


def test_admin_can_approve_reviewed_version(b4_client: TestClient) -> None:
    b4_client.b4_holder["user"] = org_admin_user(ORG, "u-admin", "admin@carbontally.test")
    response = b4_client.post("/api/v3/reports/rep-1/approve", json={})
    assert response.status_code == 200
    assert response.json()["version_status"] == "APPROVED"


def test_state_machine_refuses_invalid_transition(b4_client: TestClient) -> None:
    b4_client.b4_state["context"]["status"] = "DRAFT"
    response = b4_client.post("/api/v3/reports/rep-1/approve", json={})
    assert response.status_code == 409
    assert b4_client.b4_conn.calls == []


def test_concurrent_state_change_returns_409(b4_client: TestClient) -> None:
    b4_client.b4_state["guard_matches"] = False
    response = b4_client.post("/api/v3/reports/rep-1/approve", json={})
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# DM-5 gate
# ---------------------------------------------------------------------------
def test_owner_can_finalise_when_all_resolved(b4_client: TestClient) -> None:
    b4_client.b4_state["context"]["status"] = "APPROVED"
    b4_client.b4_state["values"] = [
        _value("req-1", "REQUIRED", "RESOLVED"),
        _value("req-2", "NOT_APPLICABLE", "UNRESOLVED"),
    ]
    response = b4_client.post("/api/v3/reports/rep-1/finalise", json={})
    assert response.status_code == 200
    assert response.json()["version_status"] == "FINAL"


def test_finalisation_blocked_by_unresolved_required(b4_client: TestClient) -> None:
    b4_client.b4_state["context"]["status"] = "APPROVED"
    b4_client.b4_state["values"] = [_value("req-7", "REQUIRED", "UNRESOLVED")]
    response = b4_client.post("/api/v3/reports/rep-1/finalise", json={})
    assert response.status_code == 409
    assert "req-7" in response.json()["error"]["message"]
    assert b4_client.b4_conn.calls == []  # blocked before any transition


def test_finalisation_blocked_by_customer_input_required(b4_client: TestClient) -> None:
    b4_client.b4_state["context"]["status"] = "APPROVED"
    b4_client.b4_state["values"] = [_value("req-9", "CUSTOMER_INPUT_REQUIRED", "UNRESOLVED")]
    response = b4_client.post("/api/v3/reports/rep-1/finalise", json={})
    assert response.status_code == 409
    assert b4_client.b4_conn.calls == []


def test_not_supported_proceeds_but_is_surfaced(b4_client: TestClient) -> None:
    """DM-5: an applicable required NOT_SUPPORTED never blocks and is never hidden."""
    b4_client.b4_state["context"]["status"] = "APPROVED"
    b4_client.b4_state["values"] = [_value("req-11", "NOT_SUPPORTED", "UNRESOLVED")]
    response = b4_client.post("/api/v3/reports/rep-1/finalise", json={})
    assert response.status_code == 200
    surfaced = response.json()["surfaced_limitations"]
    assert [s["requirement_version_id"] for s in surfaced] == ["req-11"]


def test_check_reports_gate_without_transitioning(b4_client: TestClient) -> None:
    b4_client.b4_state["values"] = [
        _value("req-2", "NOT_SUPPORTED", "UNRESOLVED"),
        _value("req-3", "REQUIRED", "UNRESOLVED"),
    ]
    response = b4_client.get("/api/v3/reports/rep-1/finalisation-check")
    assert response.status_code == 200
    body = response.json()
    assert body["can_finalise"] is False
    assert body["blocking"][0]["requirement_version_id"] == "req-3"
    assert body["surfaced_limitations"][0]["requirement_version_id"] == "req-2"
    assert body["information_only"] == []
    assert b4_client.b4_conn.calls == []


def test_check_is_readable_by_member(b4_client: TestClient) -> None:
    b4_client.b4_holder["user"] = member_user(ORG, "u-member", "member@carbontally.test")
    b4_client.b4_state["values"] = [_value("req-1", "REQUIRED", "RESOLVED")]
    response = b4_client.get("/api/v3/reports/rep-1/finalisation-check")
    assert response.status_code == 200
    assert response.json()["can_finalise"] is True


def test_check_denied_for_processing_entity_staff(b4_client: TestClient) -> None:
    b4_client.b4_holder["user"] = _pe_staff()
    response = b4_client.get("/api/v3/reports/rep-1/finalisation-check")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# S5 frozen artefact mandate (B4-D5/D6/D7)
# ---------------------------------------------------------------------------
def _frozen_client(b4_client, state_artifact=None):
    b4_client.b4_state["context"]["status"] = "APPROVED"
    b4_client.b4_state["values"] = [
        _value("req-1", "REQUIRED", "RESOLVED"),
        _value("req-2", "NOT_SUPPORTED", "UNRESOLVED"),
    ]
    if state_artifact is not None:
        b4_client.b4_state["artefact"] = state_artifact
    return b4_client


def test_finalise_freezes_the_artefact_before_the_final_state(b4_client: TestClient) -> None:
    """The mandatory artefact is rendered, stored privately and recorded (B4-D5/D6/D7)."""
    _frozen_client(b4_client)
    response = b4_client.post("/api/v3/reports/rep-1/finalise", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["version_status"] == "FINAL"
    frozen = body["frozen_artefact"]
    # The key is derived, never supplied (B4-D6).
    assert frozen["object_key"] == f"{ORG}/rep-1/{RV}.pdf"
    assert frozen["storage_bucket"] == "report-artifacts"
    assert len(frozen["content_sha256"]) == 64
    # The object exists in the (private) bucket double, exactly once.
    storage = b4_client.b4_storage
    assert list(storage.objects) == [f"{ORG}/rep-1/{RV}.pdf"]
    assert storage.uploads[0]["content_type"] == "application/pdf"
    kinds = [c[0] for c in b4_client.b4_conn.calls if c[0] != "audit"]
    assert kinds == ["artefact_insert", "set_status"]  # freeze BEFORE the transition


def test_finalise_refused_when_rendering_fails(b4_client: TestClient, monkeypatch) -> None:
    _frozen_client(b4_client)

    def _boom(**kwargs):
        raise RuntimeError("renderer exploded with a secret path /tmp/private")

    monkeypatch.setattr("engines.pdf_render.render_branded_pdf", _boom)
    response = b4_client.post("/api/v3/reports/rep-1/finalise", json={})
    assert response.status_code == 503
    # No transition, no artefact record, and no renderer internals leaked.
    assert b4_client.b4_conn.calls == []
    assert b4_client.b4_storage.objects == {}
    assert "secret path" not in response.text


def test_finalise_refused_when_report_has_no_content(b4_client: TestClient, monkeypatch) -> None:
    _frozen_client(b4_client)

    class _Empty:
        async def get_full(self, report_id: str):
            return {"id": report_id, "organization_id": ORG, "generated_content": {}}

    monkeypatch.setattr(
        "api.v3_disclosure._branded_pdf_producer",
        lambda repos, user, report: _raise_empty,  # the producer returns the failing coroutine
    )
    response = b4_client.post("/api/v3/reports/rep-1/finalise", json={})
    assert response.status_code == 409
    assert b4_client.b4_conn.calls == []


async def _raise_empty():
    from domain.disclosure import DisclosureViolation

    raise DisclosureViolation("report has no generated content to freeze")


def test_finalise_refused_when_storage_upload_fails(b4_client: TestClient, monkeypatch) -> None:
    _frozen_client(b4_client)

    class _Failing:
        def exists(self, *, object_key: str) -> bool:
            return False

        def upload(self, *, object_key: str, payload: bytes, content_type: str = "application/pdf") -> None:
            raise OSError("storage unavailable")

        def signed_url(self, *, object_key: str, expires_in: int = 300) -> str:
            raise OSError("storage unavailable")

    from api.v3_disclosure import get_report_artefact_storage_dep as dep

    b4_client.app.dependency_overrides[dep] = lambda: _Failing()
    response = b4_client.post("/api/v3/reports/rep-1/finalise", json={})
    assert response.status_code == 503
    assert b4_client.b4_conn.calls == []  # nothing transitioned


def test_finalise_refused_when_existing_artefact_hash_differs(b4_client: TestClient) -> None:
    """A frozen artefact is never rewritten (D15/DM-7) — a changed render is refused."""
    _frozen_client(b4_client, state_artifact=_artefact_row(sha="b" * 64))
    response = b4_client.post("/api/v3/reports/rep-1/finalise", json={})
    assert response.status_code == 409
    assert b4_client.b4_conn.calls == []


def test_existing_matching_artefact_is_reused_without_reupload(b4_client: TestClient) -> None:
    import hashlib

    payload = b"%PDF-1.7 frozen"
    sha = hashlib.sha256(payload).hexdigest()
    _frozen_client(b4_client, state_artifact=_artefact_row(sha=sha))
    response = b4_client.post("/api/v3/reports/rep-1/finalise", json={})
    assert response.status_code == 200
    # Reused, not rewritten: no upload and no insert.
    assert b4_client.b4_storage.uploads == []
    kinds = [c[0] for c in b4_client.b4_conn.calls if c[0] != "audit"]
    assert kinds == ["set_status"]


def test_frozen_artefact_metadata_never_returns_a_url(b4_client: TestClient) -> None:
    b4_client.b4_state["artefact"] = _artefact_row()
    response = b4_client.get("/api/v3/reports/rep-1/frozen-artefact")
    assert response.status_code == 200
    body = response.json()
    assert body["frozen"] is True
    assert body["artefact"]["object_key"] == f"{ORG}/rep-1/{RV}.pdf"
    assert "signed_url" not in body


def test_signed_url_requires_an_existing_artefact(b4_client: TestClient) -> None:
    response = b4_client.post("/api/v3/reports/rep-1/frozen-artefact/signed-url", json={})
    assert response.status_code == 404


def test_signed_url_is_short_lived(b4_client: TestClient) -> None:
    key = f"{ORG}/rep-1/{RV}.pdf"
    b4_client.b4_state["artefact"] = _artefact_row()
    b4_client.b4_storage.objects[key] = b"%PDF-1.7 frozen"
    response = b4_client.post("/api/v3/reports/rep-1/frozen-artefact/signed-url", json={})
    assert response.status_code == 200
    assert response.json()["expires_in"] == 300
    assert str(response.json()["signed_url"]).startswith("https://")


@pytest.mark.parametrize(
    "path",
    ["frozen-artefact", "frozen-artefact/signed-url"],
)
def test_pe_and_staff_denied_on_artefact_routes(b4_client: TestClient, path: str) -> None:
    for user in (_pe_staff(), admin_user()):
        b4_client.b4_holder["user"] = user
        url = f"/api/v3/reports/rep-1/{path}"
        response = b4_client.get(url) if path == "frozen-artefact" else b4_client.post(url, json={})
        assert response.status_code == 403, f"{path} not denied for {user.role}"


# ---------------------------------------------------------------------------
# A10 — every B4 write is audited (append-only audit_trail)
# ---------------------------------------------------------------------------
def test_approve_and_finalise_are_audited(b4_client: TestClient) -> None:
    _frozen_client(b4_client)
    b4_client.b4_state["context"]["status"] = "REVIEWED"
    assert b4_client.post("/api/v3/reports/rep-1/approve", json={}).status_code == 200
    kinds = [c[0] for c in b4_client.b4_conn.calls]
    assert "audit" in kinds, "the approval transition must be audited"

    b4_client.b4_conn.calls.clear()
    b4_client.b4_state["context"]["status"] = "APPROVED"
    assert b4_client.post("/api/v3/reports/rep-1/finalise", json={}).status_code == 200
    kinds = [c[0] for c in b4_client.b4_conn.calls]
    assert kinds.count("audit") >= 1, "the finalisation must be audited"


def test_signed_url_issuance_is_audited_and_carries_no_url(b4_client: TestClient) -> None:
    key = f"{ORG}/rep-1/{RV}.pdf"
    b4_client.b4_state["artefact"] = _artefact_row()
    b4_client.b4_storage.objects[key] = b"%PDF-1.7 frozen"
    response = b4_client.post("/api/v3/reports/rep-1/frozen-artefact/signed-url", json={})
    assert response.status_code == 200
    audits = [c for c in b4_client.b4_conn.calls if c[0] == "audit"]
    assert audits, "the signed-URL issuance must be audited"
    # The audit payload is args[6] (new_data); it must never contain the URL.
    payload = str(audits[0][1])
    assert response.json()["signed_url"] not in payload
