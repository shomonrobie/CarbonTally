"""Table/grid rule evaluation (spec §19).

The browser table auditor measures a rendered table (rows, columns, controls);
these rules decide, per documented table rules, whether a defect exists.
Small static tables must NOT be forced to paginate — the threshold comes from
config/table_rules.yaml.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from qa_harness.core.config import TableRule


@dataclass
class TableMeasurement:
    table_key: str
    row_count: int
    column_count: int = 0
    has_pagination: bool = False
    has_page_size: bool = False
    has_sorting: bool = False
    has_filtering: bool = False
    has_search: bool = False
    has_empty_state: bool = False
    has_error_state: bool = False
    has_context_columns: bool = False
    columns: List[str] = field(default_factory=list)
    horizontal_overflow: bool = False
    loading: bool = False

    def to_dict(self) -> Dict[str, object]:
        return {
            "table": self.table_key,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "has_pagination": self.has_pagination,
            "has_page_size": self.has_page_size,
            "has_sorting": self.has_sorting,
            "has_filtering": self.has_filtering,
            "has_search": self.has_search,
            "has_empty_state": self.has_empty_state,
            "has_error_state": self.has_error_state,
            "has_context_columns": self.has_context_columns,
            "columns": self.columns,
            "horizontal_overflow": self.horizontal_overflow,
            "loading": self.loading,
        }


def build_table_rules() -> Dict[str, "TableRule"]:
    """Load documented table rules from config/table_rules.yaml.

    Falls back to an empty mapping when the config cannot be loaded (the
    browser run layer reports the missing config; it never crashes).
    """
    from qa_harness.core.config import load_config

    try:
        config = load_config()
    except Exception:
        return {}
    return dict(config.table_rules)


class TableRuleEvaluator:
    """Evaluates measurements against a documented :class:`TableRule`."""

    def __init__(self) -> None:
        pass

    def evaluate(self, rule: TableRule, measurement: TableMeasurement) -> List[Dict[str, object]]:
        findings: List[Dict[str, object]] = []
        large = measurement.row_count >= rule.min_rows_for_pagination

        if measurement.loading:
            findings.append(self._finding(rule, measurement,
                "Table renders rows", "Table stuck loading"))
            return findings

        if large and rule.require_pagination and not measurement.has_pagination:
            findings.append(self._finding(rule, measurement,
                f"Table with ≥{rule.min_rows_for_pagination} rows offers pagination",
                f"{measurement.row_count} rows with no pagination control"))
        if large and rule.require_page_size and not measurement.has_page_size:
            findings.append(self._finding(rule, measurement,
                "Pagination offers a page-size control", "No page-size control"))
        if rule.require_sorting and not measurement.has_sorting:
            findings.append(self._finding(rule, measurement,
                "Table supports column sorting", "No sorting control"))
        if rule.require_filtering and not measurement.has_filtering:
            findings.append(self._finding(rule, measurement,
                "Table supports filtering", "No filtering control"))
        if rule.require_search and not measurement.has_search:
            findings.append(self._finding(rule, measurement,
                "Table supports search", "No search control"))
        if rule.require_context_columns and not measurement.has_context_columns:
            findings.append(self._finding(rule, measurement,
                "Table identifies organisation/client/entity context",
                "No contextual org/client/entity column"))
        if measurement.horizontal_overflow:
            findings.append(self._finding(rule, measurement,
                "Table fits the viewport", "Horizontal overflow detected"))
        return findings

    def _finding(self, rule: TableRule, measurement: TableMeasurement,
                 expected: str, actual: str) -> Dict[str, object]:
        return {
            "key": f"table:{rule.table}",
            "severity": "P2" if rule.operational else "P3",
            "expected": expected,
            "actual": actual,
            "measurements": measurement.to_dict(),
        }
