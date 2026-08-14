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
from domain.calculation import (
    CalculationSnapshot,
    EmissionLog,
    EmissionsAggregate,
)
from domain.factor import EmissionFactor
from domain.matching import FactorAlias
from domain.organization import Asset, Facility, Organization, OrganizationMetadata
from domain.provider import ImportBatch


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
    ) -> CalculationSnapshot:
        self._snapshots[snapshot.id] = snapshot
        return snapshot

    async def create(
        self,
        org_id: str,
        factor_id: str,
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
    """Satisfies ``OrgSource`` (get, get_metadata, get_facilities, get_assets)."""

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

    async def get(self, org_id: str) -> Optional[Organization]:
        return self._orgs.get(org_id)

    async def get_metadata(self, org_id: str) -> Optional[OrganizationMetadata]:
        return self._metadata.get(org_id)

    async def get_facilities(self, org_id: str) -> list[Facility]:
        return self._facilities.get(org_id, [])

    async def get_assets(self, org_id: str) -> list[Asset]:
        return self._assets.get(org_id, [])


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
    """Satisfies ``ReportsStore`` (create_generation_request + complete_generation)."""

    def __init__(self) -> None:
        self._reports: dict[str, dict[str, Any]] = {}

    async def create_generation_request(
        self, org_id: str, report_type: str, year: int, template_id: Optional[str]
    ) -> Any:
        from domain.report import GeneratedReport

        report = GeneratedReport(
            id=str(uuid.uuid4()),
            organization_id=org_id,
            report_type=report_type,
            reporting_year=year,
            storage_url="",
            file_size_bytes=0,
            generated_at=datetime.now(timezone.utc),
            page_count=0,
        )
        self._reports[report.id] = {"report": report, "content": None}
        return report

    async def complete_generation(
        self,
        report_id: str,
        storage_url: str,
        file_size: int,
        page_count: int,
        content: Optional[dict[str, Any]] = None,
    ) -> Any:
        from domain.report import GeneratedReport

        stored = self._reports[report_id]["report"]
        completed = GeneratedReport(
            id=stored.id,
            organization_id=stored.organization_id,
            report_type=stored.report_type,
            reporting_year=stored.reporting_year,
            storage_url=storage_url,
            file_size_bytes=file_size,
            generated_at=stored.generated_at,
            page_count=page_count,
        )
        self._reports[report_id] = {"report": completed, "content": content}
        return completed

    async def get(self, id: str) -> Optional[Any]:
        stored = self._reports.get(id)
        return stored["report"] if stored is not None else None

    def stored_content(self, report_id: str) -> Optional[dict[str, Any]]:
        stored = self._reports.get(report_id)
        return stored["content"] if stored is not None else None


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

    def bundle(self):
        from api.dependencies import RepositoryBundle

        return RepositoryBundle(
            factors=self.factors,
            logs=self.logs,
            organizations=self.organizations,
            imports=self.imports,
            reports=self.reports,
            audit=self.audit,
            events=self.events,
            aliases=self.aliases,
        )


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

