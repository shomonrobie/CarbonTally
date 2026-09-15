"""Phase 8 B4/S5 — frozen report artefact (pure, no I/O).

Implements PO decision **`B4-D5`/`B4-D6`/`B4-D7`** (contract §25 Amendment 3):

* the artefact is **mandatory** at finalisation — there is deliberately **no**
  optional/exception path, so nothing in this module can express "FINAL without a
  frozen artefact";
* **one** record per finalised report version;
* the private bucket is a single named constant (`report-artifacts`); no external
  storage, no alternative bucket;
* the object key is **derived**, never supplied: it cannot drift from the row;
* integrity is **SHA-256** lowercase hex — no SHA-512, no MD5 fallback.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Optional

from domain.disclosure import DisclosureViolation

#: B4-D6: the only bucket the frozen artefact may live in (private).
ARTEFACT_BUCKET = "report-artifacts"

#: B4-D6: the only content type a frozen artefact may have.
ARTEFACT_CONTENT_TYPE = "application/pdf"

#: A PDF must begin with this marker (a cheap structural sanity check).
PDF_MAGIC = b"%PDF-"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class FrozenArtefact:
    """The validated description of one frozen artefact."""

    organization_id: str
    report_id: str
    report_version_id: str
    storage_bucket: str
    object_key: str
    content_sha256: str
    byte_size: int
    content_type: str = ARTEFACT_CONTENT_TYPE

    def as_record(self, *, produced_by: Optional[str] = None) -> dict:
        return {
            "organization_id": self.organization_id,
            "report_id": self.report_id,
            "report_version_id": self.report_version_id,
            "storage_bucket": self.storage_bucket,
            "object_key": self.object_key,
            "content_sha256": self.content_sha256,
            "byte_size": self.byte_size,
            "content_type": self.content_type,
            "produced_by": produced_by,
        }


def object_key_for(organization_id: str, report_id: str, report_version_id: str) -> str:
    """B4-D6: the mandated key layout — derived, never accepted from a caller."""
    for label, value in (
        ("organization_id", organization_id),
        ("report_id", report_id),
        ("report_version_id", report_version_id),
    ):
        if not value:
            raise DisclosureViolation(f"B4 artefact: {label} is required to derive the object key")
    return f"{organization_id}/{report_id}/{report_version_id}.pdf"


def compute_sha256(payload: bytes) -> str:
    """B4-D7: SHA-256, lowercase hex."""
    return hashlib.sha256(payload).hexdigest()


def validate_sha256(value: str) -> str:
    normalised = (value or "").strip().lower()
    if not _SHA256_RE.match(normalised):
        raise DisclosureViolation(f"B4 artefact: content_sha256 must be 64 lowercase hex chars, got {value!r}")
    return normalised


def validate_artefact_payload(payload: bytes) -> bytes:
    """A frozen artefact must be real, non-empty PDF bytes."""
    if not payload:
        raise DisclosureViolation("B4 artefact: the rendered PDF is empty — finalisation is refused")
    if not payload.startswith(PDF_MAGIC):
        raise DisclosureViolation(
            "B4 artefact: the rendered artefact is not a PDF — finalisation is refused"
        )
    return payload


def build_artefact(
    *,
    organization_id: str,
    report_id: str,
    report_version_id: str,
    payload: bytes,
    storage_bucket: str = ARTEFACT_BUCKET,
    content_type: str = ARTEFACT_CONTENT_TYPE,
) -> FrozenArtefact:
    """Validate a rendered payload into a frozen-artefact description."""
    if storage_bucket != ARTEFACT_BUCKET:
        raise DisclosureViolation(
            f"B4 artefact: only the private {ARTEFACT_BUCKET!r} bucket is permitted (got {storage_bucket!r})"
        )
    if content_type != ARTEFACT_CONTENT_TYPE:
        raise DisclosureViolation(
            f"B4 artefact: only {ARTEFACT_CONTENT_TYPE!r} is permitted (got {content_type!r})"
        )
    body = validate_artefact_payload(payload)
    return FrozenArtefact(
        organization_id=str(organization_id),
        report_id=str(report_id),
        report_version_id=str(report_version_id),
        storage_bucket=storage_bucket,
        object_key=object_key_for(str(organization_id), str(report_id), str(report_version_id)),
        content_sha256=compute_sha256(body),
        byte_size=len(body),
        content_type=content_type,
    )


def assert_artefact_matches(artefact: FrozenArtefact, payload: bytes) -> None:
    """Refuse to finalise when an existing artefact disagrees with the render."""
    actual = compute_sha256(payload)
    if actual != artefact.content_sha256:
        raise DisclosureViolation(
            "B4 artefact: this report version already has a frozen artefact with a "
            "different hash - the artefact is never rewritten (D15/DM-7); create a new version"
        )
