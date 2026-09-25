"""P17-K — governed capability catalogue: contract tests over the migration TEXT.

Authority: ``docs/architecture/CT-PO-P17-DECISION-03-PO-FREEZE-CAPABILITY-STATUS-
INVESTOR-SURFACE-20250926.md`` — §18.1 Tier 2 item 7 (authorisation to author the
catalogue), §5.3 `M-1` (the non-upgrading mapping), §11.1/§11.2 (the frozen
Scope 3 rollup), §10.3 `SC-4` (the Scope 2 market-based boundary) and §18.3
`AG-1` … `AG-8` (the acceptance gates).

The repository convention for schema-boundary work is to assert the migration
TEXT (``test_b2_migration.py``, ``test_disclosure_migration.py``,
``test_p17_migrations.py``) so a declared boundary cannot drift silently. These
tests do the same for the P17-K catalogue migration, and additionally run the
`AG` gates against the REAL governed vocabulary imported from
``domain.disclosure`` and the REAL projection engine
(``domain.disclosure_projection.derive_effective_class``) — the tests do not
restate either.

What CANNOT be asserted here: anything about a rendered surface. No capability
surface exists (P17-DECISION-03 §18.1 Tier 3), so the rendering branches of the
gates are exercised by the runtime suite and reported as pending, never as
satisfied (`AGENTS.md §73`, `§74`).
"""
from __future__ import annotations

import pathlib
import re

from domain.disclosure import CARBONTALLY_CAPABILITIES, REQUIREMENT_CLASSES
from domain.disclosure_projection import derive_effective_class

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
_MIGRATIONS = _REPO_ROOT / "supabase" / "migrations"
CATALOGUE = _MIGRATIONS / "20261020000000_p17k_governed_capability_catalogue.sql"

#: The frozen `M-1` image of the category matrix (P17-DECISION-03 §11.1/§11.2).
#: Non-upgrading and one-directional: a `PARTIAL` category is never expressed as
#: `SUPPORTED`, and `NOT_IMPLEMENTED` never becomes an applicability outcome.
M1_IMAGE: dict[int, str] = {
    1: "PARTIALLY_SUPPORTED",
    2: "MISSING_CAPABILITY",
    3: "SUPPORTED",
    4: "SUPPORTED",
    5: "SUPPORTED",
    6: "SUPPORTED",
    7: "PARTIALLY_SUPPORTED",
    8: "PARTIALLY_SUPPORTED",
    9: "PARTIALLY_SUPPORTED",
    10: "MISSING_CAPABILITY",
    11: "FUTURE",
    12: "PARTIALLY_SUPPORTED",
    13: "PARTIALLY_SUPPORTED",
    14: "FUTURE",
    15: "FUTURE",
}

#: The four-way rollup the catalogue must reproduce exactly (`S3-1`, `AG-7`).
ROLLUP: dict[str, int] = {
    "SUPPORTED": 4,
    "PARTIALLY_SUPPORTED": 6,
    "FUTURE": 3,
    "MISSING_CAPABILITY": 2,
}

#: Axis-A (internal architecture) tokens. `IV-1`/`M-4`/`F-3` forbid rendering
#: them outside internal surfaces, so the catalogue must not carry them at all.
AXIS_A_TOKENS: tuple[str, ...] = ("PARTIAL", "DEFERRED", "NOT_IMPLEMENTED")

#: Literals that must never stand in for an absent / unsupported item (`AG-4`).
FORBIDDEN_ABSENCE_TOKENS: tuple[str, ...] = (
    "n/a",
    "not applicable",
    "excluded",
    "coming soon",
    "0 tco2e",
    "0tco2e",
)

_CATEGORY_ROW = re.compile(r"\(\s*(\d{1,2}),\s*'([A-Z_]+)',")


def _text() -> str:
    assert CATALOGUE.exists(), f"P17-K catalogue migration missing: {CATALOGUE}"
    return CATALOGUE.read_text(encoding="utf-8")


