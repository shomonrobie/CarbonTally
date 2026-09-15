"""Phase 8 B4/S5 — frozen artefact domain rules (pure unit tests).

Locks PO `B4-D5/D6/D7`: mandatory artefact, single private bucket, **derived**
object key, SHA-256 integrity, and no rewrite of an existing frozen artefact.
"""
from __future__ import annotations

import hashlib

import pytest

from domain.disclosure import DisclosureViolation
from domain.report_artefact import (
    ARTEFACT_BUCKET,
    ARTEFACT_CONTENT_TYPE,
    FrozenArtefact,
    assert_artefact_matches,
    build_artefact,
    compute_sha256,
    object_key_for,
    validate_artefact_payload,
    validate_sha256,
)

PDF = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n"
ORG = "11111111-1111-4111-8111-111111111111"
REP = "22222222-2222-4222-8222-222222222222"
VER = "33333333-3333-4333-8333-333333333333"


def test_object_key_is_derived_from_the_row() -> None:
    assert object_key_for(ORG, REP, VER) == f"{ORG}/{REP}/{VER}.pdf"


@pytest.mark.parametrize("kwargs", [
    {"organization_id": ""},
    {"report_id": ""},
    {"report_version_id": ""},
])
def test_object_key_requires_every_identifier(kwargs) -> None:
    args = {"organization_id": ORG, "report_id": REP, "report_version_id": VER} | kwargs
    with pytest.raises(DisclosureViolation):
        object_key_for(**args)


def test_sha256_is_lowercase_hex_of_the_bytes() -> None:
    assert compute_sha256(PDF) == hashlib.sha256(PDF).hexdigest()
    assert compute_sha256(PDF) != compute_sha256(PDF + b"x")


def test_build_artefact_records_the_mandate() -> None:
    artefact = build_artefact(
        organization_id=ORG, report_id=REP, report_version_id=VER, payload=PDF
    )
    assert artefact.storage_bucket == ARTEFACT_BUCKET == "report-artifacts"
    assert artefact.content_type == ARTEFACT_CONTENT_TYPE == "application/pdf"
    assert artefact.object_key == f"{ORG}/{REP}/{VER}.pdf"
    assert artefact.content_sha256 == hashlib.sha256(PDF).hexdigest()
    assert artefact.byte_size == len(PDF)


def test_record_shape_has_no_url_field() -> None:
    artefact = build_artefact(
        organization_id=ORG, report_id=REP, report_version_id=VER, payload=PDF
    )
    record = artefact.as_record(produced_by="u-1")
    assert "signed_url" not in record
    assert record["produced_by"] == "u-1"


def test_empty_payload_is_refused() -> None:
    with pytest.raises(DisclosureViolation):
        validate_artefact_payload(b"")


def test_non_pdf_payload_is_refused() -> None:
    with pytest.raises(DisclosureViolation):
        validate_artefact_payload(b"{\"json\": true}")


def test_alternative_bucket_is_refused() -> None:
    with pytest.raises(DisclosureViolation):
        build_artefact(
            organization_id=ORG, report_id=REP, report_version_id=VER, payload=PDF,
            storage_bucket="documents",
        )


def test_alternative_content_type_is_refused() -> None:
    with pytest.raises(DisclosureViolation):
        build_artefact(
            organization_id=ORG, report_id=REP, report_version_id=VER, payload=PDF,
            content_type="text/html",
        )


@pytest.mark.parametrize("value", ["", "zz", "a" * 63, "a" * 65, "sha256:abc", "g" * 64])
def test_invalid_hashes_are_refused(value: str) -> None:
    with pytest.raises(DisclosureViolation):
        validate_sha256(value)


def test_valid_hash_is_normalised_to_lowercase() -> None:
    assert validate_sha256("A" * 64) == "a" * 64


def test_matching_artefact_is_accepted() -> None:
    artefact = build_artefact(
        organization_id=ORG, report_id=REP, report_version_id=VER, payload=PDF
    )
    assert_artefact_matches(artefact, PDF)  # no raise


def test_mismatched_render_is_refused_never_rewritten() -> None:
    artefact = build_artefact(
        organization_id=ORG, report_id=REP, report_version_id=VER, payload=PDF
    )
    with pytest.raises(DisclosureViolation) as excinfo:
        assert_artefact_matches(artefact, PDF + b"\n% changed after approval")
    assert "never rewritten" in str(excinfo.value)


def test_frozen_artefact_is_immutable_by_construction() -> None:
    artefact = build_artefact(
        organization_id=ORG, report_id=REP, report_version_id=VER, payload=PDF
    )
    assert isinstance(artefact, FrozenArtefact)
    with pytest.raises(Exception):
        artefact.content_sha256 = "0" * 64  # type: ignore[misc]
