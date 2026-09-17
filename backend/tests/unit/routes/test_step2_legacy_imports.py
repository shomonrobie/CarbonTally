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


def test_unavailable_manual_review_queue_fails_truthfully_not_with_import_error():
    """`queue_for_manual_review` has no implementation anywhere in the release.

    The legacy auto-repair branch therefore cannot queue review work; it must
    report that truthfully (503) instead of raising `ImportError` (500).
    """
    source = (_BACKEND / "routes" / "upload.py").read_text(encoding="utf-8")
    assert "HTTP_503_SERVICE_UNAVAILABLE" in source
    # The absent helper must not remain a call target anywhere in the file.
    assert "await queue_for_manual_review(" not in source
    assert "from main import" not in source
