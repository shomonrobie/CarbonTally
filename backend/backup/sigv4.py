"""Minimal AWS Signature Version 4 signer (OID-3).

The ratified backup architecture (D2) selects the **object-store category** and
leaves the concrete client as an open implementation detail (OID-3): either a
cloud SDK (``boto3``/``aioboto3``) **or a minimal SigV4 client over ``httpx``**.

This module implements the second option. That choice is deliberate:

* ``boto3`` is **not** a declared dependency, and the architecture discourages
  adding a cloud SDK;
* ``httpx`` is already present and already used by application code
  (``backend/api/v3_consultants.py``);
* signing is a **pure, deterministic function of the request**, so it can be
  verified against the published AWS worked example with no network, no
  credentials and no provider access (see
  ``tests/unit/backup/test_sigv4_and_s3store.py``).

Only what a private, server-side ``PUT``/``GET``/``HEAD``/``DELETE``/``List``
object client needs is implemented — header-based signing with a signed
``x-amz-content-sha256``. Presigned URLs, SigV4a, chunked uploads and streaming
signatures are intentionally **out of scope**: nothing in the backup path
requires them.

Nothing here performs I/O, holds credentials in a module global, or logs a
secret. The signer returns headers; the caller owns the transport.
"""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, Optional
from urllib.parse import quote, unquote, urlsplit

#: The only signature algorithm this client emits.
ALGORITHM = "AWS4-HMAC-SHA256"

#: The terminating scope suffix for every SigV4 credential scope.
TERMINATOR = "aws4_request"

#: Characters AWS never URI-encodes (the RFC 3986 unreserved set).
_UNRESERVED = "-_.~"

#: The SHA-256 of the empty string — the payload hash of a bodyless request.
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


def uri_encode(value: str, *, encode_slash: bool = True) -> str:
    """URI-encode per the AWS SigV4 rules.

    AWS requires a **custom** encoder: every byte is encoded except the
    unreserved set, a space becomes ``%20`` (never ``+``), hex digits are
    upper-case, and ``/`` is left intact **only** in an object key.

    The standard-library encoders differ from this in subtle ways, which is why
    the function is written out rather than delegated.
    """
    safe = _UNRESERVED if encode_slash else _UNRESERVED + "/"
    return quote(value, safe=safe)


def sha256_hex(data: bytes) -> str:
    """Lower-case hex SHA-256 of ``data``."""
    return hashlib.sha256(data).hexdigest()


def hmac_sha256(key: bytes, message: str) -> bytes:
    """HMAC-SHA256 of ``message`` (UTF-8) under ``key``."""
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def derive_signing_key(secret_key: str, datestamp: str, region: str, service: str) -> bytes:
    """Derive the date/region/service-scoped signing key.

    The four-step HMAC chain is the point of SigV4: the long-lived secret never
    signs directly, so a leaked request signature cannot be replayed against
    another day, region or service.
    """
    k_date = hmac_sha256(("AWS4" + secret_key).encode("utf-8"), datestamp)
    k_region = hmac_sha256(k_date, region)
    k_service = hmac_sha256(k_region, service)
    return hmac_sha256(k_service, TERMINATOR)


def canonical_query_string(query: str) -> str:
    """Return the canonical query string for a raw query component.

    Parameters are percent-decoded and re-encoded with the AWS encoder, then
    sorted by encoded key and then encoded value. An absent component is the
    empty string (never ``"?"``).
    """
    if not query:
        return ""
    pairs: list[tuple[str, str]] = []
    for chunk in query.split("&"):
        if not chunk:
            continue
        raw_key, _, raw_value = chunk.partition("=")
        pairs.append((uri_encode(unquote(raw_key)), uri_encode(unquote(raw_value))))
    pairs.sort()
    return "&".join(f"{key}={value}" for key, value in pairs)


