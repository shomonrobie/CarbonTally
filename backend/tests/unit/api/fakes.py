"""In-memory fakes for the Phase 10 API contract suite.

These fakes satisfy the exact repository/protocol surfaces the API and engines
consume (``CalculationSink``, ``LogsSource``, ``OrgSource``, ``FactorLookup``,
``ReportsStore``, ``AuditSink``, ...) without touching the database. The
contract tests run entirely in memory — the development database is never
opened, so the DEFRA/SEAI baseline (7,029 / 20 / 7,049) is untouched.

Importing or seeding this module has zero database side effects.
"""
from __future__ import annotations

import csv
import io
import uuid
from datetime import date as _Date
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from auth import AuthUser
from domain.audit import AuditEntry, AuditQuery

#: Sentinel mirroring ``data.manual_extraction._UNSET`` — distinguishes
#: "leave untouched" from an explicit ``None`` (clear the column).
_UNSET = object()

from domain.calculation import (
    CalculationSnapshot,
    EmissionLog,
    EmissionsAggregate,
)
from domain.customer_factor import CustomerFactor
from domain.entity import ProcessingEntity
from domain.factor import EmissionFactor
from domain.issue import Issue
from domain.matching import FactorAlias
from domain.organization import Asset, Facility, Organization, OrganizationMember, OrganizationMetadata
from domain.partners import (
    ManualExtractionBatch,
    ManualExtractionItem,
    WORKFLOW_STAGE_STATUSES,
)
from domain.provider import ImportBatch
from domain.operations import QueueSettings, ReviewItem
from domain.staff import StaffProfile, StaffRole
from domain.billing import (
    BillingOrder,
    BillingPlan,
    CommercialConfig,
    CreditLedgerEntry,
    IdempotencyKey,
    PaymentRecord,
    StorageUsage,
    Subscription,
)


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

DEFRA_GAS_ACTIVITY = "Fuels > Gas fuels > Natural gas (kg CO2e) [kWh]"
SEAI_GAS_ACTIVITY = "Natural gas (kg CO2) [kWh]"


def seed_factor(
    *,
    factor_id: str,
    year: int = 2025,
    activity_type: str,
    multiplier: str,
    unit: str = "kWh",
    scope: str = "Scope 1",
    factor_source: str,
    factor_set: str,
    country: str,
    provider_key: str,
    import_batch_id: Optional[str] = None,
) -> EmissionFactor:
    return EmissionFactor(
        id=factor_id,
        reporting_year=year,
        activity_type=activity_type,
        co2e_multiplier=Decimal(multiplier),
        unit=unit,
        scope=scope,
        factor_source=factor_source,
        factor_set=factor_set,
        country=country,
        provider_key=provider_key,
        import_batch_id=import_batch_id,
        natural_key=(str(year), activity_type, country, unit, scope),
    )


def seed_defra_factor() -> EmissionFactor:
    return seed_factor(
        factor_id="factor-defra-gas",
        activity_type=DEFRA_GAS_ACTIVITY,
        multiplier="0.183",
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country="GB",
        provider_key="defra",
        import_batch_id="batch-defra-2025",
    )


def seed_seai_factor() -> EmissionFactor:
    """SEAI publishes CO2-only factors — ``gas_coverage`` must stay ``CO2``."""
    return seed_factor(
        factor_id="factor-seai-gas",
        activity_type=SEAI_GAS_ACTIVITY,
        multiplier="0.205",
        factor_source="SEAI",
        factor_set="SEAI-2025",
        country="IE",
        provider_key="seai",
        import_batch_id="batch-seai-2025",
    )


def seed_import_batch(
    *,
    batch_id: str,
    provider: str,
    year: int,
    status: str,
    is_active: bool,
    rows_total: int,
    rows_imported: int,
    created_days_ago: int = 1,
) -> ImportBatch:
    created = datetime(2025, 6, 10, tzinfo=timezone.utc)
    return ImportBatch(
        id=batch_id,
        provider_key=provider,
        provider_version=f"{year}.1",
        source_file=f"{provider}-{year}.xlsx",
        source_checksum=f"sha256-{batch_id}",
        reporting_year=year,
        status=status,
        rows_total=rows_total,
        rows_imported=rows_imported,
        rows_skipped=0,
        rows_duplicate=0,
        errors=(),
        is_active=is_active,
        created_at=created,
        created_by="system",
        rolled_back_from=None,
    )


def seed_org_a() -> tuple[Organization, OrganizationMetadata, list[Facility], list[Asset]]:
    org = Organization(id="org-a", name="Org A", country="GB", is_active=True, created_at=datetime(2025, 1, 1, tzinfo=timezone.utc))
    metadata = OrganizationMetadata(
        total_floor_area_sqm=1000.0,
        occupied_floor_area_sqm=800.0,
        fte_count=10,
        annual_revenue_gbp=1_000_000.0,
        sector="Manufacturing",
    )
    facilities = [Facility(id="fac-a1", organization_id="org-a", name="Site 1", address="1 Main St")]
    assets = [Asset(id="asset-a1", facility_id="fac-a1", organization_id="org-a", name="Boiler 1", asset_type="boiler")]
    return org, metadata, facilities, assets


def seed_org_b() -> tuple[Organization, OrganizationMetadata, list[Facility], list[Asset]]:
    org = Organization(id="org-b", name="Org B", country="IE", is_active=True, created_at=datetime(2025, 1, 1, tzinfo=timezone.utc))
    metadata = OrganizationMetadata(fte_count=5, sector="Services")
    return org, metadata, [], []


def seed_log(
    *,
    log_id: str,
    org_id: str,
    factor_id: str,
    quantity: str,
    unit: str,
    scope: str,
    day: _Date,
    calculated: str,
    snapshot_id: Optional[str] = None,
    facility_id: Optional[str] = None,
) -> EmissionLog:
    return EmissionLog(
        id=log_id,
        organization_id=org_id,
        factor_id=factor_id,
        quantity=Decimal(quantity),
        date=day,
        unit=unit,
        scope=scope,
        facility_id=facility_id,
        snapshot_id=snapshot_id,
        calculated_kg_co2e=Decimal(calculated),
        created_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
    )


def admin_user() -> AuthUser:
    return AuthUser(
        user_id="admin-1",
        email="admin@carbontally.test",
        role="admin",
        role_name="admin",
        is_staff=True,
        permissions={"can_manage_organizations": True},
    )


def member_user(org_id: str, user_id: str, email: str) -> AuthUser:
    return AuthUser(
        user_id=user_id,
        email=email,
        role="user",
        role_name="user",
        organization_id=org_id,
        is_org_member=True,
    )


def org_admin_user(org_id: str, user_id: str, email: str) -> AuthUser:
    """An organisation admin (``role_name='admin'`` short-circuits
    ``require_org_admin`` without a Supabase round-trip in unit tests)."""
    return AuthUser(
        user_id=user_id,
        email=email,
        role="org_admin",
        role_name="admin",
        organization_id=org_id,
        is_org_member=True,
    )


def org_owner_user(org_id: str, user_id: str, email: str) -> AuthUser:
    """An organisation owner (``role='org_owner'`` is recognised by
    ``require_org_admin`` — the schema's RLS treats ``owner`` as an org
    administrator)."""
    return AuthUser(
        user_id=user_id,
        email=email,
        role="org_owner",
        role_name="org_owner",
        organization_id=org_id,
        is_org_member=True,
    )


def consultant_user(user_id: str, email: str, role: str = "consultant") -> AuthUser:
    """A consultant user (not an org member — uses the consultant surface)."""
    return AuthUser(
        user_id=user_id,
        email=email,
        role=role,
        role_name=role,
        is_org_member=False,
        is_active=True,
    )


# ---------------------------------------------------------------------------
# In-memory repository fakes
# ---------------------------------------------------------------------------


class MemoryFactors:
    """``EmissionFactorsRepository`` surface used by the API + engines."""

    def __init__(self, factors: Optional[list[EmissionFactor]] = None) -> None:
        self._factors: dict[str, EmissionFactor] = {f.id: f for f in (factors or [])}

    async def get(self, id: str) -> Optional[EmissionFactor]:
        return self._factors.get(id)

    async def count_by_provider(self, provider: str) -> int:
        return sum(1 for f in self._factors.values() if f.provider_key == provider)

    async def load_all_for_index(self) -> list[EmissionFactor]:
        return list(self._factors.values())

    def add(self, factor: EmissionFactor) -> None:
        self._factors[factor.id] = factor


class MemoryLogs:
    """Satisfies ``CalculationSink`` + ``LogsSource`` (find_by_org + aggregate)."""

    def __init__(self, logs: Optional[list[EmissionLog]] = None) -> None:
        self._logs: list[EmissionLog] = list(logs or [])
        self._snapshots: dict[str, CalculationSnapshot] = {}

    async def save_snapshot(
        self,
        snapshot: CalculationSnapshot,
        *,
        activity: str,
        activity_type: str,
        factor_source: Optional[str] = None,
        factor_set: Optional[str] = None,
        import_batch_id: Optional[str] = None,
        calculated_by: Optional[str] = None,
        factor_kind: Optional[str] = None,
        customer_factor_id: Optional[str] = None,
    ) -> CalculationSnapshot:
        self._snapshots[snapshot.id] = snapshot
        return snapshot

    async def create(
        self,
        org_id: str,
        factor_id: Optional[str],
        quantity: Decimal,
        unit: str,
        scope: Optional[str],
        date: _Date,
        asset_id: Optional[str],
        facility_id: Optional[str],
        snapshot_id: str,
    ) -> EmissionLog:
        log = EmissionLog(
            id=str(uuid.uuid4()),
            organization_id=org_id,
            factor_id=factor_id,
            quantity=quantity,
            date=date,
            unit=unit,
            scope=scope,
            asset_id=asset_id,
            facility_id=facility_id,
            snapshot_id=snapshot_id,
            calculated_kg_co2e=Decimal("0"),
        )
        self._logs.append(log)
        return log

    async def save(self, entity: EmissionLog) -> EmissionLog:
        for i, log in enumerate(self._logs):
            if log.id == entity.id:
                self._logs[i] = entity
                return entity
        self._logs.append(entity)
        return entity

    async def find_by_org(self, org_id: str, period) -> list[EmissionLog]:
        return [l for l in self._logs if l.organization_id == org_id and period.contains(l.date)]

    async def aggregate(self, org_id: str, period, group_by: str) -> EmissionsAggregate:
        logs = [l for l in self._logs if l.organization_id == org_id and period.contains(l.date)]
        total = sum((l.calculated_kg_co2e for l in logs), Decimal("0"))
        by_scope: dict[str, Decimal] = {}
        by_group: dict[str, Decimal] = {}
        for log in logs:
            scope_label = log.scope or "Unspecified"
            by_scope[scope_label] = by_scope.get(scope_label, Decimal("0")) + log.calculated_kg_co2e
            key = _group_key(group_by, log)
            by_group[key] = by_group.get(key, Decimal("0")) + log.calculated_kg_co2e
        return EmissionsAggregate(
            organization_id=org_id,
            period=period,
            group_by=group_by,
            total_co2e_kg=total,
            total_rows=len(logs),
            by_scope=by_scope,
            by_group=by_group,
        )


def _group_key(group_by: str, log: EmissionLog) -> str:
    if group_by == "year":
        return f"year:{log.date.year}"
    if group_by == "month":
        return f"month:{log.date.year:04d}-{log.date.month:02d}"
    if group_by == "facility":
        return f"facility:{log.facility_id or ''}"
    if group_by == "scope":
        return f"scope:{log.scope or 'Unspecified'}"
    if group_by == "asset":
        return f"asset:{log.asset_id or ''}"
    return f"{group_by}:{log.id}"


