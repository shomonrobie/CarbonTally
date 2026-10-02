"""Unit tests for the SigV4 signer (OID-3) and the S3-compatible object store.

Two layers are tested, and they are tested *differently* on purpose:

* **The signer** is a pure function, so it is pinned to the **published AWS
  worked example** — byte-exact ``canonical_request``, ``string_to_sign`` and
  signature. That is the only meaningful way to prove a hand-written signer is
  correct: no network, no credentials, no provider access. An implementation
  that passes this vector is interoperable; one that merely "looks right" is not.
* **The store** is exercised through ``httpx.MockTransport``, so every request is
  inspected as it would go on the wire (method, URL, signed headers) and every
  failure mode can be forced deterministically.

No test in this module performs network I/O, contacts a provider, or requires
credentials.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import httpx
import pytest

from backup.errors import BackupConfigurationError, BackupStorageError
from backup.s3store import S3ObjectStore
from backup.settings import BackupSettings
from backup.sigv4 import (
    ALGORITHM,
    EMPTY_SHA256,
    TERMINATOR,
    canonical_query_string,
    sign_request,
    uri_encode,
)
from backup.storage import LocalFilesystemObjectStore, build_object_store

# -- the published AWS S3 worked example -----------------------------------
# "Signature Calculations for the Authorization Header: Transferring Payload in
# a Single Chunk" (Amazon S3 API Reference): GET /test.txt on
# examplebucket.s3.amazonaws.com with a Range header, signed at
# 20130524T000000Z.
AWS_EXAMPLE_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_EXAMPLE_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
AWS_EXAMPLE_NOW = datetime(2013, 5, 24, 0, 0, 0, tzinfo=timezone.utc)
AWS_EXAMPLE_EXPECTED_CANONICAL_REQUEST = (
    "GET\n"
    "/test.txt\n"
    "\n"
    "host:examplebucket.s3.amazonaws.com\n"
    "range:bytes=0-9\n"
    f"x-amz-content-sha256:{EMPTY_SHA256}\n"
    "x-amz-date:20130524T000000Z\n"
    "\n"
    "host;range;x-amz-content-sha256;x-amz-date\n"
    f"{EMPTY_SHA256}"
)
AWS_EXAMPLE_EXPECTED_STRING_TO_SIGN = (
    f"{ALGORITHM}\n"
    "20130524T000000Z\n"
    f"20130524/us-east-1/s3/{TERMINATOR}\n"
    "7344ae5b7ee6c3e7e6b0fe0640412a37625d1fbfff95c48bbb2dc43964946972"
)
AWS_EXAMPLE_EXPECTED_SIGNATURE = (
    "f0e8bdb87c964420e857bd35b5d6ed310bd44f0170aba48dd91039c6036bdb41"
)


def _sign_aws_example():
    return sign_request(
        method="GET",
        url="https://examplebucket.s3.amazonaws.com/test.txt",
        region="us-east-1",
        service="s3",
        access_key=AWS_EXAMPLE_ACCESS_KEY,
        secret_key=AWS_EXAMPLE_SECRET_KEY,
        payload=b"",
        headers={"Range": "bytes=0-9"},
        now=AWS_EXAMPLE_NOW,
    )


class TestSigV4WorkedExample:
    """The signer must reproduce AWS's published output exactly."""

    def test_canonical_request_matches_aws(self) -> None:
        assert _sign_aws_example().canonical_request == (
            AWS_EXAMPLE_EXPECTED_CANONICAL_REQUEST
        )

    def test_string_to_sign_matches_aws(self) -> None:
        assert _sign_aws_example().string_to_sign == AWS_EXAMPLE_EXPECTED_STRING_TO_SIGN

    def test_signature_matches_aws(self) -> None:
        assert _sign_aws_example().signature == AWS_EXAMPLE_EXPECTED_SIGNATURE

    def test_authorization_header_matches_aws(self) -> None:
        assert _sign_aws_example().headers["Authorization"] == (
            f"{ALGORITHM} Credential={AWS_EXAMPLE_ACCESS_KEY}/"
            f"20130524/us-east-1/s3/{TERMINATOR}, "
            "SignedHeaders=host;range;x-amz-content-sha256;x-amz-date, "
            f"Signature={AWS_EXAMPLE_EXPECTED_SIGNATURE}"
        )

    def test_credential_scope_is_derived_from_the_timestamp(self) -> None:
        assert (
            _sign_aws_example().credential_scope
            == f"20130524/us-east-1/s3/{TERMINATOR}"
        )

    def test_returned_headers_are_complete_and_lower_case_signed(self) -> None:
        headers = _sign_aws_example().headers
        assert headers["Host"] == "examplebucket.s3.amazonaws.com"
        assert headers["x-amz-date"] == "20130524T000000Z"
        assert headers["x-amz-content-sha256"] == EMPTY_SHA256
        assert headers["Range"] == "bytes=0-9"  # caller's header is preserved


