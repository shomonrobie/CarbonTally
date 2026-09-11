"""Harness self-tests: reusable UX / table / navigation / security / business rules (spec §19–§21)."""

from __future__ import annotations

from qa_harness.core.config import TableRule
from qa_harness.rules.business import BusinessRuleCatalog, build_business_rules
from qa_harness.rules.navigation import NavigationRuleCatalog, build_navigation_rules
from qa_harness.rules.security import SecurityRuleCatalog, build_security_rules
from qa_harness.rules.tables import TableMeasurement, TableRuleEvaluator, build_table_rules
from qa_harness.rules.ux import UxRuleCheck, build_ux_rule_checks


def test_queue_workspace_rule_flags_buried_workspace() -> None:
    check = UxRuleCheck(key="queue-workspace-focus", label="Queue → workspace focus",
                        max_queue_height_before_workspace_px=1200)
    findings = check.evaluate_queue_workspace(
        queue_height_px=2579, workspace_y_px=3180, scroll_px=2400,
        route_changed=False, is_modal_or_drawer=False, back_navigation_present=False,
    )
    assert len(findings) == 1
    assert "y≈3180px" in findings[0]["actual"]


def test_queue_workspace_rule_passes_focused_workspace() -> None:
    check = UxRuleCheck(key="queue-workspace-focus", label="Queue → workspace focus")
    findings = check.evaluate_queue_workspace(
        queue_height_px=120, workspace_y_px=200, scroll_px=0,
        route_changed=True, is_modal_or_drawer=False, back_navigation_present=True,
    )
    assert findings == []


def test_loading_error_empty_rules() -> None:
    check = UxRuleCheck(key="states", label="Loading/error/empty states")
    findings = check.evaluate_loading_error_empty(
        loading=True, blank=True, raw_js_exception=True, raw_backend_exception=False,
        unhandled_promise_rejection=False, broken_retry=False,
        meaningless_error=False, missing_empty_state=True,
        console_errors=["orgs.map is not a function"],
    )
    keys = {f["key"] for f in findings}
    assert {"permanent_loading", "blank_screen", "raw_js_exception", "missing_empty_state"} <= keys
    raw_js = next(f for f in findings if f["key"] == "raw_js_exception")
    assert raw_js["console_errors"] == ["orgs.map is not a function"]


def test_loading_error_empty_clean() -> None:
    check = UxRuleCheck(key="states", label="States")
    findings = check.evaluate_loading_error_empty(
        loading=False, blank=False, raw_js_exception=False, raw_backend_exception=False,
        unhandled_promise_rejection=False, broken_retry=False,
        meaningless_error=False, missing_empty_state=False,
    )
    assert findings == []


def test_table_rule_operational_requires_controls() -> None:
    evaluator = TableRuleEvaluator()
    rule = TableRule(table="documents", operational=True, min_rows_for_pagination=20,
                     require_pagination=True, require_sorting=True,
                     require_filtering=True, require_context_columns=True)
    measurement = TableMeasurement(
        table_key="documents", row_count=53,
        has_pagination=False, has_page_size=False,
        has_sorting=True, has_filtering=True, has_search=False,
        has_context_columns=True,
        loading=False,
    )
    findings = evaluator.evaluate(rule, measurement)
    actuals = [f["actual"] for f in findings]
    assert any("no pagination" in a.lower() for a in actuals)
    assert any("page-size" in a.lower() for a in actuals)


def test_table_rule_small_static_table_not_flagged() -> None:
    evaluator = TableRuleEvaluator()
    # A tiny static table with all optional controls disabled must not be
    # forced to paginate (spec §19: no blind pagination requirement).
    rule = TableRule(table="static", operational=False, min_rows_for_pagination=20,
                     require_pagination=True, require_page_size=False,
                     require_sorting=False, require_filtering=False,
                     require_search=False, require_context_columns=False)
    measurement = TableMeasurement(table_key="static", row_count=3, has_pagination=False)
    assert evaluator.evaluate(rule, measurement) == []


def test_table_rules_loaded_from_config() -> None:
    rules = build_table_rules()
    assert rules  # config/table_rules.yaml documents the operational tables


def test_navigation_landing_rules() -> None:
    catalog = NavigationRuleCatalog()
    result = catalog.check_landing("customer", "/home")
    assert result["ok"] is True
    bad = catalog.check_landing("customer", "/ops")
    assert bad["ok"] is False


def test_navigation_rules_documented() -> None:
    rules = build_navigation_rules()
    assert rules
    assert all(r.id and r.rule for r in rules)


def test_security_rules_documented() -> None:
    rules = build_security_rules()
    assert rules
    severities = {r.severity for r in rules}
    assert severities <= {"P0", "P1", "P2", "P3"}
    catalog = SecurityRuleCatalog(rules=rules)
    assert catalog.by_severity("P0")


def test_business_rules_documented() -> None:
    rules = build_business_rules()
    assert rules
    catalog = BusinessRuleCatalog(rules=rules)
    assert catalog.po_decisions()


def test_ux_rule_checks_loaded() -> None:
    checks = build_ux_rule_checks()
    assert checks
    assert any("queue" in c.key for c in checks)
