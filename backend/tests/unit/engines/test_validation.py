"""Unit tests for engines.validation (Phase 9A — ValidationEngine A1–A9).

Covers every approved capability, the SEAI CO2-only requirement, and the
strict-mode/event/audit side effects. All repository surfaces are fakes; no
database is touched.
"""
from __future__ import annotations

import dataclasses
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import pytest

from core.exceptions import ValidationFailedError
from core.types import DateRange
from domain.audit import AuditEntry
from domain.calculation import CalculationSnapshot, EmissionLog
from domain.factor import RESULT_PRECISION, EmissionFactor
from domain.matching import MatchRequest, MatchResult
from domain.organization import Asset, Facility, Organization, OrganizationMetadata
from domain.validation import ValidationReport, ValidationRequest
from domain.workflow import DomainEvent, ValidationFailed
from infra.event_bus import EventBus

import engines.validation as _v

_SEAI_ELECTRICITY = "Fuels > Electricity > Electricity consumption (kg CO2) [kWh]"
_DEFRA_GAS = "Fuels > Gas fuels > Natural gas (kg CO2e) [kWh]"
_SEAI_BATCH = "9e3b2c8a-1d4f-4e6b-8a7c-2f5d6e7a8b9c"


def make_factor(**kwargs: Any) -> EmissionFactor:
    return EmissionFactor(
        id=str(kwargs.get("id") or f"f-{uuid.uuid4().hex[:12]}"),
        reporting_year=int(kwargs.get("year", 2025)),
        activity_type=str(kwargs.get("activity_type") or _DEFRA_GAS),
        co2e_multiplier=Decimal(str(kwargs.get("multiplier") or "0.18400")),
        unit=kwargs.get("unit") or "kWh",
        scope=kwargs.get("scope") or "Scope 1",
        factor_source=str(kwargs.get("factor_source") or "DEFRA-DESNZ"),
        factor_set=str(kwargs.get("factor_set") or "DEFRA-2025"),
        country=str(kwargs.get("country") or "GB"),
        provider_key=str(kwargs.get("provider") or "defra"),
        import_batch_id=kwargs.get("import_batch_id"),
        natural_key=(),
    )


def make_seai_factor(**kwargs: Any) -> EmissionFactor:
    return make_factor(
        activity_type=_SEAI_ELECTRICITY,
        factor_source="SEAI",
        factor_set="SEAI-2025",
        country="IE",
        provider="seai",
        scope="Scope 2",
        multiplier="0.197803384",
        unit="kWh",
        import_batch_id=_SEAI_BATCH,
        **kwargs,
    )


def make_log(**kwargs: Any) -> EmissionLog:
    factor = kwargs.get("factor")
    return EmissionLog(
        id=str(kwargs.get("id") or f"log-{uuid.uuid4().hex[:8]}"),
        organization_id=str(kwargs.get("organization_id") or "org-1"),
        factor_id=str(kwargs.get("factor_id") or (factor.id if factor else "f-1")),
        quantity=Decimal(str(kwargs.get("quantity") or "100")),
        date=kwargs.get("date", date(2025, 6, 1)),
        unit=kwargs.get("unit", factor.unit if factor else "kWh"),
        scope=kwargs.get("scope", factor.scope if factor else "Scope 1"),
        asset_id=kwargs.get("asset_id"),
        facility_id=kwargs.get("facility_id"),
        snapshot_id=kwargs.get("snapshot_id"),
        calculated_kg_co2e=Decimal(str(kwargs.get("calculated_kg_co2e") or "0")),
    )


