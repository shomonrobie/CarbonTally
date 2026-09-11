"""OpenAPI binding-audit self-tests — fixture spec, no live app (spec §35)."""

from __future__ import annotations

import pytest

from qa_harness.scripts import audit_openapi_bindings as audit_module

# Minimal fixture OpenAPI covering every path the harness binds to. Generated
# from the live contract (V1.2); the audit must report ZERO defects against it.
FIXTURE_SPEC = {
    "openapi": "3.1.0",
    "paths": {
        "/api/v3/organizations/{org_id}": {"get": {"parameters": []}},
        "/api/v3/organizations/{org_id}/profile": {"get": {"parameters": []}},
        "/api/v3/organizations/{org_id}/members": {"get": {"parameters": []}},
        "/api/v3/consultants/me": {"get": {"parameters": []}},
        "/api/v3/consultants/me/clients": {"get": {"parameters": []}},
        "/api/v3/consultants/me/branding": {"get": {"parameters": []}},
        "/api/v3/consultants/clients/{client_id}": {"get": {"parameters": []}},
        "/api/v3/processing/dashboard": {"get": {"parameters": [
            {"name": "organization_id", "in": "query", "required": True}]}},
        "/api/v3/emissions/dashboard": {"get": {"parameters": [
            {"name": "organization_id", "in": "query", "required": True},
            {"name": "start_date", "in": "query", "required": True},
            {"name": "end_date", "in": "query", "required": True}]}},
        "/api/v3/processing/queue": {"get": {"parameters": [
            {"name": "organization_id", "in": "query", "required": True},
            {"name": "stage", "in": "query", "required": True}]}},
        "/api/v3/processing/customer-review": {"get": {"parameters": [
            {"name": "organization_id", "in": "query", "required": True}]}},
        "/api/v3/processing/status": {"get": {"parameters": [
            {"name": "organization_id", "in": "query", "required": True}]}},
        "/api/v3/processing/items/{item_id}/calculate": {"post": {"parameters": []}},
        "/api/v3/processing/items/{item_id}/extract": {"post": {"parameters": []}},
        "/api/v3/processing/items/{item_id}/map": {"post": {"parameters": []}},
        "/api/v3/processing/items/{item_id}/validate": {"post": {"parameters": []}},
        "/api/v3/processing/items/{item_id}/customer-review": {"post": {"parameters": []}},
        "/api/v3/ops/items/{item_id}/calculate": {"post": {"parameters": []}},
        "/api/v3/messaging/conversations": {"get": {"parameters": [
            {"name": "organization_id", "in": "query", "required": True}]}},
        "/api/v3/messaging/conversations/{conversation_id}/messages": {
            "get": {"parameters": []}, "post": {"parameters": []}},
        "/api/v3/reports": {"get": {"parameters": [
            {"name": "organization_id", "in": "query", "required": True}]}},
        "/api/v3/customer-factors": {"get": {"parameters": [
            {"name": "organization_id", "in": "query", "required": True}]}},
        "/api/v3/customer-factors/{item_id}/approve": {"post": {"parameters": []}},
        "/api/v3/documents": {"get": {"parameters": [
            {"name": "organization_id", "in": "query", "required": True}]}},
        "/api/v3/documents/{item_id}/signed-url": {"get": {"parameters": []}},
        "/api/v3/documents/{file_id}/signed-url": {"get": {"parameters": []}},
        "/api/v3/search": {"get": {"parameters": [
            {"name": "organization_id", "in": "query", "required": True},
            {"name": "q", "in": "query", "required": True}]}},
        "/api/v3/notifications": {"get": {"parameters": []}},
        "/api/v3/ops/me": {"get": {"parameters": []}},
        "/api/v3/ops/dashboard": {"get": {"parameters": []}},
        "/api/v3/ops/queues/operator": {"get": {"parameters": []}},
        "/api/v3/ops/queues/review": {"get": {"parameters": []}},
        "/api/v3/ops/queues/qc": {"get": {"parameters": []}},
        "/api/v3/ops/staff": {"get": {"parameters": []}},
        "/api/v3/ops/staff-roles": {"get": {"parameters": []}},
        "/api/v3/ops/entities": {"get": {"parameters": []}},
        "/api/v3/ops/entities/{entity_id}/extraction/batches": {"get": {"parameters": []}},
        "/api/v3/ops/entities/{entity_id}/dashboard": {"get": {"parameters": []}},
        "/api/v3/settings/retention": {"get": {"parameters": []}},
        "/api/v3/commercial/config": {"get": {"parameters": []}},
        "/api/v2/admin/audit": {"get": {"parameters": []}},
        "/api/v3/uploads": {"post": {"parameters": []}},
    },
}


def _run_audit(monkeypatch: pytest.MonkeyPatch, spec: dict) -> tuple[list, list]:
    monkeypatch.setattr(audit_module, "_load_spec", lambda url: spec)
    return audit_module.audit("fixture://openapi.json")


def test_audit_reports_zero_defects_on_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    path_defects, param_defects = _run_audit(monkeypatch, FIXTURE_SPEC)
    assert path_defects == [], path_defects
    assert param_defects == [], param_defects


def test_audit_flags_unknown_path(monkeypatch: pytest.MonkeyPatch) -> None:
    spec = dict(FIXTURE_SPEC)
    spec["paths"] = {p: op for p, op in spec["paths"].items()
                     if "/api/v3/commercial/config" not in p}
    path_defects, _ = _run_audit(monkeypatch, spec)
    assert any("billing_config" in d and "not in OpenAPI" in d for d in path_defects)


def test_audit_flags_missing_required_param(monkeypatch: pytest.MonkeyPatch) -> None:
    spec = dict(FIXTURE_SPEC)
    spec["paths"] = dict(spec["paths"])
    spec["paths"]["/api/v3/documents"] = {"get": {"parameters": [
        {"name": "organization_id", "in": "query", "required": True}]}}
    # Remove organization_id from the harness's documents binding via a probe
    # spec override is not possible; instead drop the param from the fixture
    # binding by patching ACTION_BINDINGS through the imported module.
    from qa_harness.workflows import executor as executor_module

    original = executor_module.ACTION_BINDINGS["view_documents"]
    try:
        executor_module.ACTION_BINDINGS["view_documents"] = (
            "GET", "/api/v3/documents"
        )
        path_defects, param_defects = _run_audit(monkeypatch, spec)
        assert any("view_documents" in d and "missing required" in d
                   for d in param_defects)
    finally:
        executor_module.ACTION_BINDINGS["view_documents"] = original


def test_load_spec_is_read_only_get(monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[str] = []

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *exc: object) -> None:
            return None

        def read(self) -> bytes:
            import json
            return json.dumps(FIXTURE_SPEC).encode()

    def fake_urlopen(url: str, timeout: int = 0) -> FakeResponse:
        opened.append(url)
        return FakeResponse()

    monkeypatch.setattr(audit_module.urllib.request, "urlopen", fake_urlopen)
    spec = audit_module._load_spec("http://localhost:8050/openapi.json")
    assert opened == ["http://localhost:8050/openapi.json"]
    assert "paths" in spec