@dataclass(frozen=True)
class SignedRequest:
    """The outcome of signing one request.

    ``headers`` is the complete set the caller must send: it includes the
    caller's headers plus ``Host``, ``x-amz-date``, ``x-amz-content-sha256`` and
    ``Authorization``. The remaining fields are retained so a failure can be
    diagnosed — and tested — **without** ever re-deriving or printing a secret.
    """

    headers: dict[str, str]
    canonical_request: str
    string_to_sign: str
    signature: str
    credential_scope: str

    def __repr__(self) -> str:  # pragma: no cover - mirrors settings repr policy
        return (
            f"SignedRequest(scope={self.credential_scope!r}, "
            f"signature=<set>, headers=<{len(self.headers)}>)"
        )


def sign_request(
    *,
    method: str,
    url: str,
    region: str,
    service: str,
    access_key: str,
    secret_key: str,
    payload: bytes = b"",
    headers: Optional[Mapping[str, str]] = None,
    now: Optional[datetime] = None,
) -> SignedRequest:
    """Sign ``method``/``url`` and return the headers to send.

    Args:
        method: HTTP method, upper-case (``PUT``, ``GET``, ``HEAD``, ``DELETE``).
        url: The absolute request URL (scheme, host, optional port, path, query).
        region: Signing region (``us-east-1`` for a Supabase S3 endpoint).
        service: Signing service (``s3``).
        access_key: The access key id (never the secret).
        secret_key: The secret access key. Used only inside this call.
        payload: The exact request body bytes. Its SHA-256 is signed, so a
            caller that tampers with the body invalidates the signature.
        headers: Additional headers to include and sign (for example
            ``Content-Type`` or ``x-amz-meta-*``).
        now: The signing instant; defaults to the current UTC time. Injected in
            tests so the result is deterministic.

    Returns:
        A :class:`SignedRequest` whose ``headers`` are ready to send.

    Raises:
        ValueError: if a required argument is blank, or ``url`` is not absolute.
            Configuration problems are raised by the caller's settings layer and
            are never silently defaulted here.
    """
    if not method:
        raise ValueError("method is required")
    if not url:
        raise ValueError("url is required")
    for name, value in (
        ("region", region),
        ("service", service),
        ("access_key", access_key),
        ("secret_key", secret_key),
    ):
        if not value:
            raise ValueError(f"{name} is required to sign a request")

    timestamp = now or datetime.now(timezone.utc)
    amz_date = timestamp.strftime("%Y%m%dT%H%M%SZ")
    datestamp = timestamp.strftime("%Y%m%d")

    parts = urlsplit(url)
    if not parts.netloc:
        raise ValueError("url must be absolute (include the host)")

    # Canonical headers: lower-case names, trimmed values, ordered by name.
    to_sign: dict[str, str] = {"host": parts.netloc}
    for name, value in (headers or {}).items():
        to_sign[name.lower()] = str(value).strip()
    payload_hash = sha256_hex(payload)
    to_sign["x-amz-date"] = amz_date
    to_sign["x-amz-content-sha256"] = payload_hash

    signed_header_names = sorted(to_sign)
    canonical_headers = "".join(
        f"{name}:{to_sign[name]}\n" for name in signed_header_names
    )
    signed_headers = ";".join(signed_header_names)

    canonical_request = "\n".join(
        (
            method.upper(),
            uri_encode(parts.path or "/", encode_slash=False),
            canonical_query_string(parts.query),
            canonical_headers,
            signed_headers,
            payload_hash,
        )
    )

    credential_scope = f"{datestamp}/{region}/{service}/{TERMINATOR}"
    string_to_sign = "\n".join(
        (
            ALGORITHM,
            amz_date,
            credential_scope,
            sha256_hex(canonical_request.encode("utf-8")),
        )
    )

    signature = hmac_sha256(
        derive_signing_key(secret_key, datestamp, region, service), string_to_sign
    ).hex()

    authorization = (
        f"{ALGORITHM} Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    out_headers = {name: value for name, value in (headers or {}).items()}
    out_headers["Host"] = parts.netloc
    out_headers["x-amz-date"] = amz_date
    out_headers["x-amz-content-sha256"] = payload_hash
    out_headers["Authorization"] = authorization

    return SignedRequest(
        headers=out_headers,
        canonical_request=canonical_request,
        string_to_sign=string_to_sign,
        signature=signature,
        credential_scope=credential_scope,
    )
