"""Unit tests for the automatic-processing service (CL-56) with fake repos."""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Optional

from domain.automatic_processing import AutomaticProcessingJob
from domain.factor import EmissionFactor
from domain.matching import MatchResult
from services.automatic_processing import AutomaticProcessingService

_ORG = "11111111-1111-4111-8111-111111111111"
_FACTOR = EmissionFactor(
    id="factor-1",
    reporting_year=2025,
    activity_type="Fuels > Liquid fuels > Diesel (kg CO2e) [litres]",
    co2e_multiplier=Decimal("2.668"),
    unit="litres",
    scope="Scope 1",
    factor_source="DEFRA-DESNZ",
    factor_set="DEFRA-2025",
)


class _FakeProcessing:
    """Durable-job store + transition recording (mirrors the repository)."""

    def __init__(self) -> None:
        self.store: dict[str, AutomaticProcessingJob] = {}
        self.marked_blocked: list[str] = []
        self.marked_failed: list[str] = []

    @staticmethod
    def _clone(job: AutomaticProcessingJob, **changes) -> AutomaticProcessingJob:
        import dataclasses

        base = dataclasses.asdict(job)
        base.update(changes)
        return AutomaticProcessingJob(**base)

    async def get(self, job_id: str) -> Optional[AutomaticProcessingJob]:
        return self.store.get(job_id)

    async def advance_stage(self, job_id: str, **kw: Any) -> Optional[AutomaticProcessingJob]:
        job = self.store[job_id]
        stage = kw.get("target_stage", job.stage)
        changes: dict[str, Any] = {
            "stage": stage,
            "status": "processing"
            if stage not in ("review", "completed", "failed", "blocked")
            else stage,
        }
        for key in ("extracted_data", "mapped_data", "validation_result",
                    "calculation_snapshot_id", "attempt_count"):
            if key in kw:
                changes[key] = kw[key]
        updated = self._clone(job, **changes)
        self.store[job_id] = updated
        return updated

    async def mark_blocked(self, job_id: str, *, reason: str, lock_token: str, **kw: Any):
        self.marked_blocked.append(reason)
        job = self.store[job_id]
        updated = self._clone(job, stage="blocked", status="manual_review",
                              manual_review_reason=reason)
        self.store[job_id] = updated
        return updated

    async def mark_failed(self, job_id: str, *, last_error: str, lock_token: str, **kw: Any):
        self.marked_failed.append(last_error)
        job = self.store[job_id]
        updated = self._clone(job, stage="failed", status="failed", last_error=last_error)
        self.store[job_id] = updated
        return updated

    async def release_lock(self, job_id: str, lock_token: str) -> bool:
        return True

    async def mark_notified(self, job_id: str):
        return None


class _FakeRepos:
    def __init__(self, job: AutomaticProcessingJob) -> None:
        self.processing = _FakeProcessing()
        self.processing.store[job.id] = job
        self.logs = _FakeLogs()
        self.organizations = _FakeOrganizations()


class _FakeFactors:
    async def get(self, factor_id: str) -> Optional[EmissionFactor]:
        return _FACTOR if factor_id == _FACTOR.id else None

    async def find_by_activity(self, activity: str, unit: Optional[str] = None, limit: int = 20):
        return [_FACTOR]


class _FakeCustomerFactors:
    async def get(self, factor_id: str):
        return None


class _FakeLogs:
    def __init__(self) -> None:
        self.snapshots: dict[str, dict] = {}

    async def find_snapshot_by_request_id(self, request_id: str) -> Optional[dict]:
        return self.snapshots.get(request_id)


class _FakeOrganizations:
    async def get_members(self, org_id: str):
        return []


class _FakeNotifications:
    async def create(self, *args: Any, **kw: Any):
        return None


class _FakeManualExtraction:
    async def save_extracted_data(self, *a: Any, **k: Any):
        return None

    async def save_mapped_data(self, *a: Any, **k: Any):
        return None

    async def set_item_status(self, *a: Any, **k: Any):
        return None

    async def save_calculation(self, *a: Any, **k: Any):
        return None


class _FakeMatchingEngine:
    async def match(self, request):
        return MatchResult(
            status="matched",
            factor=_FACTOR,
            confidence=1.0,
            methodology="keyword_search",
            stages_executed=("keyword_search",),
        )


class _FakeCalculationEngine:
    def __init__(self) -> None:
        self.calls = 0

    async def calculate(self, request):
        from types import SimpleNamespace

        self.calls += 1
        return SimpleNamespace(
            snapshot=SimpleNamespace(
                id=f"snap-{self.calls}", co2e_kg=Decimal("10.0")
            )
        )


def _csv_job(**overrides) -> AutomaticProcessingJob:
    base = dict(
        id=str(uuid.uuid4()),
        organization_id=_ORG,
        file_name="fleet.csv",
        file_url="uploads/org-1/fleet.csv",
        file_type="SPREADSHEET",
        stage="enqueued",
        status="pending",
        metadata={"mime": "text/csv"},
        source_item_id="item-1",
    )
    base.update(overrides)
    return AutomaticProcessingJob(**base)


def _make_service(job: AutomaticProcessingJob):
    repos = _FakeRepos(job)
    repos.factors = _FakeFactors()
    repos.customer_factors = _FakeCustomerFactors()
    repos.notifications = _FakeNotifications()
    repos.manual_extraction = _FakeManualExtraction()
    service = AutomaticProcessingService(
        repos,
        matching_engine=_FakeMatchingEngine(),
        calculation_engine=_FakeCalculationEngine(),
    )
    service._content_cache[job.id] = (
        "Date,Supplier,Category,Quantity (litres),Amount,Currency\n"
        "05/01/2025,Shell Fleet Solutions,Diesel fuel,1250,1775.00,GBP\n"
    ).encode("utf-8")
    return service, repos


class TestPipelineExecution:
    async def test_full_auto_flow_reaches_review(self) -> None:
        job = _csv_job()
        service, repos = _make_service(job)
        final = await service.process_job(job, "token-1")
        assert final.stage == "review"
        assert final.extracted_data is not None
        assert final.mapped_data is not None
        assert final.validation_result == {"status": "passed", "findings": []}

    async def test_blocked_job_does_not_reprocess(self) -> None:
        job = _csv_job(stage="blocked", status="manual_review")
        service, repos = _make_service(job)
        final = await service.process_job(job, "token-1")
        assert final.stage == "blocked"
        assert repos.processing.marked_blocked == []

    async def test_idempotent_resume_skips_extraction(self) -> None:
        job = _csv_job(
            stage="extracting",
            status="processing",
            extracted_data={
                "supplier": "Shell Fleet Solutions",
                "date": "05/01/2025",
                "activity": "Diesel",
                "quantity": 1250.0,
                "unit": "litres",
            },
        )
        service, repos = _make_service(job)
        final = await service.process_job(job, "token-1")
        assert final.stage == "review"
        assert final.extracted_data["activity"] == "Diesel"

    async def test_no_duplicate_calculation_reuses_snapshot(self) -> None:
        job = _csv_job()
        service, repos = _make_service(job)
        await service.process_job(job, "token-1")
        first = repos.processing.store[job.id]
        calc = service._calculation_engine
        # A re-run of the same job (e.g. after a crash) reuses the snapshot.
        await service.process_job(first, "token-2")
        assert calc.calls == 1
        second = repos.processing.store[job.id]
        assert second.calculation_snapshot_id == first.calculation_snapshot_id
