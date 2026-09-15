"""Phase 8 B1 — Disclosure Model foundation repositories (contract §22/§24).

Persistence for the 11 B1 ``public.disclosure_*`` tables. B1 API exposure is
**deferred**: this module is the domain/data boundary only (no endpoints).

* Reuse the established repository pattern (:class:`AbstractRepository`,
  service-role ``asyncpg`` pool, row mappers, ``$n`` placeholders).
* Application-layer authorization is the boundary — RLS is defence-in-depth only
  (the production RLS baseline is incomplete). Cross-tenant and immutability
  invariants are enforced here via :mod:`domain.disclosure`.
* Additive / idempotent — the reference seed is ``ON CONFLICT DO NOTHING``.
* Audit: every B1 write emits one append-only ``audit_trail`` entry through the
  existing :class:`data.audit.AuditRepository` (contract §24/§26) — no new audit
  table, category or subsystem. Emission is best-effort, mirroring the
  ``api.audit_helpers`` precedent: audit never breaks the write.
* SQL parameter typing: a positional parameter reused in more than one context
  carries an explicit cast where PostgreSQL cannot otherwise infer a single type
  (``$9::uuid`` / ``$6::varchar`` below). Removing a cast reintroduces the
  ``AmbiguousParameterError`` defect confirmed by gate V1
  (``CT-P8-B1-V1-INDEPENDENT-VERIFICATION-20260912-014``, F1/F2).
* No B2/B3/B4 — no ``evidence_line_items``, no ``source_line_item_id``, no
  intensity tables, no narrative tables.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import asyncpg

from core.logging import get_logger
from data.audit import AuditRepository
from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.audit import ACTOR_SYSTEM, AuditEntry
from domain.disclosure import (
    AUDIT_APPLICABILITY_ASSESSED,
    AUDIT_EVIDENCE_LINKED,
    AUDIT_FRAMEWORK_SEEDED,
    AUDIT_PURPOSE_SEEDED,
    AUDIT_REPORT_BOUND,
    AUDIT_VALUE_MATERIALISED,
    DisclosureViolation,
    assert_period_order,
    assert_periods_agree,
    assert_report_version_mutable,
    assert_same_organization,
    validate_applicability_status,
    validate_consolidation_approach,
    validate_evidence_completeness,
    validate_requirement_class,
    validate_value_status,
)

logger = get_logger(__name__)

#: Actor recorded for system-derived B1 writes (materialisation, bindings, the
#: reference seed). Actor-supplied writes record the acting user instead.
_SYSTEM_ACTOR = "system"

_FRAMEWORK_COLUMNS = "id, code, name, publisher, kind, is_primary_foundation, description"
_PURPOSE_COLUMNS = "id, code, name, is_statutory_positioned, description"
_FRAMEWORK_VERSION_COLUMNS = (
    "id, framework_id, version_label, legal_reference, source_tier, source_url, "
    "authoritative_source_date, status, applicable_from, applicable_to, verified_at"
)
_REQUIREMENT_COLUMNS = (
    "id, framework_version_id, requirement_code, official_identifier, identifier_status, "
    "title, requirement_class, is_quantitative, value_kind, carbontally_capability, display_order"
)


def _as_dict(row: Any) -> Optional[dict]:
    """Normalise an ``asyncpg.Record`` to a JSON-safe dict (ISO dates, str UUIDs)."""
    if row is None:
        return None
    out = dict(row)
    for key, value in list(out.items()):
        if value is not None and hasattr(value, "isoformat") and not isinstance(value, str):
            out[key] = value.isoformat()
        elif key == "id" or key.endswith("_id"):
            if value is not None:
                out[key] = str(value)
    return out


async def _record_audit(
    pool: asyncpg.Pool,
    *,
    action: str,
    entity_type: str,
    entity_id: Optional[str],
    actor: str = _SYSTEM_ACTOR,
    organization_id: Optional[str] = None,
    before: Optional[dict] = None,
    after: Optional[dict] = None,
) -> None:
    """Append ONE audit entry for a B1 write (contract §24/§26).

    Reuses the existing audit mechanism verbatim —
    :class:`data.audit.AuditRepository` over ``public.audit_trail`` — so B1 adds no
    audit table, category or subsystem. The action names are the ``report:…``
    constants in :mod:`domain.disclosure`, which the existing taxonomy classifies
    as ``CAT_REPORT`` entries.

    Emission is **best-effort**: a failure is logged and swallowed so audit can
    never break (or roll back) the B1 write — the ``api.audit_helpers`` precedent.
    Payloads stay compact and non-sensitive: identifiers/statuses only, never
    credentials, secrets, signed URLs or document payloads.
    """
    if not entity_id:
        return
    identifier = str(entity_id)
    entry = AuditEntry(
        id=str(uuid.uuid4()),
        correlation_id=identifier,
        entity_type=entity_type,
        entity_id=identifier,
        action=action,
        actor=actor,
        occurred_at=datetime.now(timezone.utc),
        before=before,
        after=after,
        actor_type=ACTOR_SYSTEM if actor == _SYSTEM_ACTOR else None,
        organization_id=organization_id,
    )
    try:
        await AuditRepository(pool).record(entry)
    except Exception:  # noqa: BLE001 — audit must never break the B1 write
        logger.exception(
            "disclosure audit (%s) failed for %s %s", action, entity_type, identifier
        )


class DisclosureCatalogRepository(AbstractRepository[dict]):
    """Global (platform-controlled) catalogue tables; read-any-authenticated."""

    async def _count(self, table: str) -> int:
        row = await self._fetch_one(f"SELECT count(*)::int AS n FROM public.{table}")
        return int(row["n"]) if row is not None else 0

    async def seed_reference_identities(self) -> dict[str, int]:
        """Idempotently seed framework + report-purpose identities (PQ-6).

        Identities ONLY (D1 / D6-R). Framework-VERSION rows are deliberately NOT
        seeded (PQ-6). Safe to re-run — no duplicates.
        """
        before_f = await self._count("disclosure_frameworks")
        before_p = await self._count("disclosure_report_purposes")
        # ``RETURNING`` yields only the rows actually inserted, so an idempotent
        # re-run audits nothing (no write happened — contract §26 audits writes).
        framework_rows = await self._fetch_all(
            """
            INSERT INTO public.disclosure_frameworks
                (code, name, publisher, kind, is_primary_foundation)
            VALUES ('GHG_PROTOCOL', 'GHG Protocol Corporate Standard',
                    'GHG Protocol / WRI & WBCSD', 'accounting_foundation', TRUE),
                   ('UK_SECR', 'UK Streamlined Energy and Carbon Reporting',
                    'UK Government (DESNZ)', 'jurisdiction_statute', FALSE),
                   ('ESRS_E1', 'ESRS E1 Climate Change',
                    'European Commission (EFRAG)', 'eu_standard', FALSE)
            ON CONFLICT (code) DO NOTHING
            RETURNING id, code
            """
        )
        purpose_rows = await self._fetch_all(
            """
            INSERT INTO public.disclosure_report_purposes
                (code, name, is_statutory_positioned)
            VALUES ('ANNUAL_CARBON', 'Annual Carbon Report', FALSE),
                   ('MANAGEMENT', 'Management Report', FALSE),
                   ('UK_SECR', 'UK SECR Report', TRUE),
                   ('ESRS_E1_QUANT', 'ESRS E1 Quantitative Report', TRUE)
            ON CONFLICT (code) DO NOTHING
            RETURNING id, code
            """
        )
        for row in framework_rows:
            await _record_audit(
                self._pool,
                action=AUDIT_FRAMEWORK_SEEDED,
                entity_type="disclosure_frameworks",
                entity_id=str(row["id"]),
                after={"code": str(row["code"])},
            )
        for row in purpose_rows:
            await _record_audit(
                self._pool,
                action=AUDIT_PURPOSE_SEEDED,
                entity_type="disclosure_report_purposes",
                entity_id=str(row["id"]),
                after={"code": str(row["code"])},
            )
        return {
            "frameworks_inserted": (await self._count("disclosure_frameworks")) - before_f,
            "purposes_inserted": (await self._count("disclosure_report_purposes")) - before_p,
        }

    async def list_frameworks(self) -> list[dict]:
        rows = await self._fetch_all(
            f"SELECT {_FRAMEWORK_COLUMNS} FROM public.disclosure_frameworks ORDER BY code"
        )
        return [_as_dict(r) for r in rows]  # type: ignore[misc]

    async def get_framework_by_code(self, code: str) -> Optional[dict]:
        row = await self._fetch_one(
            f"SELECT {_FRAMEWORK_COLUMNS} FROM public.disclosure_frameworks WHERE code = $1",
            code,
        )
        return _as_dict(row)

    async def list_report_purposes(self) -> list[dict]:
        rows = await self._fetch_all(
            f"SELECT {_PURPOSE_COLUMNS} FROM public.disclosure_report_purposes ORDER BY code"
        )
        return [_as_dict(r) for r in rows]  # type: ignore[misc]

    async def list_framework_versions(self, framework_id: str) -> list[dict]:
        rows = await self._fetch_all(
            f"SELECT {_FRAMEWORK_VERSION_COLUMNS} FROM public.disclosure_framework_versions "
            "WHERE framework_id = $1 ORDER BY version_label",
            framework_id,
        )
        return [_as_dict(r) for r in rows]  # type: ignore[misc]

    async def list_requirements(self, framework_version_id: str) -> list[dict]:
        rows = await self._fetch_all(
            f"SELECT {_REQUIREMENT_COLUMNS} FROM public.disclosure_requirement_versions "
            "WHERE framework_version_id = $1 ORDER BY display_order NULLS LAST, requirement_code",
            framework_version_id,
        )
        return [_as_dict(r) for r in rows]  # type: ignore[misc]

    async def get(self, id: str) -> Optional[dict]:
        return None

    async def save(self, entity: dict) -> dict:
        return entity

    async def delete(self, id: str) -> None:
        return None

class DisclosureRepository(AbstractRepository[dict]):
    """Organisation-scoped B1 tables + app-layer cross-tenant/immutability guards."""

    # -- ownership resolution helpers ----------------------------------------
    async def report_organization(self, report_id: str) -> Optional[str]:
        """The organisation that owns a report instance (instance spine)."""
        row = await self._fetch_one(
            "SELECT organization_id FROM public.report_generation_queue WHERE id = $1",
            report_id,
        )
        return str(row["organization_id"]) if row is not None else None

    async def report_version_owner(self, report_version_id: str) -> Optional[dict]:
        """``{organization_id, status}`` for a report VERSION, or ``None``."""
        row = await self._fetch_one(
            """
            SELECT rg.organization_id AS organization_id, rv.status AS status
            FROM public.report_versions rv
            JOIN public.report_generation_queue rg ON rg.id = rv.report_id
            WHERE rv.id = $1
            """,
            report_version_id,
        )
        if row is None:
            return None
        return {"organization_id": str(row["organization_id"]), "status": str(row["status"])}

    # -- applicability -------------------------------------------------------
    async def create_applicability_assessment(
        self,
        *,
        organization_id: str,
        framework_version_id: str,
        reporting_year: int,
        reporting_period_start: Any,
        reporting_period_end: Any,
        characteristic_snapshot: dict,
        assessed_status: str,
        basis: str,
        determined_by: Optional[str] = None,
        version: int = 1,
    ) -> dict:
        """Insert an append-only, period-dated applicability assessment (D13/APPL)."""
        validate_applicability_status(assessed_status)
        assert_period_order(reporting_period_start, reporting_period_end)
        if not (basis or "").strip():
            raise DisclosureViolation("an applicability assessment requires a cited basis")
        row = await self._fetch_one(
            """
            INSERT INTO public.disclosure_applicability_assessments
                (organization_id, framework_version_id, reporting_year,
                 reporting_period_start, reporting_period_end, characteristic_snapshot,
                 assessed_status, basis, determined_by, determined_at, version, created_by)
            -- ``$9::uuid`` is REQUIRED: ``$9`` is reused as ``determined_by``, as the
            -- ``IS NULL`` test and as ``created_by``, so PostgreSQL cannot infer a
            -- single type and raises "could not determine data type of parameter
            -- $9" (V1 F1). Do not "simplify" these casts away.
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6::jsonb, $7, $8, $9::uuid,
                    CASE WHEN $9::uuid IS NULL THEN NULL ELSE now() END, $10, $9::uuid)
            RETURNING id, organization_id, framework_version_id, reporting_year,
                      reporting_period_start, reporting_period_end, assessed_status, basis, version
            """,
            organization_id,
            framework_version_id,
            reporting_year,
            reporting_period_start,
            reporting_period_end,
            dumps_jsonb(characteristic_snapshot),
            assessed_status,
            basis,
            determined_by,
            version,
        )
        result = _as_dict(row)
        if result is None:  # pragma: no cover - INSERT … RETURNING always yields a row
            raise RuntimeError("applicability assessment insert returned no row")
        await _record_audit(
            self._pool,
            action=AUDIT_APPLICABILITY_ASSESSED,
            entity_type="disclosure_applicability_assessments",
            entity_id=str(result["id"]),
            # ``determined_by`` NULL means "system" (contract §9.8) — the audit
            # actor mirrors that so the entry is attributable either way.
            actor=determined_by or _SYSTEM_ACTOR,
            organization_id=organization_id,
            after={
                "framework_version_id": framework_version_id,
                "reporting_year": reporting_year,
                "assessed_status": assessed_status,
            },
        )
        return result

    async def get_applicability_assessment(self, assessment_id: str) -> Optional[dict]:
        row = await self._fetch_one(
            """
            SELECT id, organization_id, framework_version_id, reporting_year,
                   reporting_period_start, reporting_period_end, assessed_status, basis, version
            FROM public.disclosure_applicability_assessments WHERE id = $1
            """,
            assessment_id,
        )
        return _as_dict(row)

    # -- report-instance binding --------------------------------------------
    async def create_instance_binding(
        self,
        *,
        organization_id: str,
        report_id: str,
        purpose_version_id: str,
        reporting_period_start: Any,
        reporting_period_end: Any,
        consolidation_approach: str = "OPERATIONAL_CONTROL",
        applicability_assessment_id: Optional[str] = None,
    ) -> dict:
        """Bind a report instance to its purpose/period/consolidation (DM-2/DM-3/GP-CONS).

        Enforces (a) the report belongs to ``organization_id`` and (b) the PQ-2
        period agreement invariant against a referenced assessment.
        """
        validate_consolidation_approach(consolidation_approach)
        assert_period_order(reporting_period_start, reporting_period_end)
        owner = await self.report_organization(report_id)
        assert_same_organization(organization_id, owner)
        if applicability_assessment_id is not None:
            assessment = await self._fetch_one(
                "SELECT organization_id, reporting_period_start, reporting_period_end "
                "FROM public.disclosure_applicability_assessments WHERE id = $1",
                applicability_assessment_id,
            )
            if assessment is None:
                raise DisclosureViolation("referenced applicability assessment does not exist")
            assert_same_organization(organization_id, str(assessment["organization_id"]))
            assert_periods_agree(
                binding_period_start=reporting_period_start,
                binding_period_end=reporting_period_end,
                assessment_period_start=assessment["reporting_period_start"],
                assessment_period_end=assessment["reporting_period_end"],
            )
        row = await self._fetch_one(
            """
            INSERT INTO public.disclosure_report_instance_binding
                (organization_id, report_id, purpose_version_id, applicability_assessment_id,
                 reporting_period_start, reporting_period_end, consolidation_approach)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (report_id) DO UPDATE SET
                purpose_version_id = EXCLUDED.purpose_version_id,
                applicability_assessment_id = EXCLUDED.applicability_assessment_id,
                reporting_period_start = EXCLUDED.reporting_period_start,
                reporting_period_end = EXCLUDED.reporting_period_end,
                consolidation_approach = EXCLUDED.consolidation_approach,
                updated_at = now()
            RETURNING id, organization_id, report_id, purpose_version_id,
                      applicability_assessment_id, reporting_period_start, reporting_period_end,
                      consolidation_approach
            """,
            organization_id,
            report_id,
            purpose_version_id,
            applicability_assessment_id,
            reporting_period_start,
            reporting_period_end,
            consolidation_approach,
        )
        result = _as_dict(row)
        if result is None:  # pragma: no cover - INSERT … RETURNING always yields a row
            raise RuntimeError("report instance binding insert returned no row")
        await _record_audit(
            self._pool,
            action=AUDIT_REPORT_BOUND,
            entity_type="disclosure_report_instance_binding",
            entity_id=str(result["id"]),
            organization_id=organization_id,
            after={
                "report_id": report_id,
                "purpose_version_id": purpose_version_id,
                "reporting_period_start": str(reporting_period_start),
                "reporting_period_end": str(reporting_period_end),
                "consolidation_approach": consolidation_approach,
            },
        )
        return result

    async def get_instance_binding(self, report_id: str) -> Optional[dict]:
        row = await self._fetch_one(
            "SELECT id, organization_id, report_id, purpose_version_id, "
            "applicability_assessment_id, reporting_period_start, reporting_period_end, "
            "consolidation_approach FROM public.disclosure_report_instance_binding "
            "WHERE report_id = $1",
            report_id,
        )
        return _as_dict(row)

    # -- disclosure values ---------------------------------------------------
    async def upsert_disclosure_value(
        self,
        *,
        organization_id: str,
        report_version_id: str,
        requirement_version_id: str,
        effective_class: str,
        value_kind: str,
        reporting_year: int,
        value_status: str = "PENDING",
        requirement_mapping_id: Optional[str] = None,
        numeric_value: Any = None,
        value_unit: Optional[str] = None,
        text_value: Optional[str] = None,
        source_kind: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> dict:
        """Project one disclosure value for a report version (PQ-3/PQ-4).

        Enforces cross-tenant integrity and report-version immutability at the
        application layer. One value per (report_version, requirement_version).
        """
        validate_value_status(value_status)
        validate_requirement_class(effective_class)
        owner = await self.report_version_owner(report_version_id)
        if owner is None:
            raise DisclosureViolation("unknown report version")
        assert_same_organization(organization_id, owner["organization_id"])
        assert_report_version_mutable(owner["status"])
        # Prior materialisation state, for the audit entry's before/after (contract
        # §26: every write records before/after). One indexed lookup on the unique
        # key; ``None`` means this call inserts the first value for the pair.
        previous = await self._fetch_one(
            "SELECT value_status FROM public.disclosure_values "
            "WHERE report_version_id = $1 AND requirement_version_id = $2",
            report_version_id,
            requirement_version_id,
        )
        row = await self._fetch_one(
            """
            INSERT INTO public.disclosure_values
                (organization_id, report_version_id, requirement_version_id,
                 requirement_mapping_id, effective_class, value_status, value_kind,
                 numeric_value, value_unit, text_value, reporting_year, source_kind, reason,
                 computed_at)
            -- ``$6::varchar`` is REQUIRED: ``$6`` is compared to the text literal
            -- ``'RESOLVED'`` and assigned to the ``varchar`` column ``value_status``,
            -- so PostgreSQL otherwise deduces two types and raises "inconsistent
            -- types deduced for parameter $6 — text versus character varying"
            -- (V1 F2). Do not "simplify" these casts away.
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5, $6::varchar, $7, $8, $9,
                    $10, $11, $12, $13,
                    CASE WHEN $6::varchar = 'RESOLVED' THEN now() ELSE NULL END)
            ON CONFLICT (report_version_id, requirement_version_id) DO UPDATE SET
                requirement_mapping_id = EXCLUDED.requirement_mapping_id,
                effective_class = EXCLUDED.effective_class,
                value_status = EXCLUDED.value_status,
                value_kind = EXCLUDED.value_kind,
                numeric_value = EXCLUDED.numeric_value,
                value_unit = EXCLUDED.value_unit,
                text_value = EXCLUDED.text_value,
                source_kind = EXCLUDED.source_kind,
                reason = EXCLUDED.reason,
                computed_at = EXCLUDED.computed_at,
                updated_at = now()
            RETURNING id, organization_id, report_version_id, requirement_version_id,
                      effective_class, value_status, value_kind, reporting_year
            """,
            organization_id,
            report_version_id,
            requirement_version_id,
            requirement_mapping_id,
            effective_class,
            value_status,
            value_kind,
            numeric_value,
            value_unit,
            text_value,
            reporting_year,
            source_kind,
            reason,
        )
        result = _as_dict(row)
        if result is None:  # pragma: no cover - INSERT … RETURNING always yields a row
            raise RuntimeError("disclosure value upsert returned no row")
        await _record_audit(
            self._pool,
            action=AUDIT_VALUE_MATERIALISED,
            entity_type="disclosure_values",
            entity_id=str(result["id"]),
            organization_id=organization_id,
            before={"value_status": str(previous["value_status"])} if previous else None,
            after={
                "effective_class": effective_class,
                "value_status": value_status,
                "value_kind": value_kind,
                "reporting_year": reporting_year,
            },
        )
        return result

    async def get_disclosure_value(self, value_id: str) -> Optional[dict]:
        row = await self._fetch_one(
            "SELECT id, organization_id, report_version_id, requirement_version_id, "
            "effective_class, value_status, value_kind, reporting_year FROM public.disclosure_values "
            "WHERE id = $1",
            value_id,
        )
        return _as_dict(row)

    async def delete_disclosure_value(self, value_id: str) -> None:
        """Delete a value — permitted only while its report version is mutable (PQ-4)."""
        row = await self._fetch_one(
            """
            SELECT rv.status AS status
            FROM public.disclosure_values dv
            JOIN public.report_versions rv ON rv.id = dv.report_version_id
            WHERE dv.id = $1
            """,
            value_id,
        )
        if row is None:
            return
        assert_report_version_mutable(str(row["status"]))
        await self._execute("DELETE FROM public.disclosure_values WHERE id = $1", value_id)

    # -- value → evidence ----------------------------------------------------
    async def link_value_evidence(
        self,
        *,
        organization_id: str,
        disclosure_value_id: str,
        calculation_snapshot_id: Optional[str] = None,
        emissions_log_id: Optional[str] = None,
        source_item_id: Optional[str] = None,
        source_file_id: Optional[str] = None,
        source_page: Optional[int] = None,
        evidence_completeness: Optional[str] = None,
        contribution_share: Any = None,
        source_line_item_id: Optional[str] = None,
    ) -> dict:
        """Link a value to EXISTING evidence rows (references, never copies; DM-7).

        B2 §9.3 — ``source_line_item_id`` is an **additive optional keyword**:
        existing callers keep working unchanged. B2 §9.2 — when it is not
        supplied but a calculation snapshot is, the finer line fact is taken
        **from the snapshot** (never invented, never guessed), so the
        application-enforced consistency invariant of §8.3 holds for every
        caller.
        """
        if evidence_completeness is not None:
            validate_evidence_completeness(evidence_completeness)
        value_row = await self._fetch_one(
            "SELECT organization_id FROM public.disclosure_values WHERE id = $1",
            disclosure_value_id,
        )
        if value_row is None:
            raise DisclosureViolation("disclosure value does not exist")
        assert_same_organization(organization_id, str(value_row["organization_id"]))
        if source_line_item_id is None and calculation_snapshot_id is not None:
            snapshot_row = await self._fetch_one(
                "SELECT source_line_item_id FROM public.calculation_snapshots "
                "WHERE id = $1",
                calculation_snapshot_id,
            )
            if snapshot_row is not None and snapshot_row["source_line_item_id"]:
                source_line_item_id = str(snapshot_row["source_line_item_id"])
        if calculation_snapshot_id is not None:
            # Calculated-evidence link: UNIQUE (disclosure_value_id,
            # calculation_snapshot_id) makes a repeated link an upsert.
            row = await self._fetch_one(
                """
                INSERT INTO public.disclosure_value_evidence
                    (organization_id, disclosure_value_id, calculation_snapshot_id, emissions_log_id,
                     source_item_id, source_file_id, source_page, evidence_completeness, contribution_share,
                     source_line_item_id)
                VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5::uuid, $6::uuid, $7, $8, $9, $10::uuid)
                ON CONFLICT (disclosure_value_id, calculation_snapshot_id) DO UPDATE SET
                    emissions_log_id = EXCLUDED.emissions_log_id,
                    source_item_id = EXCLUDED.source_item_id,
                    source_file_id = EXCLUDED.source_file_id,
                    source_page = EXCLUDED.source_page,
                    evidence_completeness = EXCLUDED.evidence_completeness,
                    contribution_share = EXCLUDED.contribution_share,
                    source_line_item_id = EXCLUDED.source_line_item_id
                RETURNING id, organization_id, disclosure_value_id, calculation_snapshot_id,
                          source_item_id, source_file_id, source_page, evidence_completeness,
                          source_line_item_id
                """,
                organization_id,
                disclosure_value_id,
                calculation_snapshot_id,
                emissions_log_id,
                source_item_id,
                source_file_id,
                source_page,
                evidence_completeness,
                contribution_share,
                source_line_item_id,
            )
        else:
            # A NULL calculation_snapshot_id can never match that unique key (NULLs
            # are distinct in PostgreSQL), so a repeated link previously inserted a
            # duplicate (V1 F3; contract §25 "re-linking = no duplicates").
            # Re-linking the SAME evidence REFERENCE is made idempotent explicitly
            # here; the correction migration additionally creates
            # ``uq_dve_reference_nullsafe`` as the database-level guarantee.
            #
            # Reference identity = the four evidence columns. ``source_page`` /
            # ``evidence_completeness`` / ``contribution_share`` are that reference's
            # mutable payload, so re-linking updates them instead of adding a row.
            row = await self._fetch_one(
                """
                UPDATE public.disclosure_value_evidence SET
                    source_page = $2,
                    evidence_completeness = $3,
                    contribution_share = $4,
                    source_line_item_id = $8::uuid
                WHERE disclosure_value_id = $1::uuid
                  AND calculation_snapshot_id IS NULL
                  AND emissions_log_id IS NOT DISTINCT FROM $5::uuid
                  AND source_item_id IS NOT DISTINCT FROM $6::uuid
                  AND source_file_id IS NOT DISTINCT FROM $7::uuid
                RETURNING id, organization_id, disclosure_value_id, calculation_snapshot_id,
                          source_item_id, source_file_id, source_page, evidence_completeness,
                          source_line_item_id
                """,
                disclosure_value_id,
                source_page,
                evidence_completeness,
                contribution_share,
                emissions_log_id,
                source_item_id,
                source_file_id,
                source_line_item_id,
            )
            if row is None:
                row = await self._fetch_one(
                    """
                    INSERT INTO public.disclosure_value_evidence
                        (organization_id, disclosure_value_id, calculation_snapshot_id, emissions_log_id,
                         source_item_id, source_file_id, source_page, evidence_completeness, contribution_share,
                         source_line_item_id)
                    VALUES ($1::uuid, $2::uuid, NULL, $3::uuid, $4::uuid, $5::uuid, $6, $7, $8, $9::uuid)
                    RETURNING id, organization_id, disclosure_value_id, calculation_snapshot_id,
                              source_item_id, source_file_id, source_page, evidence_completeness,
                              source_line_item_id
                    """,
                    organization_id,
                    disclosure_value_id,
                    emissions_log_id,
                    source_item_id,
                    source_file_id,
                    source_page,
                    evidence_completeness,
                    contribution_share,
                    source_line_item_id,
                )
        result = _as_dict(row)
        if result is None:  # pragma: no cover - both branches RETURN a row
            raise RuntimeError("disclosure evidence link returned no row")
        await _record_audit(
            self._pool,
            action=AUDIT_EVIDENCE_LINKED,
            entity_type="disclosure_value_evidence",
            entity_id=str(result["id"]),
            organization_id=organization_id,
            after={
                "disclosure_value_id": disclosure_value_id,
                "calculation_snapshot_id": calculation_snapshot_id,
                "evidence_completeness": evidence_completeness,
            },
        )
        return result

    # -- AbstractRepository contract ----------------------------------------
    async def get(self, id: str) -> Optional[dict]:
        return await self.get_disclosure_value(id)

    async def save(self, entity: dict) -> dict:
        return entity

    async def delete(self, id: str) -> None:
        await self.delete_disclosure_value(id)





