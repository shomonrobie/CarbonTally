"""D32 — secure document storage helpers.

Documents live in the ``documents`` Supabase Storage bucket. D32 makes the
bucket PRIVATE and serves objects only through short-lived SIGNED URLs so that
customer documents are never exposed through predictable/public URLs.

- ``path_from_url`` extracts the canonical storage path from a public URL, a
  signed URL or a bare path (legacy rows stored public URLs).
- ``storage_signed_url`` creates a short-lived signed URL using the service
  client (expiry is mandatory — signed URLs always expire).
- ``signed_item`` returns a copy of a work item whose ``file_url`` is a fresh
  signed URL (used by the ops / customer workspace responses).
- ``create_signed_upload_url`` (Storage Management Step 1) issues a short-lived,
  object-scoped upload authorisation so the browser can upload **directly** to
  Supabase Storage; the backend never proxies the ordinary upload byte stream.
- ``object_info`` / ``object_exists`` / ``download_object_prefix`` verify a
  completed direct upload before it advances to the security-validation state.

Authorization is enforced by the API layer (org member / consultant grant /
staff scope) BEFORE any signed URL is issued — signed URLs are never returned to
unauthenticated or unauthorized callers, and the service-role credential is
never handed to the browser.

The module intentionally contains the only storage-credential usage in the
document path: every caller goes through these helpers.
"""
from __future__ import annotations

import dataclasses
from typing import Any, Optional

from infra.supabase import get_service_client

#: Storage bucket for customer documents.
DOCUMENTS_BUCKET = "documents"

#: Default signed-URL lifetime (seconds) for document viewers.
SIGNED_URL_TTL_SECONDS = 3600

#: Lifetime (seconds) of a direct-upload authorisation.  Deliberately short:
#: the token is scoped to one generated object key and one upload attempt.  The
#: effective token expiry is enforced by Supabase Storage; the value recorded
#: here is the platform's declared intention and the point after which a
#: never-completed upload is abandoned rather than accepted.
SIGNED_UPLOAD_TTL_SECONDS = 900

#: How long a ``pending_upload`` document row may still be completed.  After
#: this window the upload authorisation is stale: completion is refused and the
#: document is never accepted, downloaded or processed.
UPLOAD_COMPLETION_WINDOW_SECONDS = 86_400

#: Maximum byte prefix read back for the security gate at upload completion.
DOWNLOAD_PROBE_BYTES = 262_144

_PUBLIC_MARKER = f"/object/public/{DOCUMENTS_BUCKET}/"
_SIGNED_MARKER = f"/object/sign/{DOCUMENTS_BUCKET}/"



def path_from_url(value: Optional[str]) -> str:
    """Return the canonical storage path from a URL or bare path.

    Handles legacy public URLs (``/object/public/documents/<path>``), signed
    URLs (``/object/sign/documents/<path>?token=...``) and bare paths
    (``uploads/<org>/<date>/<file>``).
    """
    if not value:
        return ""
    if not value.startswith("http"):
        return value
    if _PUBLIC_MARKER in value:
        return value.split(_PUBLIC_MARKER, 1)[1]
    if _SIGNED_MARKER in value:
        return value.split(_SIGNED_MARKER, 1)[1].split("?", 1)[0]
    # Last-resort: whatever follows the bucket name.
    marker = f"/{DOCUMENTS_BUCKET}/"
    if marker in value:
        return value.split(marker, 1)[1].split("?", 1)[0]
    return value


def storage_signed_url(
    path: Optional[str], expires_in: int = SIGNED_URL_TTL_SECONDS
) -> str:
    """Create a short-lived signed URL for ``path`` (or ``""`` on failure)."""
    if not path:
        return ""
    try:
        result = get_service_client().storage.from_(DOCUMENTS_BUCKET).create_signed_url(
            path, int(expires_in)
        )
    except Exception:  # pragma: no cover - storage failure path
        return ""
    if not result:
        return ""
    return str(result.get("signedURL") or result.get("signedUrl") or "")


def signed_item(item: Any) -> Any:
    """Return a copy of a dataclass work item with ``file_url`` signed."""
    url = storage_signed_url(path_from_url(getattr(item, "file_url", None)))
    try:
        return dataclasses.replace(item, file_url=url)
    except (TypeError, ValueError):  # pragma: no cover - non-dataclass fallback
        return item