def _code() -> str:
    """SQL with comment lines removed, so assertions target executable code."""
    return "\n".join(
        line for line in _text().splitlines() if not line.lstrip().startswith("--")
    )


def _category_rows() -> list[tuple[int, str]]:
    """The 15 (category, carbontally_capability) pairs of the Scope 3 INSERT."""
    block = _code().split("CROSS JOIN (VALUES", 1)[1].split(
        ") AS m(category", 1
    )[0]
    return [(int(n), cap) for n, cap in _CATEGORY_ROW.findall(block)]



# ---------------------------------------------------------------------------
# AG-1 — every capability value is a member of a governed vocabulary
# ---------------------------------------------------------------------------
def test_ag_1_the_catalogue_is_exactly_the_frozen_m1_image() -> None:
    """Non-upgrade is a test, not a convention (`S3-2`, `M-6`)."""
    rows = dict(_category_rows())
    assert len(rows) == 15, rows
    assert rows == M1_IMAGE, {
        k: (rows.get(k), v) for k, v in M1_IMAGE.items() if rows.get(k) != v
    }


def test_ag_1_every_persisted_capability_is_a_governed_value() -> None:
    caps = {cap for _, cap in _category_rows()}
    assert caps <= set(CARBONTALLY_CAPABILITIES), caps - set(CARBONTALLY_CAPABILITIES)


def test_ag_1_only_governed_requirement_classes_are_used() -> None:
    code = _code()
    used = set(
        re.findall(
            r"'(REQUIRED|CONDITIONAL|OPTIONAL|NOT_APPLICABLE|"
            r"CUSTOMER_INPUT_REQUIRED|UNDETERMINED|NOT_SUPPORTED|FUTURE)'",
            code,
        )
    )
    assert used <= set(REQUIREMENT_CLASSES), used - set(REQUIREMENT_CLASSES)
    # Scope 1/2 are REQUIRED and Scope 3 is CONDITIONAL in the catalogue; the
    # product outcome is DERIVED, never written into the framework class.
    used_classes = used - set(CARBONTALLY_CAPABILITIES)
    assert used_classes == {"REQUIRED", "CONDITIONAL"}, used_classes


# ---------------------------------------------------------------------------
# AG-2 — every non-produced item carries a governed value, and the outcomes
#        `NOT_SUPPORTED` and `CUSTOMER_INPUT_REQUIRED` stay distinct
# ---------------------------------------------------------------------------
def test_ag_2_derived_outcomes_are_governed_and_distinct() -> None:
    seen: set[str] = set()
    for _category, capability in _category_rows():
        effective = derive_effective_class(
            requirement_class="CONDITIONAL",
            applicability_status="APPLIES",
            carbontally_capability=capability,
        )
        assert effective in REQUIREMENT_CLASSES, effective
        seen.add(effective)

    # MISSING_CAPABILITY -> NOT_SUPPORTED ; FUTURE -> FUTURE (both governed).
    assert seen == {"CONDITIONAL", "FUTURE", "NOT_SUPPORTED"}, seen

    product = derive_effective_class(
        requirement_class="CONDITIONAL",
        applicability_status="APPLIES",
        carbontally_capability="MISSING_CAPABILITY",
    )
    customer = derive_effective_class(
        requirement_class="CONDITIONAL",
        applicability_status="CUSTOMER_INPUT_REQUIRED",
        carbontally_capability="SUPPORTED",
    )
    assert product == "NOT_SUPPORTED"
    assert customer == "CUSTOMER_INPUT_REQUIRED"
    assert product != customer, "the two absence reasons must never be conflated (NS-2)"


