"""CT-FINAL-01 — canonical server-side upload policy.

There is **one authoritative source** for the effective upload limits: the
persisted admin-configurable upload policy (``system_settings`` /
``api.v3_settings`` — CarbonTally Admin Panel → Upload Policy).  Every
application upload ingress path resolves that policy (``resolve_policy``) and
enforces it **server-side** — the UI is never the security/limit boundary
(AGENTS.md #44).

Two layers, kept deliberately distinct so neither can be confused with the
other:

* the **ratified platform caps** — the hard ceilings configuration may never
  exceed.  They are documented platform policy, not a tunable default: the
  ``documents`` bucket is pinned at the same 10 MB per-file ceiling by
  ``20261024000000_ct_final_01_documents_bucket_size_limit.sql``.
* the **out-of-the-box effective defaults** — what applies when no
  administrator has configured anything (6 MB per file, 50 files per batch,
  500 MB per batch).

An admin-configured value may therefore *raise* a limit up to the ratified cap
or *lower* it, and can never re-open an unbounded upload path.  Uploads are
always rejected before any storage object or database row is created, so a
rejected request leaves no partial evidence.
"""
from __future__ import annotations

import logging
from typing import Dict, Mapping, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

_MB = 1024 * 1024

# ---------------------------------------------------------------------------
# Ratified platform caps (documented policy — configuration may only tighten
# relative to these, never exceed them).
# ---------------------------------------------------------------------------
PLATFORM_MAX_FILE_SIZE_MB: int = 10
PLATFORM_MAX_FILES_PER_BATCH: int = 50
PLATFORM_MAX_BATCH_TOTAL_MB: int = 500

#: Backwards-compatible aliases for the ratified caps.
MAX_FILE_SIZE_MB: int = PLATFORM_MAX_FILE_SIZE_MB
MAX_FILE_SIZE_BYTES: int = PLATFORM_MAX_FILE_SIZE_MB * _MB
MAX_FILES_PER_BATCH: int = PLATFORM_MAX_FILES_PER_BATCH
MAX_BATCH_TOTAL_MB: int = PLATFORM_MAX_BATCH_TOTAL_MB
MAX_BATCH_TOTAL_BYTES: int = PLATFORM_MAX_BATCH_TOTAL_MB * _MB

# ---------------------------------------------------------------------------
# Effective defaults when no administrator has configured a value.
# ---------------------------------------------------------------------------
DEFAULT_MAX_FILE_SIZE_MB: int = 6
DEFAULT_MAX_FILES_PER_BATCH: int = 50
DEFAULT_MAX_BATCH_TOTAL_MB: int = 500

#: The persisted-policy field names (one canonical vocabulary).
FIELD_FILE_SIZE_MB = "max_file_size_mb"
FIELD_FILES_PER_BATCH = "max_files_per_batch"
FIELD_BATCH_TOTAL_MB = "max_batch_size_mb"

POLICY_FIELDS = (FIELD_FILE_SIZE_MB, FIELD_FILES_PER_BATCH, FIELD_BATCH_TOTAL_MB)

_POLICY_DEFAULTS: Dict[str, int] = {
    FIELD_FILE_SIZE_MB: DEFAULT_MAX_FILE_SIZE_MB,
    FIELD_FILES_PER_BATCH: DEFAULT_MAX_FILES_PER_BATCH,
    FIELD_BATCH_TOTAL_MB: DEFAULT_MAX_BATCH_TOTAL_MB,
}

_POLICY_CAPS: Dict[str, int] = {
    FIELD_FILE_SIZE_MB: PLATFORM_MAX_FILE_SIZE_MB,
    FIELD_FILES_PER_BATCH: PLATFORM_MAX_FILES_PER_BATCH,
    FIELD_BATCH_TOTAL_MB: PLATFORM_MAX_BATCH_TOTAL_MB,
}

#: Machine-detectable codes returned to the caller.
CODE_FILE_TOO_LARGE = "UPLOAD_FILE_TOO_LARGE"
CODE_TOO_MANY_FILES = "UPLOAD_TOO_MANY_FILES"
CODE_BATCH_TOO_LARGE = "UPLOAD_BATCH_TOO_LARGE"
CODE_SIZE_UNKNOWN = "UPLOAD_SIZE_UNKNOWN"