def make_snapshot(**kwargs: Any) -> CalculationSnapshot:
    factor = kwargs.get("factor")
    quantity = Decimal(str(kwargs.get("quantity") or "100"))
    multiplier = Decimal(
        str(kwargs.get("multiplier") or (factor.co2e_multiplier if factor else "0.18400"))
    )
    co2e_kg = kwargs.get("co2e_kg")
    if co2e_kg is None:
        co2e_kg = (quantity * multiplier).quantize(RESULT_PRECISION)
    snapshot = CalculationSnapshot(
        id=str(kwargs.get("id") or f"snap-{uuid.uuid4().hex[:8]}"),
        match_request_id=str(kwargs.get("match_request_id") or "match-1"),
        organization_id=str(kwargs.get("organization_id") or "org-1"),
        factor_id=str(kwargs.get("factor_id") or (factor.id if factor else "f-1")),
        quantity=quantity,
        quantity_unit=str(kwargs.get("quantity_unit") or (factor.unit if factor else "kWh")),
        co2e_multiplier=multiplier,
        co2e_kg=Decimal(str(co2e_kg)),
        scope=kwargs.get("scope", factor.scope if factor else "Scope 1"),
        date=kwargs.get("date", date(2025, 6, 1)),
        reporting_year=int(kwargs.get("reporting_year") or 2025),
        methodology=str(kwargs.get("methodology") or "direct_multiply"),
        algorithm_version=str(kwargs.get("algorithm_version") or "v1.0"),
        created_at=kwargs.get("created_at", date(2025, 6, 1)),
        content_hash=str(kwargs.get("content_hash") or ""),
    )
    if not snapshot.content_hash:
        snapshot = dataclasses.replace(snapshot, content_hash=snapshot.build_content_hash())
    return snapshot


def setattr_log(log: EmissionLog, **changes: Any) -> EmissionLog:
    """Return ``log`` with fields overridden, bypassing domain validation.

    The ``EmissionLog`` domain model forbids negative quantity/co2e by
    construction, so the A6 stored-data corruption checks are exercised by
    setting attributes directly on a frozen (slots) instance.
    """
    for name, value in changes.items():
        object.__setattr__(log, name, value)
    return log



def make_org(**kwargs: Any) -> Organization:
    return Organization(
        id=str(kwargs.get("id") or "org-1"),
        name=str(kwargs.get("name") or "Test Co"),
        country=str(kwargs.get("country") or "GB"),
        is_active=bool(kwargs.get("is_active", True)),
        created_at=kwargs.get("created_at", datetime.now()),
    )


def make_metadata(**kwargs: Any) -> OrganizationMetadata:
    return OrganizationMetadata(
        total_floor_area_sqm=kwargs.get("total_floor_area_sqm"),
        occupied_floor_area_sqm=kwargs.get("occupied_floor_area_sqm"),
        fte_count=kwargs.get("fte_count"),
        annual_revenue_gbp=kwargs.get("annual_revenue_gbp"),
        sector=kwargs.get("sector"),
    )


def make_facility(facility_id: str = "fac-1", org_id: str = "org-1") -> Facility:
    return Facility(id=facility_id, organization_id=org_id, name="Facility 1", address="")


def make_asset(asset_id: str = "asset-1", org_id: str = "org-1") -> Asset:
    return Asset(
        id=asset_id,
        facility_id="fac-1",
        organization_id=org_id,
        name="Asset 1",
        asset_type="boiler",
    )


class _FakeLogs:
    def __init__(self, logs: Optional[list[EmissionLog]] = None) -> None:
        self.logs = list(logs or [])

    async def find_by_org(self, org_id: str, period: DateRange) -> list[EmissionLog]:
        return [log for log in self.logs if log.organization_id == org_id]


class _FakeOrgs:
    def __init__(
        self,
        org: Optional[Organization] = None,
        metadata: Optional[OrganizationMetadata] = None,
        facilities: Optional[list[Facility]] = None,
        assets: Optional[list[Asset]] = None,
    ) -> None:
        self.org = org
        self.metadata = metadata
        self.facilities = list(facilities or [])
        self.assets = list(assets or [])

    async def get(self, org_id: str) -> Optional[Organization]:
        return self.org

    async def get_metadata(self, org_id: str) -> Optional[OrganizationMetadata]:
        return self.metadata

    async def get_facilities(self, org_id: str) -> list[Facility]:
        return self.facilities

    async def get_assets(self, org_id: str) -> list[Asset]:
        return self.assets


class _FakeFactors:
    def __init__(self, factors: Optional[list[EmissionFactor]] = None) -> None:
        self.factors = {f.id: f for f in (factors or [])}

    async def get(self, factor_id: str) -> Optional[EmissionFactor]:
        return self.factors.get(factor_id)