class TestUriEncoding:
    """The AWS encoder differs from the standard library in specific ways."""

    def test_unreserved_characters_pass_through(self) -> None:
        assert uri_encode("aZ0-_.~") == "aZ0-_.~"

    def test_slash_is_encoded_by_default_but_preserved_for_object_keys(self) -> None:
        assert uri_encode("a/b") == "a%2Fb"
        assert uri_encode("a/b", encode_slash=False) == "a/b"

    def test_space_becomes_percent_twenty_not_plus(self) -> None:
        assert uri_encode("a b") == "a%20b"

    def test_reserved_characters_are_encoded_with_upper_case_hex(self) -> None:
        assert uri_encode("k=v&x") == "k%3Dv%26x"
        assert uri_encode("=") == "%3D"

    def test_utf8_is_encoded_byte_wise(self) -> None:
        assert uri_encode("é") == "%C3%A9"


class TestCanonicalQueryString:
    def test_absent_query_is_the_empty_string(self) -> None:
        assert canonical_query_string("") == ""

    def test_pairs_are_sorted_by_key_then_value(self) -> None:
        assert canonical_query_string("b=2&a=1") == "a=1&b=2"
        assert canonical_query_string("a=2&a=1") == "a=1&a=2"

    def test_empty_valued_parameter_keeps_its_equals_sign(self) -> None:
        assert canonical_query_string("acl") == "acl="

    def test_values_are_decoded_then_re_encoded(self) -> None:
        assert canonical_query_string("prefix=a%2Fb") == "prefix=a%2Fb"
        assert canonical_query_string("prefix=a b") == "prefix=a%20b"

    def test_stray_separators_are_ignored(self) -> None:
        assert canonical_query_string("&&") == ""


