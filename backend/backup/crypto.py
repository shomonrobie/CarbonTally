"""Authenticated encryption for backup artifacts (D3).

Mechanism: **AES-256-GCM** via ``cryptography`` (already present in the backend
environment; no subprocess, no CLI, no Docker — D1-compatible).

Envelope format (a self-describing single blob)::

    b"CTBKP1\\n"                      magic + envelope version
    <json header>\\n                  {"v":1,"alg":"AES-256-GCM","key_id":…,
                                      "nonce":<base64>}
    <ciphertext || 16-byte GCM tag>

The **header bytes are passed as GCM associated data**, so any tampering with the
version, algorithm, key id or nonce causes decryption to fail — the header is
authenticated, not merely informative.

Key-handling rules (non-negotiable):

* the key is supplied by configuration (``CT_BACKUP_ENCRYPTION_KEY``, base64
  32 bytes) — never hard-coded, never committed, never logged, never written into
  the artifact or the manifest;
* only the **key id** (a non-secret label) appears in the envelope and manifest;
* a fresh random 96-bit nonce is generated per artifact (GCM requires uniqueness
  per key);
* plaintext is never logged and never persisted beside the artifact.
"""
from __future__ import annotations

import base64
import json
import os
from typing import Optional

from backup.errors import BackupArtifactError, BackupIntegrityError
from backup.settings import DEFAULT_KEY_ID

MAGIC = b"CTBKP1\n"
ENVELOPE_VERSION = 1
ALGORITHM = "AES-256-GCM"
NONCE_BYTES = 12
KEY_BYTES = 32


def generate_key() -> bytes:
    """Generate a new random 32-byte AES-256 key.

    Provided for **tests and future key provisioning**. The production key must
    come from secret custody — never from this function at runtime.
    """
    return os.urandom(KEY_BYTES)


def encode_key(key: bytes) -> str:
    """Encode a key as base64 for placement in a secret store."""
    if len(key) != KEY_BYTES:
        raise ValueError("AES-256 key must be exactly 32 bytes")
    return base64.b64encode(key).decode("ascii")


def encrypt(plaintext: bytes, key: bytes, *, key_id: str = DEFAULT_KEY_ID) -> bytes:
    """Encrypt ``plaintext`` into a self-contained envelope.

    Args:
        plaintext: archive bytes (already compressed).
        key: 32-byte AES-256 key.
        key_id: non-secret identifier recorded in the envelope header.

    Returns:
        Envelope bytes: magic + JSON header + ciphertext(+tag).
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    if len(key) != KEY_BYTES:
        raise BackupIntegrityError("encryption key must be exactly 32 bytes")

    nonce = os.urandom(NONCE_BYTES)
    header = {
        "v": ENVELOPE_VERSION,
        "alg": ALGORITHM,
        "key_id": key_id,
        "nonce": base64.b64encode(nonce).decode("ascii"),
    }
    header_bytes = MAGIC + _encode_header(header) + b"\n"
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, header_bytes)
    return header_bytes + ciphertext


def decrypt(envelope: bytes, key: bytes) -> bytes:
    """Decrypt an envelope created by :func:`encrypt`.

    Raises:
        BackupArtifactError: the envelope is structurally invalid.
        BackupIntegrityError: authentication failed (wrong key or tampering).
    """
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    if not envelope.startswith(MAGIC):
        raise BackupArtifactError("not a CarbonTally backup envelope")
    body = envelope[len(MAGIC):]
    newline = body.find(b"\n")
    if newline < 0:
        raise BackupArtifactError("envelope header is not terminated")
    header_bytes = MAGIC + body[: newline + 1]
    ciphertext = body[newline + 1:]
    header = _decode_header(body[:newline])

    if header.get("v") != ENVELOPE_VERSION:
        raise BackupArtifactError(
            "unsupported envelope version", details={"version": header.get("v")}
        )
    if header.get("alg") != ALGORITHM:
        raise BackupArtifactError(
            "unsupported envelope algorithm", details={"alg": header.get("alg")}
        )
    try:
        nonce = base64.b64decode(str(header["nonce"]), validate=True)
    except (KeyError, ValueError) as exc:
        raise BackupArtifactError("envelope nonce is missing or invalid") from exc
    if len(nonce) != NONCE_BYTES:
        raise BackupArtifactError("envelope nonce has an invalid length")

    if len(key) != KEY_BYTES:
        raise BackupIntegrityError("encryption key must be exactly 32 bytes")
    try:
        return AESGCM(key).decrypt(nonce, ciphertext, header_bytes)
    except InvalidTag as exc:
        raise BackupIntegrityError(
            "artifact authentication failed: wrong encryption key or tampered ciphertext"
        ) from exc


def read_envelope_metadata(envelope: bytes) -> dict[str, str]:
    """Return the (non-secret) envelope header without decrypting.

    Useful for diagnostics and for selecting the correct key id.
    """
    if not envelope.startswith(MAGIC):
        raise BackupArtifactError("not a CarbonTally backup envelope")
    body = envelope[len(MAGIC):]
    newline = body.find(b"\n")
    if newline < 0:
        raise BackupArtifactError("envelope header is not terminated")
    header = _decode_header(body[:newline])
    return {
        "envelope_version": str(header.get("v")),
        "algorithm": str(header.get("alg")),
        "key_id": str(header.get("key_id")),
    }


def resolved_key_id(key_id: Optional[str]) -> str:
    """Return a usable key id for the envelope/manifest."""
    return (key_id or DEFAULT_KEY_ID).strip() or DEFAULT_KEY_ID


def _encode_header(header: dict[str, object]) -> bytes:
    return json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _decode_header(raw: bytes) -> dict[str, object]:
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BackupArtifactError("envelope header is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise BackupArtifactError("envelope header is not a JSON object")
    return parsed

