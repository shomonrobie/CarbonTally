"""D-11 — `report-artifacts` bucket preflight (operational provisioning check).

The bucket is operationally provisioned (PO decision: no migration creates it), so
the application exposes a read-only preflight that reports whether the private
bucket exists in the current environment. Absence or provider error must be
reported as ``False`` (fail-safe), never raised.
"""
from __future__ import annotations

import sys
from types import SimpleNamespace

from domain.report_artefact import ARTEFACT_BUCKET
from services.report_artefact_storage import (
    InMemoryReportArtefactStorage,
    SupabaseReportArtefactStorage,
)


class _FakeStorage3:
    def __init__(self, names: list[str] | None = None, *, raise_error: bool = False) -> None:
        self._names = names or []
        self._raise = raise_error

    def list_buckets(self):
        if self._raise:
            raise RuntimeError("storage backend unreachable")
        return [SimpleNamespace(name=n) for n in self._names]


def _install_client(monkeypatch, storage3: _FakeStorage3) -> None:
    module = SimpleNamespace(
        get_service_client=lambda: SimpleNamespace(storage=storage3)
    )
    monkeypatch.setitem(sys.modules, "infra.supabase", module)


class TestBucketPreflight:
    def test_memory_double_reports_provisioned(self) -> None:
        assert InMemoryReportArtefactStorage().bucket_exists() is True

    def test_missing_bucket_reports_false(self, monkeypatch) -> None:
        _install_client(monkeypatch, _FakeStorage3(["documents"]))
        assert SupabaseReportArtefactStorage().bucket_exists() is False

    def test_present_bucket_reports_true(self, monkeypatch) -> None:
        _install_client(monkeypatch, _FakeStorage3(["documents", ARTEFACT_BUCKET]))
        assert SupabaseReportArtefactStorage().bucket_exists() is True

    def test_provider_error_reports_false_and_never_raises(self, monkeypatch) -> None:
        _install_client(monkeypatch, _FakeStorage3(raise_error=True))
        assert SupabaseReportArtefactStorage().bucket_exists() is False

    def test_preflight_is_read_only(self, monkeypatch) -> None:
        """The preflight must not create, upload or delete anything."""
        calls: list[str] = []

        class _Recording(_FakeStorage3):
            def list_buckets(self):
                calls.append("list_buckets")
                return super().list_buckets()

            def create_bucket(self, *_a, **_k):  # pragma: no cover - must not run
                calls.append("create_bucket")
                raise AssertionError("the preflight must never create a bucket")

            def upload(self, *_a, **_k):  # pragma: no cover - must not run
                calls.append("upload")
                raise AssertionError("the preflight must never upload")

        _install_client(monkeypatch, _Recording(["documents", ARTEFACT_BUCKET]))
        assert SupabaseReportArtefactStorage().bucket_exists() is True
        assert calls == ["list_buckets"]
