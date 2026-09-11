"""Local demo credential loading — spec V1.2.

The shared local demo password lives in a **gitignored** repository-root file
(``.local-demo-credentials.md``) so operators do not have to export
``CARBON_TALLY_DEMO_PASSWORD`` in every shell. This module:

* locates the repository-root credential file,
* parses the shared demo password and (informational) representative emails,
* keeps the credential only in memory — never in ``repr()``/``str()``/logs,
* honours ``CARBON_TALLY_DEMO_PASSWORD`` / ``DEMO_PASSWORD`` first (explicit
  environment override wins over the file),
* structurally refuses to hand the shared password to any non-demo identity.

The credential file provides the **authentication secret**; the identity
model (``identities/loader.py``) remains authoritative for the population.
The file must stay gitignored and must never be committed.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DEMO_CREDENTIALS_FILENAME = ".local-demo-credentials.md"
DEMO_DOMAIN = "demo.carbontally.local"

# Password line format used by the current credentials file:
#   Local-only password (shared): **<shared-demo-password>**
_PASSWORD_LINE = re.compile(
    r"^Local-only password \(shared\):\s*\*{1,2}(.+?)\*{1,2}\s*$"
)
# Fallback: raw remainder after the colon (no bold markers).
_PASSWORD_LINE_RAW = re.compile(r"^Local-only password \(shared\):\s*(.+?)\s*$")
# Markdown table row cell containing a demo email (informational only).
_TABLE_EMAIL = re.compile(r"\b([A-Za-z0-9._%+-]+@demo\.carbontally\.local)\b")

# Minimum length for a credential the harness can safely redact everywhere
# (core/secrets.py ignores shorter values to avoid mangling ordinary text).
MIN_PASSWORD_LENGTH = 6

_PASSWORD_PLACEHOLDER = "SET"
_NONE_PLACEHOLDER = "NOT SET"


class CredentialsError(ValueError):
    """Raised when the credential file exists but cannot be used safely."""


@dataclass(frozen=True)
class DemoCredentials:
    """In-memory demo credentials. Never serialize/str this object.

    ``repr()``/``str()``/``to_dict()`` only ever expose the SOURCE and whether
    a password is present — never the password itself.
    """

    source: str = "none"                       # environment | file | none
    password: str = field(default="", repr=False, compare=False)
    file_path: Optional[Path] = field(default=None, repr=False)
    representative_emails: List[str] = field(default_factory=list, repr=False)

    def __str__(self) -> str:
        return f"DemoCredentials(source={self.source!r}, password={_password_state(self.password)})"

    @property
    def has_password(self) -> bool:
        return bool(self.password)

    def to_dict(self) -> Dict[str, object]:
        """Safe serialization — never contains the password."""
        return {
            "source": self.source,
            "password": _password_state(self.password),
            "file_path": str(self.file_path) if self.file_path else None,
            "representative_emails": list(self.representative_emails),
        }


def _password_state(password: str) -> str:
    return _PASSWORD_PLACEHOLDER if password else _NONE_PLACEHOLDER


# --------------------------------------------------------------------------- #
# Location
# --------------------------------------------------------------------------- #

def repo_root(start: Optional[Path] = None) -> Optional[Path]:
    """First ancestor of ``start`` containing a ``.git`` marker."""
    current = Path(start or Path(__file__).resolve().parent).resolve()
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def find_credentials_file(start: Optional[Path] = None,
                          filename: str = DEMO_CREDENTIALS_FILENAME) -> Optional[Path]:
    """Locate the repository-root credentials file.

    Search order: the ``.git``-marked repo root, then the harness root's
    parent, then the harness root itself. Returns ``None`` when absent
    (callers treat that as ``source: none`` → authenticated QA SKIPPED).
    """
    candidates: List[Path] = []
    root = repo_root(start)
    if root is not None:
        candidates.append(root / filename)
    harness_parent = Path(__file__).resolve().parent.parent.parent
    if harness_parent not in candidates:
        candidates.append(harness_parent / filename)
    harness_root = Path(__file__).resolve().parent.parent
    candidates.append(harness_root / filename)
    for path in candidates:
        if path.exists():
            return path
    return None


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #

def parse_credentials_file(text: str) -> Dict[str, object]:
    """Parse the credentials-file text.

    Returns ``{"password": str, "representative_emails": [...]}``. Raises
    :class:`CredentialsError` when the file exists but the password cannot be
    found or is unsafe to handle.
    """
    password = ""
    for line in text.splitlines():
        stripped = line.strip()
        match = _PASSWORD_LINE.match(stripped) or _PASSWORD_LINE_RAW.match(stripped)
        if match:
            password = match.group(1).strip()
            break
    if not password:
        raise CredentialsError(
            "credential file has no 'Local-only password (shared):' line"
        )
    if len(password) < MIN_PASSWORD_LENGTH:
        raise CredentialsError(
            f"credential file password is too short to redact safely "
            f"(< {MIN_PASSWORD_LENGTH} chars)"
        )
    emails: List[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            emails.extend(_TABLE_EMAIL.findall(line))
    # de-duplicate, preserve order
    seen: set[str] = set()
    unique_emails: List[str] = []
    for email in emails:
        if email not in seen:
            seen.add(email)
            unique_emails.append(email)
    return {"password": password, "representative_emails": unique_emails}


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

def load_demo_credentials(credentials_path: Optional[Path] = None,
                          env: Optional[Dict[str, Optional[str]]] = None,
                          ) -> DemoCredentials:
    """Load demo credentials with precedence:

    1. explicit environment  (``CARBON_TALLY_DEMO_PASSWORD``, else ``DEMO_PASSWORD``)
    2. local credentials file
    3. none → ``source="none"`` (authenticated QA SKIPPED — never guessed)
    """
    environment = os.environ if env is None else {k: (v or "") for k, v in env.items()}
    env_password = environment.get("CARBON_TALLY_DEMO_PASSWORD") or environment.get("DEMO_PASSWORD")
    if env_password:
        return DemoCredentials(source="environment", password=env_password)

    path = credentials_path if credentials_path is not None else find_credentials_file()
    if path is None or not path.exists():
        return DemoCredentials(source="none")
    try:
        parsed = parse_credentials_file(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CredentialsError(f"cannot read credential file {path}: {exc}") from exc
    return DemoCredentials(
        source="file",
        password=str(parsed["password"]),
        file_path=path,
        representative_emails=list(parsed["representative_emails"]),
    )


# --------------------------------------------------------------------------- #
# Structural safeguards
# --------------------------------------------------------------------------- #

def is_demo_email(email: str) -> bool:
    return email.lower().endswith(f"@{DEMO_DOMAIN}")


def password_for(identity: Any, credentials: Optional[DemoCredentials] = None) -> str:
    """Return the shared demo password ONLY for a demo identity.

    ``identity`` may be an ``identities.loader.Identity`` (uses ``is_demo``)
    or a plain email string (domain-checked). Raises ``ValueError`` for
    non-demo identities so the shared credential is never handed to audit /
    system fixtures or arbitrary caller-supplied emails.
    """
    email = getattr(identity, "email", None) or identity
    is_demo = getattr(identity, "is_demo", None)
    if is_demo is None:
        is_demo = is_demo_email(str(email))
    if not is_demo:
        raise ValueError(
            f"refusing shared demo credential for non-demo identity {email!r}"
        )
    creds = credentials if credentials is not None else load_demo_credentials()
    if not creds.has_password:
        raise CredentialsError("no demo credential available (environment or local file)")
    return creds.password


def demo_credentials_summary(credentials_path: Optional[Path] = None,
                             env: Optional[Dict[str, Optional[str]]] = None) -> Dict[str, str]:
    """Safe summary for preflight/console — never contains the password."""
    creds = load_demo_credentials(credentials_path=credentials_path, env=env)
    source_label = {
        "environment": "environment",
        "file": "local credentials file",
        "none": "NOT SET",
    }.get(creds.source, creds.source)
    return {
        "source": source_label,
        "password": _password_state(creds.password),
    }


__all__ = [
    "CredentialsError",
    "DEMO_CREDENTIALS_FILENAME",
    "DemoCredentials",
    "MIN_PASSWORD_LENGTH",
    "demo_credentials_summary",
    "find_credentials_file",
    "is_demo_email",
    "load_demo_credentials",
    "parse_credentials_file",
    "password_for",
    "repo_root",
]
