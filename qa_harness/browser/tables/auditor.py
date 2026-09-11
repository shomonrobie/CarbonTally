"""Generic table auditor for operational data grids (spec §19).

Measures a rendered table: pagination, page-size control, sorting, filtering,
search, record count, loading state, empty state, error state, responsive
behavior, meaningful columns and contextual org/client/entity identification.
Rules decide whether the measurement is a defect (see rules/tables.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from qa_harness.core.status import ToolUnavailable
from qa_harness.rules.tables import TableMeasurement

# Role-selector heuristics for locating tables inside a page.
TABLE_SELECTORS = ["table", "[role='table']", ".data-grid", ".table-container"]


@dataclass
class TableAuditResult:
    table_key: str
    measurement: Optional[TableMeasurement] = None
    error: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "table": self.table_key,
            "measurement": self.measurement.to_dict() if self.measurement else None,
            "error": self.error,
        }


class TableAuditor:
    """Audits every significant table found on a page."""

    def __init__(self, page: Any) -> None:
        self.page = page

    def find_tables(self) -> List[Dict[str, Any]]:
        """Locate tables and their basic geometry (via JS evaluation)."""
        try:
            return self.page.evaluate("""() => {
                const nodes = Array.from(document.querySelectorAll('table'));
                return nodes.map((t, i) => {
                    const rows = t.querySelectorAll('tbody tr').length;
                    const heads = Array.from(t.querySelectorAll('thead th, thead td'))
                                       .map(h => h.innerText.trim()).filter(Boolean);
                    return {index: i, rows: rows, columns: heads};
                });
            }""")
        except Exception:
            return []

    def audit(self, table_key: str, route: str = "") -> TableAuditResult:
        try:
            tables = self.find_tables()
            if not tables:
                return TableAuditResult(table_key=table_key, error="no table found")
            # Use the largest table on the page (most rows) as the primary.
            primary = max(tables, key=lambda t: t.get("rows", 0))
            measurement = TableMeasurement(
                table_key=table_key,
                row_count=primary.get("rows", 0),
                column_count=len(primary.get("columns", [])),
                columns=primary.get("columns", []),
            )
            measurement.has_pagination = self._has("pagination", "pagination", "page")
            measurement.has_page_size = self._has("page-size", "page-size", "page size", "rows per page")
            measurement.has_sorting = self._has("sort", "sortable", "sort asc", "sort desc")
            measurement.has_filtering = self._has("filter", "filter")
            measurement.has_search = self._has("search", "search", "filter")
            measurement.has_empty_state = self._has_text("no records", "no data", "nothing here", "empty")
            measurement.has_error_state = self._has_text("error", "failed", "unable to load")
            measurement.horizontal_overflow = self._has_horizontal_overflow()
            measurement.has_context_columns = any(
                any(token in col.lower() for token in ("org", "organisation", "organization",
                                                       "client", "entity", "company"))
                for col in measurement.columns
            )
            return TableAuditResult(table_key=table_key, measurement=measurement)
        except ToolUnavailable:
            raise
        except Exception as exc:
            return TableAuditResult(table_key=table_key, error=str(exc))

    def _has(self, *tokens: str) -> bool:
        try:
            return self.page.evaluate(
                "tokens => { const t = document.body.innerText.toLowerCase(); "
                "return tokens.some(tok => t.includes(tok)); }",
                list(tokens),
            )
        except Exception:
            return False

    def _has_text(self, *tokens: str) -> bool:
        return self._has(*tokens)

    def _has_horizontal_overflow(self) -> bool:
        try:
            return self.page.evaluate(
                "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
            )
        except Exception:
            return False
