"""Unit tests for backup encryption (``backup.crypto``) — D3.

Covers: round trip, wrong-key rejection, ciphertext tamper detection, header
authenticity, envelope metadata and key handling.
"""
from __future__ import annotations

import base64

import pytest

from backup.crypto import (
    ALGORITHM,
    ENVELOPE_VERSION,
    MAGIC,
    decrypt,
    encode_key,
    encrypt,
    generate_key,
    read_envelope_metadata,
)
from backup.errors import BackupArtifactError, BackupIntegrityError

PLAINTEXT = b"COPY public.organizations (id) FROM stdin;\n1\tAcme\n\\.\n"


class TestRoundTrip:
    def test_encrypt_then_decrypt_restores_plaintext(self) -> None:
        key = generate_key()
        envelope = encrypt(PLAINTEXT, key, key_id="unit-key")
        assert decrypt(envelope, key) == PLAINTEXT

    def test_envelope_does_not_contain_the_plaintext(self) -> None:
        key = generate_key()
        envelope = encrypt(PLAINTEXT, key, key_id="unit-key")
        assert PLAINTEXT not in envelope
        assert b"Acme" not in envelope

    def test_envelope_does_not_contain_the_key(self) -> None:
        key = generate_key()
        envelope = encrypt(PLAINTEXT, key, key_id="unit-key")
        assert key not in envelope
        assert base64.b64encode(key) not in envelope

    def test_envelope_metadata_is_readable_without_the_key(self) -> None:
        envelope = encrypt(PLAINTEXT, generate_key(), key_id="metadata-key")
        metadata = read_envelope_metadata(envelope)
        assert metadata["algorithm"] == ALGORITHM
        assert metadata["key_id"] == "metadata-key"
        assert metadata["envelope_version"] == str(ENVELOPE_VERSION)
        assert envelope.startswith(MAGIC)

    def test_nonce_differs_between_encryptions(self) -> None:
        key = generate_key()
        first = encrypt(PLAINTEXT, key)
        second = encrypt(PLAINTEXT, key)
        assert first != second
        assert read_envelope_metadata(first)["key_id"] == read_envelope_metadata(second)["key_id"]


class TestKeyHandling:
    def test_generate_key_is_32_bytes_and_unique(self) -> None:
        first, second = generate_key(), generate_key()
        assert len(first) == 32 and first != second

    def test_encode_key_round_trips_via_base64(self) -> None:
        key = generate_key()
        assert base64.b64decode(encode_key(key)) == key

    def test_encode_key_rejects_wrong_length(self) -> None:
        with pytest.raises(ValueError):
            encode_key(b"short")

    def test_encrypt_rejects_malformed_key(self) -> None:
        with pytest.raises(BackupIntegrityError):
            encrypt(PLAINTEXT, b"too-short")

    def test_decrypt_rejects_malformed_key(self) -> None:
        envelope = encrypt(PLAINTEXT, generate_key())
        with pytest.raises(BackupIntegrityError):
            decrypt(envelope, b"too-short")


class TestTamperAndWrongKey:
    def test_wrong_key_is_rejected(self) -> None:
        envelope = encrypt(PLAINTEXT, generate_key())
        with pytest.raises(BackupIntegrityError):
            decrypt(envelope, generate_key())

    def test_tampered_ciphertext_is_rejected(self) -> None:
        key = generate_key()
        envelope = bytearray(encrypt(PLAINTEXT, key))
        envelope[-1] ^= 0x01
        with pytest.raises(BackupIntegrityError):
            decrypt(bytes(envelope), key)

    def test_tampered_header_is_rejected(self) -> None:
        key = generate_key()
        envelope = encrypt(PLAINTEXT, key, key_id="header-key")
        tampered = envelope.replace(b"header-key", b"header-kez")
        assert tampered != envelope
        with pytest.raises((BackupIntegrityError, BackupArtifactError)):
            decrypt(tampered, key)

    def test_non_envelope_input_is_rejected(self) -> None:
        with pytest.raises(BackupArtifactError):
            decrypt(b"not-an-envelope", generate_key())

    def test_unterminated_header_is_rejected(self) -> None:
        with pytest.raises(BackupArtifactError):
            decrypt(MAGIC + b'{"v":1}', generate_key())

    def test_unsupported_envelope_version_is_rejected(self) -> None:
        key = generate_key()
        envelope = encrypt(PLAINTEXT, key)
        forged = MAGIC + b'{"alg":"AES-256-GCM","key_id":"k","nonce":"AAAAAAAAAAAAAAAA","v":99}\n' + b"x"
        with pytest.raises(BackupArtifactError):
            decrypt(forged, key)
        assert decrypt(envelope, key) == PLAINTEXT
