"""Phase 8 B4/S5 — frozen-artefact storage adapter (private bucket, signed URLs).

PO `B4-D6`: the artefact lives in the **private** Supabase Storage bucket
``report-artifacts`` and is reachable only through **short-lived signed URLs**
issued after the caller has been authorized. No public URL is ever constructed
(contrast ``services.storage``, which converts a public document URL to a signed
one — the artefact path never has a public form at all).

The adapter is injected so that tests exercise the mandate without touching real
storage.
"""
from __future__ import annotations

from typing import Optional, Protocol

from core.logging import get_logger
from domain.report_artefact import ARTEFACT_BUCKET, ARTEFACT_CONTENT_TYPE

logger = get_logger(__name__)

#: Short-lived by mandate: five minutes is long enough for a browser to start a
#: download and short enough that a leaked URL is not durable.
SIGNED_URL_TTL_SECONDS = 300


class ReportArtefactStorage(Protocol):
    """Minimal storage surface the finalisation path needs."""

    def upload(
        self, *, object_key: str, payload: bytes, content_type: str = ARTEFACT_CONTENT_TYPE
    ) -> None: ...

    def signed_url(self, *, object_key: str, expires_in: int = SIGNED_URL_TTL_SECONDS) -> str: ...

    def exists(self, *, object_key: str) -> bool: ...

    def bucket_exists(self) -> bool: ...


class SupabaseReportArtefactStorage:
    """The real adapter — private bucket, no public URL path."""

    def __init__(self, bucket: str = ARTEFACT_BUCKET) -> None:
        self._bucket = bucket

    def _bucket_client(self):
        from infra.supabase import get_service_client

        return get_service_client().storage.from_(self._bucket)

    def upload(
        self, *, object_key: str, payload: bytes, content_type: str = ARTEFACT_CONTENT_TYPE
    ) -> None:
        self._bucket_client().upload(
            path=object_key,
            file=payload,
            file_options={"content-type": content_type, "upsert": "false"},
        )

    def signed_url(self, *, object_key: str, expires_in: int = SIGNED_URL_TTL_SECONDS) -> str:
        result = self._bucket_client().create_signed_url(object_key, expires_in)
        if isinstance(result, dict):
            return str(result.get("signedURL") or result.get("signedUrl") or "")
        return str(getattr(result, "signed_url", "") or "")

    def exists(self, *, object_key: str) -> bool:
        try:
            self._bucket_client().list(path=object_key.rsplit("/", 1)[0])
        except Exception:  # noqa: BLE001 - absence is the safe answer
            return False
        return True

    def bucket_exists(self) -> bool:
        """D-11 preflight: is the private bucket provisioned in this environment?

        Read-only. The bucket is operationally provisioned (no migration creates
        it), so this is the application-level check an operator can run before
        relying on report finalisation. Absence (or any provider error) is
        reported as ``False`` — fail-safe, never an exception.
        """
        try:
            from infra.supabase import get_service_client

            buckets = get_service_client().storage.list_buckets()
        except Exception:  # noqa: BLE001 - absence/unreachable is the safe answer
            return False
        for bucket in buckets or []:
            name = bucket.get("name") if isinstance(bucket, dict) else getattr(bucket, "name", None)
            if name == self._bucket:
                return True
        return False


class InMemoryReportArtefactStorage:
    """Deterministic test double (used by the unit and runtime suites)."""

    def __init__(self, bucket: str = ARTEFACT_BUCKET) -> None:
        self._bucket = bucket
        self.objects: dict[str, bytes] = {}
        self.uploads: list[dict] = []

    @property
    def bucket(self) -> str:
        return self._bucket

    def upload(
        self, *, object_key: str, payload: bytes, content_type: str = ARTEFACT_CONTENT_TYPE
    ) -> None:
        if object_key in self.objects:
            raise FileExistsError(
                f"B4 artefact: object {object_key} already exists in the private bucket - "
                "a frozen artefact is never overwritten"
            )
        self.objects[object_key] = bytes(payload)
        self.uploads.append({"object_key": object_key, "content_type": content_type, "byte_size": len(payload)})

    def signed_url(self, *, object_key: str, expires_in: int = SIGNED_URL_TTL_SECONDS) -> str:
        if object_key not in self.objects:
            raise FileNotFoundError(object_key)
        return f"https://signed.test/{self._bucket}/{object_key}?expires_in={expires_in}"

    def exists(self, *, object_key: str) -> bool:
        return object_key in self.objects

    def bucket_exists(self) -> bool:
        """The deterministic double always has its bucket provisioned."""
        return True


_storage: Optional[ReportArtefactStorage] = None


def get_report_artefact_storage() -> ReportArtefactStorage:
    """Process-wide adapter (mirrors ``infra.supabase.get_service_client``)."""
    global _storage
    if _storage is None:
        _storage = SupabaseReportArtefactStorage()
    return _storage


def set_report_artefact_storage(storage: Optional[ReportArtefactStorage]) -> None:
    """Swap the adapter (tests / explicit wiring)."""
    global _storage
    _storage = storage
