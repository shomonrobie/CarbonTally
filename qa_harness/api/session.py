"""Authenticated API session pool (spec §11).

Represents the identity population as live sessions: a password-grant login
per demo identity against the local Supabase GoTrue endpoint. Sessions are
cached per email; tokens are never logged or persisted (redacted at
serialization). Non-demo identities are structurally refused by
:func:`~qa_harness.browser.auth.session.demo_login` — the shared demo
password is never tried against audit/system fixtures.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from qa_harness.browser.auth.session import AuthSession, demo_login
from qa_harness.core.config import TargetEnv
from qa_harness.core.status import ToolUnavailable
from qa_harness.identities.loader import Identity

try:
    import requests  # type: ignore
    _REQUESTS = True
except ImportError:  # pragma: no cover
    requests = None  # type: ignore
    _REQUESTS = False


@dataclass
class ApiSessionPool:
    """Cached demo sessions with deterministic, redacted access."""

    env: TargetEnv
    password: str = ""
    timeout: int = 20
    _sessions: Dict[str, AuthSession] = field(default_factory=dict, init=False)

    @classmethod
    def from_env(cls, env: TargetEnv, password: str) -> "ApiSessionPool":
        return cls(env=env, password=password)

    def session(self, identity: Identity) -> AuthSession:
        """Return (and cache) a session for a demo identity.

        Raises :class:`ToolUnavailable` when ``requests`` is missing or the
        GoTrue endpoint is unreachable; raises ``ValueError`` for non-demo
        identities (structural guard).
        """
        if not _REQUESTS:
            raise ToolUnavailable("requests", "pip install requests")
        cached = self._sessions.get(identity.email)
        if cached is not None:
            return cached
        session = demo_login(
            self.env.supabase_auth_url, identity, self.password, timeout=self.timeout
        )
        if session.error or not session.access_token:
            raise ToolUnavailable(
                "goTrue login",
                f"{identity.email}: {session.error or 'no access token in response'}",
            )
        self._sessions[identity.email] = session
        return session

    def headers(self, identity: Identity) -> Dict[str, str]:
        """Authorization headers for a demo identity's session."""
        session = self.session(identity)
        return {"Authorization": f"Bearer {session.access_token}"}

    def get(self, email: str) -> Optional[AuthSession]:
        return self._sessions.get(email)

    @property
    def authenticated(self) -> List[str]:
        return list(self._sessions)

    def close(self) -> None:
        self._sessions.clear()