# ---------------------------------------------------------------------------
# Storage Management Step 1 — direct-to-storage (signed) upload + verification
# ---------------------------------------------------------------------------


def create_signed_upload_url(
    path: str, bucket: str = DOCUMENTS_BUCKET
) -> dict:
    """Return a short-lived signed upload authorisation for ``path``.

    The returned mapping is intentionally minimal and contains **no** long-lived
    credential: only the object-scoped signed URL and its single-use token.

        {"url": str, "token": str, "path": str, "expires_in": int}

    ``url`` is the absolute Supabase Storage endpoint the browser PUTs the bytes
    to (``.../object/upload/sign/{bucket}/{path}?token=...``).  The caller must
    already have been authorized by the API layer — this function performs no
    authorization of its own.
    """
    if not path:
        raise ValueError("a storage path is required to sign an upload")
    result = get_service_client().storage.from_(bucket).create_signed_upload_url(path)
    if not result:
        return {}
    if isinstance(result, dict):
        url = result.get("signed_url") or result.get("signedUrl") or result.get("url") or ""
        token = result.get("token") or ""
        signed_path = result.get("path") or path
    else:  # pragma: no cover - newer typed responses
        url = (
            getattr(result, "signed_url", None)
            or getattr(result, "signedUrl", None)
            or getattr(result, "url", None)
            or ""
        )
        token = getattr(result, "token", "") or ""
        signed_path = getattr(result, "path", path) or path
    return {
        "url": str(url),
        "token": str(token),
        "path": str(signed_path),
        "expires_in": SIGNED_UPLOAD_TTL_SECONDS,
    }


def object_info(path: str, bucket: str = DOCUMENTS_BUCKET) -> Optional[dict]:
    """Return storage metadata for ``path`` (``None`` when it does not exist).

    Used to verify that a browser-completed direct upload actually landed before
    the document advances past ``pending_upload``.
    """
    if not path:
        return None
    try:
        client = get_service_client()
        file_api = client.storage.from_(bucket)
        info = file_api.info(path)
    except Exception:  # pragma: no cover - storage failure path
        return None
    return dict(info) if info else None


def stored_object_size(info: Optional[dict]) -> Optional[int]:
    """Best-effort byte size from a storage ``info`` payload."""
    if not info:
        return None
    for key in ("size", "contentLength", "content_length", "Content-Length"):
        value = info.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    metadata = info.get("metadata")
    if isinstance(metadata, dict):
        for key in ("size", "contentLength", "content-length"):
            value = metadata.get(key)
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue
    return None


def download_object(
    path: str,
    *,
    max_bytes: Optional[int] = None,
    bucket: str = DOCUMENTS_BUCKET,
) -> Optional[bytes]:
    """Read a stored object back for server-side processing (never rewritten).

    Step 2J: the direct-upload completion path uses this to give a
    directly-uploaded document the *same* downstream processing semantics as a
    server-proxied upload (page count, OCR prefill).  ``max_bytes`` bounds the
    read to the effective upload allowance, so the read is never larger than the
    platform's own per-file cap.  The bytes are returned to the caller only —
    nothing is written back, so the original uploaded document remains the
    unmodified evidence object (Step 1F / Step 2P).
    """
    if not path:
        return None
    try:
        content = get_service_client().storage.from_(bucket).download(path)
    except Exception:  # pragma: no cover - storage failure path
        return None
    if content is None:
        return None
    if isinstance(content, str):  # pragma: no cover - defensive
        content = content.encode("utf-8", "replace")
    raw = bytes(content)
    if max_bytes is not None:
        return raw[:max_bytes]
    return raw


def download_object_prefix(
    path: str,
    *,
    max_bytes: int = DOWNLOAD_PROBE_BYTES,
    bucket: str = DOCUMENTS_BUCKET,
) -> Optional[bytes]:
    """Read back at most ``max_bytes`` of a stored object for the security gate.

    Returns ``None`` when the object cannot be read.  The returned value is a
    prefix of the stored object — it is never written back, so the original
    uploaded document remains the unmodified evidence object (Step 1F).
    """
    if not path:
        return None
    try:
        content = get_service_client().storage.from_(bucket).download(path)
    except Exception:  # pragma: no cover - storage failure path
        return None
    if content is None:
        return None
    if isinstance(content, str):  # pragma: no cover - defensive
        content = content.encode("utf-8", "replace")
    return bytes(content)[:max_bytes]

