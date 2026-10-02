"""S3-compatible object store (D2 / OID-3) — the first *production* provider.

Phase 1 shipped only ``local`` and ``memory`` providers and deliberately
selected no production destination. The ratified architecture names the
off-site destination as **Supabase Storage** (an S3-compatible endpoint), and
OID-3 left the client as an open detail: a cloud SDK **or** a minimal SigV4
client over ``httpx``. This module is the second option, for the reasons
recorded in :mod:`backup.sigv4`.

Scope of this provider:

* the five operations the backup service needs — ``put``, ``get``, ``head``,
  ``list`` and ``delete`` — over path-style addressing (what Supabase Storage
  exposes) with virtual-host addressing available for AWS proper;
* SigV4 header signing with a signed ``x-amz-content-sha256``;
* **storage only** — this module never dumps, compresses, encrypts or inspects a
  backup. It receives ciphertext, exactly like the local provider.

Deliberate non-goals (nothing in the backup path needs them): multipart uploads,
presigned URLs, bucket lifecycle policy, server-side encryption, and retries
that hide a failure. A failure is surfaced as :class:`BackupStorageError`; the
caller decides whether to retry.

Credentials are held on the instance and are **never** placed in a return value,
an exception message or a log line.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional

import httpx

from backup.errors import BackupStorageError
from backup.settings import BackupSettings
from backup.sigv4 import sign_request, uri_encode
from backup.storage import StoredObject

#: The signing service for every request this provider makes.
SERVICE = "s3"

#: Default per-request timeout. A backup object can be large, so the read/write
#: timeouts are generous while the connect timeout stays short.
DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)

#: S3 XML namespace used by ListObjectsV2.
_S3_NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"

#: Longest provider error message surfaced in ``details`` (never the whole body).
_MAX_REASON = 200


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _etag_algorithm(etag: Optional[str]) -> Optional[str]:
    """Classify an S3 ETag's algorithm without ever calling it SHA-256.

    A single-part S3 ETag is the MD5 of the object; a multipart ETag carries a
    ``-<part-count>`` suffix and is **not** a plain MD5. Either way it is a
    provider checksum, never an application SHA-256 (F11).
    """
    if not etag:
        return None
    return "etag-multipart" if "-" in etag else "etag-md5"


class S3ObjectStore:
    """An :class:`backup.storage.ObjectStore` backed by an S3-compatible API.

    Args:
        settings: The resolved backup settings. The S3 fields are read from it,
            so there is exactly one configuration path.
        client: An optional pre-built ``httpx.AsyncClient`` (injected in tests
            through ``httpx.MockTransport``). When omitted the store owns a
            client and must be closed with :meth:`aclose`.
    """

    def __init__(
        self,
        settings: BackupSettings,
        *,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        endpoint, region, bucket, access_key, secret_key = settings.require_s3()
        self._endpoint = endpoint.rstrip("/")
        self._region = region
        self._bucket = bucket
        self._access_key = access_key
        self._secret_key = secret_key
        self._prefix = settings.s3_prefix.strip("/")
        self._path_style = settings.s3_path_style
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)

    # -- lifecycle ---------------------------------------------------------

    async def aclose(self) -> None:
        """Close the owned HTTP client (a no-op for an injected client)."""
        if self._owns_client:
            await self._client.aclose()

    def __repr__(self) -> str:  # pragma: no cover - mirrors settings repr policy
        return (
            f"S3ObjectStore(region={self._region!r}, bucket={self._bucket!r}, "
            f"path_style={self._path_style}, access_key=<set>, secret=<set>)"
        )

    # -- URL / key plumbing ------------------------------------------------

    def _full_key(self, key: str) -> str:
        """Apply the configured prefix to a caller-supplied key."""
        return f"{self._prefix}/{key}" if self._prefix else key

    def _base(self) -> str:
        """The scheme+host (path-style) or bucket-qualified host."""
        if self._path_style:
            return f"{self._endpoint}/{self._bucket}"
        scheme, _, host = self._endpoint.partition("://")
        return f"{scheme}://{self._bucket}.{host}"

    def _object_url(self, full_key: str, query: str = "") -> str:
        """Build the request URL for one object.

        The key is URI-encoded with the AWS encoder, which preserves ``/`` inside
        the key and encodes every other reserved byte.
        """
        base = f"{self._base()}/{uri_encode(full_key, encode_slash=False)}"
        return f"{base}?{query}" if query else base

    def _bucket_url(self, query: str) -> str:
        """Build the request URL for a bucket-level (List) call."""
        return f"{self._base()}?{query}"

    # -- transport ---------------------------------------------------------

    async def _request(
        self,
        method: str,
        url: str,
        *,
        payload: bytes = b"",
        headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        """Sign and send one request, translating transport failures.

        A network fault becomes a :class:`BackupStorageError` so every caller
        sees one error type regardless of provider.
        """
        signed = sign_request(
            method=method,
            url=url,
            region=self._region,
            service=SERVICE,
            access_key=self._access_key,
            secret_key=self._secret_key,
            payload=payload,
            headers=headers,
        )
        try:
            return await self._client.request(
                method,
                url,
                content=payload if payload else None,
                headers=signed.headers,
                timeout=DEFAULT_TIMEOUT,
            )
        except httpx.HTTPError as exc:
            raise BackupStorageError(
                "object store request failed",
                details={"reason": type(exc).__name__},
            ) from exc

    @staticmethod
    def _reason(response: httpx.Response) -> str:
        """Extract a short, safe reason from an S3 error body.

        Only the S3 ``<Code>``/``<Message>`` are kept, and the message is
        truncated: a provider body is never echoed back whole.
        """
        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            return f"HTTP {response.status_code}"
        fields: dict[str, str] = {}
        for element in root.iter():
            name = element.tag.split("}")[-1]
            if name in ("Code", "Message") and element.text:
                fields[name] = element.text.strip()
        parts = [fields.get("Code", f"HTTP {response.status_code}")]
        if "Message" in fields:
            parts.append(fields["Message"][:_MAX_REASON])
        return ": ".join(parts)

    def _failure(self, response: httpx.Response, key: str) -> BackupStorageError:
        return BackupStorageError(
            "object store rejected the request",
            details={"key": key, "status": response.status_code, "reason": self._reason(response)},
        )

    # -- ObjectStore protocol ----------------------------------------------

    async def put_object(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> StoredObject:
        """Store ciphertext under ``key`` and return its provider metadata.

        ``content_sha256`` is deliberately ``None``: S3 does not guarantee a
        SHA-256 of the object content, so claiming one would be a lie the F11
        contract exists to prevent. The ETag is reported as a *provider*
        checksum instead.
        """
        full_key = self._full_key(key)
        headers = {"Content-Type": content_type}
        for name, value in (metadata or {}).items():
            headers[f"x-amz-meta-{name.lower()}"] = str(value)
        response = await self._request(
            "PUT", self._object_url(full_key), payload=data, headers=headers
        )
        if not 200 <= response.status_code < 300:
            raise self._failure(response, key)
        etag = response.headers.get("etag")
        return StoredObject(
            key=full_key,
            size_bytes=len(data),
            created_at=_now_iso(),
            content_sha256=None,
            provider_checksum=etag,
            provider_checksum_algorithm=_etag_algorithm(etag),
            content_type=content_type,
            metadata=dict(metadata or {}),
        )

    async def get_object(self, key: str) -> bytes:
        """Read an object's bytes, raising a typed error when it is absent."""
        response = await self._request("GET", self._object_url(key))
        if response.status_code == 404:
            raise BackupStorageError("object not found", details={"key": key})
        if not 200 <= response.status_code < 300:
            raise self._failure(response, key)
        return response.content

    async def head_object(self, key: str) -> StoredObject:
        """Return object metadata without transferring the body."""
        response = await self._request("HEAD", self._object_url(key))
        if response.status_code == 404:
            raise BackupStorageError("object not found", details={"key": key})
        if not 200 <= response.status_code < 300:
            raise self._failure(response, key)
        etag = response.headers.get("etag")
        metadata = {
            name[len("x-amz-meta-") :]: value
            for name, value in response.headers.items()
            if name.lower().startswith("x-amz-meta-")
        }
        try:
            size = int(response.headers.get("content-length", "0"))
        except ValueError:  # pragma: no cover - defensive
            size = 0
        return StoredObject(
            key=key,
            size_bytes=size,
            created_at=response.headers.get("last-modified", _now_iso()),
            content_sha256=None,
            provider_checksum=etag,
            provider_checksum_algorithm=_etag_algorithm(etag),
            content_type=response.headers.get("content-type", "application/octet-stream"),
            metadata=metadata,
        )

    async def list_objects(self, prefix: str = "") -> list[StoredObject]:
        """List objects under ``prefix``, following ListObjectsV2 pagination.

        ``prefix`` is a *caller* prefix and is combined with the configured
        store prefix, so the caller never has to know the store's layout.
        """
        full_prefix = self._full_key(prefix) if prefix else self._prefix
        found: list[StoredObject] = []
        token: Optional[str] = None
        while True:
            query = "list-type=2"
            if full_prefix:
                query += f"&prefix={uri_encode(full_prefix, encode_slash=False)}"
            if token:
                query += f"&continuation-token={uri_encode(token)}"
            response = await self._request("GET", self._bucket_url(query))
            if not 200 <= response.status_code < 300:
                raise self._failure(response, prefix or "<all>")
            root = ET.fromstring(response.content)
            for element in root.iter(f"{_S3_NS}Contents"):
                fields = {
                    child.tag.split("}")[-1]: (child.text or "")
                    for child in element
                }
                found.append(
                    StoredObject(
                        key=fields.get("Key", ""),
                        size_bytes=int(fields.get("Size", "0") or 0),
                        created_at=fields.get("LastModified", _now_iso()),
                        content_sha256=None,
                        provider_checksum=(fields.get("ETag") or None),
                        provider_checksum_algorithm=_etag_algorithm(fields.get("ETag")),
                    )
                )
            truncated = "false"
            next_token: Optional[str] = None
            for element in root.iter(f"{_S3_NS}IsTruncated"):
                truncated = (element.text or "false").strip().lower()
            if truncated != "true":
                break
            for element in root.iter(f"{_S3_NS}NextContinuationToken"):
                next_token = (element.text or "").strip() or None
            if not next_token:  # pragma: no cover - a malformed provider response
                break
            token = next_token
        return sorted(found, key=lambda item: item.key)

    async def delete_object(self, key: str) -> None:
        """Delete an object, tolerating an already-absent one (idempotent)."""
        response = await self._request("DELETE", self._object_url(key))
        if response.status_code == 404 or 200 <= response.status_code < 300:
            return
        raise self._failure(response, key)
