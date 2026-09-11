"""OpenAPI / endpoint discovery and recording (spec §10).

The run layer fetches the backend's OpenAPI document (``/openapi.json``) and
records for every endpoint: method, path, authentication, parameters, request
schema, response schema, expected status and actual status. Unexpected
5xx/4xx responses are flagged — but 401/403/409/422 are legitimate in many
flows, so the flagging logic is explicit, never blanket.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Statuses that are legitimate for many endpoints and must NOT be reported as
# defects without additional context.
LEGITIMATE_4XX = {400, 401, 403, 404, 409, 422}

# Statuses that are always worth investigating when they appear in a 2xx-expected call.
UNEXPECTED_STATUSES = {500, 502, 503, 504}


@dataclass
class ApiEndpoint:
    method: str
    path: str
    auth_required: bool = True
    parameters: List[Dict[str, object]] = field(default_factory=list)
    request_schema: Optional[Dict[str, object]] = None
    response_schema: Optional[Dict[str, object]] = None
    expected_status: Optional[int] = None
    actual_status: Optional[int] = None
    summary: str = ""
    tag: str = ""

    @property
    def key(self) -> str:
        return f"{self.method.upper()} {self.path}"

    def to_dict(self) -> Dict[str, object]:
        return {
            "method": self.method.upper(),
            "path": self.path,
            "auth_required": self.auth_required,
            "summary": self.summary,
            "tag": self.tag,
            "expected_status": self.expected_status,
            "actual_status": self.actual_status,
            "parameters": self.parameters,
        }


class EndpointInventory:
    """Builds an endpoint inventory from an OpenAPI document."""

    def __init__(self, openapi: Optional[Dict[str, Any]] = None,
                 api_prefix: str = "/api/v3") -> None:
        self.openapi = openapi or {}
        self.api_prefix = api_prefix.rstrip("/")
        self.endpoints: List[ApiEndpoint] = []
        self._built = False

    def build(self) -> List[ApiEndpoint]:
        if self._built:
            return self.endpoints
        paths = self.openapi.get("paths", {})
        # Auth applies when the operation declares security, or when the
        # document declares a global security requirement. The mere presence
        # of securitySchemes in components does NOT make every endpoint
        # authenticated (public endpoints omit security entirely).
        global_security = self.openapi.get("security")
        for path, methods in paths.items():
            for method, spec in methods.items():
                if method.lower() not in ("get", "post", "put", "patch", "delete", "head", "options"):
                    continue
                security = spec.get("security")
                auth_required = security is not None or bool(global_security)
                self.endpoints.append(ApiEndpoint(
                    method=method.upper(),
                    path=path,
                    auth_required=auth_required,
                    parameters=list(spec.get("parameters", [])),
                    request_schema=spec.get("requestBody"),
                    response_schema=spec.get("responses"),
                    summary=spec.get("summary", ""),
                    tag=(spec.get("tags") or [""])[0],
                ))
        self._built = True
        return self.endpoints

    def v3_endpoints(self) -> List[ApiEndpoint]:
        return [e for e in self.build() if e.path.startswith(self.api_prefix)]

    def by_tag(self, tag: str) -> List[ApiEndpoint]:
        return [e for e in self.build() if e.tag == tag]

    def unexpected(self) -> List[ApiEndpoint]:
        """Endpoints whose actual status is unexpected for the expectation.

        Only server errors (5xx) are flagged here; 4xx responses are NOT
        reported as defects without context — 401/403/409/422 are legitimate
        for many flows (spec §10). Contextual 4xx misbehaviour (e.g. a 403
        where the actor should be allowed) is handled by the authorization
        matrix and workflow layers instead.
        """
        result = []
        for e in self.build():
            if e.actual_status is None or e.expected_status is None:
                continue
            if e.actual_status in UNEXPECTED_STATUSES:
                result.append(e)
        return result
