"""Browser + API authentication session (spec §11).

The run layer logs in representative identities (password grant against the
local Supabase GoTrue endpoint), obtains a session and records: session →
identity → role → organisation → relationship → landing route. Detection
targets: wrong role, wrong organisation, wrong landing page, unexpected
onboarding, redirect loop, session loss, login failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from qa_harness.core.status import ToolUnavailable
from qa_harness.identities.loader import Identity

try:
    import requests  # type: ignore
    _REQUESTS_AVAILABLE = True
except ImportError:  # pragma: no cover
    requests = None  # type: ignore
    _REQUESTS_AVAILABLE = False


@dataclass
class AuthSession:
    email: str
    access_token: str = ""          # never logged/printed — redacted everywhere
    refresh_token: str = ""
    expires_at: Optional[int] = None
    user_id: str = ""
    role: str = ""                  # resolved identity role (never from token claims alone)
    landing_route: str = ""
    error: str = ""

    def to_safe_dict(self) -> Dict[str, object]:
        """Serializable representation with every token redacted."""
        return {
            "email": self.email,
            "user_id": self.user_id,
            "role": self.role,
            "landing_route": self.landing_route,
            "has_access_token": bool(self.access_token),
            "error": self.error,
        }


def demo_login(auth_url: str, identity: Identity, password: str,
               timeout: int = 15) -> AuthSession:
    """Password-grant login for a DEMO identity (shared demo password).

    Structurally refuses non-demo identities (OHD audit / system fixtures),
    so the shared demo password is never tried against accounts outside the
    ``@demo.carbontally.local`` population.
    """
    if not identity.is_demo:
        raise ValueError(
            f"refusing demo-password login for non-demo identity {identity.email}"
        )
    return login_via_password_grant(auth_url, identity.email, password, timeout=timeout)


def login_via_password_grant(auth_url: str, email: str, password: str,
                             timeout: int = 15) -> AuthSession:
    """Password-grant login against GoTrue (``/auth/v1/token?grant_type=password``).

    Raises :class:`ToolUnavailable` when ``requests`` is missing. The returned
    session never carries the password and callers must treat the tokens as
    redacted secrets.
    """
    if not _REQUESTS_AVAILABLE:
        raise ToolUnavailable("requests", "pip package not installed")
    endpoint = auth_url.rstrip("/") + "/auth/v1/token?grant_type=password"
    try:
        response = requests.post(endpoint, json={"email": email, "password": password}, timeout=timeout)
    except requests.RequestException as exc:  # type: ignore
        return AuthSession(email=email, error=f"login request failed: {exc}")
    if response.status_code != 200:
        return AuthSession(email=email, error=f"login failed: HTTP {response.status_code}")
    body = response.json()
    session = body.get("access_token", "")
    refresh = body.get("refresh_token", "")
    user = body.get("user", {}) or {}
    return AuthSession(
        email=email,
        access_token=session,
        refresh_token=refresh,
        expires_at=body.get("expires_at"),
        user_id=user.get("id", ""),
    )


def auth_headers(session: AuthSession) -> Dict[str, str]:
    """Bearer authorization header for authenticated API calls."""
    return {"Authorization": f"Bearer {session.access_token}"}
