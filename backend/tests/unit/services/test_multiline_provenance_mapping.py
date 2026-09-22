"""CL-57 / 026 — multi-row PDF provenance through extraction → mapping → factor → calculation.

Locks the bounded repairs made by `CT-STEP2-MULTILINE-PROVENANCE-MAPPING-026`:

* every candidate line carries its **literal source description** (source evidence) as well as
  its quantity/unit/order/source line, so a row whose canonical activity keyword did not resolve
  still reaches the existing matcher;
* the mapping stage preserves each row's own identity (`source_ordinal`, `line_number`,
  `source_line`) instead of relying on list position, and records **explicitly unresolved** rows
  rather than dropping them — never fabricating an activity or a factor;
* the calculation request keeps the per-row provenance needed to trace a report line back to its
  source row, and the single-line document path is unchanged.
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Optional

import pytest

from domain.automatic_processing import AutomaticProcessingJob
from domain.matching import MatchResult
from services import automatic_processing as ap
from services import extraction_fidelity as p1

ORG = "00000000-0000-4000-8000-000000000001"

#: Verbatim text layer of the production oracle (`multi_fuel.pdf`, 2 pages).
MULTI_FUEL_PAGE_1 = (
    "Pure Energy PLC\n"
    "967 Renewable Road\n"
    "Liverpool\n"
    "IV47 7UK\n"
    "UK\n"
    "FUEL INVOICE\n"
    "Ref No.: PWR/2026/8130\n"
    "Date: May 08, 2026\n"
    "Buyer: Power Power & Co\n"
    "Period: Apr 01, 2026 – Apr 30, 2026\n"
    "ID: multi_fuel\n"
    "Description Qty Unit Rate Subtotal\n"
    "Gas usage 5,362.2000 kWh €0.0670 €359.2700\n"
    "Diesel supply 4,434.4000 L €1.6190 €7,179.2900\n"
    "Waste disposal 60 t €105.8140 €6,348.8400\n"
    "Water supply 163.2000 m³ €2.0130 €328.5200\n"
    "Power consumption 24,620.5000 kWh €0.1710 €4,210.1100\n"
    "Subtotal: €18,426.0300\n"
    "Sales Tax: €3,685.2000\n"
    "Net Payable: €22,111.2300\n"
    "Terms: Net 30 days.\n"
)
MULTI_FUEL = MULTI_FUEL_PAGE_1 + "\f" + "For testing purposes only\n"

ORACLE_ROWS = (
    ("Gas usage 5,362.2000 kWh €0.0670 €359.2700", 5362.2, "kwh"),
    ("Diesel supply 4,434.4000 L €1.6190 €7,179.2900", 4434.4, "l"),
    ("Waste disposal 60 t €105.8140 €6,348.8400", 60.0, "t"),
    ("Water supply 163.2000 m³ €2.0130 €328.5200", 163.2, "m3"),
    ("Power consumption 24,620.5000 kWh €0.1710 €4,210.1100", 24620.5, "kwh"),
)

SINGLE_LINE = "Acme Water Ltd\nInvoice 1234\nElectricity supply 12,500 kWh 2,340.00\n"

FACTOR = SimpleNamespace(
    id="factor-1",
    activity_type="Diesel (average biofuel blend)",
    unit="litres",
    scope="scope_1",
)


class _RecordingMatcher:
    """Records the match requests the mapping stage issues."""

    def __init__(self, *, unmatched: tuple[str, ...] = ()) -> None:
        self.requests: list[Any] = []
        self.unmatched = unmatched

    async def match(self, request):
        self.requests.append(request)
        if any(token in request.activity for token in self.unmatched):
            return MatchResult(
                status="unmatched", factor=None, confidence=0.0,
                methodology="keyword_search", stages_executed=("keyword_search",),
            )
        return MatchResult(
            status="matched", factor=FACTOR, confidence=1.0,
            methodology="keyword_search", stages_executed=("keyword_search",),
        )


class _RecordingCalculator:
    """Records the calculation requests (the calculation provenance surface)."""

    def __init__(self) -> None:
        self.requests: list[Any] = []

    async def calculate(self, request):
        self.requests.append(request)
        n = len(self.requests)
        return SimpleNamespace(
            snapshot=SimpleNamespace(id=f"snap-{n}", co2e_kg=Decimal("10.0"))
        )


class _FakeProcessing:
    def __init__(self, job: AutomaticProcessingJob) -> None:
        self.store = {job.id: job}
        self.stages: list[dict[str, Any]] = []
        self.blocked: list[str] = []

    async def advance_stage(self, job_id: str, *, target_stage: str, lock_token: str, **kw: Any):
        self.stages.append({"stage": target_stage, **kw})
        return self.store[job_id]

    async def mark_blocked(self, job_id: str, *, reason: str, lock_token: str, **kw: Any):
        self.blocked.append(reason)
        return self.store[job_id]

    async def mark_notified(self, job_id: str):
        return None

    async def release_lock(self, job_id: str, lock_token: str) -> bool:
        return True

    async def mark_failed(self, job_id: str, *, last_error: str, lock_token: str, **kw: Any):
        self.blocked.append(last_error)
        return self.store[job_id]


class _FakeFactors:
    def __init__(self) -> None:
        self.lookups: list[str] = []

    async def get(self, factor_id: str):
        self.lookups.append(factor_id)
        return FACTOR if factor_id == FACTOR.id else None

    async def find_by_activity(self, activity: str, **kw: Any):
        return [FACTOR]


class _FakeCustomerFactors:
    async def get(self, factor_id: str):
        return None


class _FakeManualExtraction:
    def __init__(self) -> None:
        self.mapped: list[Any] = []

    async def save_mapped_data(self, *a: Any, **k: Any):
        self.mapped.append((a, k))
        return None

    async def set_item_status(self, *a: Any, **k: Any):
        return None

    async def save_calculation(self, *a: Any, **k: Any):
        return None


class _FakeEvidenceLineItems:
    """Ordinal → materialised line-id lookup (B2 surface, read-only).

    ``pages`` seeds the authoritative per-line ``source_page`` that
    ``evidence_line_items`` would hold for an ordinal (``None`` = no verified page).
    """

    def __init__(self, pages: Optional[dict[int, Optional[int]]] = None) -> None:
        self.pages = dict(pages or {})
        self.reads: list[str] = []

    async def get_by_ordinals(self, item_id: str, ordinals):
        return {ordinal: f"line-{item_id}-{ordinal}" for ordinal in ordinals}

    async def get(self, line_id: str):
        """The authoritative line row (only ``source_page`` is consumed here)."""
        self.reads.append(line_id)
        ordinal = int(str(line_id).rsplit("-", 1)[-1])
        return {
            "id": line_id,
            "line_number": ordinal,
            "source_page": self.pages.get(ordinal),
        }


class _FakeLogs:
    async def find_snapshot_by_request_id(self, request_id: str):
        return None


class _FakeNotifications:
    async def create(self, *a: Any, **k: Any):
        return None


class _FakeOrganizations:
    async def get_members(self, org_id: str):
        return []


def _repos(job: AutomaticProcessingJob, *, line_pages=None):
    return SimpleNamespace(
        processing=_FakeProcessing(job),
        factors=_FakeFactors(),
        customer_factors=_FakeCustomerFactors(),
        manual_extraction=_FakeManualExtraction(),
        evidence_line_items=_FakeEvidenceLineItems(line_pages),
        logs=_FakeLogs(),
        notifications=_FakeNotifications(),
        organizations=_FakeOrganizations(),
    )


def _multi_row_job(items, **overrides) -> AutomaticProcessingJob:
    base = dict(
        id=str(uuid.uuid4()),
        organization_id=ORG,
        file_name="multi_row_invoice.pdf",
        file_url="uploads/org-1/multi_row_invoice.pdf",
        file_type="PDF",
        stage="mapping",
        status="processing",
        metadata={"mime": "application/pdf", "page_count": 2},
        source_item_id="item-1",
        extracted_data={"date": "2026-05-08", "supplier": "Pure Energy PLC",
                        "line_items": items},
        automation_extracted_data={"date": "2026-05-08", "supplier": "Pure Energy PLC",
                                   "line_items": items},
        validation_result={"status": "passed"},
    )
    base.update(overrides)
    return AutomaticProcessingJob(**base)


def _items():
    items, coverage = p1.build_line_items(MULTI_FUEL, method="pdf_text", page_count=2)
    return items, coverage


# -- 1-9 / 16: five distinct rows, evidence preserved, single-line unchanged ---
def test_extraction_yields_five_distinct_line_items_with_source_evidence() -> None:
    items, coverage = _items()
    assert len(items) == 5
    assert coverage["candidate_lines"] == 5 and coverage["line_items"] == 5
    assert [item["source_line"] for item in items] == [row for row, _q, _u in ORACLE_ROWS]
    assert [item["line_number"] for item in items] == [1, 2, 3, 4, 5]
    assert len({item["source_line"] for item in items}) == 5


@pytest.mark.parametrize(("raw", "quantity", "unit"), ORACLE_ROWS)
def test_row_evidence_survives_extraction(raw: str, quantity: float, unit: str) -> None:
    items, _ = _items()
    item = next(i for i in items if i["source_line"] == raw)
    assert item["quantity"] == quantity            # correct quantity column
    assert item["unit"] == unit                    # no unit borrowed from a neighbour
    assert item["description"]                     # literal source text always carried
    assert raw.split()[0].lower() in item["description"].lower()
    assert item["page"] == 1                       # page_basis is `document`; nothing invented


def test_description_is_carried_even_when_a_canonical_activity_resolved() -> None:
    items, _ = _items()
    without_activity = [i for i in items if "activity" not in i]
    assert without_activity, "oracle row 5 has no canonical activity keyword"
    assert all(i.get("description") for i in without_activity)
    assert all(i.get("description") for i in items)


def test_source_order_and_values_are_not_blended_positionally() -> None:
    items, _ = _items()
    assert [i["quantity"] for i in items] == [5362.2, 4434.4, 60.0, 163.2, 24620.5]
    assert [i["unit"] for i in items] == ["kwh", "l", "t", "m3", "kwh"]


def test_single_line_document_is_unchanged() -> None:
    items, _ = p1.build_line_items(SINGLE_LINE, method="pdf_text", page_count=1)
    assert len(items) == 1
    assert items[0]["quantity"] == 12500.0 and items[0]["unit"] == "kwh"


# -- 10 / 15: mapping-input and unresolved-entry contracts (no fabrication) ---
def test_mapping_input_prefers_activity_then_literal_description() -> None:
    assert ap._mapping_input_text({"activity": "Diesel"}) == "Diesel"
    assert (
        ap._mapping_input_text({"description": "Power consumption kWh"})
        == "Power consumption kWh"
    )
    assert (
        ap._mapping_input_text({"activity": " ", "description": "Water supply"})
        == "Water supply"
    )
    assert ap._mapping_input_text({}) == ""


def test_line_identity_never_invents_fields() -> None:
    assert ap._line_identity({}, 0) == {"source_ordinal": 1}
    assert ap._line_identity({"line_number": 3, "source_line": "Waste disposal 60 t"}, 2) == {
        "source_ordinal": 3,
        "line_number": 3,
        "source_line": "Waste disposal 60 t",
    }


def test_unresolved_entry_preserves_identity_and_carries_no_factor() -> None:
    entry = ap._unresolved_mapping_entry(
        {"line_number": 5, "source_line": "Power consumption 24,620.5000 kWh"},
        4,
        "no confident factor",
        activity="Power consumption",
        unit="kwh",
    )
    assert entry["status"] == "unmapped"
    assert entry["source_ordinal"] == 5 and entry["line_number"] == 5
    assert "factor_id" not in entry and "mapping_confidence" not in entry


def _service(repos, *, matcher=None, calculator=None):
    return ap.AutomaticProcessingService(
        repos,
        matching_engine=matcher or _RecordingMatcher(),
        calculation_engine=calculator or _RecordingCalculator(),
    )


# -- 10-11: mapping preserves each row's own identity ------------------------
async def test_mapping_preserves_each_rows_own_identity() -> None:
    items, _ = _items()
    job = _multi_row_job(items)
    repos = _repos(job)
    service = _service(repos)
    assert await service._map(job, "token") == "validating"
    lines = repos.processing.stages[-1]["mapped_data"]["line_items"]
    assert len(lines) == 5
    assert [line["source_ordinal"] for line in lines] == [1, 2, 3, 4, 5]
    assert [line["source_line"] for line in lines] == [row for row, _q, _u in ORACLE_ROWS]
    assert [line["line_number"] for line in lines] == [1, 2, 3, 4, 5]
    assert all(line["status"] == "mapped" and line["factor_id"] for line in lines)
    assert repos.processing.blocked == []


async def test_row_without_a_keyword_reaches_the_matcher_with_its_source_text() -> None:
    items, _ = _items()
    job = _multi_row_job(items)
    repos = _repos(job)
    matcher = _RecordingMatcher(unmatched=("Power consumption",))
    service = _service(repos, matcher=matcher)
    assert await service._map(job, "token") == "blocked"
    # the row was asked about (it used to be dropped before any match attempt) …
    assert any("Power consumption" in request.activity for request in matcher.requests)
    # … and the governed outcome is an explicit, truthful manual-review block
    assert any("line 5" in reason for reason in repos.processing.blocked)
    # nothing partial was persisted while a row is unresolved (no silent partial mapping)
    assert all("mapped_data" not in stage for stage in repos.processing.stages)


async def test_unresolved_row_produces_an_explicit_unmapped_entry() -> None:
    items, _ = _items()
    job = _multi_row_job(items, extracted_data={
        "date": "2026-05-08",
        "line_items": [
            {"description": "Unmappable row", "quantity": 1.0, "unit": "kwh",
             "line_number": 1, "source_line": "Unmappable row 1 kWh"},
        ],
    })
    repos = _repos(job)
    matcher = _RecordingMatcher(unmatched=("Unmappable",))
    service = _service(repos, matcher=matcher)
    await service._map(job, "token")
    assert matcher.requests[0].activity == "Unmappable row"
    assert any("line 1" in reason for reason in repos.processing.blocked)


# -- 12-14: calculation keeps per-row provenance; report can trace back ------
def _mapped_job(items, mapped):
    job = _multi_row_job(items, mapped_data=mapped)
    return job


async def test_calculation_carries_per_row_provenance() -> None:
    items, _ = _items()
    # derive the real mapping the same way production does
    seed_job = _multi_row_job(items)
    seed_repos = _repos(seed_job)
    await _service(seed_repos)._map(seed_job, "token")
    mapped_data = seed_repos.processing.stages[-1]["mapped_data"]

    job = _mapped_job(items, mapped_data)
    repos = _repos(job)
    calculator = _RecordingCalculator()
    service = _service(repos, calculator=calculator)
    stage = await service._calculate(job, "token")
    assert stage == "review", repos.processing.blocked

    requests = calculator.requests
    assert len(requests) == 5
    assert [str(r.quantity) for r in requests] == [
        "5362.2", "4434.4", "60.0", "163.2", "24620.5",
    ]
    # the source unit survives into the mapping record (canonical unit spelling) …
    assert [str(line["unit"]).lower() for line in mapped_data["line_items"]] == [
        "kwh", "litres", "tonnes", "cubic metres", "kwh",
    ]
    # … and the calculation request carries a unit for every row (the engine's own
    # alias resolution decides the final spelling — see the 026 report limitation)
    assert all(r.quantity_unit for r in requests)
    # report → source trace: every calculation carries its document + line identity …
    assert {r.source_item_id for r in requests} == {"item-1"}
    assert {r.source_file for r in requests} == {"multi_row_invoice.pdf"}
    assert [r.source_line_item_id for r in requests] == [
        "line-item-1-1", "line-item-1-2", "line-item-1-3", "line-item-1-4", "line-item-1-5",
    ]
    # … and the factor used is traced, never invented
    assert all(r.factor is not None and r.factor.id == FACTOR.id for r in requests)




# -- F-B2-7: ``source_page`` is a source LOCATION, never a page count ---------
async def test_calculation_source_page_is_the_authoritative_line_page() -> None:
    """The snapshot's page must come from the evidence line, not ``page_count``."""
    items, _ = _items()
    seed_job = _multi_row_job(items)
    seed_repos = _repos(seed_job)
    await _service(seed_repos)._map(seed_job, "token")
    mapped_data = seed_repos.processing.stages[-1]["mapped_data"]

    # The document reports 8 pages; every authoritative line lives on page 2.
    job = _multi_row_job(
        items,
        mapped_data=mapped_data,
        metadata={"mime": "application/pdf", "page_count": 8},
    )
    repos = _repos(job, line_pages={1: 2, 2: 2, 3: 2, 4: 2, 5: 2})
    calculator = _RecordingCalculator()
    stage = await _service(repos, calculator=calculator)._calculate(job, "token")

    assert stage == "review", repos.processing.blocked
    pages = [r.source_page for r in calculator.requests]
    assert pages == [2, 2, 2, 2, 2]
    assert 8 not in pages, "the document page count must never be a source page"


async def test_calculation_source_page_is_null_when_no_line_page_is_verifiable() -> None:
    """With no authoritative per-line page the value stays NULL (never a count)."""
    items, _ = _items()
    seed_job = _multi_row_job(items)
    seed_repos = _repos(seed_job)
    await _service(seed_repos)._map(seed_job, "token")
    mapped_data = seed_repos.processing.stages[-1]["mapped_data"]

    job = _multi_row_job(
        items,
        mapped_data=mapped_data,
        metadata={"mime": "application/pdf", "page_count": 8},
    )
    repos = _repos(job)  # no materialised per-line page
    calculator = _RecordingCalculator()
    stage = await _service(repos, calculator=calculator)._calculate(job, "token")

    assert stage == "review", repos.processing.blocked
    assert [r.source_page for r in calculator.requests] == [None] * 5