def test_ag_2_scope2_market_based_is_not_recorded_as_producible() -> None:
    """`SC-4` / §9.4 item 4: no market-based engine exists."""
    code = _code()
    assert "'MARKET_BASED'" in code
    # The GP-S2-MB row's tail: class, scope, method, order, governed capability.
    assert "'REQUIRED', 'Scope 2', 'MARKET_BASED', 3, 'MISSING_CAPABILITY'," in code
    for producible in ("'SUPPORTED'", "'PARTIALLY_SUPPORTED'",
                       "'STRUCTURED_INPUT_REQUIRED'", "'EXTERNAL_INPUT_REQUIRED'"):
        assert f"'MARKET_BASED', 3, {producible}" not in code, producible
    derived = derive_effective_class(
        requirement_class="REQUIRED",
        applicability_status="APPLIES",
        carbontally_capability="MISSING_CAPABILITY",
    )
    assert derived == "NOT_SUPPORTED"


# ---------------------------------------------------------------------------
# AG-3 — no Axis-A token is usable as a status on a non-internal surface
# ---------------------------------------------------------------------------
def test_ag_3_no_axis_a_token_appears_anywhere_in_the_catalogue() -> None:
    """Not as a value, and not as prose a consumer could copy out (`M-3`, `M-4`)."""
    code = _code().upper()
    for token in AXIS_A_TOKENS:
        assert not re.search(rf"\b{token}\b", code), token
    for _category, capability in _category_rows():
        assert capability not in AXIS_A_TOKENS


def test_ag_3_the_internal_status_axis_is_absent_from_the_schema_contract() -> None:
    code = _code()
    assert "architecture_status" not in code
    assert "ADD COLUMN" not in code.upper()


def test_ag_3_no_applicability_vocabulary_is_used() -> None:
    """`F-1` / PO-3: no customer applicability concept, and never a tenant state."""
    code = _code()
    for token in ("'NOT_APPLICABLE'", "'DOES_NOT_APPLY'", "NO_DATA_YET",
                  "EXCLUDED_WITH_REASON", "applicability"):
        assert token not in code, token


# ---------------------------------------------------------------------------
# AG-4 — absence is never rendered as 0, a placeholder or an absence claim
# ---------------------------------------------------------------------------
def test_ag_4_no_placeholder_stands_in_for_an_absent_item() -> None:
    prose = _text().lower()
    for token in FORBIDDEN_ABSENCE_TOKENS:
        assert token not in prose, token


def test_ag_4_no_fabricated_emissions_figure_is_stored() -> None:
    assert not re.search(r"\d+(?:\.\d+)?\s*(?:kg|t|tonnes?)?\s*co2e", _text(), re.I)


# ---------------------------------------------------------------------------
# AG-5 — the catalogue cannot become a tenant-data path (`SEC-1`, `SEC-3`)
# ---------------------------------------------------------------------------
def test_ag_5_the_catalogue_references_no_tenant_key_or_tenant_table() -> None:
    code = _code()
    for token in ("organization_id", "organisations", "organizations", "facilities",
                  "disclosure_values", "disclosure_applicability_assessments",
                  "report_versions"):
        assert token not in code, token


# ---------------------------------------------------------------------------
# AG-6 — one governed value per requirement, with no per-surface variant
# ---------------------------------------------------------------------------
def test_ag_6_no_second_capability_or_coverage_column_is_introduced() -> None:
    """`F-2`/`F-8`: one governed value, no per-surface variant, no coverage field."""
    code = _code()
    columns = code.split("INSERT INTO public.disclosure_requirement_versions (", 1)[1]
    columns = columns.split(")", 1)[0]
    for column in ("investor_capability", "customer_capability", "coverage",
                   "completeness", "materiality", "assurance", "investor_status"):
        assert column not in columns, column
    # And the same words are absent from the row VALUES a surface could render.
    values = code.split("CROSS JOIN (VALUES", 1)[1]
    for column in ("investor_capability", "customer_capability", "coverage",
                   "completeness", "materiality", "assurance"):
        assert column not in values, column


