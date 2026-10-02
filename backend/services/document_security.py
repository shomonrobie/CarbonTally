"""Storage Management Step 1 — document security gate (lifecycle + scanning).

This module owns the **security state machine** and the **scanning boundary** for
customer/consultant-uploaded documents.  It implements the ratified target
lifecycle without inventing a vendor or a second tenancy:

    PENDING_UPLOAD -> SECURITY_CHECK_PENDING -> CLEAN | REJECTED
                                            -> PROCESSING -> FAILED

Design rules taken from the ratified product decisions and Step 1 scope:

* The client organisation is the storage anchor; nothing here is consultant
  specific.  Consultant provenance travels in application metadata/audit, never
  in a storage path or a second namespace.
* A document that has not passed the security gate **must not** enter normal
  emission-calculation processing (``create_document_and_enqueue`` and the
  direct-upload completion path both consult :func:`scan_document`).
* The built-in :class:`StructuralScanner` **always executes**.  It performs the
  server-side validations OWASP requires (extension allow-list, actual
  magic-byte detection, declared-vs-detected type agreement, filename/path
  safety, empty/truncated uploads) and detects the industry-standard EICAR test
  signature.
* An external malware scanner is an **integration/configuration boundary**
  (:data:`SCANNER_ENV_VAR`).  When it is not configured the verdict is recorded
  as ``structural`` — the platform never claims a document was virus-scanned.
  A configured provider that is unavailable degrades to the structural verdict
  and records that fact as a finding; the structural blockers still fail closed.
* No derivation, recompression, OCR or rasterisation happens here: the uploaded
  object is the evidence object and is never mutated.

Statuses are stored in the pre-existing free-text ``organization_files.status``
column (``VARCHAR`` with no CHECK constraint in the initial schema), so this
change needs no migration.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Callable, Optional, Protocol

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifecycle vocabulary (organization_files.status)
# ---------------------------------------------------------------------------

#: The browser has been given a signed upload URL but no object has been confirmed.
STATUS_PENDING_UPLOAD = "pending_upload"
#: The object exists and awaits the security gate.
STATUS_SECURITY_CHECK_PENDING = "security_check_pending"
#: The security gate accepted the object; it may enter normal processing.
STATUS_CLEAN = "clean"
#: The security gate rejected the object; it never enters processing.
STATUS_REJECTED = "rejected"
#: The object is in the normal processing pipeline.
STATUS_PROCESSING = "processing"
#: Processing failed terminally.
STATUS_FAILED = "failed"
#: Storage Management Step 2F — an **abandoned** upload: the browser was given a
#: signed upload URL and never completed it inside the completion window.  The
#: row is retained (provenance is never silently destroyed) but the state is
#: terminal: not processable, not downloadable, and completion is impossible.
STATUS_UPLOAD_EXPIRED = "upload_expired"
#: Pre-existing status written by the historical proxied upload path.  Treated
#: as accepted-by-legacy so existing rows are not retro-blocked.
LEGACY_STATUS_UPLOADED = "uploaded"

DOCUMENT_STATUSES: tuple[str, ...] = (
    STATUS_PENDING_UPLOAD,
    STATUS_SECURITY_CHECK_PENDING,
    STATUS_CLEAN,
    STATUS_REJECTED,
    STATUS_PROCESSING,
    STATUS_FAILED,
    STATUS_UPLOAD_EXPIRED,
    LEGACY_STATUS_UPLOADED,
)

#: Permitted status transitions (``current -> allowed targets``).  ``uploaded``
#: is the legacy entry point; ``clean``/``rejected`` are the gate outcomes and
#: are terminal for the gate itself (``clean`` may advance into processing).
STATUS_TRANSITIONS: dict[str, tuple[str, ...]] = {
    STATUS_PENDING_UPLOAD: (
        STATUS_SECURITY_CHECK_PENDING,
        STATUS_REJECTED,
        STATUS_UPLOAD_EXPIRED,
    ),
    STATUS_SECURITY_CHECK_PENDING: (STATUS_CLEAN, STATUS_REJECTED, STATUS_FAILED),
    LEGACY_STATUS_UPLOADED: (STATUS_SECURITY_CHECK_PENDING, STATUS_CLEAN, STATUS_REJECTED),
    STATUS_CLEAN: (STATUS_PROCESSING, STATUS_FAILED),
    STATUS_PROCESSING: (STATUS_FAILED,),
    STATUS_REJECTED: (),
    STATUS_FAILED: (STATUS_CLEAN,),
    # Step 2F — an abandoned upload is terminal: nothing may revive it, so an
    # expired authorisation can never be completed later.
    STATUS_UPLOAD_EXPIRED: (),
}

#: Statuses whose stored bytes may be signed for a download/preview.
DOWNLOADABLE_STATUSES: frozenset[str] = frozenset(
    {STATUS_CLEAN, STATUS_PROCESSING, LEGACY_STATUS_UPLOADED, STATUS_FAILED}
)

#: Statuses that must never enter the processing pipeline.
BLOCKED_FROM_PROCESSING: frozenset[str] = frozenset(
    {STATUS_REJECTED, STATUS_PENDING_UPLOAD, STATUS_UPLOAD_EXPIRED}
)


def can_transition(current: Optional[str], target: str) -> bool:
    """Return ``True`` when ``current -> target`` is a permitted transition.

    An unknown/legacy current status (including ``None``) may only move to a
    security-gate state — never straight to ``processing``.
    """
    if target not in DOCUMENT_STATUSES:
        return False
    if current is None:
        return target == STATUS_SECURITY_CHECK_PENDING
    if current == target:
        return True
    return target in STATUS_TRANSITIONS.get(current, ())


def is_processable(status: Optional[str]) -> bool:
    """Whether a document in ``status`` may enter normal processing."""
    if status is None:
        return False
    return status not in BLOCKED_FROM_PROCESSING


def is_downloadable(status: Optional[str]) -> bool:
    """Whether the stored bytes for ``status`` may be signed for a viewer.

    ``None`` (pre-existing rows written before this lifecycle existed) is treated
    as legacy-accepted so historical documents remain viewable.  A document in
    ``pending_upload``/``security_check_pending`` has not passed the gate, and a
    ``rejected`` (quarantined) document must never be served.
    """
    if status is None:
        return True
    return status in DOWNLOADABLE_STATUSES



# ---------------------------------------------------------------------------
# Scanning boundary
# ---------------------------------------------------------------------------

#: Environment variable selecting the malware-scanner integration.  Only the
#: built-in structural scanner ships in Step 1; any other value is treated as a
#: not-yet-installed provider and degrades honestly (see :func:`resolve_scanner`).
SCANNER_ENV_VAR = "CARBONTALLY_DOCUMENT_SCANNER"

#: Provider ids.
SCANNER_STRUCTURAL = "structural"
SCANNER_DISABLED = "disabled"

# ---------------------------------------------------------------------------
# Step 2D — explicit malware-scanning configuration and scanner result states
# ---------------------------------------------------------------------------
#
# Step 1 shipped the scanning boundary but never claimed a virus scan.  Step 2
# makes the boundary *explicit* and adds the state machine the brief requires,
# without inventing a vendor, a credential or a commercial commitment:
#
# * ``CARBONTALLY_DOCUMENT_SCANNER``              — which provider is configured;
# * ``CARBONTALLY_DOCUMENT_SCANNER_REQUIRED``     — whether an EXTERNAL verdict
#   is a precondition for normal processing.
#
# When the required switch is ON and no installed provider can return an
# external verdict, the document is **quarantined**, not accepted: a scanner
# that could not establish safety must never be reported as "clean".  A
# provider is installed by registering its factory (below); no provider is
# registered in this repository, so the honest default remains the structural
# gate.
SCANNER_REQUIRED_ENV_VAR = "CARBONTALLY_DOCUMENT_SCANNER_REQUIRED"

_TRUTHY = frozenset({"1", "true", "yes", "on", "required"})

#: Scanner result states.  Deliberately finer-grained than the lifecycle
#: verdict: "the scanner could not run / could not establish safety" is a
#: distinct outcome from "the document is clean" and from "the document is
#: malware", and must never be collapsed into either.
SCAN_STATE_CLEAN = "clean"
SCAN_STATE_MALWARE = "malware"
SCAN_STATE_STRUCTURAL_REJECTION = "structural_rejection"
SCAN_STATE_SCANNER_UNAVAILABLE = "scanner_unavailable"
SCAN_STATE_SCANNER_ERROR = "scanner_error"

SCAN_STATES: tuple[str, ...] = (
    SCAN_STATE_CLEAN,
    SCAN_STATE_MALWARE,
    SCAN_STATE_STRUCTURAL_REJECTION,
    SCAN_STATE_SCANNER_UNAVAILABLE,
    SCAN_STATE_SCANNER_ERROR,
)

#: The states in which a document may be treated as accepted by the gate.
ACCEPTING_SCAN_STATES: frozenset[str] = frozenset({SCAN_STATE_CLEAN})

#: Byte prefix inspected by the built-in scanner.  The ratified per-file cap is
#: 10 MiB, so the ordinary case inspects the whole object; the slice keeps the
#: check bounded if a larger object ever exists.
SCAN_PREFIX_BYTES = 262_144

#: Severities.
SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_BLOCKER = "blocker"

#: Industry-standard, harmless antivirus test string (EICAR).  Its presence is
#: proof that the gate is wired, not evidence that a real scanner ran.
EICAR_TEST_SIGNATURE = (
    b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
)

#: The document extensions the product classifies and can render inline.  This
#: is exactly the ``_RENDERABLE_MIME_BY_EXT`` vocabulary — no new product limit
#: and no new supported type is invented here.
ALLOWED_DOCUMENT_EXTENSIONS: frozenset[str] = frozenset(
    {"pdf", "jpg", "jpeg", "png", "gif", "webp", "bmp", "csv", "xlsx", "xls"}
)

#: Declared-extension -> content family.  A detected family that is not in the
#: declared extension's accepted set is a mismatch (blocker).
_EXTENSION_FAMILY: dict[str, str] = {
    "pdf": "pdf",
    "jpg": "image",
    "jpeg": "image",
    "png": "image",
    "gif": "image",
    "webp": "image",
    "bmp": "image",
    "xlsx": "zip_container",
    "xls": "ole_container",
    "csv": "text",
}

_FAMILY_COMPATIBILITY: dict[str, frozenset[str]] = {
    "pdf": frozenset({"pdf"}),
    "image": frozenset({"image"}),
    "zip_container": frozenset({"zip_container"}),
    "ole_container": frozenset({"ole_container"}),
    "text": frozenset({"text", "markup"}),
}

#: (prefix bytes, detected family, offset).  Ordered; first match wins.
_SIGNATURES: tuple[tuple[bytes, str, int], ...] = (
    (b"%PDF-", "pdf", 0),
    (b"\xff\xd8\xff", "image", 0),
    (b"\x89PNG\r\n\x1a\n", "image", 0),
    (b"GIF8", "image", 0),
    (b"BM", "image", 0),
    (b"PK\x03\x04", "zip_container", 0),
    (b"\xd0\xcf\x11\xe0", "ole_container", 0),
    (b"MZ", "executable", 0),
    (b"\x7fELF", "executable", 0),
    (b"\xca\xfe\xba\xbe", "executable", 0),
    (b"#!", "script", 0),
    (b"<!DOCTYPE", "markup", 0),
    (b"<html", "markup", 0),
    (b"<?xml", "markup", 0),
    (b"<svg", "markup", 0),
)

#: Families that are never acceptable as a stored evidence document.  For a
#: declared text type (csv) they are recorded as a warning instead: the bytes
#: stay inert (served as text) and rejecting a legitimate CSV whose first two
#: characters happen to be ``MZ`` would be a false positive on customer data.
_NEVER_ACCEPTED_FAMILIES: frozenset[str] = frozenset({"executable", "script"})

#: PDF active-content markers — reported, never silently stripped (the original
#: object is the evidence object and is never rewritten).
_PDF_ACTIVE_CONTENT_MARKERS: tuple[bytes, ...] = (
    b"/JavaScript",
    b"/JS ",
    b"/OpenAction",
    b"/Launch",
    b"/EmbeddedFile",
)


@dataclass(frozen=True, slots=True)
class ScanFinding:
    """One observation made by the security gate."""

    code: str
    detail: str
    severity: str = SEVERITY_INFO


@dataclass(frozen=True, slots=True)
class ScanVerdict:
    """The outcome of the security gate for one document."""

    verdict: str                       # ``clean`` | ``rejected``
    scanner: str                       # provider id that produced the verdict
    findings: tuple[ScanFinding, ...] = ()
    scanned_bytes: int = 0
    external_scan_available: bool = False
    #: Step 2D — the finer-grained scanner result state (see ``SCAN_STATES``).
    scan_state: str = SCAN_STATE_CLEAN
    #: Step 2D — whether an external verdict was a precondition for acceptance.
    external_scan_required: bool = False
    #: Step 2D — operator-facing reason when an external scanner could not run.
    scanner_error: str = ""

    @property
    def accepted(self) -> bool:
        """A document is accepted only on a clean, accepting scan state.

        Step 2D: a structural pass is not enough when an external scan was
        required and could not be obtained — ``scanner_unavailable`` /
        ``scanner_error`` are fail-closed and never counted as clean.
        """
        if self.verdict != STATUS_CLEAN:
            return False
        return self.scan_state in ACCEPTING_SCAN_STATES

    @property
    def blockers(self) -> tuple[ScanFinding, ...]:
        return tuple(f for f in self.findings if f.severity == SEVERITY_BLOCKER)

    @property
    def status(self) -> str:
        return STATUS_CLEAN if self.accepted else STATUS_REJECTED

    def external_scan_claimed(self) -> bool:
        """Whether this verdict may be described to a user as a virus scan.

        True only when the verdict actually came from an external provider — the
        platform never claims ``virus_scanned: true`` on a structural verdict.
        """
        return bool(self.external_scan_available) and self.scanner not in (
            SCANNER_STRUCTURAL,
            "",
        )

    def as_scanner_unavailable(self, *, required_provider: str, detail: str) -> "ScanVerdict":
        """Fail closed when a required external scan could not be obtained."""
        finding = ScanFinding(
            "scanner_unavailable",
            detail,
            SEVERITY_BLOCKER,
        )
        return ScanVerdict(
            verdict=STATUS_REJECTED,
            scanner=required_provider or self.scanner,
            findings=self.findings + (finding,),
            scanned_bytes=self.scanned_bytes,
            external_scan_available=False,
            scan_state=SCAN_STATE_SCANNER_UNAVAILABLE,
            external_scan_required=True,
            scanner_error=detail,
        )

    def as_scanner_error(self, *, error: str) -> "ScanVerdict":
        """Fail closed when the configured external scanner raised."""
        finding = ScanFinding("scanner_error", error, SEVERITY_BLOCKER)
        return ScanVerdict(
            verdict=STATUS_REJECTED,
            scanner=self.scanner,
            findings=self.findings + (finding,),
            scanned_bytes=self.scanned_bytes,
            external_scan_available=False,
            scan_state=SCAN_STATE_SCANNER_ERROR,
            external_scan_required=True,
            scanner_error=error,
        )

    def as_metadata(self) -> dict:
        """JSON-safe scan provenance for ``organization_files.metadata``.

        Byte content is never included — only codes, severities and short
        operator-facing details.
        """
        return {
            "verdict": self.verdict,
            "scanner": self.scanner,
            "scan_state": self.scan_state,
            "external_scan_available": self.external_scan_available,
            "external_scan_required": self.external_scan_required,
            "virus_scanned": self.external_scan_claimed(),
            "scanned_bytes": self.scanned_bytes,
            "scanner_error": self.scanner_error,
            "findings": [
                {"code": f.code, "severity": f.severity, "detail": f.detail}
                for f in self.findings
            ],
        }


class DocumentScanner(Protocol):
    """The scanning integration point."""

    name: str

    def scan(
        self,
        *,
        content: bytes,
        filename: str,
        declared_mime: str,
        extension: str,
    ) -> ScanVerdict:  # pragma: no cover - protocol
        ...



class StructuralScanner:
    """The built-in, vendor-free document security gate.

    It **always runs** and does not claim to be antivirus software: the verdict
    it produces is a *structural* verdict (extension/type/format/signature).
    Malware detection proper is the external scanner integration point.
    """

    name = SCANNER_STRUCTURAL

    def scan(
        self,
        *,
        content: bytes,
        filename: str,
        declared_mime: str,
        extension: str,
    ) -> ScanVerdict:
        from services.storage_keys import is_safe_filename, sanitize_display_name

        findings: list[ScanFinding] = []
        head = content[:SCAN_PREFIX_BYTES]

        if not content:
            findings.append(
                ScanFinding(
                    "empty_file",
                    "the uploaded object contains no bytes",
                    SEVERITY_BLOCKER,
                )
            )

        if not is_safe_filename(filename) or sanitize_display_name(filename) != filename:
            findings.append(
                ScanFinding(
                    "unsafe_filename",
                    "the supplied file name contains path separators or control "
                    "characters and is not accepted as provenance",
                    SEVERITY_BLOCKER,
                )
            )

        if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
            findings.append(
                ScanFinding(
                    "extension_not_allowed",
                    f"'.{extension}' is not an allowed document extension"
                    if extension
                    else "the upload has no file extension",
                    SEVERITY_BLOCKER,
                )
            )

        declared_family = _EXTENSION_FAMILY.get(extension)
        detected = _detect_family(head)

        if detected in _NEVER_ACCEPTED_FAMILIES:
            if declared_family == "text":
                findings.append(
                    ScanFinding(
                        "executable_signature_in_text",
                        f"executable/script signature '{detected}' found in a "
                        "text-declared document; the object is inert but flagged",
                        SEVERITY_WARNING,
                    )
                )
            else:
                findings.append(
                    ScanFinding(
                        "executable_content",
                        "the object carries an executable/script signature "
                        f"('{detected}') that is never accepted as evidence",
                        SEVERITY_BLOCKER,
                    )
                )
        elif detected is None:
            findings.append(
                ScanFinding(
                    "content_type_unverified",
                    "no recognised file signature was found; the content type "
                    "could not be confirmed from the bytes",
                    SEVERITY_WARNING,
                )
            )
        elif declared_family is None or detected not in _FAMILY_COMPATIBILITY.get(
            declared_family, frozenset()
        ):
            findings.append(
                ScanFinding(
                    "content_type_mismatch",
                    f"the bytes are '{detected}' but the document declares "
                    f"'.{extension}'",
                    SEVERITY_BLOCKER,
                )
            )
        else:
            findings.append(
                ScanFinding(
                    "content_type_confirmed",
                    f"declared '.{extension}' agrees with the detected "
                    f"'{detected}' content",
                )
            )

        if (declared_mime or "").strip().lower() in ("", "application/octet-stream"):
            findings.append(
                ScanFinding(
                    "declared_mime_generic",
                    "the browser supplied a generic content type; the stored "
                    "content type is the canonical type for the extension",
                    SEVERITY_WARNING,
                )
            )

        if EICAR_TEST_SIGNATURE in head:
            findings.append(
                ScanFinding(
                    "malware_signature",
                    "the industry-standard EICAR antivirus test signature was "
                    "detected",
                    SEVERITY_BLOCKER,
                )
            )

        if detected == "pdf" or extension == "pdf":
            for marker in _PDF_ACTIVE_CONTENT_MARKERS:
                if marker in head:
                    findings.append(
                        ScanFinding(
                            "pdf_active_content",
                            "the PDF contains the active-content marker "
                            f"'{marker.decode('latin-1').strip()}'",
                            SEVERITY_WARNING,
                        )
                    )

        rejected = any(f.severity == SEVERITY_BLOCKER for f in findings)
        # Step 2D — distinguish a detected malware signature from a structural
        # rejection so the recorded state is never ambiguous.
        malware = any(f.code == "malware_signature" for f in findings)
        if rejected:
            state = SCAN_STATE_MALWARE if malware else SCAN_STATE_STRUCTURAL_REJECTION
        else:
            state = SCAN_STATE_CLEAN
        return ScanVerdict(
            verdict=STATUS_REJECTED if rejected else STATUS_CLEAN,
            scanner=self.name,
            findings=tuple(findings),
            scanned_bytes=len(head),
            external_scan_available=False,
            scan_state=state,
        )


def _detect_family(head: bytes) -> Optional[str]:
    """Return the detected content family for ``head`` (or ``None``)."""
    for prefix, family, offset in _SIGNATURES:
        if head[offset : offset + len(prefix)] == prefix:
            if prefix == b"RIFF":
                return "image" if head[8:12] == b"WEBP" else "riff"
            return family
    return None




#: Installed external scanner providers: provider id -> factory.  A deployment
#: that has an approved malware-scanning provider registers its adapter here (or
#: imports a module that does) and points ``CARBONTALLY_DOCUMENT_SCANNER`` at the
#: provider id.  No provider is registered by this repository.
_SCANNER_REGISTRY: dict[str, Callable[[], DocumentScanner]] = {}


def register_scanner(provider_id: str, factory: Callable[[], DocumentScanner]) -> None:
    """Install a malware-scanner provider under ``provider_id``.

    The adapter must return a :class:`ScanVerdict` and must set
    ``external_scan_available=True`` only when it really obtained a provider
    verdict.  Registration performs no I/O and no credential handling.
    """
    key = (provider_id or "").strip().lower()
    if not key or key in (SCANNER_STRUCTURAL, SCANNER_DISABLED):
        raise ValueError("a scanner provider id must be a distinct, non-empty id")
    _SCANNER_REGISTRY[key] = factory


def unregister_scanner(provider_id: str) -> None:
    """Remove a registered provider (tests / explicit unwiring)."""
    _SCANNER_REGISTRY.pop((provider_id or "").strip().lower(), None)


def installed_scanners() -> tuple[str, ...]:
    """The provider ids installed in this process (never includes structural)."""
    return tuple(sorted(_SCANNER_REGISTRY))


def configured_scanner_id() -> str:
    """The provider id the deployment asked for (``""`` = not configured)."""
    return (os.getenv(SCANNER_ENV_VAR) or "").strip().lower()


def external_scan_required() -> bool:
    """Whether an external malware-scan verdict is a precondition to accept.

    Configured by ``CARBONTALLY_DOCUMENT_SCANNER_REQUIRED``.  Off by default:
    with the switch off the platform behaves exactly as Step 1 documented (the
    structural gate is the only gate and every verdict says so).
    """
    return (os.getenv(SCANNER_REQUIRED_ENV_VAR) or "").strip().lower() in _TRUTHY


def external_scan_status() -> dict:
    """Read-only description of the scanning configuration (for reports/ops)."""
    configured = configured_scanner_id()
    return {
        "configured_provider": configured or None,
        "installed_providers": list(installed_scanners()),
        "external_scan_required": external_scan_required(),
        "built_in_scanner": SCANNER_STRUCTURAL,
        "external_scan_available": configured in _SCANNER_REGISTRY,
    }


def resolve_scanner() -> DocumentScanner:
    """Return the configured scanner.

    * nothing configured (or the built-in id) -> the always-on structural gate;
    * a configured provider that IS installed -> that provider's adapter;
    * a configured provider that is NOT installed -> the structural gate, with a
      warning.  The recorded verdict then names the scanner that actually ran
      and leaves ``external_scan_available`` false, so the platform never claims
      a vendor scan it did not perform.  When an external scan is *required*
      (:func:`external_scan_required`) that honesty becomes fail-closed in
      :func:`scan_document` — the document is quarantined instead.

    An adapter that raises while being constructed degrades to the structural
    gate (quarantine rather than a crash; the verdict still never claims a scan).
    """
    configured = configured_scanner_id()
    if configured in ("", SCANNER_STRUCTURAL, "builtin", "built-in"):
        return StructuralScanner()
    factory = _SCANNER_REGISTRY.get(configured)
    if factory is not None:
        try:
            return factory()
        except Exception as exc:  # noqa: BLE001 - a broken adapter must not accept
            logger.error(
                "the configured document scanner %s could not be constructed (%s); "
                "no malware scan will be claimed",
                configured,
                exc,
            )
            return StructuralScanner()
    logger.warning(
        "%s=%s is not an installed scanner provider; using the built-in "
        "structural scanner (no malware scan is claimed)",
        SCANNER_ENV_VAR,
        configured,
    )
    return StructuralScanner()


def scan_document(
    *,
    content: bytes,
    filename: str,
    declared_mime: str = "",
    extension: Optional[str] = None,
    scanner: Optional[DocumentScanner] = None,
) -> ScanVerdict:
    """Run the configured security gate over ``content`` and return the verdict.

    Step 2D: when an external scan is required and the scanner that actually ran
    could not establish safety, the verdict is returned **fail-closed**
    (``scanner_unavailable``) instead of being reported as clean.  A scanner that
    raises produces ``scanner_error`` — also fail-closed — rather than an
    exception escaping into the upload path.
    """
    if extension is None:
        from services.storage_keys import split_extension

        extension = split_extension(filename)
    active = scanner or resolve_scanner()
    try:
        verdict = active.scan(
            content=content,
            filename=filename,
            declared_mime=declared_mime,
            extension=extension,
        )
    except Exception as exc:  # noqa: BLE001 - fail closed, never fail open
        logger.error("the document security gate raised (%s)", exc)
        return ScanVerdict(
            verdict=STATUS_REJECTED,
            scanner=getattr(active, "name", "") or "unknown",
            scan_state=SCAN_STATE_SCANNER_ERROR,
            external_scan_required=external_scan_required(),
            scanner_error=str(exc)[:300],
        ).as_scanner_error(error=f"the document security gate raised: {str(exc)[:200]}")
    if external_scan_required() and not verdict.external_scan_available:
        required = configured_scanner_id()
        return verdict.as_scanner_unavailable(
            required_provider=required,
            detail=(
                "an external malware scan is required for this deployment "
                f"({SCANNER_REQUIRED_ENV_VAR}=true) but the provider "
                f"'{required or 'not configured'}' is not installed/available; "
                "the document is quarantined and no malware-free status is claimed"
            ),
        )
    return verdict


def rejection_detail(verdict: ScanVerdict) -> str:
    """Operator-facing 422 detail for a rejected upload (never includes bytes)."""
    reasons = "; ".join(f.detail for f in verdict.blockers) or "security validation failed"
    return f"Document rejected by the security gate: {reasons}"