class TestSignRequestBehaviour:
    def test_signing_is_deterministic_for_a_fixed_instant(self) -> None:
        first = _sign_aws_example()
        second = _sign_aws_example()
        assert first.signature == second.signature
        assert first.headers == second.headers

    def test_a_different_instant_changes_the_signature(self) -> None:
        later = sign_request(
            method="GET",
            url="https://examplebucket.s3.amazonaws.com/test.txt",
            region="us-east-1",
            service="s3",
            access_key=AWS_EXAMPLE_ACCESS_KEY,
            secret_key=AWS_EXAMPLE_SECRET_KEY,
            now=datetime(2013, 5, 25, 0, 0, 0, tzinfo=timezone.utc),
        )
        assert later.signature != AWS_EXAMPLE_EXPECTED_SIGNATURE

    def test_the_payload_is_covered_by_the_signature(self) -> None:
        """A tampered body must invalidate the signature (integrity, F11)."""
        original = sign_request(
            method="PUT",
            url="https://examplebucket.s3.amazonaws.com/backup.enc",
            region="us-east-1",
            service="s3",
            access_key=AWS_EXAMPLE_ACCESS_KEY,
            secret_key=AWS_EXAMPLE_SECRET_KEY,
            payload=b"ciphertext-a",
            now=AWS_EXAMPLE_NOW,
        )
        tampered = sign_request(
            method="PUT",
            url="https://examplebucket.s3.amazonaws.com/backup.enc",
            region="us-east-1",
            service="s3",
            access_key=AWS_EXAMPLE_ACCESS_KEY,
            secret_key=AWS_EXAMPLE_SECRET_KEY,
            payload=b"ciphertext-b",
            now=AWS_EXAMPLE_NOW,
        )
        assert original.signature != tampered.signature
        assert original.headers["x-amz-content-sha256"] == hashlib.sha256(
            b"ciphertext-a"
        ).hexdigest()
        assert original.headers["x-amz-content-sha256"] != EMPTY_SHA256

    def test_signed_headers_are_lower_cased_and_alphabetical(self) -> None:
        signed = sign_request(
            method="PUT",
            url="https://examplebucket.s3.amazonaws.com/backup.enc",
            region="us-east-1",
            service="s3",
            access_key=AWS_EXAMPLE_ACCESS_KEY,
            secret_key=AWS_EXAMPLE_SECRET_KEY,
            headers={"Content-Type": "application/octet-stream", "X-Custom": " v "},
            now=AWS_EXAMPLE_NOW,
        )
        signed_headers = signed.canonical_request.split("\n\n")[2].split("\n")[0]
        assert signed_headers == (
            "content-type;host;x-amz-content-sha256;x-amz-date;x-custom"
        )
        # the canonical header block is alphabetical and its values are trimmed
        header_block = signed.canonical_request.split("\n\n")[1]
        assert header_block.split("\n") == [
            "content-type:application/octet-stream",
            "host:examplebucket.s3.amazonaws.com",
            f"x-amz-content-sha256:{EMPTY_SHA256}",
            "x-amz-date:20130524T000000Z",
            "x-custom:v",
        ]

    def test_a_blank_credential_is_refused_rather_than_defaulted(self) -> None:
        for field in ("region", "service", "access_key", "secret_key"):
            kwargs = {
                "method": "GET",
                "url": "https://examplebucket.s3.amazonaws.com/x",
                "region": "us-east-1",
                "service": "s3",
                "access_key": AWS_EXAMPLE_ACCESS_KEY,
                "secret_key": AWS_EXAMPLE_SECRET_KEY,
            }
            kwargs[field] = ""
            with pytest.raises(ValueError):
                sign_request(**kwargs)  # type: ignore[arg-type]

    def test_a_relative_url_is_refused(self) -> None:
        with pytest.raises(ValueError):
            sign_request(
                method="GET",
                url="/test.txt",
                region="us-east-1",
                service="s3",
                access_key=AWS_EXAMPLE_ACCESS_KEY,
                secret_key=AWS_EXAMPLE_SECRET_KEY,
            )

    def test_repr_never_reveals_the_signature(self) -> None:
        rendered = repr(_sign_aws_example())
        assert AWS_EXAMPLE_EXPECTED_SIGNATURE not in rendered
        assert AWS_EXAMPLE_SECRET_KEY not in rendered
        assert "signature=<set>" in rendered


# -- S3 provider fixtures --------------------------------------------------

ENDPOINT = "https://projectref.supabase.co/storage/v1/s3"
BUCKET = "carbontally-backups"
ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
SECRET_KEY = "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY"
S3_NS = "http://s3.amazonaws.com/doc/2006-03-01/"


def _s3_settings(**overrides: str) -> BackupSettings:
    env = {
        "CT_BACKUP_OBJECT_STORE": "s3",
        "CT_BACKUP_S3_ENDPOINT": ENDPOINT,
        "CT_BACKUP_S3_BUCKET": BUCKET,
        "CT_BACKUP_S3_ACCESS_KEY": ACCESS_KEY,
        "CT_BACKUP_S3_SECRET_KEY": SECRET_KEY,
    }
    env.update(overrides)
    return BackupSettings.from_env(env)


def _store(
    handler, *, seen: list[httpx.Request] | None = None, **overrides: str
) -> S3ObjectStore:
    """Build a store whose transport is a mock, recording every request."""

    def recording_handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return handler(request)

    return S3ObjectStore(
        _s3_settings(**overrides),
        client=httpx.AsyncClient(transport=httpx.MockTransport(recording_handler)),
    )


