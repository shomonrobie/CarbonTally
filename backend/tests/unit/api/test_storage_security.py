"""D32 — storage security tests.

Covers the private-documents hardening:
- ``services.storage.path_from_url`` (public/signed URL + bare path parsing)
- ``GET /api/v3/documents/{id}/signed-url`` authorization (org member only)
"""
from __future__ import annotations

import pytest

from services.storage import path_from_url
from tests.unit.api.fakes import member_user


class _FakeDoc:
    def __init__(self, doc_id: str, org_id: str, path: str) -> None:
        self.id = doc_id
        self.organization_id = org_id
        self.path = path


def _install_doc(world, doc: _FakeDoc) -> None:
    async def _get(file_id: str):
        return doc if file_id == doc.id else None

    world.files.get = _get  # type: ignore[method-assign]


# ---------------------------------------------------------------------------
# path_from_url
# ---------------------------------------------------------------------------


def test_path_from_url_handles_bare_path():
    assert path_from_url("uploads/org-a/2025/01/file.pdf") == "uploads/org-a/2025/01/file.pdf"
    assert path_from_url("") == ""
    assert path_from_url(None) == ""


def test_path_from_url_extracts_from_public_url():
    url = "https://supabase.local/storage/v1/object/public/documents/uploads/org-a/f.pdf"
    assert path_from_url(url) == "uploads/org-a/f.pdf"


def test_path_from_url_extracts_from_signed_url():
    url = "https://supabase.local/storage/v1/object/sign/documents/uploads/org-a/f.pdf?token=abc"
    assert path_from_url(url) == "uploads/org-a/f.pdf"


# ---------------------------------------------------------------------------
# GET /api/v3/documents/{id}/signed-url
# ---------------------------------------------------------------------------


def test_signed_url_org_member_allowed(client, world, user_provider, monkeypatch):
    import api.v3_documents as v3_documents

    doc = _FakeDoc("doc-a", "org-a", "uploads/org-a/2025/f.pdf")
    _install_doc(world, doc)
    monkeypatch.setattr(v3_documents, "storage_signed_url", lambda p, **k: "https://signed/x")
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    resp = client.get("/api/v3/documents/doc-a/signed-url")
    assert resp.status_code == 200
    assert resp.json()["url"] == "https://signed/x"


def test_signed_url_cross_org_denied(client, world, user_provider, monkeypatch):
    import api.v3_documents as v3_documents

    doc = _FakeDoc("doc-a", "org-a", "uploads/org-a/2025/f.pdf")
    _install_doc(world, doc)
    monkeypatch.setattr(v3_documents, "storage_signed_url", lambda p, **k: "https://signed/x")
    user_provider.set_user(member_user("org-b", "u-b", "b@example.test"))
    assert client.get("/api/v3/documents/doc-a/signed-url").status_code == 403


def test_signed_url_unknown_document_404(client, world, user_provider, monkeypatch):
    import api.v3_documents as v3_documents

    monkeypatch.setattr(v3_documents, "storage_signed_url", lambda p, **k: "https://signed/x")
    user_provider.set_user(member_user("org-a", "u-a", "a@example.test"))
    assert client.get("/api/v3/documents/nope/signed-url").status_code == 404
