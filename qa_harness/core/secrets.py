"""Automatic secret redaction for reports, logs, screenshots metadata and
console output.

The QA Harness never prints or persists secrets (spec §37). This module:

* discovers secret values from the environment (only the environment variable
  NAMES are read — never from source code),
* applies regex patterns for well-known secret shapes (JWTs, Supabase keys,
  GoTrue tokens, signed URLs, generic API keys),
* exposes :func:`redact` for any string and :func:`redact_json_safe` for
  objects destined for JSON serialization.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Set, Union

REDACTED = "[REDACTED]"

# Environment variables whose VALUES must never be exposed. The harness only
# reads the variable name from this list and pulls the value from the
# environment at redaction time — nothing is hard-coded.
SECRET_ENV_VARS: List[str] = [
    "CARBON_TALLY_DEMO_PASSWORD",
    "DEMO_PASSWORD",
    "OPENROUTER_AGEN_SWARM_V1_API_KEY",
    "OPENROUTER_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_ANON_KEY",
    "SUPABASE_JWT_SECRET",
    "DATABASE_URL",
    "POSTGRES_DSN",
    "POSTGRES_PASSWORD",
    "RESEND_API_KEY",
    "GITHUB_TOKEN",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "OPENHANDS_AUTOMATION_API_KEY",
]

# Regexes for secret-shaped strings. Applied regardless of environment.
_SECRET_PATTERNS: List[re.Pattern] = [
    # JWT / JWS (three base64url segments)
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    # Supabase service role keys (sb_secret_...)
    re.compile(r"sb_secret_[A-Za-z0-9_-]{10,}"),
    # Supabase publishable keys
    re.compile(r"sb_publishable_[A-Za-z0-9_-]{10,}"),
    # GoTrue / JWT bearer tokens
    re.compile(r"(?i)(bearer|token|access_token|refresh_token)[=:]\s*\S+"),
    # Signed URL query tokens
    re.compile(r"([?&]token=)[A-Za-z0-9._~%+-]{8,}"),
    re.compile(r"([?&]signature=)[A-Za-z0-9._~%+-]{8,}"),
    # Generic long API keys
    re.compile(r"(?i)(api[_-]?key|secret|password|passwd|pwd)\s*[=:]\s*['\"]?[A-Za-z0-9_\-\./+]{8,}"),
    # AWS-style access keys
    re.compile(r"AKIA[0-9A-Z]{16}"),
    # Private key blocks
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.DOTALL),
]


class Redactor:
    """Redacts secret-shaped strings and known environment secret values."""

    def __init__(self, extra_values: Optional[Iterable[str]] = None) -> None:
        self._values: Set[str] = set()
        for env_name in SECRET_ENV_VARS:
            value = os.environ.get(env_name)
            if value:
                self._values.add(value)
        for value in extra_values or ():
            if value:
                self._values.add(value)
        # Never redact very short values (would mangle ordinary text).
        self._values = {v for v in self._values if len(v) >= 6}

    def redact(self, text: str) -> str:
        """Return ``text`` with every known secret value and secret shape
        replaced by ``[REDACTED]``."""
        if not text:
            return text
        for value in sorted(self._values, key=len, reverse=True):
            if value in text:
                text = text.replace(value, REDACTED)
        for pattern in _SECRET_PATTERNS:
            text = pattern.sub(REDACTED, text)
        return text

    def redact_json_safe(self, obj: Any) -> Any:
        """Recursively redact strings inside an object tree."""
        if isinstance(obj, str):
            return self.redact(obj)
        if isinstance(obj, list):
            return [self.redact_json_safe(item) for item in obj]
        if isinstance(obj, tuple):
            return tuple(self.redact_json_safe(item) for item in obj)
        if isinstance(obj, dict):
            return {key: self.redact_json_safe(value) for key, value in obj.items()}
        return obj

    def safe_dumps(self, obj: Any, **kwargs: Any) -> str:
        """json.dumps with redaction applied to every string."""
        return json.dumps(self.redact_json_safe(obj), **kwargs)


default_redactor = Redactor()


def redact(text: str) -> str:
    """Module-level convenience: redact using the default redactor."""
    return default_redactor.redact(text)


def describe_available_secrets() -> List[str]:
    """Return the NAMES of secret env vars that are present (never values)."""
    present = []
    for env_name in SECRET_ENV_VARS:
        if os.environ.get(env_name):
            present.append(env_name)
    return present