def _list_xml(
    entries: list[tuple[str, int, str, str]],
    *,
    truncated: bool = False,
    token: str | None = None,
) -> str:
    body = "".join(
        f"<Contents><Key>{key}</Key><Size>{size}</Size>"
        f"<LastModified>{modified}</LastModified><ETag>{etag}</ETag></Contents>"
        for key, size, modified, etag in entries
    )
    tail = "<IsTruncated>false</IsTruncated>"
    if truncated:
        tail = "<IsTruncated>true</IsTruncated>"
        if token:
            tail += f"<NextContinuationToken>{token}</NextContinuationToken>"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<ListBucketResult xmlns="{S3_NS}">{body}{tail}</ListBucketResult>'
    )


class TestS3Settings:
    def test_s3_is_now_an_accepted_object_store(self) -> None:
        settings = _s3_settings()
        assert settings.object_store == "s3"
        assert settings.s3_endpoint == ENDPOINT
        assert settings.s3_bucket == BUCKET

    def test_region_and_addressing_have_production_safe_defaults(self) -> None:
        settings = _s3_settings()
        assert settings.s3_region == "us-east-1"
        assert settings.s3_path_style is True  # Supabase Storage is path-style
        assert settings.s3_prefix == ""

    def test_addressing_can_be_switched_to_virtual_host(self) -> None:
        assert _s3_settings(CT_BACKUP_S3_PATH_STYLE="0").s3_path_style is False
        assert _s3_settings(CT_BACKUP_S3_PATH_STYLE="false").s3_path_style is False
        assert _s3_settings(CT_BACKUP_S3_PATH_STYLE="1").s3_path_style is True

    def test_require_s3_returns_the_tuple_the_store_needs(self) -> None:
        assert _s3_settings().require_s3() == (
            ENDPOINT,
            "us-east-1",
            BUCKET,
            ACCESS_KEY,
            SECRET_KEY,
        )

    def test_require_s3_names_every_missing_setting(self) -> None:
        settings = BackupSettings.from_env({"CT_BACKUP_OBJECT_STORE": "s3"})
        with pytest.raises(BackupConfigurationError) as excinfo:
            settings.require_s3()
        missing = excinfo.value.details["missing"]
        assert missing == [
            "CT_BACKUP_S3_ACCESS_KEY",
            "CT_BACKUP_S3_BUCKET",
            "CT_BACKUP_S3_ENDPOINT",
            "CT_BACKUP_S3_SECRET_KEY",
        ]

    def test_selecting_s3_dispatches_to_the_s3_store(self) -> None:
        """The factory is the *only* place that decides which provider to build."""
        store = build_object_store(_s3_settings())
        assert isinstance(store, S3ObjectStore)

    def test_unrelated_stores_are_not_required_to_be_configured(self) -> None:
        """Selecting local must never demand S3 credentials."""
        settings = BackupSettings.from_env({"CT_BACKUP_OBJECT_STORE": "local"})
        assert settings.s3_endpoint == ""
        assert settings.s3_bucket == ""
        assert isinstance(build_object_store(settings), LocalFilesystemObjectStore)

    def test_secrets_are_never_repr_ed(self) -> None:
        rendered = repr(_s3_settings())
        assert SECRET_KEY not in rendered
        assert ACCESS_KEY not in rendered
        assert "s3_secret_key=<set>" in rendered
        assert "s3_access_key=<set>" in rendered

    def test_build_object_store_selects_the_s3_provider(self) -> None:
        store = build_object_store(_s3_settings())
        assert isinstance(store, S3ObjectStore)
        assert repr(store) == (
            "S3ObjectStore(region='us-east-1', bucket='carbontally-backups', "
            "path_style=True, access_key=<set>, secret=<set>)"
        )