class UploadLimitExceeded(Exception):
    """A server-side upload limit was exceeded (fail-closed, no write made)."""

    def __init__(self, code: str, detail: str, status_code: int = 413) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status_code = status_code


def platform_limits() -> Dict[str, int]:
    """The ratified platform caps, for UI display and configuration validation."""
    return {
        "max_file_size_mb": PLATFORM_MAX_FILE_SIZE_MB,
        "max_file_size_bytes": MAX_FILE_SIZE_BYTES,
        "max_files_per_batch": PLATFORM_MAX_FILES_PER_BATCH,
        "max_batch_size_mb": PLATFORM_MAX_BATCH_TOTAL_MB,
        "max_batch_total_bytes": MAX_BATCH_TOTAL_BYTES,
    }


def default_limits() -> Dict[str, int]:
    """The effective defaults applied when nothing has been configured."""
    return dict(_POLICY_DEFAULTS)


def _positive_int(value) -> Optional[int]:
    """A strictly positive integer, or ``None`` when the value is unusable.

    ``bool`` is rejected explicitly: ``True`` is an ``int`` in Python and must
    never be silently accepted as the number ``1``.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str):
        text = value.strip()
        if not text or not text.isdigit():
            return None
        parsed = int(text)
        return parsed if parsed > 0 else None
    return None


def validate_upload_policy(
    *,
    max_file_size_mb=None,
    max_files_per_batch=None,
    max_batch_size_mb=None,
) -> Dict[str, Optional[int]]:
    """Validate an admin-supplied upload policy.

    Returns the normalised values (``None`` for a field the caller omitted, i.e.
    "leave the current value unchanged").  Raises ``ValueError`` with a
    field-level, user-legible message for anything malformed: non-numeric, zero,
    negative, or above the ratified platform cap.
    """
    supplied = {
        FIELD_FILE_SIZE_MB: max_file_size_mb,
        FIELD_FILES_PER_BATCH: max_files_per_batch,
        FIELD_BATCH_TOTAL_MB: max_batch_size_mb,
    }
    units = {
        FIELD_FILE_SIZE_MB: "MB",
        FIELD_FILES_PER_BATCH: "files",
        FIELD_BATCH_TOTAL_MB: "MB",
    }
    validated: Dict[str, Optional[int]] = {}
    for field, raw in supplied.items():
        if raw is None:
            validated[field] = None
            continue
        value = _positive_int(raw)
        if value is None:
            raise ValueError(
                f"{field} must be a whole number of {units[field]} greater than "
                f"zero (received {raw!r})"
            )
        if value > _POLICY_CAPS[field]:
            raise ValueError(
                f"{field} may not exceed the ratified platform limit of "
                f"{_POLICY_CAPS[field]} {units[field]}"
            )
        validated[field] = value
    return validated


def effective_policy(configured: Optional[Mapping] = None) -> Dict[str, int]:
    """Resolve the effective limits from a (possibly absent/partial) policy.

    Unset, NULL or unusable stored values fall back to the documented defaults —
    never to "unlimited" — and every value is clamped to the ratified cap.
    """
    configured = configured if isinstance(configured, Mapping) else {}
    effective: Dict[str, int] = {}
    for field, default in _POLICY_DEFAULTS.items():
        value = _positive_int(configured.get(field))
        effective[field] = default if value is None else min(value, _POLICY_CAPS[field])
    return effective


def effective_file_limit_mb(configured_limit_mb=None) -> int:
    return effective_policy({FIELD_FILE_SIZE_MB: configured_limit_mb})[
        FIELD_FILE_SIZE_MB
    ]


def effective_file_limit_bytes(configured_limit_mb=None) -> int:
    """The effective per-file ceiling in bytes."""
    return effective_file_limit_mb(configured_limit_mb) * _MB


def effective_max_files(configured_max_files=None) -> int:
    return effective_policy({FIELD_FILES_PER_BATCH: configured_max_files})[
        FIELD_FILES_PER_BATCH
    ]


def effective_batch_total_bytes(configured_total_mb=None) -> int:
    return effective_policy({FIELD_BATCH_TOTAL_MB: configured_total_mb})[
        FIELD_BATCH_TOTAL_MB
    ] * _MB


# ---------------------------------------------------------------------------
# Persisted-policy resolution (used by every ingress path)
# ---------------------------------------------------------------------------
async def resolve_policy(settings_repo) -> Dict[str, int]:
    """Read the persisted upload policy and return the effective limits.

    Fail-closed: if the repository is unavailable or returns something
    unusable, the documented defaults apply (never "unlimited"), so an
    infrastructure problem can never widen an upload path.
    """
    configured = None
    if settings_repo is not None:
        try:
            configured = await settings_repo.get_upload_policy()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "upload policy read failed; applying the documented defaults: %s", exc
            )
            configured = None
    return effective_policy(configured)


async def resolve_configured_policy(settings_repo) -> Dict[str, Optional[int]]:
    """Return the persisted configuration as supplied (``None`` = unconfigured)."""
    configured = None
    if settings_repo is not None:
        try:
            configured = await settings_repo.get_upload_policy()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("upload policy read failed: %s", exc)
            configured = None
    if not isinstance(configured, Mapping):
        return {field: None for field in POLICY_FIELDS}
    return {field: _positive_int(configured.get(field)) for field in POLICY_FIELDS}


def enforce_single_file(
    filename: Optional[str],
    size_bytes,
    *,
    configured_limit_mb=None,
) -> int:
    """Validate one upload; returns its size in bytes.

    Raises ``UploadLimitExceeded`` (HTTP 413) when the file is larger than the
    effective limit, or when the size is unknown — an unknown size must never
    bypass the limit.
    """
    size = _positive_int(size_bytes) if size_bytes else None
    limit_mb = effective_file_limit_mb(configured_limit_mb)
    limit = limit_mb * _MB
    if size is None and size_bytes != 0:
        raise UploadLimitExceeded(
            CODE_SIZE_UNKNOWN,
            f"{CODE_SIZE_UNKNOWN}: the size of '{filename or 'unnamed'}' could not "
            "be determined, so the platform cannot apply the "
            f"{limit_mb}MB limit.",
        )
    if (size or 0) > limit:
        raise UploadLimitExceeded(
            CODE_FILE_TOO_LARGE,
            f"{CODE_FILE_TOO_LARGE}: '{filename or 'unnamed'}' is "
            f"{(size or 0) / _MB:.1f}MB; the platform limit is "
            f"{limit_mb}MB per file.",
        )
    return size or 0


def enforce_batch(
    files: Sequence[Tuple[Optional[str], int]],
    *,
    configured_limit_mb=None,
    configured_max_files=None,
    configured_total_mb=None,
) -> int:
    """Validate a batch **before** anything is uploaded; returns the total bytes.

    Enforces the file count first (HTTP 400 — a request-shape problem), then the
    per-file limit, then the batch total (HTTP 413).  Raises
    ``UploadLimitExceeded`` on the first violation.
    """
    max_files = effective_max_files(configured_max_files)
    if len(files) > max_files:
        raise UploadLimitExceeded(
            CODE_TOO_MANY_FILES,
            f"{CODE_TOO_MANY_FILES}: {len(files)} files submitted; the platform "
            f"limit is {max_files} files per batch.",
            status_code=400,
        )
    total_limit = effective_batch_total_bytes(configured_total_mb)

    total = 0
    for filename, size in files:
        total += enforce_single_file(
            filename, size, configured_limit_mb=configured_limit_mb
        )
    if total > total_limit:
        raise UploadLimitExceeded(
            CODE_BATCH_TOO_LARGE,
            f"{CODE_BATCH_TOO_LARGE}: the batch totals "
            f"{total / _MB:.1f}MB; the platform limit is "
            f"{total_limit // _MB}MB per batch.",
        )
    return total


def human_summary(configured: Optional[Mapping] = None) -> str:
    """One-line operator-facing summary of the effective limits."""
    effective = effective_policy(configured)
    return (
        f"{effective[FIELD_FILE_SIZE_MB]}MB per file, "
        f"{effective[FIELD_FILES_PER_BATCH]} files per batch, "
        f"{effective[FIELD_BATCH_TOTAL_MB]}MB per batch"
    )
