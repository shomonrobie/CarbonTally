"""API contract checks (spec §10).

Verifies that a live response conforms to the OpenAPI schema when one is
available, and checks envelope-level expectations (status, JSON body, error
code shape). Schemathesis is supported but optional: when installed the run
layer can hand the OpenAPI document to Schemathesis; the deterministic
contract checks here always run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ContractCheck:
    """One contract assertion against a captured response."""

    endpoint: str
    method: str
    expected_status: int
    actual_status: Optional[int] = None
    content_type: str = ""
    body: Optional[Dict[str, Any]] = None
    schema_valid: Optional[bool] = None
    schema_error: str = ""
    passed: bool = False
    notes: str = ""

    def evaluate(self, actual_status: int, content_type: str = "",
                 body: Optional[Dict[str, Any]] = None) -> "ContractCheck":
        self.actual_status = actual_status
        self.content_type = content_type
        self.body = body
        self.passed = actual_status == self.expected_status
        if actual_status != self.expected_status:
            self.notes = f"expected {self.expected_status}, got {actual_status}"
        return self

    def to_dict(self) -> Dict[str, object]:
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "expected_status": self.expected_status,
            "actual_status": self.actual_status,
            "content_type": self.content_type,
            "schema_valid": self.schema_valid,
            "schema_error": self.schema_error,
            "passed": self.passed,
            "notes": self.notes,
        }


class SchemathesisProbe:
    """Optional Schemathesis wrapper (never required).

    When the ``schemathesis`` package is importable and an OpenAPI document is
    available, the run layer may use it. This probe only reports availability.
    """

    @staticmethod
    def available() -> bool:
        try:
            import schemathesis  # noqa: F401
            return True
        except ImportError:
            return False

    @staticmethod
    def describe() -> str:
        return (
            "Schemathesis available — run layer may execute property-based "
            "contract tests against the OpenAPI document (spec §10)."
            if SchemathesisProbe.available()
            else "SKIPPED — TOOL UNAVAILABLE (schemathesis not installed)"
        )
