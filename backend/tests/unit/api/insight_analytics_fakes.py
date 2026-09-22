"""Fakes for the Phase 8 Insight analytics tests (test support only).

Two layers are covered in the Phase 8 analytics suite, and each is replaced by the
right kind of double so the assertions stay honest:

* the **SQL layer** (``data.emissions_logs``) is covered by *pure* unit tests over
  ``_snapshot_filter_clause`` / ``_analytics_expression`` / ``_containment_pattern``
  (the functions that build the statement), which prove allowlisting, positional
  parameterisation and bounds without a database;
* the **tool/service layer** is covered against the doubles below, which record the
  arguments they received and return canned rows, so a test can assert exactly what
  the deterministic layer asked for (filters, dimension, period, bound) and how the
  result was shaped, without re-implementing SQL in Python.

LIMITATION (stated, not hidden): the SQL itself was not executed in this
environment. Executing these statements (and the limiter's atomic statements)
requires a disposable database; the F-046-1 invariant forbids running the
destructive integration harness against any persistent database, so that
verification remains an integration task.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Optional

from domain.insight_query import (
    canonical_scope,
    parse_iso_date,
    parse_int,
    resolve_amount_bounds,
)


class InsightLogsFake:
    """Records analytics calls and returns canned snapshot/aggregate rows."""

    def __init__(self) -> None:
        self.snapshots: list[dict[str, Any]] = []
        self.groups: list[dict[str, Any]] = []
        self.labels: dict[str, str] = {}
        self.group_snapshots: list[dict[str, Any]] = []
        self.totals = {"rows": 0, "co2e": Decimal("0")}
        self.calls: list[dict[str, Any]] = []
        self.match_count_override: Optional[int] = None
        self.provenance_count_override: Optional[int] = None
        # P2 — per-period overrides so a two-period comparison can be driven with
        # different authoritative totals/groups per period. When a period has no
        # entry the single-period ``totals``/``groups`` values above are used, so
        # every existing test keeps its original behaviour.
        self.period_totals: dict[tuple[str, str], dict[str, Any]] = {}
        self.period_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}

    @staticmethod
    def _period_key(period: Any) -> tuple[str, str]:
        start = getattr(period, "start_date", None)
        end = getattr(period, "end_date", None)
        return (str(start), str(end))

    def set_period(self, start: str, end: str, *, rows: int, co2e: str) -> None:
        """Declare the authoritative totals for one bounded period."""
        self.period_totals[(start, end)] = {"rows": int(rows), "co2e": Decimal(co2e)}

    def set_period_groups(self, start: str, end: str, groups: list[dict[str, Any]]) -> None:
        """Declare the authoritative grouped rows for one bounded period."""
        self.period_groups[(start, end)] = [dict(g) for g in groups]

    async def search_snapshots(self, org_id: str, filters: dict, limit: int) -> list[dict]:
        self.calls.append(
            {"method": "search_snapshots", "org": org_id, "filters": dict(filters), "limit": limit}
        )
        rows = [r for r in self.snapshots if r.get("organization_id") == org_id]
        return [r for r in rows if _matches(r, filters)][:limit]

    async def count_matching_snapshots(self, org_id: str, filters: dict, cap: int) -> int:
        self.calls.append(
            {"method": "count_matching_snapshots", "org": org_id, "filters": dict(filters), "cap": cap}
        )
        if self.match_count_override is not None:
            return self.match_count_override
        rows = [r for r in self.snapshots if r.get("organization_id") == org_id and _matches(r, filters)]
        return min(len(rows), cap)

    async def aggregate_groups(self, org_id: str, period, dimension: str, limit: int) -> list[dict]:
        self.calls.append(
            {
                "method": "aggregate_groups",
                "org": org_id,
                "period": period,
                "dimension": dimension,
                "limit": limit,
            }
        )
        rows = self.period_groups.get(self._period_key(period), self.groups)
        return [dict(g) for g in rows][:limit]

    async def group_labels(self, org_id: str, dimension: str, keys: list[str]) -> dict[str, str]:
        self.calls.append(
            {"method": "group_labels", "org": org_id, "dimension": dimension, "keys": list(keys)}
        )
        return {k: self.labels[k] for k in keys if k in self.labels}

    async def aggregate(self, org_id: str, period, group_by: str):
        self.calls.append({"method": "aggregate", "org": org_id, "period": period, "group_by": group_by})
        totals = self.period_totals.get(self._period_key(period), self.totals)
        return SimpleNamespace(
            total_co2e_kg=Decimal(str(totals["co2e"])),
            total_rows=int(totals["rows"]),
        )

    async def list_group_snapshots(
        self, org_id: str, period, dimension: str, group_key: str, limit: int
    ) -> list[dict]:
        self.calls.append(
            {
                "method": "list_group_snapshots",
                "org": org_id,
                "period": period,
                "dimension": dimension,
                "group_key": group_key,
                "limit": limit,
            }
        )
        return [dict(r) for r in self.group_snapshots][:limit]

    async def count_group_snapshots(
        self, org_id: str, period, dimension: str, group_key: str, cap: int
    ) -> int:
        self.calls.append(
            {
                "method": "count_group_snapshots",
                "org": org_id,
                "period": period,
                "dimension": dimension,
                "group_key": group_key,
                "cap": cap,
            }
        )
        if self.provenance_count_override is not None:
            return self.provenance_count_override
        return min(len(self.group_snapshots), cap)

    def method_calls(self, name: str) -> list[dict]:
        return [c for c in self.calls if c["method"] == name]


def snapshot_row(
    snapshot_id: str,
    *,
    organization_id: str,
    date_value: str = "2024-02-02",
    co2e: str = "20000",
    activity_type: str = "diesel",
    scope: str = "Scope 1",
    reporting_year: int = 2024,
    source_line_item_id: str = "line-1",
    asset_id: str = "asset-1",
    facility_id: str = "facility-1",
    supplier_id: Optional[str] = None,
) -> dict[str, Any]:
    """One authoritative snapshot row plus its log-level lineage attributes."""
    return {
        "id": snapshot_id,
        "organization_id": organization_id,
        "activity": activity_type,
        "activity_type": activity_type,
        "quantity": Decimal("10"),
        "quantity_unit": "litres",
        "co2e_multiplier": Decimal("2.5"),
        "co2e_kg": Decimal(str(co2e)),
        "scope": scope,
        "date": date.fromisoformat(date_value),
        "reporting_year": reporting_year,
        "methodology": "direct_multiply",
        "algorithm_version": "v1",
        "content_hash": "hash",
        "factor_id": "factor-1",
        "factor_kind": "emission_factor",
        "customer_factor_id": None,
        "factor_source": "DEFRA",
        "source_item_id": "item-1",
        "source_line_item_id": source_line_item_id,
        "asset_id": asset_id,
        "facility_id": facility_id,
        "supplier_id": supplier_id,
    }


def provenance_row(snapshot_id: str, *, co2e: str = "20000") -> dict[str, Any]:
    """One bounded provenance row (snapshot identity + basis only)."""
    return {
        "id": snapshot_id,
        "date": date(2024, 2, 2),
        "activity_type": "diesel",
        "scope": "Scope 1",
        "co2e_kg": Decimal(str(co2e)),
        "source_line_item_id": "line-1",
    }


# --------------------------------------------------------------------------
# Interaction-path doubles (Layer-1 message/state, Layer-2 evidence, audit)
# --------------------------------------------------------------------------
class InsightConversationFake:
    """Layer-1 conversation + message store (I1 shape, in memory)."""

    def __init__(self, conversation_id: str, organization_id: str, created_by: str) -> None:
        self.conversation_id = conversation_id
        self.organization_id = organization_id
        self.created_by = created_by
        self.messages: list[dict[str, Any]] = []

    async def get_conversation(self, *, conversation_id, organization_id):
        if conversation_id != self.conversation_id or organization_id != self.organization_id:
            return None
        return SimpleNamespace(
            id=self.conversation_id,
            organization_id=self.organization_id,
            created_by=self.created_by,
        )

    async def add_message(self, **kwargs):
        message = {"id": f"msg-{len(self.messages) + 1}", **kwargs}
        self.messages.append(message)
        return SimpleNamespace(**message)


class InsightInteractionFake:
    """Layer-2 interaction + tool-call evidence (append-only, in memory)."""

    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.tool_calls: list[dict[str, Any]] = []
        self.order: list[str] = []

    async def create_interaction(self, **kwargs):
        interaction_id = f"int-{len(self.rows) + 1}"
        row = {
            "id": interaction_id,
            "lifecycle": "received",
            "answer_status": None,
            "narration_state": "not_attempted",
            "provider": None,
            "model": None,
            "model_version": None,
            "tokens_used": None,
            "cost": None,
            "tool_call_count": 0,
            "reference_count": 0,
            "error_class": None,
            "audit_record_id": None,
            "metadata": {},
            **kwargs,
        }
        self.rows[interaction_id] = row
        self.order.append(interaction_id)
        return SimpleNamespace(**row)

    async def find_by_idempotency_key(self, *, organization_id, idempotency_key):
        for row in self.rows.values():
            if (
                row["organization_id"] == organization_id
                and row.get("idempotency_key") == idempotency_key
            ):
                return SimpleNamespace(**row)
        return None

    async def mark_executing(self, *, interaction_id, organization_id):
        self.rows[interaction_id]["lifecycle"] = "executing"

    async def complete_interaction(self, *, interaction_id, organization_id, **kwargs):
        self.rows[interaction_id].update(kwargs)

    async def record_tool_call(self, **kwargs):
        record = SimpleNamespace(id=f"call-{len(self.tool_calls) + 1}", **kwargs)
        self.tool_calls.append(kwargs)
        return record

    async def list_tool_calls(self, *, interaction_id, organization_id):
        return [SimpleNamespace(**call) for call in self.tool_calls]


class AuditSinkFake:
    """Minimal canonical audit sink (records entity/before/after entries)."""

    def __init__(self) -> None:
        self.entries: list[Any] = []

    async def record(self, entry):
        self.entries.append(entry)
        return entry

    async def query(self, filters):
        return list(self.entries)


def _matches(row: dict[str, Any], filters: dict[str, Any]) -> bool:
    """Restate the documented filter semantics for the test double.

    This is a double, not the system under test: the real filtering is SQL, which
    the pure builder tests in ``tests/unit/data/test_p8_insight_analytics_sql.py``
    pin directly. The semantics are restated here only so the tool layer can be
    exercised end to end without a database.
    """
    start = parse_iso_date(filters.get("start_date"))
    end = parse_iso_date(filters.get("end_date"))
    row_date = row.get("date")
    if start is not None and (row_date is None or row_date < start):
        return False
    if end is not None and (row_date is None or row_date > end):
        return False
    year = parse_int(filters.get("reporting_year"))
    if year is not None and row.get("reporting_year") != year:
        return False
    bounds = resolve_amount_bounds(filters)
    if bounds is not None:
        value = row.get("co2e_kg")
        if value is None or value < bounds.low or value > bounds.high:
            return False
    activity = str(filters.get("activity") or "").strip().lower()
    if activity and activity not in str(row.get("activity_type") or "").lower():
        return False
    # The SQL layer canonicalises the scope filter before comparing.
    scope = canonical_scope(filters.get("scope"))
    if scope and str(row.get("scope")) != str(scope):
        return False
    for key, attribute in (
        ("supplier_id", "supplier_id"),
        ("facility_id", "facility_id"),
        ("asset_id", "asset_id"),
    ):
        if filters.get(key) and str(row.get(attribute)) != str(filters[key]):
            return False
    return True
