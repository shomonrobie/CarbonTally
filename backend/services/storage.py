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

Authorization is enforced by the API layer (org member / staff scope) BEFORE
any signed URL is issued — signed URLs are never returned to unauthenticated
or unauthorized callers.
"""
from __future__ import annotations

import dataclasses
from typing import Any, Optional

from infra.supabase import get_service_client

#: Storage bucket for customer documents.
DOCUMENTS_BUCKET = "documents"

#: Default signed-URL lifetime (seconds) for document viewers.
SIGNED_URL_TTL_SECONDS = 3600

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