class TestS3ObjectStore:
    async def test_put_signs_and_sends_a_path_style_put(self) -> None:
        seen: list[httpx.Request] = []
        store = _store(
            lambda request: httpx.Response(
                200, headers={"ETag": '"d41d8cd98f00b204e9800998ecf8427e"'}
            ),
            seen=seen,
        )
        stored = await store.put_object(
            "backups/abc/artifact.enc",
            b"ciphertext",
            content_type="application/octet-stream",
            metadata={"backup-id": "abc"},
        )

        request = seen[0]
        assert request.method == "PUT"
        assert str(request.url) == f"{ENDPOINT}/{BUCKET}/backups/abc/artifact.enc"
        assert request.headers["authorization"].startswith(
            f"{ALGORITHM} Credential={ACCESS_KEY}/"
        )
        assert request.headers["x-amz-date"]
        assert request.headers["x-amz-content-sha256"] == hashlib.sha256(
            b"ciphertext"
        ).hexdigest()
        assert request.headers["x-amz-meta-backup-id"] == "abc"
        assert request.headers["content-type"] == "application/octet-stream"
        assert request.content == b"ciphertext"

        assert stored.key == "backups/abc/artifact.enc"
        assert stored.size_bytes == len(b"ciphertext")
        # F11: S3 gives no SHA-256 guarantee, so the application digest is absent
        # and the ETag is reported as a *provider* checksum instead.
        assert stored.content_sha256 is None
        assert stored.provider_checksum == '"d41d8cd98f00b204e9800998ecf8427e"'
        assert stored.provider_checksum_algorithm == "etag-md5"
        assert stored.metadata == {"backup-id": "abc"}

    async def test_multipart_etags_are_not_labelled_as_md5(self) -> None:
        store = _store(
            lambda request: httpx.Response(200, headers={"ETag": '"abc-4"'})
        )
        stored = await store.put_object("k", b"x")
        assert stored.provider_checksum_algorithm == "etag-multipart"

    async def test_configured_prefix_is_applied_and_reported(self) -> None:
        seen: list[httpx.Request] = []
        store = _store(
            lambda request: httpx.Response(200),
            seen=seen,
            CT_BACKUP_S3_PREFIX="carbontally/",
        )
        stored = await store.put_object("backups/abc/artifact.enc", b"x")
        assert stored.key == "carbontally/backups/abc/artifact.enc"
        assert str(seen[0].url).endswith(
            f"/{BUCKET}/carbontally/backups/abc/artifact.enc"
        )

    async def test_get_returns_the_bytes_and_sends_a_bodyless_sha256(self) -> None:
        seen: list[httpx.Request] = []
        store = _store(
            lambda request: httpx.Response(200, content=b"ciphertext"), seen=seen
        )
        assert await store.get_object("backups/abc/artifact.enc") == b"ciphertext"
        assert seen[0].method == "GET"
        assert seen[0].headers["x-amz-content-sha256"] == EMPTY_SHA256
        assert seen[0].content == b""

    async def test_missing_object_raises_a_typed_error(self) -> None:
        store = _store(lambda request: httpx.Response(404))
        with pytest.raises(BackupStorageError) as excinfo:
            await store.get_object("backups/abc/absent.enc")
        assert excinfo.value.code == "BACKUP_STORAGE_ERROR"
        assert excinfo.value.http_status == 502
        assert excinfo.value.details["key"] == "backups/abc/absent.enc"

    async def test_head_parses_metadata_without_a_body(self) -> None:
        seen: list[httpx.Request] = []
        store = _store(
            lambda request: httpx.Response(
                200,
                headers={
                    "Content-Length": "42",
                    "ETag": '"9c1e2f"',
                    "Last-Modified": "Wed, 01 Oct 2026 10:00:00 GMT",
                    "Content-Type": "application/octet-stream",
                    "x-amz-meta-key-id": "key-v1",
                },
            ),
            seen=seen,
        )
        head = await store.head_object("backups/abc/artifact.enc")
        assert seen[0].method == "HEAD"
        assert head.size_bytes == 42
        assert head.created_at == "Wed, 01 Oct 2026 10:00:00 GMT"
        assert head.content_sha256 is None
        assert head.provider_checksum == '"9c1e2f"'
        assert head.provider_checksum_algorithm == "etag-md5"
        assert head.metadata == {"key-id": "key-v1"}

    async def test_list_follows_continuation_tokens(self) -> None:
        seen: list[httpx.Request] = []
        first = _list_xml(
            [("backups/1/a.enc", 11, "2026-10-01T10:00:00.000Z", '"e1"')],
            truncated=True,
            token="NEXT-TOKEN",
        )
        second = _list_xml(
            [("backups/2/b.enc", 22, "2026-10-02T10:00:00.000Z", '"e2"')]
        )

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.params.get("continuation-token"):
                return httpx.Response(200, text=second)
            return httpx.Response(200, text=first)

        store = _store(handler, seen=seen)
        items = await store.list_objects("backups/")

        assert [item.key for item in items] == ["backups/1/a.enc", "backups/2/b.enc"]
        assert items[0].size_bytes == 11
        assert items[0].provider_checksum == '"e1"'
        assert len(seen) == 2
        assert seen[0].url.params.get("list-type") == "2"
        assert seen[0].url.params.get("prefix") == "backups/"
        assert seen[0].url.params.get("continuation-token") is None
        assert seen[1].url.params.get("continuation-token") == "NEXT-TOKEN"

    async def test_list_stops_when_the_provider_is_not_truncated(self) -> None:
        seen: list[httpx.Request] = []
        store = _store(
            lambda request: httpx.Response(
                200,
                text=_list_xml(
                    [("backups/1/a.enc", 1, "2026-10-01T10:00:00.000Z", '"e"')]
                ),
            ),
            seen=seen,
        )
        assert len(await store.list_objects()) == 1
        assert len(seen) == 1

    async def test_delete_is_idempotent(self) -> None:
        for status in (204, 200, 404):
            store = _store(lambda request, status=status: httpx.Response(status))
            await store.delete_object("backups/abc/artifact.enc")

    async def test_provider_error_is_reported_without_echoing_the_body(self) -> None:
        body = (
            '<?xml version="1.0"?><Error><Code>AccessDenied</Code>'
            f"<Message>{'x' * 500}secret-body</Message></Error>"
        )
        store = _store(lambda request: httpx.Response(403, text=body))
        with pytest.raises(BackupStorageError) as excinfo:
            await store.put_object("backups/abc/artifact.enc", b"ciphertext")
        error = excinfo.value
        assert error.details["status"] == 403
        assert error.details["reason"].startswith("AccessDenied")
        assert len(error.details["reason"]) < 300
        assert "secret-body" not in str(error)
        assert SECRET_KEY not in str(error)
        assert SECRET_KEY not in repr(error.details)

    async def test_a_non_xml_error_body_still_yields_a_reason(self) -> None:
        store = _store(lambda request: httpx.Response(503, text="<html>oops"))
        with pytest.raises(BackupStorageError) as excinfo:
            await store.get_object("backups/abc/artifact.enc")
        assert excinfo.value.details["status"] == 503
        assert excinfo.value.details["reason"]

    async def test_transport_failure_becomes_a_typed_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        store = _store(handler)
        with pytest.raises(BackupStorageError) as excinfo:
            await store.get_object("backups/abc/artifact.enc")
        assert excinfo.value.details["reason"] == "ConnectError"

    async def test_virtual_host_addressing_for_aws_style_endpoints(self) -> None:
        seen: list[httpx.Request] = []
        store = _store(
            lambda request: httpx.Response(200),
            seen=seen,
            CT_BACKUP_S3_ENDPOINT="https://s3.amazonaws.com",
            CT_BACKUP_S3_PATH_STYLE="0",
        )
        await store.put_object("backups/abc/artifact.enc", b"x")
        assert str(seen[0].url) == (
            f"https://{BUCKET}.s3.amazonaws.com/backups/abc/artifact.enc"
        )

    async def test_special_characters_in_a_key_are_uri_encoded(self) -> None:
        seen: list[httpx.Request] = []
        store = _store(lambda request: httpx.Response(200), seen=seen)
        await store.put_object("backups/a b/artifact.enc", b"x")
        assert str(seen[0].url).endswith(f"/{BUCKET}/backups/a%20b/artifact.enc")

    async def test_an_injected_client_is_not_closed_by_the_store(self) -> None:
        store = _store(lambda request: httpx.Response(200, content=b"ciphertext"))
        await store.aclose()
        assert await store.get_object("backups/abc/artifact.enc") == b"ciphertext"

    async def test_the_store_satisfies_the_object_store_protocol(self) -> None:
        from backup.storage import ObjectStore

        assert isinstance(_store(lambda request: httpx.Response(200)), ObjectStore)