class MemoryOrganizations:
    """Satisfies ``OrgSource`` + the V3 customer-admin surface (Phase 6)."""

    def __init__(
        self,
        orgs: Optional[list[Organization]] = None,
        metadata: Optional[dict[str, OrganizationMetadata]] = None,
        facilities: Optional[dict[str, list[Facility]]] = None,
        assets: Optional[dict[str, list[Asset]]] = None,
    ) -> None:
        self._orgs = {o.id: o for o in (orgs or [])}
        self._metadata = dict(metadata or {})
        self._facilities = dict(facilities or {})
        self._assets = dict(assets or {})
        self._billing_modes: dict[str, Optional[str]] = {}
        self._profiles: dict[str, dict[str, Any]] = {}
        for o in (orgs or []):
            self._profiles[o.id] = {
                "id": o.id,
                "name": o.name,
                "country": o.country,
                "is_active": o.is_active,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "updated_at": None,
                "company_number": None,
                "industry": None,
                "sector": None,
                "company_size": None,
                "vat_number": None,
                "registration_number": None,
                "registered_address": None,
                "timezone": None,
                "currency": "GBP",
                "financial_year_end": None,
                "reporting_standard": None,
                "secr_enabled": False,
                "esrs_enabled": False,
                "issb_enabled": False,
                "default_factor_year": None,
                "preferred_units": None,
                "website": None,
                "primary_contact_email": None,
                "primary_contact_name": None,
                "billing_contact_email": None,
                "billing_contact_name": None,
                "subscription_status": None,
                "subscription_tier": None,
                "billing_address": None,
                "tax_rate": None,
                "metadata": {},
                "address_line1": None,
                "address_line2": None,
                "city": None,
                "county": None,
                "postcode": None,
                "eircode": None,
                "language": None,
                "locale": None,
                "vat_region": None,
                "vat_registered": False,
                "tax_region": None,
                "registration_region": None,
                "sic_code": None,
                "naics_code": None,
                "nace_code": None,
                "business_structure": None,
                "is_public": False,
                "is_listed": False,
                "reporting_frequency": None,
                "accounting_standard": None,
                "sustainability_standard": None,
                "carbon_tax_region": None,
                "data_protection_officer": None,
                "privacy_policy_url": None,
                "terms_url": None,
            }
        self._metadata_full: dict[str, dict[str, Any]] = {}
        for org_id, meta in (metadata or {}).items():
            self._metadata_full[org_id] = {
                "organization_id": org_id,
                "total_employees": None,
                "full_time_employees": None,
                "part_time_employees": None,
                "contract_employees": None,
                "average_employees": meta.fte_count,
                "annual_revenue": meta.annual_revenue_gbp,
                "ebitda": None,
                "total_assets": None,
                "total_facilities": None,
                "total_floor_area_sqft": None,
                "occupied_floor_area_sqft": None,
                "renewable_energy_percentage": None,
                "carbon_offset_percentage": None,
                "energy_intensity": None,
                "reporting_standard": None,
                "fiscal_year_start": None,
                "fiscal_year_end": None,
                "primary_contact_name": None,
                "primary_contact_email": None,
                "primary_contact_phone": None,
                "sustainability_officer_name": None,
                "sustainability_officer_email": None,
                "industry_sector": meta.sector,
                "naics_code": None,
                "sic_code": None,
                "custom_metrics": {},
                "total_floor_area_sqm": meta.total_floor_area_sqm,
                "occupied_floor_area_sqm": meta.occupied_floor_area_sqm,
                "updated_at": None,
                "updated_by": None,
            }
        # Member records (mirror the production email-joined shape).
        self._members: dict[str, dict[str, Any]] = {}

    async def get(self, org_id: str) -> Optional[Organization]:
        return self._orgs.get(org_id)

    async def get_metadata(self, org_id: str) -> Optional[OrganizationMetadata]:
        return self._metadata.get(org_id)

    async def get_facilities(self, org_id: str) -> list[Facility]:
        return self._facilities.get(org_id, [])

    async def get_assets(self, org_id: str) -> list[Asset]:
        return self._assets.get(org_id, [])

    # -- V3 customer-admin surface (Phase 6) -------------------------------
    async def get_profile(self, org_id: str) -> Optional[dict[str, Any]]:
        return self._profiles.get(org_id)

    # -- D27 / D19 adoption surface ---------------------------------------
    async def get_full(self, org_id: str) -> Optional[dict[str, Any]]:
        profile = self._profiles.get(org_id)
        if profile is None:
            return None
        return {**profile, "customer_type": self._profiles.get(org_id, {}).get("customer_type")}

    async def set_customer_type(self, org_id: str, customer_type: str) -> bool:
        profile = self._profiles.get(org_id)
        if profile is None:
            return False
        profile["customer_type"] = customer_type
        return True

    async def get_metadata_full(self, org_id: str) -> Optional[dict[str, Any]]:
        return self._metadata_full.get(org_id)

    async def update_profile(
        self, org_id: str, fields: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        profile = self._profiles.get(org_id)
        if profile is None:
            return None
        profile.update(fields)
        return dict(profile)

    async def update_metadata_full(
        self, org_id: str, fields: dict[str, Any], updated_by: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        if org_id not in self._metadata_full:
            self._metadata_full[org_id] = {"organization_id": org_id}
        self._metadata_full[org_id].update(fields)
        self._metadata_full[org_id]["updated_by"] = updated_by
        return dict(self._metadata_full[org_id])

    def add_member_record(self, member: dict[str, Any]) -> None:
        self._members[member["id"]] = member

    async def list_members_with_email(self, org_id: str) -> list[dict[str, Any]]:
        return [dict(m) for m in self._members.values() if m["organization_id"] == org_id]

    async def get_member(self, member_id: str) -> Optional[dict[str, Any]]:
        member = self._members.get(member_id)
        return dict(member) if member is not None else None

    # -- D35 self-service onboarding surface --------------------------------
    async def get_active_memberships_for_user(self, user_id: str) -> list[OrganizationMember]:
        """Every ACTIVE organisation membership for ``user_id``."""
        return [
            OrganizationMember(
                id=str(m["id"]),
                organization_id=str(m["organization_id"]),
                user_id=str(m["user_id"]),
                role=str(m["role"]),
                is_active=bool(m.get("is_active", True)),
            )
            for m in self._members.values()
            if m["user_id"] == user_id and m.get("is_active", True)
        ]

    async def create_with_owner(
        self,
        *,
        org_id: str,
        name: str,
        country: Optional[str],
        owner_user_id: str,
        primary_contact_email: Optional[str] = None,
        company_number: Optional[str] = None,
        billing_mode: Optional[str] = None,
    ) -> dict[str, Any]:
        """Atomically create an organisation + its initial OWNER membership."""
        org = Organization(
            id=org_id,
            name=name,
            country=country or "",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        self._orgs[org_id] = org
        self._profiles[org_id] = {
            "id": org_id,
            "name": name,
            "country": country,
            "is_active": True,
            "created_at": org.created_at.isoformat(),
            "updated_at": None,
            "company_number": company_number,
            "primary_contact_email": primary_contact_email,
            "customer_type": None,
            "billing_mode": billing_mode,
        }
        self._billing_modes[org_id] = billing_mode
        member = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "user_id": owner_user_id,
            "role": "owner",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._members[member["id"]] = member
        return {
            "organization": org,
            "member": OrganizationMember(
                id=member["id"],
                organization_id=org_id,
                user_id=owner_user_id,
                role="owner",
                is_active=True,
            ),
        }

    async def get_billing_mode(self, org_id: str) -> Optional[str]:
        """The per-customer commercial mode (CREDIT | STANDARD), D37-0."""
        return self._billing_modes.get(org_id)

    async def list_all(self) -> list[Organization]:
        """Every organisation, by name (operations/commercial surface)."""
        return sorted(self._orgs.values(), key=lambda o: (o.name or "").lower())


class MemoryImports:
    """``ImportsRepository`` read surface used by the admin endpoints."""

    def __init__(self, batches: Optional[list[ImportBatch]] = None) -> None:
        self._batches: list[ImportBatch] = list(batches or [])

    async def get_history(self, provider: str) -> list[ImportBatch]:
        rows = [b for b in self._batches if b.provider_key == provider]
        return sorted(rows, key=lambda b: b.created_at, reverse=True)

    async def get_active(self, provider: str, year: int) -> Optional[ImportBatch]:
        for b in self._batches:
            if b.provider_key == provider and b.reporting_year == year and b.is_active:
                return b
        return None

    async def get(self, id: str) -> Optional[ImportBatch]:
        return next((b for b in self._batches if b.id == id), None)

    def add(self, batch: ImportBatch) -> None:
        self._batches.append(batch)


class MemoryReports:
    """Satisfies ``ReportsStore`` + the V3 reports dashboard surface."""

    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _row_to_full(self, row: dict[str, Any]) -> dict[str, Any]:
        """Mirror the production ``_row_to_report_full`` shape."""
        generated = row.get("generated_content") or {}
        inner = generated.get("content") if isinstance(generated, dict) else None
        page_count = (
            int(generated.get("page_count") or 0) if isinstance(generated, dict) else 0
        )
        shaped = dict(row)
        shaped["generated_content"] = inner
        shaped["page_count"] = page_count
        return shaped

    def _as_generated(self, row: dict[str, Any]):
        from domain.report import GeneratedReport

        generated_at = row.get("completed_at") or row.get("created_at")
        return GeneratedReport(
            id=row["id"],
            organization_id=row["organization_id"],
            report_type=row["report_type"],
            reporting_year=row["reporting_year"],
            storage_url=str(row.get("final_report_url") or ""),
            file_size_bytes=int(row.get("final_report_size_bytes") or 0),
            generated_at=generated_at,
            page_count=int(row.get("page_count") or 0),
        )

    async def create_generation_request(
        self,
        org_id: str,
        report_type: str,
        year: int,
        template_id: Optional[str],
        created_by: Optional[str] = None,
        report_name: Optional[str] = None,
    ) -> Any:
        report_id = str(uuid.uuid4())
        row = {
            "id": report_id,
            "organization_id": org_id,
            "user_id": created_by,
            "template_id": template_id,
            "report_type": report_type,
            "reporting_year": year,
            "report_name": report_name,
            "status": "pending",
            "progress_percentage": None,
            "current_step": None,
            "generated_content": None,
            "page_count": 0,
            "final_report_url": "",
            "final_report_file_name": None,
            "final_report_size_bytes": 0,
            "created_at": self._now(),
            "created_by": created_by,
            "started_at": None,
            "completed_at": None,
            "updated_at": self._now(),
            "updated_by": None,
            "error_log": None,
            "metadata": {},
        }
        self._rows[report_id] = row
        return self._as_generated(row)

    async def complete_generation(
        self,
        report_id: str,
        storage_url: str,
        file_size: int,
        page_count: int,
        content: Optional[dict[str, Any]] = None,
    ) -> Any:
        row = self._rows.get(report_id)
        if row is None:
            raise RuntimeError(f"report {report_id!r} does not exist")
        generated: dict[str, Any] = {"page_count": page_count}
        if content is not None:
            generated["content"] = content
        row["status"] = "completed"
        row["final_report_url"] = storage_url
        row["final_report_size_bytes"] = file_size
        row["generated_content"] = generated
        row["completed_at"] = self._now()
        row["updated_at"] = self._now()
        return self._as_generated(row)

    async def mark_generating(
        self, report_id: str, user_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        row = self._rows.get(report_id)
        if row is None:
            return None
        row["status"] = "generating"
        row["started_at"] = self._now()
        row["updated_by"] = user_id
        return self._row_to_full(row)

    async def mark_failed(
        self, report_id: str, error_log: str, user_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        row = self._rows.get(report_id)
        if row is None:
            return None
        row["status"] = "failed"
        row["error_log"] = error_log
        row["updated_by"] = user_id
        row["updated_at"] = self._now()
        return self._row_to_full(row)

    async def get(self, id: str) -> Optional[Any]:
        row = self._rows.get(id)
        return self._as_generated(row) if row is not None else None

    async def get_full(self, id: str) -> Optional[dict[str, Any]]:
        row = self._rows.get(id)
        return self._row_to_full(row) if row is not None else None

    async def list_full(
        self,
        org_id: str,
        *,
        status: Optional[str] = None,
        report_type: Optional[str] = None,
        reporting_year: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        rows = [self._row_to_full(r) for r in self._rows.values() if r["organization_id"] == org_id]
        if status is not None:
            rows = [r for r in rows if r["status"] == status]
        if report_type is not None:
            rows = [r for r in rows if r["report_type"] == report_type]
        if reporting_year is not None:
            rows = [r for r in rows if r["reporting_year"] == reporting_year]
        rows.sort(key=lambda r: r["created_at"], reverse=True)
        return rows[offset : offset + limit]

    async def count_by_status(self, org_id: str) -> dict[str, int]:
        counts = {s: 0 for s in ("pending", "generating", "completed", "failed")}
        for r in self._rows.values():
            if r["organization_id"] == org_id:
                counts[r["status"]] = counts.get(r["status"], 0) + 1
        return counts

    def seed_report(
        self,
        *,
        report_id: str,
        org_id: str,
        report_type: str = "annual",
        year: int = 2025,
        status: str = "completed",
        created_by: Optional[str] = "u-1",
        report_name: Optional[str] = None,
        content: Optional[dict[str, Any]] = None,
        error_log: Optional[str] = None,
    ) -> dict[str, Any]:
        row = {
            "id": report_id,
            "organization_id": org_id,
            "user_id": created_by,
            "template_id": None,
            "report_type": report_type,
            "reporting_year": year,
            "report_name": report_name or f"{report_type} {year}",
            "status": status,
            "progress_percentage": 100 if status == "completed" else None,
            "current_step": None,
            "generated_content": content,
            "page_count": 12 if content else 0,
            "final_report_url": "" if status != "completed" else f"storage/reports/{report_id}.json",
            "final_report_file_name": None,
            "final_report_size_bytes": 2048 if content else 0,
            "created_at": self._now(),
            "created_by": created_by,
            "started_at": None,
            "completed_at": self._now() if status == "completed" else None,
            "updated_at": self._now(),
            "updated_by": None,
            "error_log": error_log,
            "metadata": {},
        }
        self._rows[report_id] = row
        return dict(row)

    def stored_content(self, report_id: str) -> Optional[dict[str, Any]]:
        row = self._rows.get(report_id)
        if row is None:
            return None
        content = row.get("generated_content")
        return content.get("content") if isinstance(content, dict) else None


class MemoryReportVersions:
    """In-memory ``ReportVersionsRepository`` surface (V3 report versioning)."""

    def __init__(self) -> None:
        self._versions: list[dict[str, Any]] = []

    async def next_version_number(self, report_id: str) -> int:
        nums = [v["version_number"] for v in self._versions if v["report_id"] == report_id]
        return (max(nums) if nums else 0) + 1

    async def create(
        self,
        report_id: str,
        *,
        version_number: int,
        content: Optional[dict[str, Any]] = None,
        file_url: str = "",
        file_name: Optional[str] = None,
        created_by: Optional[str] = None,
        notes: Optional[str] = None,
        change_summary: Optional[str] = None,
        is_current: bool = True,
    ) -> dict[str, Any]:
        version = {
            "id": str(uuid.uuid4()),
            "report_id": report_id,
            "version_number": version_number,
            "content": content or {},
            "file_url": file_url,
            "file_name": file_name,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "notes": notes,
            "change_summary": change_summary,
            "is_current": is_current,
        }
        self._versions.append(version)
        return dict(version)

    async def list_for_report(self, report_id: str) -> list[dict[str, Any]]:
        rows = [v for v in self._versions if v["report_id"] == report_id]
        rows.sort(key=lambda v: v["version_number"], reverse=True)
        return [dict(v) for v in rows]

    async def get_current(self, report_id: str) -> Optional[dict[str, Any]]:
        rows = [v for v in self._versions if v["report_id"] == report_id and v["is_current"]]
        return dict(rows[0]) if rows else None

    async def get(self, id: str) -> Optional[dict[str, Any]]:
        return next((dict(v) for v in self._versions if v["id"] == id), None)

    async def save(self, entity: dict) -> dict:
        return entity

    async def delete(self, id: str) -> None:
        self._versions = [v for v in self._versions if v["id"] != id]


class MemorySuppliers:
    """In-memory ``SuppliersRepository`` surface (V3 suppliers).

    Mirrors the real repository contract (``data/suppliers.py``): records are
    returned as :class:`domain.partners.Supplier` objects, never dicts.
    """

    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}

    def seed(self, supplier: dict[str, Any]) -> None:
        self._rows[supplier["id"]] = supplier

    @staticmethod
    def _to_supplier(row: dict[str, Any]) -> "Supplier":
        from domain.partners import Supplier

        return Supplier(
            id=row["id"],
            organization_id=row["organization_id"],
            name=row["name"],
            type=row.get("type"),
            supplier_category_id=row.get("supplier_category_id"),
            contact_name=row.get("contact_name"),
            contact_email=row.get("contact_email"),
            contact_phone=row.get("contact_phone"),
            country=row.get("country"),
            vat_number=row.get("vat_number"),
            website=row.get("website"),
            supplier_type=row.get("supplier_type"),
            annual_emissions=row.get("annual_emissions"),
            supplier_rating=row.get("supplier_rating"),
            is_certified=bool(row.get("is_certified", False)),
            is_active=bool(row.get("is_active", True)),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            metadata=row.get("metadata") or {},
        )

    async def search_for_org(
        self,
        org_id: str,
        *,
        search: Optional[str] = None,
        category_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list["Supplier"]:
        rows = [dict(r) for r in self._rows.values() if r["organization_id"] == org_id]
        if status == "active":
            rows = [r for r in rows if r.get("is_active", True)]
        elif status == "inactive":
            rows = [r for r in rows if not r.get("is_active", True)]
        else:
            rows = [r for r in rows if r.get("is_active", True)]
        if category_id is not None:
            rows = [r for r in rows if r.get("supplier_category_id") == category_id]
        if search:
            needle = search.lower()
            rows = [
                r for r in rows
                if needle in str(r.get("name") or "").lower()
                or needle in str(r.get("contact_email") or "").lower()
                or needle in str(r.get("contact_name") or "").lower()
            ]
        rows.sort(key=lambda r: str(r.get("name") or ""))
        return [self._to_supplier(r) for r in rows[offset : offset + limit]]

    async def list_for_org(self, org_id: str) -> list["Supplier"]:
        return await self.search_for_org(org_id)

    async def get(self, supplier_id: str) -> Optional["Supplier"]:
        row = self._rows.get(supplier_id)
        return self._to_supplier(row) if row is not None else None

    async def create(
        self,
        org_id: str,
        name: str,
        type_: Optional[str],
        supplier_type: Optional[str],
        contact_name: Optional[str],
        contact_email: Optional[str],
        contact_phone: Optional[str],
        country: Optional[str],
        vat_number: Optional[str],
        metadata: Optional[dict],
        created_by: Optional[str],
    ) -> "Supplier":
        row = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "name": name,
            "type": type_,
            "supplier_category_id": None,
            "contact_name": contact_name,
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "country": country,
            "vat_number": vat_number,
            "website": None,
            "supplier_type": supplier_type,
            "annual_emissions": None,
            "supplier_rating": None,
            "is_certified": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        self._rows[row["id"]] = row
        return self._to_supplier(row)

    async def update(
        self,
        supplier_id: str,
        name: Optional[str],
        contact_email: Optional[str],
        is_active: Optional[bool],
    ) -> Optional["Supplier"]:
        row = self._rows.get(supplier_id)
        if row is None:
            return None
        if name is not None:
            row["name"] = name
        if contact_email is not None:
            row["contact_email"] = contact_email
        if is_active is not None:
            row["is_active"] = is_active
        return self._to_supplier(row)

    async def remove(self, supplier_id: str) -> None:
        row = self._rows.get(supplier_id)
        if row is not None:
            row["is_active"] = False

    async def save(self, entity):
        return entity

    async def delete(self, id: str) -> None:
        return None


class MemoryInvitations:
    """In-memory ``InvitationsRepository`` surface (V3 invitations)."""

    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}

    async def create(
        self,
        org_id: str,
        email: str,
        *,
        token: str,
        role_id: Optional[str] = None,
        invited_by: Optional[str] = None,
        status: str = "pending",
        expires_at: Any = None,
    ) -> dict[str, Any]:
        row = {
            "id": str(uuid.uuid4()),
            "email": email,
            "role_id": role_id,
            "organization_id": org_id,
            "invited_by": invited_by,
            "token": token,
            "status": status,
            "expires_at": (
                expires_at.isoformat() if hasattr(expires_at, "isoformat") else expires_at
            ),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._rows[row["id"]] = row
        return dict(row)

    async def get(self, invitation_id: str) -> Optional[dict[str, Any]]:
        row = self._rows.get(invitation_id)
        return dict(row) if row is not None else None

    async def list_for_org(self, org_id: str) -> list[dict[str, Any]]:
        rows = [dict(r) for r in self._rows.values() if r["organization_id"] == org_id]
        rows.sort(key=lambda r: r["created_at"], reverse=True)
        return rows

    async def revoke(self, invitation_id: str) -> Optional[dict[str, Any]]:
        row = self._rows.get(invitation_id)
        if row is None:
            return None
        row["status"] = "revoked"
        return dict(row)

    async def save(self, entity):
        return entity

    async def delete(self, id: str) -> None:
        self._rows.pop(id, None)


class MemoryRoles:
    """In-memory ``RolesRepository`` surface (V3 roles reference)."""

    def __init__(self, roles: Optional[list[dict[str, Any]]] = None) -> None:
        self._roles = {r["name"]: r for r in (roles or [])}

    def seed(self, role: dict[str, Any]) -> None:
        """Register a role row (id/name/permissions) for permission resolution."""
        self._roles[role["name"]] = dict(role)

    async def get_by_name(self, name: str) -> Optional[dict[str, Any]]:
        return dict(self._roles[name]) if name in self._roles else None

    async def list(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self._roles.values()]

    async def get(self, id: str) -> Optional[dict[str, Any]]:
        return next((dict(r) for r in self._roles.values() if r.get("id") == id), None)

    async def save(self, entity):
        return entity

    async def delete(self, id: str) -> None:
        return None


class MemoryTenant:
    """In-memory ``TenantRepository`` surface (member/facility/asset writes)."""

    def __init__(self) -> None:
        self._members: dict[str, dict[str, Any]] = {}
        self._facilities: dict[str, dict[str, Any]] = {}
        self._assets: dict[str, dict[str, Any]] = {}

    def seed_member(self, member: dict[str, Any]) -> None:
        self._members[member["id"]] = member

    def seed_facility(self, facility: dict[str, Any]) -> None:
        self._facilities[facility["id"]] = facility

    def seed_asset(self, asset: dict[str, Any]) -> None:
        self._assets[asset["id"]] = asset

    # -- members -----------------------------------------------------------
    async def get_member_by_user(self, org_id: str, user_id: str):
        for member in self._members.values():
            if member["organization_id"] == org_id and member["user_id"] == user_id:
                return member
        return None

    async def add_member(self, org_id: str, user_id: str, role: str) -> dict[str, Any]:
        member = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "user_id": user_id,
            "role": role,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._members[member["id"]] = member
        return dict(member)

    async def update_member(
        self, member_id: str, role: Optional[str], is_active: Optional[bool]
    ) -> Optional[dict[str, Any]]:
        member = self._members.get(member_id)
        if member is None:
            return None
        if role is not None:
            member["role"] = role
        if is_active is not None:
            member["is_active"] = is_active
        return dict(member)

    async def remove_member(self, member_id: str) -> None:
        member = self._members.get(member_id)
        if member is not None:
            member["is_active"] = False

    # -- facilities --------------------------------------------------------
    async def get_facility(self, facility_id: str):
        from domain.operations import FacilityDetail

        facility = self._facilities.get(facility_id)
        if facility is None:
            return None
        return FacilityDetail(
            id=facility["id"],
            organization_id=facility["organization_id"],
            name=facility["name"],
            postcode=facility.get("postcode"),
            country=facility.get("country") or "GB",
            type=facility.get("type"),
            is_active=facility.get("is_active", True),
            created_at=facility.get("created_at"),
            updated_at=facility.get("updated_at"),
            metadata=facility.get("metadata") or {},
        )

    async def add_facility(
        self,
        org_id: str,
        name: str,
        postcode: Optional[str],
        country: str,
        type_: Optional[str],
        metadata: dict,
    ) -> dict[str, Any]:
        facility = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "name": name,
            "postcode": postcode,
            "country": country,
            "type": type_,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata,
        }
        self._facilities[facility["id"]] = facility
        return dict(facility)

    async def update_facility(
        self, facility_id: str, name: Optional[str], is_active: Optional[bool]
    ) -> Optional[dict[str, Any]]:
        facility = self._facilities.get(facility_id)
        if facility is None:
            return None
        if name is not None:
            facility["name"] = name
        if is_active is not None:
            facility["is_active"] = is_active
        return dict(facility)

    async def remove_facility(self, facility_id: str) -> None:
        facility = self._facilities.get(facility_id)
        if facility is not None:
            facility["is_active"] = False

    # -- assets ------------------------------------------------------------
    async def get_asset(self, asset_id: str):
        from domain.operations import AssetDetail

        asset = self._assets.get(asset_id)
        if asset is None:
            return None
        return AssetDetail(
            id=asset["id"],
            organization_id=asset["organization_id"],
            facility_id=asset.get("facility_id"),
            name=asset["name"],
            type=asset.get("type"),
            description=asset.get("description"),
            serial_number=asset.get("serial_number"),
            is_active=asset.get("is_active", True),
            created_at=asset.get("created_at"),
            metadata=asset.get("metadata") or {},
        )

    async def add_asset(
        self,
        org_id: str,
        facility_id: Optional[str],
        name: str,
        type_: Optional[str],
        metadata: dict,
    ) -> dict[str, Any]:
        asset = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "facility_id": facility_id,
            "name": name,
            "type": type_,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata,
        }
        self._assets[asset["id"]] = asset
        return dict(asset)

    async def update_asset(
        self, asset_id: str, name: Optional[str], is_active: Optional[bool]
    ) -> Optional[dict[str, Any]]:
        asset = self._assets.get(asset_id)
        if asset is None:
            return None
        if name is not None:
            asset["name"] = name
        if is_active is not None:
            asset["is_active"] = is_active
        return dict(asset)

    async def remove_asset(self, asset_id: str) -> None:
        asset = self._assets.get(asset_id)
        if asset is not None:
            asset["is_active"] = False

    async def get(self, id: str):
        return None

    async def save(self, entity):
        return entity

    async def delete(self, id: str) -> None:
        return None


class MemoryConsultants:
    """In-memory ``ConsultantsRepository`` surface (V3 consultants)."""

    def __init__(self) -> None:
        from domain.partners import (
            ConsultantClient,
            ConsultantFirmMember,
            ConsultantProfile,
            ConsultantTask,
        )

        self._profile_type = ConsultantProfile
        self._member_type = ConsultantFirmMember
        self._client_type = ConsultantClient
        self._task_type = ConsultantTask
        self._profiles: dict[str, object] = {}
        self._members: list[object] = []
        self._clients: list[object] = []
        self._tasks: list[object] = []
        self._brandings: dict[str, object] = {}

    def seed_profile(self, profile_id, user_id, company_name="Acme Consultants"):
        profile = self._profile_type(
            id=profile_id, user_id=user_id, company_name=company_name, is_active=True
        )
        self._profiles[profile_id] = profile
        return profile

    def seed_firm_member(
        self,
        firm_id,
        user_id,
        role="consultant",
        *,
        can_manage_clients=False,
        can_upload_documents=False,
        can_generate_reports=False,
        can_manage_team=False,
        client_access=None,
        is_active=True,
    ):
        member = self._member_type(
            id=f"fm-{user_id}",
            firm_id=firm_id,
            user_id=user_id,
            role=role,
            is_active=is_active,
            can_manage_clients=can_manage_clients,
            can_upload_documents=can_upload_documents,
            can_generate_reports=can_generate_reports,
            can_manage_team=can_manage_team,
            client_access=list(client_access or []),
        )
        self._members.append(member)
        return member

    def seed_client(self, client_id, consultant_id, organization_id, client_name, status="active"):
        client = self._client_type(
            id=client_id,
            consultant_id=consultant_id,
            organization_id=organization_id,
            client_name=client_name,
            status=status,
        )
        self._clients.append(client)
        return client

    # -- profiles -----------------------------------------------------------
    async def get_profile_by_user(self, user_id: str):
        return next((p for p in self._profiles.values() if p.user_id == user_id), None)

    async def create_profile(self, user_id: str, company_name: str):
        profile = self._profile_type(
            id=f"firm-{user_id}", user_id=user_id, company_name=company_name, is_active=True
        )
        self._profiles[profile.id] = profile
        return profile

    # -- firm members -------------------------------------------------------
    async def list_firm_members(self, firm_id: str):
        return [m for m in self._members if m.firm_id == firm_id]

    async def get_firm_member_by_user(self, firm_id: str, user_id: str):
        return next(
            (m for m in self._members if m.firm_id == firm_id and m.user_id == user_id),
            None,
        )

    async def add_firm_member(self, firm_id: str, user_id: str, role: str):
        member = self._member_type(
            id=f"fm-{user_id}", firm_id=firm_id, user_id=user_id, role=role, is_active=True
        )
        self._members.append(member)
        return member

    # -- clients ------------------------------------------------------------
    async def list_clients(self, consultant_id: str):
        return [c for c in self._clients if c.consultant_id == consultant_id]

    async def add_client(
        self,
        consultant_id,
        organization_id,
        client_name,
        client_industry=None,
        client_contact_email=None,
        client_contact_name=None,
    ):
        client = self._client_type(
            id=f"client-{organization_id}",
            consultant_id=consultant_id,
            organization_id=organization_id,
            client_name=client_name,
            client_industry=client_industry,
            client_contact_email=client_contact_email,
            client_contact_name=client_contact_name,
            status="active",
        )
        self._clients.append(client)
        return client

    async def get_client(self, client_id: str):
        return next((c for c in self._clients if c.id == client_id), None)

    async def get_client_by_org(self, consultant_id: str, organization_id: str):
        return next(
            (
                c for c in self._clients
                if c.consultant_id == consultant_id and c.organization_id == organization_id
            ),
            None,
        )

    async def update_client_status(self, client_id: str, status: str):
        from dataclasses import replace

        for i, client in enumerate(self._clients):
            if client.id == client_id:
                updated = replace(client, status=status)
                self._clients[i] = updated
                return updated
        return None

    async def transition_client_lifecycle(self, client_id, target_status, *, actor_id=None):
        from dataclasses import replace
        from datetime import datetime, timezone

        for i, client in enumerate(self._clients):
            if client.id == client_id:
                updated = replace(
                    client,
                    status=target_status,
                    ended_at=datetime.now(timezone.utc) if target_status == "ended" else client.ended_at,
                    ended_by=actor_id if target_status == "ended" else client.ended_by,
                    lifecycle_updated_at=datetime.now(timezone.utc),
                )
                self._clients[i] = updated
                return updated
        return None

    async def list_active_client_grants(self, organization_id: str):
        return [c for c in self._clients if c.organization_id == organization_id and c.status == "active"]

    # -- branding (D21 white-label foundation) ------------------------------
    def seed_branding(self, profile_id, **kwargs):
        from domain.branding import ConsultantBranding

        branding = ConsultantBranding(profile_id=profile_id, **kwargs)
        self._brandings[profile_id] = branding
        return branding

    async def get_branding(self, profile_id: str):
        from domain.branding import ConsultantBranding

        branding = self._brandings.get(profile_id)
        if branding is None:
            # Mirror the real repo: the consultant_profiles row always exists,
            # so the projection is a zero-config branding (all flags off).
            branding = ConsultantBranding(profile_id=profile_id)
            self._brandings[profile_id] = branding
        return branding

    async def update_branding(self, profile_id: str, fields: dict):
        from dataclasses import replace
        from domain.branding import ConsultantBranding

        current = self._brandings.get(profile_id)
        if current is None:
            current = ConsultantBranding(profile_id=profile_id)
            self._brandings[profile_id] = current
        known = {
            k: v for k, v in fields.items()
            if k in getattr(ConsultantBranding, "__dataclass_fields__", {})
        }
        updated = replace(current, **known)
        self._brandings[profile_id] = updated
        return updated

    async def get(self, id: str):
        return None

    async def save(self, entity):
        return entity

    async def delete(self, id: str) -> None:
        return None

    # -- tasks --------------------------------------------------------------
    async def list_tasks(self, consultant_id: str, status: Optional[str] = None):
        rows = [t for t in self._tasks if t.consultant_id == consultant_id]
        if status is not None:
            rows = [t for t in rows if t.status == status]
        return rows

    async def create_task(
        self, consultant_id, task_title, task_type, priority, client_id, metadata
    ):
        task = self._task_type(
            id=f"task-{len(self._tasks) + 1}",
            consultant_id=consultant_id,
            task_title=task_title,
            client_id=client_id,
            task_type=task_type,
            priority=priority,
            status="open",
            metadata=metadata or {},
        )
        self._tasks.append(task)
        return task

    async def update_task_status(self, task_id: str, status: str):
        from dataclasses import replace

        for i, task in enumerate(self._tasks):
            if task.id == task_id:
                updated = replace(task, status=status)
                self._tasks[i] = updated
                return updated
        return None


class MemoryManualExtraction:
    """In-memory manual-extraction surface (batches/items/workflow/QC/ops).

    Mirrors the repository surface consumed by the customer Phase 3 workflow and
    the Phase 8 operations layer. Items/batches are stored as the immutable
    domain dataclasses; ``set_status``/``set_batches`` keep the Phase 7 minimal
    seeding helpers working for the consultant surface.
    """

    def __init__(self) -> None:
        self._status: dict[str, dict] = {}
        self._org_batches: dict[str, list] = {}
        self._batches: dict[str, ManualExtractionBatch] = {}
        self._items: dict[str, ManualExtractionItem] = {}
        self._next_item_seen: set[str] = set()

    # -- Phase 7 minimal seeding helpers (consultant surface) ----------------
    def set_status(self, org_id: str, status: dict) -> None:
        self._status[org_id] = status

    def set_batches(self, org_id: str, batches: list) -> None:
        self._org_batches[org_id] = batches

    async def workflow_status(self, org_id: str) -> dict:
        return self._status.get(org_id, {})

    async def list_batches(self, org_id: str) -> list:
        return self._org_batches.get(org_id, [])

    async def list_batches_with_counts(self, org_id: str) -> list:
        from dataclasses import asdict

        out = []
        for batch in self._org_batches.get(org_id, []):
            count = sum(1 for it in self._items.values() if it.batch_id == batch.id)
            out.append({**asdict(batch), "item_count": count})
        return out

    # -- batches -------------------------------------------------------------
    async def create_batch(
        self,
        org_id: str,
        batch_name: str,
        total_documents: int = 0,
        total_pages: int = 0,
        total_cost: float = 0.0,
        currency: str = "GBP",
        batch_description: Optional[str] = None,
        price_per_page: Optional[float] = None,
        created_by: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> ManualExtractionBatch:
        batch = ManualExtractionBatch(
            id=f"batch-{uuid.uuid4()}",
            organization_id=org_id,
            batch_name=batch_name,
            batch_description=batch_description,
            entity_id=entity_id,
            total_documents=total_documents,
            total_pages=total_pages,
            total_cost=total_cost,
            price_per_page=price_per_page,
            currency=currency,
            status="open",
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
        )
        self._batches[batch.id] = batch
        return batch

    async def get_batch(self, batch_id: str) -> Optional[ManualExtractionBatch]:
        return self._batches.get(batch_id)

    async def update_batch(
        self,
        batch_id: str,
        status: Optional[str] = None,
        assigned_to: Any = _UNSET,
        assigned_by: Optional[str] = None,
        entity_id: Any = _UNSET,
        customer_notes: Optional[str] = None,
        staff_notes: Optional[str] = None,
        updated_by: Optional[str] = None,
    ) -> Optional[ManualExtractionBatch]:
        batch = self._batches.get(batch_id)
        if batch is None:
            return None
        from dataclasses import replace

        updated = replace(
            batch,
            status=status if status is not None else batch.status,
            assigned_to=(
                assigned_to
                if assigned_to is not _UNSET
                else batch.assigned_to
            ),
            assigned_by=assigned_by if assigned_by is not None else batch.assigned_by,
            entity_id=entity_id if entity_id is not _UNSET else batch.entity_id,
            customer_notes=customer_notes if customer_notes is not None else batch.customer_notes,
            staff_notes=staff_notes if staff_notes is not None else batch.staff_notes,
            assigned_at=(
                datetime.now(timezone.utc)
                if assigned_to is not _UNSET
                or entity_id is not _UNSET
                or status == "in_progress"
                else batch.assigned_at
            ),
        )
        self._batches[batch_id] = updated
        return updated

    async def complete_batch(self, batch_id: str, completed_by: str) -> Optional[ManualExtractionBatch]:
        batch = self._batches.get(batch_id)
        if batch is None:
            return None
        from dataclasses import replace

        updated = replace(
            batch,
            status="completed",
            completed_by=completed_by,
            completed_at=datetime.now(timezone.utc),
        )
        self._batches[batch_id] = updated
        return updated

    async def cancel_batch(self, batch_id: str, updated_by: str) -> Optional[ManualExtractionBatch]:
        batch = self._batches.get(batch_id)
        if batch is None:
            return None
        from dataclasses import replace

        updated = replace(batch, status="cancelled", updated_by=updated_by)
        self._batches[batch_id] = updated
        return updated

    async def batch_progress(self, batch_id: str) -> Optional[dict]:
        batch = self._batches.get(batch_id)
        if batch is None:
            return None
        by_status: dict[str, int] = {}
        for item in self._items.values():
            if item.batch_id == batch_id:
                by_status[item.status or "pending"] = by_status.get(item.status or "pending", 0) + 1
        total = sum(by_status.values())
        stages = {
            stage: sum(by_status.get(s, 0) for s in statuses)
            for stage, statuses in WORKFLOW_STAGE_STATUSES.items()
        }
        done = by_status.get("approved", 0) + by_status.get("qc_approved", 0)
        return {
            "batch": batch,
            "total_items": total,
            "by_status": by_status,
            "by_stage": stages,
            "pct_complete": round(done / total * 100, 2) if total else 0.0,
        }



    # -- items ---------------------------------------------------------------
    async def create_item(
        self,
        batch_id: str,
        file_name: str,
        file_url: str,
        page_count: int = 1,
        document_type: Optional[str] = None,
        status: str = "pending",
    ) -> ManualExtractionItem:
        item = ManualExtractionItem(
            id=f"item-{uuid.uuid4()}",
            batch_id=batch_id,
            file_name=file_name,
            file_url=file_url,
            page_count=page_count,
            document_type=document_type,
            status=status,
            created_at=datetime.now(timezone.utc),
        )
        self._items[item.id] = item
        return item

    async def get_item(self, item_id: str) -> Optional[ManualExtractionItem]:
        return self._items.get(item_id)

    async def list_items(self, batch_id: str) -> list[ManualExtractionItem]:
        return [i for i in self._items.values() if i.batch_id == batch_id]

    async def update_item(
        self,
        item_id: str,
        extracted_data: Optional[dict] = None,
        mapped_data: Optional[dict] = None,
        calculated_emissions_kg_co2e: Optional[float] = None,
        updated_by: Optional[str] = None,
    ) -> Optional[ManualExtractionItem]:
        item = self._items.get(item_id)
        if item is None:
            return None
        from dataclasses import replace

        updated = replace(
            item,
            extracted_data=extracted_data if extracted_data is not None else item.extracted_data,
            mapped_data=mapped_data if mapped_data is not None else item.mapped_data,
            calculated_emissions_kg_co2e=(
                calculated_emissions_kg_co2e
                if calculated_emissions_kg_co2e is not None
                else item.calculated_emissions_kg_co2e
            ),
        )
        self._items[item_id] = updated
        return updated

    async def set_item_status(
        self, item_id: str, status: str
    ) -> Optional[ManualExtractionItem]:
        item = self._items.get(item_id)
        if item is None:
            return None
        from dataclasses import replace

        updated = replace(item, status=status)
        self._items[item_id] = updated
        return updated


    async def save_extracted_data(
        self, item_id: str, extracted_data: dict, extracted_by: str
    ) -> Optional[ManualExtractionItem]:
        item = self._items.get(item_id)
        if item is None:
            return None
        from dataclasses import replace

        updated = replace(
            item,
            status="extracted",
            extracted_data=extracted_data,
            extracted_by=extracted_by,
            extracted_at=datetime.now(timezone.utc),
        )
        self._items[item_id] = updated
        return updated

    async def save_mapped_data(
        self,
        item_id: str,
        mapped_data: dict,
        mapped_facility_id: Optional[str],
        mapped_asset_id: Optional[str],
        mapped_supplier_id: Optional[str],
        emission_factor_used: Optional[str],
    ) -> Optional[ManualExtractionItem]:
        item = self._items.get(item_id)
        if item is None:
            return None
        from dataclasses import replace

        updated = replace(
            item,
            status="mapped",
            mapped_data=mapped_data,
            mapped_facility_id=mapped_facility_id,
            mapped_asset_id=mapped_asset_id,
            mapped_supplier_id=mapped_supplier_id,
            emission_factor_used=emission_factor_used,
        )
        self._items[item_id] = updated
        return updated

    async def save_calculation(
        self,
        item_id: str,
        calculated_emissions_kg_co2e: float,
        mapped_data: Optional[dict] = None,
    ) -> Optional[ManualExtractionItem]:
        item = self._items.get(item_id)
        if item is None:
            return None
        from dataclasses import replace

        updated = replace(
            item,
            status="calculated",
            calculated_emissions_kg_co2e=calculated_emissions_kg_co2e,
            mapped_data=mapped_data if mapped_data is not None else item.mapped_data,
        )
        self._items[item_id] = updated
        return updated

    async def customer_review(
        self,
        item_id: str,
        approved: bool,
        reviewed_by: str,
        rejection_reason: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[ManualExtractionItem]:
        item = self._items.get(item_id)
        if item is None:
            return None
        from dataclasses import replace

        updated = replace(
            item,
            status="approved" if approved else "rejected",
            customer_approved=approved,
            customer_reviewed_by=reviewed_by,
            customer_reviewed_at=datetime.now(timezone.utc),
            customer_rejection_reason=rejection_reason,
            customer_notes=notes,
        )
        self._items[item_id] = updated
        return updated


    # -- queues --------------------------------------------------------------
    async def next_item(
        self, org_id: str, stage: str, exclude_item_id: Optional[str] = None
    ) -> Optional[ManualExtractionItem]:
        statuses = WORKFLOW_STAGE_STATUSES.get(stage)
        if statuses is None:
            return None
        candidates = [
            i
            for i in self._items.values()
            if i.status in statuses
            and i.id != (exclude_item_id or "")
            and self._batches.get(i.batch_id) is not None
            and self._batches[i.batch_id].organization_id == org_id
        ]
        if not candidates:
            return None
        return sorted(
            candidates,
            key=lambda i: i.created_at or datetime.min.replace(tzinfo=timezone.utc),
        )[0]

    async def list_by_stage(self, org_id: str, stage: str, limit: int = 100) -> list:
        statuses = WORKFLOW_STAGE_STATUSES.get(stage)
        if statuses is None:
            return []
        return [
            i
            for i in self._items.values()
            if i.status in statuses
            and self._batches.get(i.batch_id) is not None
            and self._batches[i.batch_id].organization_id == org_id
        ][:limit]

    async def list_customer_review(self, org_id: str) -> list:
        return [
            i
            for i in self._items.values()
            if i.status == "customer_review"
            and self._batches.get(i.batch_id) is not None
            and self._batches[i.batch_id].organization_id == org_id
        ]

    async def workflow_dashboard(self, org_id: str) -> dict:
        batches = [b for b in self._batches.values() if b.organization_id == org_id]
        items = [
            i
            for i in self._items.values()
            if self._batches.get(i.batch_id) is not None
            and self._batches[i.batch_id].organization_id == org_id
        ]
        by_status: dict[str, int] = {}
        for item in items:
            by_status[item.status or "pending"] = by_status.get(item.status or "pending", 0) + 1
        return {
            "batches": {"total": len(batches)},
            "items": {"total": len(items), "by_status": by_status},
            "queues": {
                "qc_pending": 0,
                "customer_review": by_status.get("customer_review", 0),
            },
        }

    # -- QC ------------------------------------------------------------------
    async def list_qc_pending(self) -> list[ManualExtractionItem]:
        return [
            i for i in self._items.values()
            if i.status == "extracted" and i.quality_score is None
        ]

    async def qc_review(
        self,
        item_id: str,
        quality_score: int,
        qc_notes: Optional[str],
        qc_by: str,
        approved: bool,
    ) -> Optional[ManualExtractionItem]:
        item = self._items.get(item_id)
        if item is None:
            return None
        from dataclasses import replace

        updated = replace(
            item,
            status="qc_approved" if approved else "qc_rejected",
            quality_score=quality_score,
            qc_notes=qc_notes,
            qc_by=qc_by,
            qc_at=datetime.now(timezone.utc),
        )
        self._items[item_id] = updated
        return updated


    # -- operations (Phase 8) ------------------------------------------------
    async def ops_dashboard_all(self) -> dict:
        by_status: dict[str, int] = {}
        for item in self._items.values():
            by_status[item.status or "pending"] = by_status.get(item.status or "pending", 0) + 1
        total = sum(by_status.values())
        stages = {
            stage: sum(by_status.get(s, 0) for s in statuses)
            for stage, statuses in WORKFLOW_STAGE_STATUSES.items()
        }
        batch_status: dict[str, int] = {}
        for batch in self._batches.values():
            key = batch.status or "open"
            batch_status[key] = batch_status.get(key, 0) + 1
        return {
            "batches": {"total": len(self._batches), "by_status": batch_status},
            "items": {
                "total": total,
                "by_status": by_status,
                "by_stage": stages,
                "pct_complete": round(
                    (by_status.get("approved", 0) + by_status.get("qc_approved", 0)) / total * 100, 2
                )
                if total
                else 0.0,
            },
            "queues": {
                "qc_pending": len(await self.list_qc_pending()),
                "customer_review": by_status.get("customer_review", 0),
            },
        }

    async def list_operator_batches(
        self, staff_user_id: str, status: Optional[str] = None
    ) -> list[ManualExtractionBatch]:
        batches = [
            b
            for b in self._batches.values()
            if b.entity_id is None  # D22: entity-assigned batches are the entity's work
            and (
                b.assigned_to == staff_user_id
                or (b.assigned_to is None and b.status in ("open", "in_progress"))
            )
        ]
        if status is not None:
            batches = [b for b in batches if b.status == status]
        return batches

    async def next_operator_item(
        self,
        staff_user_id: str,
        stage: str,
        exclude_item_id: Optional[str] = None,
    ) -> Optional[ManualExtractionItem]:
        statuses = WORKFLOW_STAGE_STATUSES.get(stage)
        if statuses is None:
            return None
        candidates = [
            i
            for i in self._items.values()
            if i.status in statuses
            and i.id != (exclude_item_id or "")
            and self._batches.get(i.batch_id) is not None
            and self._batches[i.batch_id].entity_id is None  # D22 isolation
            and (
                self._batches[i.batch_id].assigned_to == staff_user_id
                or (
                    self._batches[i.batch_id].assigned_to is None
                    and self._batches[i.batch_id].status in ("open", "in_progress")
                )
            )
        ]
        if not candidates:
            return None
        return sorted(
            candidates,
            key=lambda i: i.created_at or datetime.min.replace(tzinfo=timezone.utc),
        )[0]

    # -- entity extraction workspace (D22) -----------------------------------
    async def list_entity_batches(
        self, entity_id: str, status: Optional[str] = None
    ) -> list[ManualExtractionBatch]:
        batches = [
            b for b in self._batches.values() if b.entity_id == entity_id
        ]
        if status is not None:
            batches = [b for b in batches if b.status == status]
        return batches

    async def list_entity_items(
        self,
        entity_id: str,
        stage: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[ManualExtractionItem]:
        statuses = WORKFLOW_STAGE_STATUSES.get(stage) if stage is not None else None
        return [
            i
            for i in self._items.values()
            if self._batches.get(i.batch_id) is not None
            and self._batches[i.batch_id].entity_id == entity_id
            and (statuses is None or i.status in statuses)
            and (status is None or i.status == status)
        ]

    async def next_entity_item(
        self,
        entity_id: str,
        stage: str,
        exclude_item_id: Optional[str] = None,
    ) -> Optional[ManualExtractionItem]:
        statuses = WORKFLOW_STAGE_STATUSES.get(stage)
        if statuses is None:
            return None
        candidates = [
            i
            for i in self._items.values()
            if i.status in statuses
            and i.id != (exclude_item_id or "")
            and self._batches.get(i.batch_id) is not None
            and self._batches[i.batch_id].entity_id == entity_id
            and self._batches[i.batch_id].status != "cancelled"
        ]
        if not candidates:
            return None
        return sorted(
            candidates,
            key=lambda i: i.created_at or datetime.min.replace(tzinfo=timezone.utc),
        )[0]

    async def entity_workflow_dashboard(self, entity_id: str) -> dict:
        batches = [b for b in self._batches.values() if b.entity_id == entity_id]
        by_status: dict[str, int] = {}
        for item in self._items.values():
            batch = self._batches.get(item.batch_id)
            if batch is None or batch.entity_id != entity_id:
                continue
            by_status[item.status or "pending"] = by_status.get(item.status or "pending", 0) + 1
        total = sum(by_status.values())
        stages = {
            stage: sum(by_status.get(s, 0) for s in statuses)
            for stage, statuses in WORKFLOW_STAGE_STATUSES.items()
        }
        batch_status: dict[str, int] = {}
        for batch in batches:
            key = batch.status or "open"
            batch_status[key] = batch_status.get(key, 0) + 1
        return {
            "entity_id": entity_id,
            "batches": {"total": len(batches), "by_status": batch_status},
            "items": {
                "total": total,
                "by_status": by_status,
                "by_stage": stages,
                "pct_complete": round(
                    (by_status.get("approved", 0) + by_status.get("qc_approved", 0)) / total * 100, 2
                )
                if total
                else 0.0,
            },
            "queues": {
                "qc_pending": by_status.get("extracted", 0),
                "customer_review": by_status.get("customer_review", 0),
            },
        }

    async def get(self, id: str):
        return self._items.get(id) or self._batches.get(id)

    async def save(self, entity):
        return entity

    async def delete(self, id: str) -> None:
        return None


class MemoryFiles:
    """Minimal in-memory organization-files surface (documents)."""

    def __init__(self) -> None:
        self._rows: dict[str, list] = {}
        self._by_id: dict[str, object] = {}

    def set_files(self, org_id: str, files: list) -> None:
        self._rows[org_id] = files
        for f in files:
            fid = getattr(f, "id", None)
            if fid:
                self._by_id[str(fid)] = f

    def add_file(self, file_row: object) -> None:
        self._by_id[str(getattr(file_row, "id"))] = file_row

    async def list_for_org(self, org_id: str, status=None, limit=100, offset=0) -> list:
        return self._rows.get(org_id, [])

    async def get(self, id: str):
        return self._by_id.get(str(id))

    async def get_by_path(self, path: str):
        for f in self._by_id.values():
            if getattr(f, "path", None) == path:
                return f
        return None

    async def save(self, entity):
        return entity

    async def delete(self, id: str) -> None:
        return None


class _StubRepo:
    """Minimal no-op repo satisfying an unused ``RepositoryBundle`` field."""

    async def get(self, id: str):
        return None

    async def save(self, entity):
        return entity

    async def delete(self, id: str) -> None:
        return None

    async def list_for_user(self, user_id: str, unread_only: bool = False, limit: int = 100, offset: int = 0):
        return []

    async def count_for_user(self, user_id: str, unread_only: bool = False) -> int:
        return 0


class MemoryExports:
    """In-memory ``ExportsRepository`` surface (V3 exports / export auth)."""

    async def emissions(
        self,
        org_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        scope: Optional[str] = None,
        limit: int = 10000,
    ) -> list[dict[str, Any]]:
        return []

    async def documents(self, org_id: str) -> list[dict[str, Any]]:
        return []

    async def get(self, id: str):
        return None

    async def save(self, entity):
        return entity

    async def delete(self, id: str) -> None:
        return None


class MemoryAudit:
    """Satisfies ``AuditSink`` + the audit-repository read surface."""

    def __init__(self, entries: Optional[list[AuditEntry]] = None) -> None:
        self._entries: list[AuditEntry] = list(entries or [])

    async def record(self, entry: AuditEntry) -> AuditEntry:
        self._entries.append(entry)
        return entry

    async def query(self, filters: AuditQuery) -> list[AuditEntry]:
        rows = list(self._entries)
        if filters.correlation_id is not None:
            rows = [e for e in rows if e.correlation_id == filters.correlation_id]
        if filters.entity_type is not None:
            rows = [e for e in rows if e.entity_type == filters.entity_type]
        if filters.entity_id is not None:
            rows = [e for e in rows if e.entity_id == filters.entity_id]
        if filters.action is not None:
            rows = [e for e in rows if e.action == filters.action]
        if filters.actor is not None:
            rows = [e for e in rows if e.actor == filters.actor]
        if filters.occurred_after is not None:
            rows = [e for e in rows if e.occurred_at >= filters.occurred_after]
        if filters.occurred_before is not None:
            rows = [e for e in rows if e.occurred_at <= filters.occurred_before]
        rows.sort(key=lambda e: e.occurred_at, reverse=True)
        return rows[filters.offset : filters.offset + filters.limit]

    async def export_csv(self, filters: AuditQuery) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            ["id", "correlation_id", "entity_type", "entity_id", "action", "actor", "occurred_at"]
        )
        for entry in await self.query(filters):
            writer.writerow(
                [
                    entry.id,
                    entry.correlation_id,
                    entry.entity_type,
                    entry.entity_id,
                    entry.action,
                    entry.actor,
                    entry.occurred_at.isoformat(),
                ]
            )
        return buffer.getvalue()

    async def get_by_correlation(self, correlation_id: str) -> list[AuditEntry]:
        rows = [e for e in self._entries if e.correlation_id == correlation_id]
        rows.sort(key=lambda e: e.occurred_at)
        return rows

    async def get(self, id: str) -> Optional[AuditEntry]:
        return next((e for e in self._entries if e.id == id), None)

    async def save(self, entity: AuditEntry) -> AuditEntry:
        return await self.record(entity)

    async def delete(self, id: str) -> None:
        self._entries = [e for e in self._entries if e.id != id]


class MemoryEvents:
    """Minimal events surface (not exercised by Phase 10 endpoints)."""

    def __init__(self) -> None:
        self._events: list[Any] = []

    async def store(self, event: Any) -> Any:
        self._events.append(event)
        return event

    async def get_by_correlation(self, correlation_id: str) -> list[Any]:
        return [e for e in self._events if getattr(e, "correlation_id", "") == correlation_id]

    async def get(self, id: str) -> Optional[Any]:
        return next((e for e in self._events if getattr(e, "event_id", "") == id), None)

class MemoryDiscovery:
    """In-memory ``DiscoveryRepository`` surface (D27 / D19)."""

    def __init__(self) -> None:
        from domain.discovery import DiscoveryRequest

        self._request_type = DiscoveryRequest
        self._requests: list[Any] = []
        self._candidates: list[Any] = []

    def seed_org(self, org_id, name="Existing Org", *, country="GB", industry=None, company_number=None, contact_email=None):
        from domain.discovery import DiscoveryCandidate

        candidate = DiscoveryCandidate(
            organization_id=org_id,
            name=name,
            country=country,
            industry=industry,
            company_number=company_number,
            data_summary={"documents": 3, "emissions_logs": 5},
        )
        self._candidates.append(candidate)
        return candidate

    async def get(self, request_id: str):
        return next((r for r in self._requests if r.id == request_id), None)

    async def get_for_org(self, request_id: str, organization_id: str):
        return next(
            (r for r in self._requests if r.id == request_id and r.organization_id == organization_id),
            None,
        )

    async def list_for_org(self, organization_id: str):
        return [r for r in self._requests if r.organization_id == organization_id]

    async def get_for_candidate(self, organization_id: str, candidate_organization_id: str):
        return next(
            (
                r
                for r in self._requests
                if r.organization_id == organization_id
                and r.candidate_organization_id == candidate_organization_id
            ),
            None,
        )

    async def get_for_onboarding(self, request_id: str, created_by: str):
        """Pre-org-creation (organization_id IS NULL) request for its creator."""
        return next(
            (
                r
                for r in self._requests
                if r.id == request_id
                and r.organization_id is None
                and r.created_by == created_by
            ),
            None,
        )

    async def get_onboarding_by_candidate(
        self, candidate_organization_id: str, created_by: str
    ):
        return next(
            (
                r
                for r in self._requests
                if r.candidate_organization_id == candidate_organization_id
                and r.organization_id is None
                and r.created_by == created_by
                and r.status in ("pending_verification", "verified")
            ),
            None,
        )

    async def create_onboarding_request(
        self, *, candidate_organization_id, created_by, verification_method="email", note=None
    ):
        request = self._request_type(
            id=f"onboarding-discovery-{len(self._requests) + 1}",
            candidate_organization_id=candidate_organization_id,
            organization_id=None,
            created_by=created_by,
            verification_method=verification_method,
            note=note,
        )
        self._requests.append(request)
        return request

    async def count_for_candidate(self, candidate_organization_id: str) -> int:
        return len(
            [
                r
                for r in self._requests
                if r.candidate_organization_id == candidate_organization_id
                and r.status in ("pending_verification", "verified", "adopted")
            ]
        )

    async def lookup_candidates(self, **kwargs):
        return list(self._candidates)

    async def _org_data_summary(self, organization_id: str) -> dict:
        return {"documents": 3, "emissions_logs": 5}


    async def create_request(self, *, organization_id, candidate_organization_id, verification_method="email", note=None):
        request = self._request_type(
            id=f"discovery-{len(self._requests) + 1}",
            organization_id=organization_id,
            candidate_organization_id=candidate_organization_id,
            verification_method=verification_method,
            note=note,
        )
        self._requests.append(request)
        return request

    async def store_verification_code(self, request_id, code, *, ttl_seconds=900):
        from data.discovery import hash_verification_code
        from dataclasses import replace
        from datetime import datetime, timedelta, timezone

        for i, request in enumerate(self._requests):
            if request.id == request_id:
                updated = replace(
                    request,
                    verification_code_hash=hash_verification_code(code),
                    verification_code_expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
                    verification_attempts=0,
                )
                self._requests[i] = updated
                return updated
        return None

    async def verify_code(self, request_id, code, *, verified_by):
        from data.discovery import hash_verification_code
        from dataclasses import replace
        from datetime import datetime, timezone

        request = await self.get(request_id)
        if request is None or request.status != "pending_verification":
            return False, "request not pending"
        if not request.verification_code_hash or hash_verification_code(code.strip()) != request.verification_code_hash:
            return False, "invalid verification code"
        for i, req in enumerate(self._requests):
            if req.id == request_id:
                updated = replace(
                    req, status="verified", verified_by=verified_by,
                    verified_at=datetime.now(timezone.utc),
                )
                self._requests[i] = updated
        return True, "verified"

    async def staff_verify(self, request_id, *, verified_by):
        from dataclasses import replace
        from datetime import datetime, timezone

        for i, request in enumerate(self._requests):
            if request.id == request_id and request.status == "pending_verification":
                updated = replace(
                    request, status="verified", verified_by=verified_by,
                    verified_at=datetime.now(timezone.utc),
                )
                self._requests[i] = updated
                return True
        return False

    async def adopt(self, request_id, *, choice, scope, adopted_by):
        from dataclasses import replace
        from datetime import datetime, timezone

        for i, request in enumerate(self._requests):
            if request.id == request_id:
                updated = replace(
                    request, status="adopted", adoption_choice=choice,
                    adoption_scope=scope or {}, adopted_by=adopted_by,
                    adopted_at=datetime.now(timezone.utc),
                )
                self._requests[i] = updated
                return updated
        return None

    async def discard(self, request_id, *, discarded_by, note=None):
        from dataclasses import replace
        from datetime import datetime, timezone

        for i, request in enumerate(self._requests):
            if request.id == request_id:
                updated = replace(
                    request, status="discarded", adoption_choice="discard",
                    discarded_by=discarded_by, discarded_at=datetime.now(timezone.utc),
                    note=note or request.note,
                )
                self._requests[i] = updated
                return updated
        return None

    async def save(self, entity):
        return entity

    async def delete(self, id: str) -> None:
        return None


class MemoryMessaging:
    """In-memory ``MessagingRepository`` surface (D27 / D19)."""

    def __init__(self) -> None:
        from domain.messaging import Conversation, ConversationParticipant, Message

        self._conversation_type = Conversation
        self._participant_type = ConversationParticipant
        self._message_type = Message
        self._conversations: list[Any] = []
        self._participants: list[Any] = []
        self._messages: list[Any] = []

    async def get(self, conversation_id: str):
        return next((c for c in self._conversations if c.id == conversation_id), None)

    async def create_conversation(self, *, organization_id, subject, created_by):
        conversation = self._conversation_type(
            id=f"conv-{len(self._conversations) + 1}",
            organization_id=organization_id,
            subject=subject,
            created_by=created_by,
        )
        self._conversations.append(conversation)
        return conversation

    async def list_conversations_for_org(self, organization_id, *, limit=100, offset=0):
        return [c for c in self._conversations if c.organization_id == organization_id]

    async def count_conversations_for_org(self, organization_id: str) -> int:
        return len([c for c in self._conversations if c.organization_id == organization_id])

    async def close_conversation(self, conversation_id, *, closed_by):
        return True

    async def add_participant(self, *, conversation_id, user_id, metadata=None):
        participant = self._participant_type(
            id=f"part-{len(self._participants) + 1}",
            conversation_id=conversation_id,
            user_id=user_id,
            metadata=metadata or {},
        )
        self._participants.append(participant)
        return participant

    async def list_participants(self, conversation_id: str):
        return [p for p in self._participants if p.conversation_id == conversation_id]

    async def set_participant_active(self, conversation_id, user_id, is_active):
        return True

    async def send_message(self, *, conversation_id, sender_id, organization_id, content):
        message = self._message_type(
            id=f"msg-{len(self._messages) + 1}",
            conversation_id=conversation_id,
            sender_id=sender_id,
            organization_id=organization_id,
            content=content,
        )
        self._messages.append(message)
        return message

    async def list_messages(self, conversation_id, *, limit=200, offset=0):
        return [m for m in self._messages if m.conversation_id == conversation_id]

    async def count_messages(self, conversation_id: str) -> int:
        return len([m for m in self._messages if m.conversation_id == conversation_id])

    async def mark_conversation_read(self, conversation_id, user_id):
        return True

    async def save(self, entity):
        return entity

class MemoryWhiteLabel:
    """In-memory ``WhiteLabelRepository`` surface (D27 / D19)."""

    def __init__(self) -> None:
        from domain.whitelabel import CustomDomain, CustomSender

        self._domain_type = CustomDomain
        self._sender_type = CustomSender
        self._domains: list[Any] = []
        self._senders: list[Any] = []

    async def get(self, domain_id: str):
        return next((d for d in self._domains if d.id == domain_id), None)

    async def get_domain_for_consultant(self, domain_id, consultant_id):
        return next(
            (d for d in self._domains if d.id == domain_id and d.consultant_id == consultant_id),
            None,
        )

    async def list_domains(self, consultant_id: str):
        return [d for d in self._domains if d.consultant_id == consultant_id]

    async def create_domain(self, *, consultant_id, domain):
        domain_row = self._domain_type(
            id=f"domain-{len(self._domains) + 1}",
            consultant_id=consultant_id,
            domain=domain,
            verification_token=f"token-{domain}",
        )
        self._domains.append(domain_row)
        return domain_row

    async def verify_domain(self, domain_id, consultant_id, *, token):
        from dataclasses import replace

        domain = await self.get_domain_for_consultant(domain_id, consultant_id)
        if domain is None:
            return False, "domain not found"
        if domain.verification_token != token.strip():
            return False, "invalid verification token"
        for i, d in enumerate(self._domains):
            if d.id == domain_id:
                self._domains[i] = replace(d, status="verified")
        return True, "verified"

    async def activate_domain(self, domain_id, consultant_id):
        from dataclasses import replace

        for i, d in enumerate(self._domains):
            if d.id == domain_id and d.consultant_id == consultant_id and d.status == "verified":
                self._domains[i] = replace(d, status="active")
                return True
        return False

    async def remove_domain(self, domain_id, consultant_id):
        from dataclasses import replace

        for i, d in enumerate(self._domains):
            if d.id == domain_id and d.consultant_id == consultant_id:
                self._domains[i] = replace(d, status="removed_suspended")
                return True
        return False

    async def get_sender(self, sender_id: str):
        return next((s for s in self._senders if s.id == sender_id), None)

    async def get_sender_for_consultant(self, sender_id, consultant_id):
        return next(
            (s for s in self._senders if s.id == sender_id and s.consultant_id == consultant_id),
            None,
        )

    async def list_senders(self, consultant_id: str):
        return [s for s in self._senders if s.consultant_id == consultant_id]

    async def create_sender(self, *, consultant_id, email):
        sender = self._sender_type(
            id=f"sender-{len(self._senders) + 1}",
            consultant_id=consultant_id,
            email=email,
            domain=email.split("@")[-1],
            verification_token="sender-token",
        )
        self._senders.append(sender)
        return sender

    async def verify_sender(self, sender_id, consultant_id):
        from dataclasses import replace

        for i, s in enumerate(self._senders):
            if s.id == sender_id and s.consultant_id == consultant_id and s.status == "pending":
                self._senders[i] = replace(s, status="verified")
                return True
        return False

    async def remove_sender(self, sender_id, consultant_id):
        from dataclasses import replace

        for i, s in enumerate(self._senders):
            if s.id == sender_id and s.consultant_id == consultant_id:
                self._senders[i] = replace(s, status="removed")
                return True
        return False

    async def save(self, entity):
        return entity

    async def delete(self, id: str) -> None:
        return None


class MemoryReporting:
    """``ReportingRepository`` surface (in-memory, D30). Canned per-test data."""

    def __init__(self) -> None:
        self.emissions_summary_result: dict = {
            "total_kg": 0.0, "row_count": 0, "by_scope": [], "by_month": [],
        }
        self.document_summary_result: dict = {
            "total_documents": 0, "processing_by_status": {}, "processed": 0,
            "pending": 0, "requiring_attention": 0,
        }
        self.processing_summary_result: dict = {
            "batches": {"total": 0, "by_status": {}},
            "items": {"total": 0, "by_stage": {}, "mapped": 0, "unmapped": 0, "complete_pct": 0.0},
        }
        self.issues_summary_result: dict = {"by_status": {}, "open": 0, "sla_breached_open": 0}
        self.report_summary_result: dict = {}
        self.portfolio_result: list[dict] = []
        self.platform_result: dict = {}
        self.review_result: dict = {}
        self.qc_result: dict = {}
        self.entity_performance_result: dict = {}

    async def emissions_summary(self, *args, **kwargs):
        return self.emissions_summary_result

    async def document_summary(self, *args, **kwargs):
        return self.document_summary_result

    async def processing_summary(self, *args, **kwargs):
        return self.processing_summary_result

    async def issues_summary(self, *args, **kwargs):
        return self.issues_summary_result

    async def report_summary(self, *args, **kwargs):
        return self.report_summary_result

    async def consultant_portfolio(self, *args, **kwargs):
        return self.portfolio_result

    async def platform_overview(self, *args, **kwargs):
        return self.platform_result

    async def review_reporting(self, *args, **kwargs):
        return self.review_result

    async def qc_reporting(self, *args, **kwargs):
        return self.qc_result

    async def entity_performance(self, *args, **kwargs):
        return self.entity_performance_result

    # --- D31 fakes -----------------------------------------------------
    emissions_trend_result: dict = {"organization_id": "org-a", "months": []}
    member_activity_result: list = []
    consultant_client_detail_result: Optional[dict] = None
    queue_aging_result: dict = {}

    async def emissions_trend(self, *args, **kwargs):
        return self.emissions_trend_result

    async def member_activity(self, *args, **kwargs):
        return self.member_activity_result

    async def consultant_client_detail(self, *args, **kwargs):
        return self.consultant_client_detail_result

    async def queue_aging(self, *args, **kwargs):
        return self.queue_aging_result



class MemoryBillingPlans:
    """``BillingPlansRepository`` surface (in-memory, D37-0 versioned)."""

    def __init__(self, plans: Optional[list[BillingPlan]] = None) -> None:
        self._plans: list[BillingPlan] = list(plans or [])

    async def get(self, id: str) -> Optional[BillingPlan]:
        return next((p for p in self._plans if p.id == id), None)

    async def list_current(self, *, active_only: bool = False) -> list[BillingPlan]:
        current = [p for p in self._plans if p.effective_to is None]
        if active_only:
            current = [p for p in current if p.is_active]
        return sorted(current, key=lambda p: p.plan_code)

    async def history(self, plan_code: str) -> list[BillingPlan]:
        return sorted(
            (p for p in self._plans if p.plan_code == plan_code),
            key=lambda p: p.version,
        )

    async def get_current_by_code(self, plan_code: str) -> Optional[BillingPlan]:
        current = [p for p in self._plans if p.plan_code == plan_code and p.effective_to is None]
        if not current:
            return None
        return max(current, key=lambda p: p.version)

    async def get_version(self, plan_code: str, version: int) -> Optional[BillingPlan]:
        return next(
            (p for p in self._plans if p.plan_code == plan_code and p.version == version),
            None,
        )

    async def create(self, plan: BillingPlan, *, created_by: Optional[str]) -> BillingPlan:
        self._plans.append(plan)
        return plan

    async def publish_new_version(
        self,
        *,
        plan_code: str,
        fields: dict[str, Any],
        reason: Optional[str],
        updated_by: Optional[str],
    ) -> BillingPlan:
        current = await self.get_current_by_code(plan_code)
        base_version = current.version if current is not None else 0
        if current is not None:
            self._plans = [
                _close_plan(p) if p.id == current.id else p for p in self._plans
            ]
        now = datetime.now(timezone.utc)
        base = current or BillingPlan(
            id=str(uuid.uuid4()), plan_code=plan_code, name=plan_code, price=0
        )
        new = BillingPlan(
            id=str(uuid.uuid4()),
            plan_code=plan_code,
            name=fields.get("name") or base.name,
            description=fields.get("description", base.description),
            price=fields.get("price", base.price),
            currency=fields.get("currency") or base.currency,
            billing_interval=fields.get("billing_interval") or base.billing_interval,
            included_credits=int(fields.get("included_credits", base.included_credits)),
            included_storage_bytes=int(fields.get("included_storage_bytes", base.included_storage_bytes)),
            team_member_limit=fields.get("team_member_limit", base.team_member_limit),
            processing_limits=fields.get("processing_limits", base.processing_limits),
            features=fields.get("features", base.features),
            billing_mode=fields.get("billing_mode", base.billing_mode),
            assisted_processing_available=bool(fields.get("assisted_processing_available", base.assisted_processing_available)),
            managed_processing_available=bool(fields.get("managed_processing_available", base.managed_processing_available)),
            api_access=bool(fields.get("api_access", base.api_access)),
            is_active=bool(fields.get("is_active", base.is_active)),
            version=base_version + 1,
            version_label=f"v{base_version + 1}",
            effective_from=now,
            effective_to=None,
            created_at=now,
        )
        self._plans.append(new)
        return new

    async def save(self, entity: BillingPlan) -> BillingPlan:
        return entity

    async def delete(self, id: str) -> None:
        return None


def _close_plan(plan: BillingPlan) -> BillingPlan:
    from dataclasses import replace

    return replace(plan, effective_to=datetime.now(timezone.utc))

class MemoryBillingConfig:
    """``BillingCommercialConfigRepository`` surface (in-memory, versioned)."""

    def __init__(self, configs: Optional[list[CommercialConfig]] = None) -> None:
        self._configs: list[CommercialConfig] = list(configs or [])
        if not self._configs:
            self._configs = [
                CommercialConfig(
                    id="cfg-default-mode",
                    config_key="default_billing_mode",
                    config_value={"mode": "CREDIT"},
                    version=1,
                    reason="seed",
                    effective_from=datetime(2026, 8, 1, tzinfo=timezone.utc),
                ),
                CommercialConfig(
                    id="cfg-credit-rules",
                    config_key="credit_rules",
                    config_value={"classes": [{"class": "simple", "credits": 1}]},
                    version=1,
                    reason="seed",
                    effective_from=datetime(2026, 8, 1, tzinfo=timezone.utc),
                ),
            ]

    async def get(self, id: str) -> Optional[CommercialConfig]:
        return next((c for c in self._configs if c.id == id), None)

    async def get_current(self, config_key: str) -> Optional[CommercialConfig]:
        current = [c for c in self._configs if c.config_key == config_key and c.effective_to is None]
        if not current:
            return None
        return max(current, key=lambda c: c.version)

    async def list_current(self) -> list[CommercialConfig]:
        current: dict[str, CommercialConfig] = {}
        for c in self._configs:
            if c.effective_to is None:
                existing = current.get(c.config_key)
                if existing is None or c.version > existing.version:
                    current[c.config_key] = c
        return sorted(current.values(), key=lambda c: c.config_key)

    async def history(self, config_key: str) -> list[CommercialConfig]:
        return sorted(
            (c for c in self._configs if c.config_key == config_key),
            key=lambda c: c.version,
        )

    async def get_default_billing_mode(self) -> str:
        current = await self.get_current("default_billing_mode")
        if current is not None and current.config_value:
            mode = current.config_value.get("mode")
            if mode in ("CREDIT", "STANDARD"):
                return str(mode)
        return "CREDIT"

    async def update_version(
        self,
        *,
        config_key: str,
        config_value: dict[str, Any],
        reason: Optional[str],
        updated_by: Optional[str],
    ) -> CommercialConfig:
        current = await self.get_current(config_key)
        base_version = current.version if current is not None else 0
        if current is not None:
            self._configs = [
                _close_config(c) if c.id == current.id else c for c in self._configs
            ]
        now = datetime.now(timezone.utc)
        new = CommercialConfig(
            id=str(uuid.uuid4()),
            config_key=config_key,
            config_value=config_value,
            version=base_version + 1,
            reason=reason,
            effective_from=now,
            effective_to=None,
            created_by=updated_by,
        )
        self._configs.append(new)
        return new

    async def save(self, entity: CommercialConfig) -> CommercialConfig:
        return entity

    async def delete(self, id: str) -> None:
        return None


def _close_config(config: CommercialConfig) -> CommercialConfig:
    from dataclasses import replace

    return replace(config, effective_to=datetime.now(timezone.utc))


class MemoryCreditLedger:
    """``BillingCreditLedgerRepository`` surface (append-only, in-memory)."""

    def __init__(self, entries: Optional[list[CreditLedgerEntry]] = None) -> None:
        self._entries: list[CreditLedgerEntry] = list(entries or [])

    async def get(self, id: str) -> Optional[CreditLedgerEntry]:
        return next((e for e in self._entries if e.id == id), None)

    async def record(self, entry: CreditLedgerEntry) -> CreditLedgerEntry:
        if entry.external_reference is not None:
            dup = next(
                (
                    e
                    for e in self._entries
                    if e.organization_id == entry.organization_id
                    and e.external_reference == entry.external_reference
                ),
                None,
            )
            if dup is not None:
                raise RuntimeError(
                    f"duplicate external_reference {entry.external_reference!r}"
                )
        self._entries.append(entry)
        return entry

    async def list_for_org(self, organization_id: str) -> list[CreditLedgerEntry]:
        return [e for e in self._entries if e.organization_id == organization_id]

    async def balance(self, organization_id: str) -> int:
        return sum(
            e.credit_delta
            for e in self._entries
            if e.organization_id == organization_id
        )

    async def save(self, entity: CreditLedgerEntry) -> CreditLedgerEntry:
        return entity

    async def delete(self, id: str) -> None:
        return None

    async def _fetch_one(self, query: str, *args) -> tuple:
        # STANDARD-mode usage aggregation stub (in-memory: no usage rows).
        return (0,)


class MemorySubscriptions:
    """``SubscriptionsRepository`` surface (in-memory, org-scoped lifecycle)."""

    def __init__(self) -> None:
        self._subs: list[Subscription] = []

    async def get(self, id: str) -> Optional[Subscription]:
        return next((s for s in self._subs if s.id == id), None)

    async def get_active_for_org(self, organization_id: str) -> Optional[Subscription]:
        active = [
            s for s in self._subs
            if s.organization_id == organization_id and s.lifecycle_status in
            ("trial", "active", "past_due", "suspended")
        ]
        if not active:
            return None
        return max(active, key=lambda s: s.created_at or datetime.min.replace(tzinfo=timezone.utc))

    async def get_latest_for_org(self, organization_id: str) -> Optional[Subscription]:
        rows = [s for s in self._subs if s.organization_id == organization_id]
        if not rows:
            return None
        return max(rows, key=lambda s: s.created_at or datetime.min.replace(tzinfo=timezone.utc))

    async def list_for_org(self, organization_id: str) -> list[Subscription]:
        return [s for s in self._subs if s.organization_id == organization_id]

    async def list_all(self) -> list[Subscription]:
        return list(self._subs)

    async def upsert_active(self, subscription: Subscription, *, created_by: Optional[str]) -> Subscription:
        self._subs = [
            _close_sub(s) if (s.organization_id == subscription.organization_id
                              and s.lifecycle_status in ("trial", "active", "past_due", "suspended"))
            else s
            for s in self._subs
        ]
        self._subs.append(subscription)
        return subscription

    async def update_status(self, id: str, lifecycle_status: str, *, updated_by: Optional[str]) -> Optional[Subscription]:
        for i, s in enumerate(self._subs):
            if s.id == id:
                from dataclasses import replace
                self._subs[i] = replace(s, lifecycle_status=lifecycle_status)
                return self._subs[i]
        return None

    async def save(self, entity: Subscription) -> Subscription:
        return entity

    async def delete(self, id: str) -> None:
        return None


def _close_sub(sub: Subscription) -> Subscription:
    from dataclasses import replace

    return replace(sub, lifecycle_status="cancelled")


class MemoryBillingOrders:
    """``BillingOrdersRepository`` surface (in-memory, common order model)."""

    def __init__(self) -> None:
        self._orders: list[BillingOrder] = []

    async def get(self, id: str) -> Optional[BillingOrder]:
        return next((o for o in self._orders if o.id == id), None)

    async def get_for_org(self, id: str, organization_id: str) -> Optional[BillingOrder]:
        return next(
            (o for o in self._orders if o.id == id and o.organization_id == organization_id),
            None,
        )

    async def list_for_org(self, organization_id: str) -> list[BillingOrder]:
        return [o for o in self._orders if o.organization_id == organization_id]

    async def list_all(self, *, status: Optional[str] = None) -> list[BillingOrder]:
        if status:
            return [o for o in self._orders if o.status == status]
        return list(self._orders)

    async def create(self, order: BillingOrder, *, created_by: Optional[str]) -> BillingOrder:
        self._orders.append(order)
        return order

    async def update_status(self, id: str, status: str, *, actor: Optional[str] = None,
                            metadata: Optional[dict[str, Any]] = None) -> Optional[BillingOrder]:
        for i, o in enumerate(self._orders):
            if o.id == id:
                from dataclasses import replace
                self._orders[i] = replace(o, status=status, metadata=metadata or o.metadata)
                return self._orders[i]
        return None

    async def mark_approved(self, id: str, *, approved_by: Optional[str] = None) -> Optional[BillingOrder]:
        for i, o in enumerate(self._orders):
            if o.id == id:
                from dataclasses import replace
                self._orders[i] = replace(o, status="approved", approved_by=approved_by,
                                          approved_at=datetime.now(timezone.utc))
                return self._orders[i]
        return None

    async def mark_completed(self, id: str) -> Optional[BillingOrder]:
        for i, o in enumerate(self._orders):
            if o.id == id:
                from dataclasses import replace
                self._orders[i] = replace(o, status="completed", completed_at=datetime.now(timezone.utc))
                return self._orders[i]
        return None

    async def save(self, entity: BillingOrder) -> BillingOrder:
        return entity

    async def delete(self, id: str) -> None:
        return None

class MemoryStorageUsage:
    """``StorageUsageRepository`` surface (in-memory snapshots)."""

    def __init__(self) -> None:
        self._snapshots: list[StorageUsage] = []

    async def get(self, id: str) -> Optional[StorageUsage]:
        return next((s for s in self._snapshots if s.id == id), None)

    async def latest_for_org(self, organization_id: str) -> Optional[StorageUsage]:
        rows = [s for s in self._snapshots if s.organization_id == organization_id]
        if not rows:
            return None
        return max(rows, key=lambda s: s.measured_at or datetime.min.replace(tzinfo=timezone.utc))

    async def history_for_org(self, organization_id: str) -> list[StorageUsage]:
        return [s for s in self._snapshots if s.organization_id == organization_id]

    async def record(self, usage: StorageUsage) -> StorageUsage:
        self._snapshots.append(usage)
        return usage

    async def save(self, entity: StorageUsage) -> StorageUsage:
        return entity

    async def delete(self, id: str) -> None:
        return None

    async def _fetch_one(self, query: str, *args) -> tuple:
        # STORAGE aggregation stub (in-memory: no org files rows).
        return (0,)


class MemoryPaymentRecords:
    """``PaymentRecordsRepository`` surface (in-memory, provider-neutral)."""

    def __init__(self) -> None:
        self._records: list[PaymentRecord] = []

    async def get(self, id: str) -> Optional[PaymentRecord]:
        return next((r for r in self._records if r.id == id), None)

    async def list_for_org(self, organization_id: str) -> list[PaymentRecord]:
        return [r for r in self._records if r.organization_id == organization_id]

    async def list_all(self) -> list[PaymentRecord]:
        return list(self._records)

    async def create(self, record: PaymentRecord) -> PaymentRecord:
        self._records.append(record)
        return record

    async def update_status(self, id: str, status: str, *, provider_transaction_ref: Optional[str] = None) -> Optional[PaymentRecord]:
        for i, r in enumerate(self._records):
            if r.id == id:
                from dataclasses import replace
                self._records[i] = replace(
                    r, status=status,
                    provider_transaction_ref=provider_transaction_ref or r.provider_transaction_ref,
                )
                return self._records[i]
        return None

    async def save(self, entity: PaymentRecord) -> PaymentRecord:
        return entity

    async def delete(self, id: str) -> None:
        return None


class MemoryIdempotency:
    """``IdempotencyRepository`` surface (in-memory, durable keys)."""

    def __init__(self) -> None:
        self._keys: dict[str, IdempotencyKey] = {}

    async def get(self, key: str) -> Optional[IdempotencyKey]:
        return self._keys.get(key)

    async def claim(self, key: str, operation: str, *, entity_type: Optional[str] = None,
                    entity_id: Optional[str] = None, request_hash: Optional[str] = None) -> IdempotencyKey:
        if key in self._keys:
            raise RuntimeError("duplicate idempotency key")
        entry = IdempotencyKey(key=key, operation=operation, entity_type=entity_type,
                               entity_id=entity_id, request_hash=request_hash,
                               created_at=datetime.now(timezone.utc))
        self._keys[key] = entry
        return entry

    async def save(self, entity: IdempotencyKey) -> IdempotencyKey:
        return entity

    async def delete(self, id: str) -> None:
        return None


class MemoryUsageTracking:
    """``UsageTrackingRepository`` surface (in-memory, STANDARD usage)."""

    def __init__(self) -> None:
        self._rows: list[dict] = []

    async def record(self, organization_id: str, units: int, when=None) -> None:
        self._rows.append({"organization_id": organization_id, "units": units,
                           "when": when or datetime.now(timezone.utc)})

    async def _fetch_one(self, query: str, *args) -> tuple:
        org_id = args[0] if args else None
        total = sum(r["units"] for r in self._rows if r["organization_id"] == org_id)
        return (total,)

    async def save(self, entity) -> object:
        return entity

    async def delete(self, id: str) -> None:
        return None


class InMemoryWorld:
    """One fully-wired in-memory world: repos + shared audit store + event bus.

    Mirrors the production composition root (prep-pack §4.1) but backed by the
    memory fakes. Nothing here touches the database.
    """

    def __init__(
        self,
        *,
        factors: Optional[list[EmissionFactor]] = None,
        logs: Optional[list[EmissionLog]] = None,
        batches: Optional[list[ImportBatch]] = None,
        aliases: Optional[list[FactorAlias]] = None,
        audit: Optional[list[AuditEntry]] = None,
        customer_factors: Optional[list[CustomerFactor]] = None,
        entities: Optional[list[ProcessingEntity]] = None,
        issues: Optional[list[Issue]] = None,
    ) -> None:
        org_a, meta_a, fac_a, asset_a = seed_org_a()
        org_b, meta_b, fac_b, asset_b = seed_org_b()

        self.factors = MemoryFactors(factors if factors is not None else [seed_defra_factor(), seed_seai_factor()])
        self.logs = MemoryLogs(
            logs

            if logs is not None
            else [
                seed_log(
                    log_id="log-a1",
                    org_id="org-a",
                    factor_id="factor-defra-gas",
                    quantity="1000",
                    unit="kWh",
                    scope="Scope 1",
                    day=_Date(2025, 6, 1),
                    calculated="183.000000",
                    snapshot_id="snap-a1",
                    facility_id="fac-a1",
                )
            ]
        )
        self.organizations = MemoryOrganizations(
            orgs=[org_a, org_b],
            metadata={"org-a": meta_a, "org-b": meta_b},
            facilities={"org-a": fac_a, "org-b": fac_b},
            assets={"org-a": asset_a, "org-b": asset_b},
        )
        self.imports = MemoryImports(
            batches
            if batches is not None
            else [
                seed_import_batch(
                    batch_id="batch-defra-2025",
                    provider="defra",
                    year=2025,
                    status="completed",
                    is_active=True,
                    rows_total=7029,
                    rows_imported=7029,
                ),
                seed_import_batch(
                    batch_id="batch-defra-2024",
                    provider="defra",
                    year=2024,
                    status="completed",
                    is_active=False,
                    rows_total=7029,
                    rows_imported=7029,
                ),
                seed_import_batch(
                    batch_id="batch-seai-2025",
                    provider="seai",
                    year=2025,
                    status="completed",
                    is_active=True,
                    rows_total=20,
                    rows_imported=20,
                ),
            ]
        )
        self.reports = MemoryReports()
        self.audit = MemoryAudit(audit or [])
        self.events = MemoryEvents()
        self.aliases = MemoryAliases(
            aliases
            if aliases is not None
            else [
                FactorAlias(
                    id="alias-ng",
                    organization_id=None,
                    alias_text="NG",
                    target_activity_type=DEFRA_GAS_ACTIVITY,
                    target_provider_key="defra",
                    created_by="admin-1",
                    created_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
                ),
                FactorAlias(
                    id="alias-a1",
                    organization_id="org-a",
                    alias_text="GasNet",
                    target_activity_type=DEFRA_GAS_ACTIVITY,
                    target_provider_key="defra",
                    created_by="admin-1",
                    created_at=datetime(2025, 6, 2, tzinfo=timezone.utc),
                ),
            ]
        )
        self.customer_factors = MemoryCustomerFactors(customer_factors or [])
        self.entities = MemoryEntities(entities or [])
        self.issues = MemoryIssues(issues or [])
        self.report_versions = MemoryReportVersions()
        self.exports = MemoryExports()
        self.suppliers = MemorySuppliers()
        self.invitations = MemoryInvitations()
        self.roles = MemoryRoles()
        self.tenant = MemoryTenant()
        self.consultants = MemoryConsultants()
        self.manual_extraction = MemoryManualExtraction()
        self.files = MemoryFiles()
        self.review_queue = MemoryReviewQueue()
        self.queue_settings = MemoryQueueSettings()
        self.staff = MemoryStaff()
        self.discovery = MemoryDiscovery()
        self.messaging = MemoryMessaging()
        self.whitelabel = MemoryWhiteLabel()
        self.reporting = MemoryReporting()
        self.billing_plans = MemoryBillingPlans()
        self.billing_config = MemoryBillingConfig()
        self.billing_ledger = MemoryCreditLedger()
        self.billing_subscriptions = MemorySubscriptions()
        self.billing_orders = MemoryBillingOrders()
        self.billing_storage = MemoryStorageUsage()
        self.billing_payments = MemoryPaymentRecords()
        self.billing_idempotency = MemoryIdempotency()
        self.billing_usage = MemoryUsageTracking()

    def bundle(self):
        from api.dependencies import RepositoryBundle

        return RepositoryBundle(
            factors=self.factors,
            logs=self.logs,
            organizations=self.organizations,
            imports=self.imports,
            reports=self.reports,
            report_versions=self.report_versions,
            audit=self.audit,
            events=self.events,
            aliases=self.aliases,
            customer_factors=self.customer_factors,
            entities=self.entities,
            issues=self.issues,
            invitations=self.invitations,
            roles=self.roles,
            tenant=self.tenant,
            files=self.files,
            batches=_StubRepo(),
            review_queue=self.review_queue,
            queue_settings=self.queue_settings,
            verifications=_StubRepo(),
            notifications=_StubRepo(),
            exports=self.exports,
            consultants=self.consultants,
            discovery=self.discovery,
            messaging=self.messaging,
            whitelabel=self.whitelabel,
            manual_extraction=self.manual_extraction,
            suppliers=self.suppliers,
            staff=self.staff,
            reporting=self.reporting,
            billing_plans=self.billing_plans,
            billing_config=self.billing_config,
            billing_ledger=self.billing_ledger,
            billing_subscriptions=self.billing_subscriptions,
            billing_orders=self.billing_orders,
            billing_storage=self.billing_storage,
            billing_payments=self.billing_payments,
            billing_idempotency=self.billing_idempotency,
            billing_usage=self.billing_usage,
        )


class MemoryCustomerFactors:
    """``CustomerFactorsRepository`` surface (in-memory, V3 ADR-V3-002)."""

    def __init__(self, factors: Optional[list[CustomerFactor]] = None) -> None:
        self._factors: list[CustomerFactor] = list(factors or [])

    async def get(self, id: str) -> Optional[CustomerFactor]:
        return next((f for f in self._factors if f.id == id), None)

    async def get_org_factors(self, org_id: str) -> list[CustomerFactor]:
        return [f for f in self._factors if f.organization_id == org_id]

    async def get_active_for_org(self, org_id: str) -> list[CustomerFactor]:
        return [
            f for f in self._factors
            if f.organization_id == org_id and f.status == "active"
        ]

    async def get_by_activity(
        self, org_id: str, activity_type: str
    ) -> list[CustomerFactor]:
        return [
            f for f in self._factors
            if f.organization_id == org_id and f.activity_type == activity_type
        ]

    async def save(self, entity: CustomerFactor) -> CustomerFactor:
        for i, existing in enumerate(self._factors):
            if existing.id == entity.id:
                self._factors[i] = entity
                return entity
        self._factors.append(entity)
        return entity

    async def update_status(
        self, id: str, status: str, *, updated_by: Optional[str] = None
    ) -> CustomerFactor:
        existing = await self.get(id)
        if existing is None:
            raise RuntimeError(f"customer factor {id!r} does not exist")
        from dataclasses import replace
        updated = replace(existing, status=status, updated_by=updated_by)
        await self.save(updated)
        return updated

    async def delete(self, id: str) -> None:
        raise NotImplementedError("customer_factors are never hard-deleted")


class MemoryEntities:
    """``ProcessingEntitiesRepository`` surface (in-memory, V3 ADR-V3-001)."""

    def __init__(self, entities: Optional[list[ProcessingEntity]] = None) -> None:
        self._entities: list[ProcessingEntity] = list(entities or [])

    async def get(self, id: str) -> Optional[ProcessingEntity]:
        return next((e for e in self._entities if e.id == id), None)

    async def list_all(self) -> list[ProcessingEntity]:
        return list(self._entities)

    async def list_by_status(self, status: str) -> list[ProcessingEntity]:
        return [e for e in self._entities if e.status == status]

    async def save(self, entity: ProcessingEntity) -> ProcessingEntity:
        for i, existing in enumerate(self._entities):
            if existing.id == entity.id:
                self._entities[i] = entity
                return entity
        self._entities.append(entity)
        return entity

    async def update_status(
        self, id: str, status: str, *, updated_by: Optional[str] = None
    ) -> ProcessingEntity:
        existing = await self.get(id)
        if existing is None:
            raise RuntimeError(f"processing entity {id!r} does not exist")
        from dataclasses import replace
        updated = replace(existing, status=status, updated_by=updated_by)
        await self.save(updated)
        return updated

    async def delete(self, id: str) -> None:
        raise NotImplementedError("processing_entities are never hard-deleted")


class MemoryIssues:
    """``IssuesRepository`` surface (in-memory, V3 ADR-V3-009)."""

    def __init__(self, issues: Optional[list[Issue]] = None) -> None:
        self._issues: list[Issue] = list(issues or [])

    async def get(self, id: str) -> Optional[Issue]:
        return next((i for i in self._issues if i.id == id), None)

    async def list_for_org(self, org_id: str, limit: int = 100, offset: int = 0) -> list[Issue]:
        rows = [
            i for i in self._issues
            if i.organization_id == org_id and i.entity_id is None
        ]
        rows.sort(key=lambda i: (i.created_at or "", i.id), reverse=True)
        return rows[offset:offset + limit]

    async def count_for_org(self, org_id: str) -> int:
        return sum(
            1 for i in self._issues
            if i.organization_id == org_id and i.entity_id is None
        )

    async def list_for_entity(self, entity_id: str) -> list[Issue]:
        return [i for i in self._issues if i.entity_id == entity_id]

    async def list_for_work_item(self, work_item_id: str) -> list[Issue]:
        return [i for i in self._issues if i.work_item_id == work_item_id]

    async def list_open(self, *, organization_id: Optional[str] = None) -> list[Issue]:
        active = ("open", "in_progress", "on_hold", "escalated")
        if organization_id is not None:
            return [
                i for i in self._issues
                if i.status in active and i.organization_id == organization_id
            ]
        return [i for i in self._issues if i.status in active]

    async def save(self, entity: Issue) -> Issue:
        for i, existing in enumerate(self._issues):
            if existing.id == entity.id:
                self._issues[i] = entity
                return entity
        self._issues.append(entity)
        return entity

    async def update_status(
        self,
        id: str,
        status: str,
        *,
        reopened_at: Optional[datetime] = None,
        updated_by: Optional[str] = None,
    ) -> Issue:
        existing = await self.get(id)
        if existing is None:
            raise RuntimeError(f"issue {id!r} does not exist")
        from dataclasses import replace
        updated = replace(
            existing,
            status=status,
            reopened_at=reopened_at if reopened_at is not None else existing.reopened_at,
            updated_by=updated_by,
        )
        await self.save(updated)
        return updated

    async def delete(self, id: str) -> None:
        raise NotImplementedError("issues are never hard-deleted")


def seed_audit_entry(
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    correlation_id: str,
    actor: str = "system",
    ip_address: Optional[str] = None,
) -> AuditEntry:
    """Build an audit entry for seeding/admin tests."""
    return AuditEntry(
        id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor=actor,
        occurred_at=datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc),
        changed_fields={"example": True},
        ip_address=ip_address,
    )


class MemoryAliases:
    """``FactorAliasesRepository`` surface for the admin alias endpoints."""

    def __init__(self, aliases: Optional[list[FactorAlias]] = None) -> None:
        self._aliases: list[FactorAlias] = list(aliases or [])

    async def find_by_alias(self, alias: str, org_id: Optional[str]) -> Optional[FactorAlias]:
        org_matches = [a for a in self._aliases if a.organization_id == org_id and a.alias_text == alias]
        if org_matches:
            return org_matches[0]
        global_matches = [a for a in self._aliases if a.organization_id is None and a.alias_text == alias]
        return global_matches[0] if global_matches else None

    async def get_global_aliases(self) -> list[FactorAlias]:
        return [a for a in self._aliases if a.organization_id is None]

    async def get_org_aliases(self, org_id: str) -> list[FactorAlias]:
        return [a for a in self._aliases if a.organization_id == org_id]

    async def get(self, id: str) -> Optional[FactorAlias]:
        return next((a for a in self._aliases if a.id == id), None)

    async def save(self, entity: FactorAlias) -> FactorAlias:
        for i, existing in enumerate(self._aliases):
            if existing.id == entity.id:
                self._aliases[i] = entity
                return entity
        self._aliases.append(entity)
        return entity

    async def delete(self, id: str) -> None:
        self._aliases = [a for a in self._aliases if a.id != id]


# ---------------------------------------------------------------------------
# Phase 8 operations fakes
# ---------------------------------------------------------------------------


class MemoryStaff:
    """In-memory ``StaffRepository`` surface (staff roster + roles + ops
    aggregates). Stores :class:`StaffProfile` / :class:`StaffRole` rows."""

    def __init__(self) -> None:
        self._profiles: dict[str, StaffProfile] = {}
        self._roles: dict[str, StaffRole] = {}

    def seed_profile(self, profile: StaffProfile) -> None:
        self._profiles[profile.id] = profile

    def seed_role(self, role: StaffRole) -> None:
        self._roles[role.id] = role

    async def get_by_user(self, user_id: str) -> Optional[StaffProfile]:
        return next((p for p in self._profiles.values() if p.user_id == user_id), None)

    async def get(self, id: str) -> Optional[StaffProfile]:
        return self._profiles.get(id)

    async def list_profiles(self) -> list[StaffProfile]:
        return sorted(
            self._profiles.values(), key=lambda p: (p.first_name, p.last_name, p.id)
        )

    async def list_entity_staff(self, entity_id: str) -> list[StaffProfile]:
        return sorted(
            [p for p in self._profiles.values() if p.entity_id == entity_id],
            key=lambda p: (p.first_name, p.last_name, p.id),
        )

    async def create_profile(
        self,
        user_id: str,
        first_name: str,
        last_name: str,
        email: str,
        role_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        max_concurrent_tasks: Optional[int] = None,
        created_by: Optional[str] = None,
    ) -> StaffProfile:
        profile = StaffProfile(
            id=f"sp-{uuid.uuid4()}",
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role_id=role_id,
            entity_id=entity_id,
            max_concurrent_tasks=max_concurrent_tasks,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
        )
        self._profiles[profile.id] = profile
        return profile

    async def update_profile(
        self,
        profile_id: str,
        *,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        role_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        max_concurrent_tasks: Optional[int] = None,
        is_active: Optional[bool] = None,
        updated_by: Optional[str] = None,
    ) -> Optional[StaffProfile]:
        profile = self._profiles.get(profile_id)
        if profile is None:
            return None
        from dataclasses import replace

        updated = replace(
            profile,
            first_name=first_name if first_name is not None else profile.first_name,
            last_name=last_name if last_name is not None else profile.last_name,
            email=email if email is not None else profile.email,
            role_id=role_id if role_id is not None else profile.role_id,
            entity_id=entity_id if entity_id is not None else profile.entity_id,
            max_concurrent_tasks=(
                max_concurrent_tasks
                if max_concurrent_tasks is not None
                else profile.max_concurrent_tasks
            ),
            is_active=is_active if is_active is not None else profile.is_active,
            updated_by=updated_by if updated_by is not None else profile.updated_by,
            updated_at=datetime.now(timezone.utc),
        )
        self._profiles[profile_id] = updated
        return updated

    async def set_entity(
        self, profile_id: str, entity_id: Optional[str], updated_by: Optional[str] = None
    ) -> Optional[StaffProfile]:
        return await self.update_profile(
            profile_id, entity_id=entity_id, updated_by=updated_by
        )

    async def save(self, entity: StaffProfile) -> StaffProfile:
        self._profiles[entity.id] = entity
        return entity

    async def delete(self, id: str) -> None:
        raise NotImplementedError("staff_profiles are never hard-deleted")

    async def get_role(self, role_id: str) -> Optional[StaffRole]:
        return self._roles.get(role_id)

    async def list_roles(self) -> list[StaffRole]:
        return sorted(self._roles.values(), key=lambda r: (r.name, r.id))

    async def ops_dashboard(self) -> dict:
        internal = [p for p in self._profiles.values() if p.entity_id is None]
        entity = [p for p in self._profiles.values() if p.entity_id is not None]
        return {
            "organizations": {"total": 0},
            "entities": {"total": 0, "by_status": {}},
            "staff": {
                "total": len(self._profiles),
                "internal": len(internal),
                "entity_staff": len(entity),
                "by_entity": {},
            },
            "review_queue": {"total": 0, "by_status": {}, "sla_breached": 0},
            "issues": {"total": 0, "by_status": {}},
        }

    async def entity_dashboard(self, entity_id: str) -> dict:
        return {
            "entity": {"id": entity_id, "name": entity_id, "status": "active"},
            "staff_count": len(await self.list_entity_staff(entity_id)),
            "review_queue": {"total": 0, "by_status": {}, "sla_breached": 0},
            "issues": {"total": 0, "by_status": {}},
        }


class MemoryReviewQueue:
    """In-memory ``ReviewQueueRepository`` surface over ``ReviewItem`` rows."""

    def __init__(self) -> None:
        self._items: dict[str, ReviewItem] = {}

    def seed_item(self, item: ReviewItem) -> None:
        self._items[item.id] = item

    async def create_item(
        self,
        org_id: str,
        file_name: str,
        status: str,
        file_id: Optional[str] = None,
        file_url: Optional[str] = None,
        file_type: Optional[str] = None,
        data_type: Optional[str] = None,
        priority: int = 1,
        batch_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        auto_extraction_result: Optional[dict] = None,
        customer_notes: Optional[str] = None,
    ) -> ReviewItem:
        item = ReviewItem(
            id=f"rv-{uuid.uuid4()}",
            organization_id=org_id,
            file_name=file_name,
            status=status,
            priority=priority,
            entity_id=entity_id,
            batch_id=batch_id,
            file_id=file_id,
            file_url=file_url,
            file_type=file_type,
            data_type=data_type,
            auto_extraction_result=auto_extraction_result,
            customer_notes=customer_notes,
            created_at=datetime.now(timezone.utc),
        )
        self._items[item.id] = item
        return item

    async def get(self, review_id: str) -> Optional[ReviewItem]:
        return self._items.get(review_id)

    async def list_items(
        self,
        org_id: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReviewItem]:
        items = list(self._items.values())
        if org_id is not None:
            items = [i for i in items if i.organization_id == org_id]
        if status is not None:
            items = [i for i in items if i.status == status]
        if assigned_to is not None:
            items = [i for i in items if i.assigned_to == assigned_to]
        items.sort(
            key=lambda i: (
                i.priority,
                i.created_at or datetime.min.replace(tzinfo=timezone.utc),
            )
        )
        return items[offset : offset + limit]

    async def assign(
        self,
        review_id: str,
        assigned_to: str,
        assigned_by: str,
        sla_deadline: Optional[str] = None,
    ) -> Optional[ReviewItem]:
        item = self._items.get(review_id)
        if item is None:
            return None
        from dataclasses import replace

        updated = replace(
            item,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            status="assigned",
            sla_deadline=sla_deadline or item.sla_deadline,
        )
        self._items[review_id] = updated
        return updated

    async def complete(
        self,
        review_id: str,
        manual_extraction_result: dict,
        review_time_seconds: int,
    ) -> Optional[ReviewItem]:
        item = self._items.get(review_id)
        if item is None:
            return None
        from dataclasses import replace

        updated = replace(
            item,
            status="completed",
            manual_extraction_result=manual_extraction_result,
            review_time_seconds=review_time_seconds,
            completed_at=datetime.now(timezone.utc),
        )
        self._items[review_id] = updated
        return updated

    async def update_status(self, review_id: str, status: str) -> Optional[ReviewItem]:
        item = self._items.get(review_id)
        if item is None:
            return None
        from dataclasses import replace

        updated = replace(item, status=status)
        self._items[review_id] = updated
        return updated

    async def save(self, entity: ReviewItem) -> ReviewItem:
        self._items[entity.id] = entity
        return entity

    async def delete(self, id: str) -> None:
        return None


class MemoryQueueSettings:
    """In-memory ``QueueSettingsRepository`` surface (single settings row)."""

    def __init__(self) -> None:
        self._settings = QueueSettings(
            max_reviews_per_staff=5,
            sla_hours=48,
            auto_assign_enabled=True,
            escalation_hours=24,
            priority_weights={"high": 1.0, "medium": 0.6, "low": 0.3},
        )

    async def get_settings(self) -> QueueSettings:
        return self._settings

    async def update_settings(
        self,
        max_reviews_per_staff: Optional[int],
        sla_hours: Optional[int],
        auto_assign_enabled: Optional[bool],
        escalation_hours: Optional[int],
        priority_weights: Optional[dict],
        updated_by: Optional[str],
    ) -> QueueSettings:
        from dataclasses import replace

        current = self._settings
        self._settings = replace(
            current,
            max_reviews_per_staff=(
                max_reviews_per_staff
                if max_reviews_per_staff is not None
                else current.max_reviews_per_staff
            ),
            sla_hours=sla_hours if sla_hours is not None else current.sla_hours,
            auto_assign_enabled=(
                auto_assign_enabled
                if auto_assign_enabled is not None
                else current.auto_assign_enabled
            ),
            escalation_hours=(
                escalation_hours
                if escalation_hours is not None
                else current.escalation_hours
            ),
            priority_weights=(
                dict(priority_weights)
                if priority_weights is not None
                else current.priority_weights
            ),
            updated_by=updated_by,
        )
        return self._settings

    async def get(self, id: str):
        return await self.get_settings()

    async def save(self, entity: QueueSettings) -> QueueSettings:
        self._settings = entity
        return entity

    async def delete(self, id: str) -> None:
        return None


def staff_user(
    user_id: str = "u-staff",
    *,
    email: str = "staff@carbontally.test",
    permissions: Optional[dict] = None,
    entity_id: Optional[str] = None,
    role_name: str = "staff",
) -> AuthUser:
    """An authenticated CarbonTally staff identity (internal by default)."""
    return AuthUser(
        user_id=user_id,
        email=email,
        role="staff",
        role_name=role_name,
        permissions=permissions or {},
        is_active=True,
        is_staff=True,
        is_admin=False,
        entity_id=entity_id,
    )


def entity_operator_user(entity_id: str, user_id: str = "u-entity-op") -> AuthUser:
    """An authenticated processing-entity staff identity."""
    return AuthUser(
        user_id=user_id,
        email=f"{user_id}@entity.test",
        role="entity_staff",
        role_name="entity_operator",
        permissions={},
        is_active=True,
        is_staff=True,
        is_admin=False,
        entity_id=entity_id,
    )