def test_ag_6_each_requirement_code_is_generated_exactly_once() -> None:
    code = _code()
    assert code.count("'GP-S3-CAT-' || lpad") == 1
    literals = set(re.findall(r"'(GP-[A-Z0-9-]+)'", code))
    assert literals == {"GP-S1", "GP-S2-LB", "GP-S2-MB", "GP-S3-CAT-"}, literals
    # 3 explicit codes + the 15 generated ones = the 18 governed requirements.
    assert len(literals) + len(_category_rows()) - 1 == 18


# ---------------------------------------------------------------------------
# AG-7 — the four-way rollup, never a total (`S3-1`)
# ---------------------------------------------------------------------------
def test_ag_7_the_catalogue_reproduces_the_frozen_rollup() -> None:
    rows = [cap for _category, cap in _category_rows()]
    assert len(rows) == 15
    counts = {cap: rows.count(cap) for cap in sorted(set(rows))}
    assert counts == ROLLUP, counts


def test_ag_7_no_unqualified_total_claim_is_made() -> None:
    code = _code().lower()
    for phrase in ("all 15", "15 categories supported", "total = 15"):
        assert phrase not in code, phrase


# ---------------------------------------------------------------------------
# AG-8 — any capability claim carries provenance, and no illustrated result
# ---------------------------------------------------------------------------
def test_ag_8_every_row_carries_provenance_or_an_explicit_unresolved_marker() -> None:
    code = _code()
    for column in ("source_locator", "authoritative_text_ref", "source_tier",
                   "identifier_status", "official_identifier"):
        assert column in code, column
    assert "'UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION'" in code
    # No official identifier literal is supplied for any row: none is invented.
    assert re.search(r"r\.requirement_code,\n\s+NULL,", code)
    assert re.search(r"lpad\(c\.category::text, 2, '0'\),\n\s+NULL,", code)


def test_ag_8_the_migration_states_what_it_is_not() -> None:
    prose = _text().lower()
    assert "reference data only" in prose
    assert "not a claim about any customer" in prose
    assert "no tenant state exists" in prose


# ---------------------------------------------------------------------------
# Discipline: additive-only, idempotent, fail-loud, PQ-6-compliant
# ---------------------------------------------------------------------------
def test_additive_only_no_ddl_is_performed() -> None:
    code = _code().upper()
    for forbidden in ("CREATE TABLE", "ALTER TABLE", "ADD COLUMN", "CREATE TYPE",
                      "DROP ", "DELETE FROM", "TRUNCATE", "UPDATE PUBLIC."):
        assert forbidden not in code, forbidden


def test_both_inserts_are_idempotent() -> None:
    code = _code()
    assert "ON CONFLICT (framework_id, version_label) DO NOTHING" in code
    assert "ON CONFLICT (framework_version_id, requirement_code) DO NOTHING" in code


def test_fail_loud_guards_are_present() -> None:
    """An empty or partially-mapped catalogue must fail, not pass silently (§74)."""
    code = _code()
    assert "RAISE EXCEPTION" in code
    assert "the GHG_PROTOCOL framework identity is absent" in code
    assert "governed capability catalogue incomplete" in code
    assert "(n_sup, n_part, n_fut, n_miss) <> (4, 6, 3, 2)" in code
    assert "the frozen matrix requires 4/6/3/2" in code


def test_pq_6_no_version_identity_or_date_is_invented() -> None:
    code = _code()
    # The version label is the authoritative-evidence record's own wording.
    label = "'Corporate Accounting and Reporting Standard (2004 revised edition)'"
    assert label in code
    assert code.count(label) >= 2  # declared AND matched on
    # No invented date and no legal reference are asserted for the version row.
    assert not re.search(r"DATE\s*'", code)
    assert not re.search(r"'20\d{2}-\d{2}-\d{2}'", code)
    assert "'IN_FORCE'" in code


def test_the_category_names_come_from_the_governed_taxonomy() -> None:
    """One database, one naming of a category — the names are not restated."""
    code = _code()
    assert "JOIN public.scope3_categories c ON c.category BETWEEN 1 AND 15" in code
    assert "c.name" in code
    assert "Purchased goods" not in code