class _AuditSink:
    """In-memory audit sink recording ``log_action`` calls."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    async def log_action(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        correlation_id: str,
        actor: Optional[str] = None,
        changed_fields: Optional[dict[str, Any]] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        before: Any = None,
        after: Any = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor or "system",
            occurred_at=datetime.now(timezone.utc),
            changed_fields=dict(changed_fields or {}),
            reason=reason,
            ip_address=ip_address,
            before=before,
            after=after,
        )
        self.entries.append(entry)
        return entry


def codes(report: ValidationReport) -> list[str]:
    return [issue.code for issue in report.issues]


def make_match_request(**kwargs: Any) -> MatchRequest:
    return MatchRequest(
        id=str(kwargs.get("id", "match-1")),
        activity=str(kwargs.get("activity", "Diesel")),
        country=str(kwargs.get("country", "GB")),
        reporting_year=int(kwargs.get("year", 2025)),
        unit=kwargs.get("unit", "kWh"),
        scope=kwargs.get("scope", "Scope 1"),
        preferred_provider=kwargs.get("preferred_provider"),
    )


def make_match_result(**kwargs: Any) -> MatchResult:
    factor = kwargs.get("factor") or make_factor()
    return MatchResult(
        status=str(kwargs.get("status", "matched")),
        factor=kwargs.get("factor", factor),
        confidence=float(kwargs.get("confidence", 1.0)),
        methodology=str(kwargs.get("methodology", "exact_match")),
        provider=kwargs.get("provider", factor.provider_key),
        request_id=str(kwargs.get("request_id", "match-1")),
    )


class TestA1Input:
    def test_valid_input(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        report = engine.validate_input(
            activity="Diesel", quantity=Decimal("100"), reporting_year=2025,
            quantity_unit="litres",
        )
        assert report.ok

    def test_empty_activity_error(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        report = engine.validate_input(
            activity="", quantity=Decimal("100"), reporting_year=2025
        )
        assert not report.ok
        assert _v.CODE_INPUT_ACTIVITY_EMPTY in codes(report)

    def test_negative_quantity_error(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        report = engine.validate_input(
            activity="Diesel", quantity=Decimal("-1"), reporting_year=2025
        )
        assert not report.ok
        assert _v.CODE_INPUT_QUANTITY_NEGATIVE in codes(report)

    def test_implausible_year_error(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        report = engine.validate_input(
            activity="Diesel", quantity=Decimal("100"), reporting_year=1899
        )
        assert not report.ok
        assert _v.CODE_INPUT_YEAR_RANGE in codes(report)

    def test_missing_unit_when_factor_requires_error(self) -> None:
        factor = make_factor(unit="kWh")
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        report = engine.validate_input(
            activity="Gas", quantity=Decimal("100"), reporting_year=2025, factor=factor
        )
        assert not report.ok
        assert _v.CODE_INPUT_UNIT_MISSING in codes(report)

    def test_seai_co2_only_input_valid(self) -> None:
        factor = make_seai_factor()
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        report = engine.validate_input(
            activity="Electricity", quantity=Decimal("100"), reporting_year=2025,
            quantity_unit="kWh", factor=factor,
        )
        assert report.ok


class TestA2Reproducibility:
    def test_valid_snapshot_ok(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        report = engine.validate_snapshot(make_snapshot())
        assert report.ok

    def test_co2e_mismatch_error(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        snap = dataclasses.replace(make_snapshot(), co2e_kg=Decimal("99"))
        report = engine.validate_snapshot(snap)
        assert not report.ok
        assert _v.CODE_CALC_MISMATCH in codes(report)

    def test_rounding_tolerance_warning(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        snap = make_snapshot(quantity="1", multiplier="0.18400")
        drifted = dataclasses.replace(
            snap, co2e_kg=Decimal("0.184000") + Decimal("0.0000005")
        )
        report = engine.validate_snapshot(drifted)
        assert _v.CODE_CALC_ROUNDING in codes(report)
        assert _v.CODE_CALC_MISMATCH not in codes(report)

    def test_empty_hash_error(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        snap = dataclasses.replace(make_snapshot(), content_hash="")
        report = engine.validate_snapshot(snap)
        assert not report.ok
        assert _v.CODE_HASH_EMPTY in codes(report)

    def test_hash_mismatch_error(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        snap = dataclasses.replace(make_snapshot(), content_hash="0" * 64)
        report = engine.validate_snapshot(snap)
        assert not report.ok
        assert _v.CODE_HASH_MISMATCH in codes(report)


class TestA3Match:
    def test_matched_correct_ok(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        factor = make_factor()
        report = engine.validate_match(
            make_match_request(factor=factor), make_match_result(factor=factor)
        )
        assert report.ok

    def test_incorrect_factor_country_error(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        factor = make_factor(country="IE", provider="seai")
        report = engine.validate_match(
            make_match_request(country="GB"), make_match_result(factor=factor)
        )
        assert not report.ok
        assert _v.CODE_MATCH_COUNTRY in codes(report)

    def test_incorrect_provider_error(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        factor = make_seai_factor()
        report = engine.validate_match(
            make_match_request(country="IE", preferred_provider="defra"),
            make_match_result(factor=factor),
        )
        assert not report.ok
        assert _v.CODE_MATCH_PROVIDER in codes(report)

    def test_unit_mismatch_error(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        factor = make_factor(unit="kWh")
        report = engine.validate_match(
            make_match_request(unit="litres"), make_match_result(factor=factor)
        )
        assert not report.ok
        assert _v.CODE_MATCH_UNIT in codes(report)

    def test_no_match_warning(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        result = MatchResult.no_match([], ["keyword_search"], request_id="match-0")
        report = engine.validate_match(make_match_request(), result)
        assert report.ok
        assert _v.CODE_MATCH_NO_RESULT in codes(report)

    def test_low_confidence_warning(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        factor = make_factor()
        report = engine.validate_match(
            make_match_request(factor=factor),
            make_match_result(factor=factor, confidence=0.5),
        )
        assert report.ok
        assert _v.CODE_MATCH_LOW_CONFIDENCE in codes(report)

    def test_matched_without_factor_error(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        malformed = make_match_result()
        object.__setattr__(malformed, "factor", None)
        report = engine.validate_match(make_match_request(), malformed)
        assert not report.ok
        assert _v.CODE_MATCH_NO_FACTOR in codes(report)


class TestA4ScopeUnit:
    def test_valid_log_ok(self) -> None:
        factor = make_factor()
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = make_log(factor=factor, snapshot_id="s", calculated_kg_co2e=Decimal("18.4"))
        report = engine._validate_log_consistency(log, factor)
        assert report.ok

    def test_unit_mismatch_error(self) -> None:
        factor = make_factor(unit="kWh")
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = make_log(factor=factor, unit="litres")
        report = engine._validate_log_consistency(log, factor)
        assert not report.ok
        assert _v.CODE_UNIT_MISMATCH in codes(report)

    def test_scope_mismatch_error(self) -> None:
        factor = make_factor(scope="Scope 1")
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = make_log(factor=factor, scope="Scope 2")
        report = engine._validate_log_consistency(log, factor)
        assert not report.ok
        assert _v.CODE_SCOPE_MISMATCH in codes(report)

    def test_unknown_scope_error(self) -> None:
        factor = make_factor(scope="Bogus")
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = make_log(factor=factor, scope="Bogus")
        report = engine._validate_log_consistency(log, factor)
        assert not report.ok
        assert _v.CODE_SCOPE_UNKNOWN in codes(report)

    def test_missing_scope_warning(self) -> None:
        factor = make_factor(scope="Scope 1")
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = make_log(factor=factor, scope=None)
        report = engine._validate_log_consistency(log, factor)
        assert report.ok
        assert _v.CODE_SCOPE_MISSING in codes(report)

    def test_family_mismatch_warning(self) -> None:
        factor = make_factor(activity_type=_SEAI_ELECTRICITY, scope="Scope 1")
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = make_log(factor=factor)
        report = engine._validate_log_consistency(log, factor)
        assert report.ok
        assert _v.CODE_SCOPE_FAMILY in codes(report)

    def test_seai_electricity_scope2_has_no_family_warning(self) -> None:
        factor = make_seai_factor()
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = make_log(factor=factor, unit="kWh", scope="Scope 2")
        report = engine._validate_log_consistency(log, factor)
        assert report.ok
        assert _v.CODE_SCOPE_FAMILY not in codes(report)


class TestA5SnapshotProvenance:
    def test_seai_snapshot_with_provenance_ok(self) -> None:
        factor = make_seai_factor()
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        snap = make_snapshot(factor=factor)
        report = engine.validate_snapshot(
            snap, factor,
            factor_source="SEAI", factor_set="SEAI-2025",
            import_batch_id=factor.import_batch_id,
        )
        assert report.ok

    def test_seai_snapshot_missing_provenance_warning(self) -> None:
        factor = make_seai_factor()
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        snap = make_snapshot(factor=factor)
        report = engine.validate_snapshot(snap, factor)
        assert report.ok
        assert _v.CODE_SNAPSHOT_PROVENANCE_MISSING in codes(report)

    def test_batch_mismatch_error(self) -> None:
        factor = make_seai_factor()
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        snap = make_snapshot(factor=factor)
        report = engine.validate_snapshot(snap, factor, import_batch_id="different-batch")
        assert not report.ok
        assert _v.CODE_SNAPSHOT_BATCH_MISMATCH in codes(report)

    def test_source_mismatch_error(self) -> None:
        factor = make_seai_factor()
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        snap = make_snapshot(factor=factor)
        report = engine.validate_snapshot(
            snap, factor,
            factor_source="DEFRA-DESNZ", factor_set="SEAI-2025",
            import_batch_id=factor.import_batch_id,
        )
        assert not report.ok
        assert _v.CODE_SNAPSHOT_SOURCE_MISMATCH in codes(report)

    def test_provenance_context_carries_gas_coverage(self) -> None:
        factor = make_seai_factor()
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        snap = make_snapshot(factor=factor)
        report = engine.validate_snapshot(snap, factor)
        issue = next(i for i in report.issues if i.code == _v.CODE_SNAPSHOT_PROVENANCE_MISSING)
        assert issue.context["gas_coverage"] == "CO2"


class TestA6Integrity:
    def test_valid_log_ok(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = make_log(snapshot_id="s", calculated_kg_co2e=Decimal("18.4"))
        report = engine._validate_log_integrity(log)
        assert report.ok

    def test_negative_quantity_error(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = setattr_log(make_log(), quantity=Decimal("-1"))
        report = engine._validate_log_integrity(log)
        assert not report.ok
        assert _v.CODE_QUANTITY_NEGATIVE in codes(report)

    def test_negative_co2e_error(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = setattr_log(make_log(), calculated_kg_co2e=Decimal("-1"))
        report = engine._validate_log_integrity(log)
        assert not report.ok
        assert _v.CODE_CO2E_NEGATIVE in codes(report)

    def test_snapshot_link_missing_warning(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = make_log(calculated_kg_co2e=Decimal("18.4"), snapshot_id=None)
        report = engine._validate_log_integrity(log)
        assert report.ok
        assert _v.CODE_SNAPSHOT_LINK_MISSING in codes(report)

    async def test_orphan_factor_error(self) -> None:
        factor = make_factor()
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = make_log(factor=factor, factor_id="missing-factor")
        report = await engine.validate_logs([log], 2025)
        assert not report.ok
        assert _v.CODE_FACTOR_ORPHAN in codes(report)


class TestA7Period:
    def test_year_mismatch_warning(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = make_log(date=date(2024, 6, 1))
        report = engine._validate_log_period(log, 2025, period=None, strict=False)
        assert report.ok
        assert _v.CODE_YEAR_MISMATCH in codes(report)

    def test_out_of_period_warning_when_not_strict(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = make_log(date=date(2025, 12, 1))
        period = DateRange(date(2025, 1, 1), date(2025, 6, 30))
        report = engine._validate_log_period(log, 2025, period=period, strict=False)
        assert report.ok
        assert _v.CODE_OUT_OF_PERIOD in codes(report)

    def test_out_of_period_error_when_strict(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        log = make_log(date=date(2025, 12, 1))
        period = DateRange(date(2025, 1, 1), date(2025, 6, 30))
        report = engine._validate_log_period(log, 2025, period=period, strict=True)
        assert not report.ok
        assert _v.CODE_OUT_OF_PERIOD in codes(report)


class TestA8Org:
    async def test_org_not_found_error(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(org=None), _FakeFactors())
        report = await engine.validate_org("missing", 2025)
        assert not report.ok
        assert _v.CODE_ORG_NOT_FOUND in codes(report)

    async def test_inactive_org_error(self) -> None:
        engine = _v.ValidationEngine(
            _FakeLogs(), _FakeOrgs(org=make_org(is_active=False)), _FakeFactors()
        )
        report = await engine.validate_org("org-1", 2025)
        assert not report.ok
        assert _v.CODE_ORG_INACTIVE in codes(report)

    async def test_metadata_missing_warning(self) -> None:
        engine = _v.ValidationEngine(
            _FakeLogs(), _FakeOrgs(org=make_org(), metadata=None), _FakeFactors()
        )
        report = await engine.validate_org("org-1", 2025, require_intensity_metadata=True)
        assert report.ok
        assert _v.CODE_METADATA_MISSING in codes(report)

    async def test_metadata_present_no_warning(self) -> None:
        engine = _v.ValidationEngine(
            _FakeLogs(),
            _FakeOrgs(org=make_org(), metadata=make_metadata(fte_count=10)),
            _FakeFactors(),
        )
        report = await engine.validate_org("org-1", 2025, require_intensity_metadata=True)
        assert report.ok
        assert _v.CODE_METADATA_MISSING not in codes(report)

    async def test_entity_not_in_org_error(self) -> None:
        factor = make_factor()
        engine = _v.ValidationEngine(
            _FakeLogs(),
            _FakeOrgs(
                org=make_org(),
                facilities=[make_facility("fac-1")],
                assets=[make_asset("asset-1")],
            ),
            _FakeFactors([factor]),
        )
        log = make_log(
            factor=factor, facility_id="fac-9", asset_id="asset-1",
            snapshot_id="s", calculated_kg_co2e=Decimal("1"),
        )
        report = await engine._validate_membership("org-1", [log])
        assert not report.ok
        assert _v.CODE_ENTITY_NOT_IN_ORG in codes(report)


class TestA9Verify:
    async def test_verify_valid_snapshots_ok(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        report = await engine.verify_snapshots(
            [make_snapshot(), make_snapshot(id="snap-2")]
        )
        assert report.ok

    async def test_verify_detects_tampered_snapshot(self) -> None:
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        good = make_snapshot()
        bad = dataclasses.replace(make_snapshot(id="snap-bad"), co2e_kg=Decimal("99"))
        report = await engine.verify_snapshots([good, bad])
        assert not report.ok
        assert _v.CODE_CALC_MISMATCH in codes(report)


class TestGasCoverage:
    def test_defra_is_co2e(self) -> None:
        assert _v.gas_coverage(make_factor()) == "CO2e"

    def test_seai_is_co2(self) -> None:
        assert _v.gas_coverage(make_seai_factor()) == "CO2"

    def test_co2_label_suffix_detected(self) -> None:
        factor = make_factor(activity_type=_SEAI_ELECTRICITY, factor_source="CUSTOM")
        assert _v.gas_coverage(factor) == "CO2"


class TestSeaiCo2:
    async def test_valid_seai_calculation_validates_clean(self) -> None:
        """A full SEAI CO2-only pipeline validates clean — no CH4/N2O needed."""
        factor = make_seai_factor()
        log = make_log(
            factor=factor, unit="kWh", scope="Scope 2", facility_id="fac-1",
            snapshot_id="snap-1", calculated_kg_co2e=Decimal("19.780338"),
        )
        period = DateRange(date(2025, 1, 1), date(2025, 12, 31))
        engine = _v.ValidationEngine(
            _FakeLogs([log]),
            _FakeOrgs(org=make_org(), facilities=[make_facility("fac-1")]),
            _FakeFactors([factor]),
        )
        request = ValidationRequest(organization_id="org-1", reporting_year=2025, period=period)
        report = await engine.validate(request)
        assert report.ok

        snap = make_snapshot(factor=factor, quantity="100", multiplier="0.197803384")
        snap_report = engine.validate_snapshot(
            snap, factor,
            factor_source="SEAI", factor_set="SEAI-2025",
            import_batch_id=factor.import_batch_id,
        )
        assert snap_report.ok

    async def test_seai_ie_match_is_valid(self) -> None:
        """A3: a matched SEAI/IE factor for an IE request is clean."""
        factor = make_seai_factor()
        engine = _v.ValidationEngine(_FakeLogs(), _FakeOrgs(), _FakeFactors())
        report = engine.validate_match(
            make_match_request(country="IE", unit="kWh", preferred_provider="seai"),
            make_match_result(factor=factor),
        )
        assert report.ok

    async def test_composite_validation_scope_filter(self) -> None:
        """validate() honours the request scope filter."""
        factor = make_factor()  # Scope 1
        excluded = make_log(factor=factor, scope="Scope 2")
        included = make_log(factor=factor, scope="Scope 1", snapshot_id="s")
        period = DateRange(date(2025, 1, 1), date(2025, 12, 31))
        engine = _v.ValidationEngine(
            _FakeLogs([included, excluded]),
            _FakeOrgs(org=make_org()),
            _FakeFactors([factor]),
        )
        request = ValidationRequest(
            organization_id="org-1", reporting_year=2025, period=period,
            scope_filter="Scope 1",
        )
        report = await engine.validate(request)
        # Scope 1 log has no issues; the Scope 2 log is filtered out.
        assert report.ok


class TestStrictAndSideEffects:
    async def test_strict_raises_validation_failed_error(self) -> None:
        factor = make_factor()
        bad_log = make_log(factor=factor, unit="litres", snapshot_id="s")
        period = DateRange(date(2025, 1, 1), date(2025, 12, 31))
        engine = _v.ValidationEngine(
            _FakeLogs([bad_log]),
            _FakeOrgs(org=make_org(), facilities=[make_facility("fac-1")]),
            _FakeFactors([factor]),
        )
        request = ValidationRequest(
            organization_id="org-1", reporting_year=2025, period=period, strict=True
        )
        with pytest.raises(ValidationFailedError):
            await engine.validate(request)

    async def test_non_strict_returns_report(self) -> None:
        factor = make_factor()
        bad_log = make_log(factor=factor, unit="litres", snapshot_id="s")
        period = DateRange(date(2025, 1, 1), date(2025, 12, 31))
        engine = _v.ValidationEngine(
            _FakeLogs([bad_log]),
            _FakeOrgs(org=make_org(), facilities=[make_facility("fac-1")]),
            _FakeFactors([factor]),
        )
        request = ValidationRequest(
            organization_id="org-1", reporting_year=2025, period=period, strict=False
        )
        report = await engine.validate(request)
        assert not report.ok
        assert _v.CODE_UNIT_MISMATCH in codes(report)

    async def test_publishes_validation_failed_event(self) -> None:
        factor = make_factor()
        bus = EventBus()
        received: list[DomainEvent] = []

        async def capture(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(None, capture)
        bad_log = make_log(factor=factor, unit="litres", snapshot_id="s")
        period = DateRange(date(2025, 1, 1), date(2025, 12, 31))
        engine = _v.ValidationEngine(
            _FakeLogs([bad_log]),
            _FakeOrgs(org=make_org(), facilities=[make_facility("fac-1")]),
            _FakeFactors([factor]),
            event_bus=bus,
        )
        request = ValidationRequest(
            organization_id="org-1", reporting_year=2025, period=period, strict=True
        )
        with pytest.raises(ValidationFailedError):
            await engine.validate(request)
        await bus.drain()
        failed = [e for e in received if isinstance(e, ValidationFailed)]
        assert len(failed) == 1
        assert failed[0].entity_id == "org-1"
        assert failed[0].entity_type == "organization"
        assert len(failed[0].errors) >= 1

    async def test_audits_validation(self) -> None:
        audit = _AuditSink()
        period = DateRange(date(2025, 1, 1), date(2025, 12, 31))
        engine = _v.ValidationEngine(
            _FakeLogs([]),
            _FakeOrgs(org=make_org(), facilities=[make_facility("fac-1")]),
            _FakeFactors(),
            audit_logger=audit,
        )
        request = ValidationRequest(organization_id="org-1", reporting_year=2025, period=period)
        report = await engine.validate(request)
        assert report.ok
        assert len(audit.entries) == 1
        entry = audit.entries[0]
        assert entry.action == "validation:completed"
        assert entry.entity_type == "organization"
        assert entry.entity_id == "org-1"
        assert entry.after["ok"] is True

    def test_constructor_requires_repos(self) -> None:
        with pytest.raises(ValueError, match="logs_repo"):
            _v.ValidationEngine(None, _FakeOrgs(), _FakeFactors())  # type: ignore[arg-type]









