"""Step 2 / WS-C — legacy route import repair (F-03 / F-12).

The mounted legacy routes imported helpers `from main import …` where those names
**do not exist**, so the endpoints raised `ImportError` (HTTP 500) at request
time. These tests are deliberately static (AST/text) so they run without
production credentials or a database.
"""
from __future__ import annotations

import ast
import pathlib

_BACKEND = pathlib.Path(__file__).resolve().parents[3]
_LEGACY_ROUTES = (
    _BACKEND / "routes" / "upload.py",
    _BACKEND / "routes" / "admin" / "extraction.py",
)
#: The helpers the legacy routes must resolve, and the module that really owns them.
_HELPERS = (
    "process_fuel_data",
    "process_utility_data",
    "process_scope3_data",
    "extract_issues_from_result",
    "get_emission_factor",
)


def test_no_legacy_route_imports_from_main():
    for path in _LEGACY_ROUTES:
        source = path.read_text(encoding="utf-8")
        assert "from main import" not in source, f"{path.name} still imports from main"
        assert "\nimport main\n" not in source, f"{path.name} still imports main"


def test_utils_emissions_defines_every_required_helper():
    tree = ast.parse((_BACKEND / "utils" / "emissions.py").read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    missing = [name for name in _HELPERS if name not in defined]
    assert not missing, f"utils.emissions is missing {missing}"


def test_upload_route_imports_its_helpers_from_utils_emissions():
    tree = ast.parse((_BACKEND / "routes" / "upload.py").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "utils.emissions":
            imported.update(alias.name for alias in node.names)
    for name in ("process_fuel_data", "process_utility_data", "process_scope3_data",
                 "extract_issues_from_result", "get_emission_factor"):
        assert name in imported, f"routes/upload.py does not import {name}"


def test_admin_extraction_imports_the_factor_helper_from_utils_emissions():
    source = (_BACKEND / "routes" / "admin" / "extraction.py").read_text(encoding="utf-8")
    assert "from utils.emissions import get_emission_factor" in source


def test_manual_review_queueing_uses_the_v3_adapter_not_an_absent_helper():
    """Step 2C / POD-2 (PO decision C) — deliberate contract change.

    Previously the legacy auto-repair branch could not queue review work at all
    (`queue_for_manual_review` has no implementation in the release) and answered a
    truthful 503. It now translates the legacy request into the CURRENT V3
    manual-review workflow through the shared document pipeline, and reports a
    truthful 400 when the legacy caller cannot supply a safe request. What must
    never come back is an `ImportError` (500) or a silent discard.
    """
    source = (_BACKEND / "routes" / "upload.py").read_text(encoding="utf-8")
    assert "legacy_queue_for_manual_review(" in source          # the adapter is invoked
    assert "LegacyManualReviewError" in source                  # truthful 400 path
    assert "status.HTTP_400_BAD_REQUEST" in source
    # The absent helper must not remain a call target anywhere in the file, and no
    # absent `main` import may remain (both previously produced a 500).
    assert "await queue_for_manual_review(" not in source
    assert "from main import" not in source
    # The retired 503 must not linger as the normal path.
    assert "HTTP_503_SERVICE_UNAVAILABLE" not in source
