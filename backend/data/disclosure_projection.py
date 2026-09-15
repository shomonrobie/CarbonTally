"""Phase 8 B3 — disclosure projection data layer (repositories).

Read models B3 needs (authoritative rows, evidence coverage, the B2 value→line
join, the intensity catalogue) and the org-scoped intensity-ratio write. It
performs **no calculation** and never writes to an authoritative table: values
are persisted through the B1 :class:`data.disclosure.DisclosureRepository`.
"""
from __future__ import annotations

from typing import Any, Optional

import asyncpg

from data.base import AbstractRepository


def _rows(records: Any) -> list[dict]:
    return [dict(record) for record in records]


class DisclosureProjectionRepository(AbstractRepository[dict]):
    """B3 read models + intensity catalogue/selection access."""

    # -- AbstractRepository compliance (this repository is a read model) ---
    async def get(self, id: str) -> Optional[dict]:
        return None

    async def save(self, entity: dict) -> dict:
        return entity

    async def delete(self, id: str) -> None:
        return None

    # -- report context ------------------------------------------------------
    async def report_context(self, report_version_id: str) -> Optional[dict]:
        """``{organization_id, report_id, status, reporting_year}`` for a version."""
        row = await self._fetch_one(
            """
            SELECT rg.organization_id AS organization_id, rv.report_id AS report_id,
                   rv.status AS status, rg.reporting_year AS reporting_year
            FROM public.report_versions rv
            JOIN public.report_generation_queue rg ON rg.id = rv.report_id
            WHERE rv.id = $1
            """,
            report_version_id,
        )
        if row is None:
            return None
        return {
            "organization_id": str(row["organization_id"]),
            "report_id": str(row["report_id"]),
            "status": str(row["status"]),
            "reporting_year": int(row["reporting_year"]),
        }

    # -- requirement set for a purpose ---------------------------------------
    async def list_purpose_requirements(self, purpose_version_id: str) -> list[dict]:
        """The ordered requirement set of a purpose version (DM-2 projection)."""
        return _rows(
            await self._fetch_all(
                """
                SELECT rv.id AS requirement_version_id, rv.requirement_code,
                       rv.requirement_class, rv.value_kind, rv.is_quantitative,
                       rv.unit_hint, rv.scope_hint, rv.carbontally_capability,
                       rv.official_identifier, rv.identifier_status,
                       pr.display_order, pr.required_for_finalisation,
                       pr.purpose_specific_class
                FROM public.disclosure_purpose_requirements pr
                JOIN public.disclosure_requirement_versions rv
                     ON rv.id = pr.requirement_version_id
                WHERE pr.purpose_version_id = $1
                ORDER BY pr.display_order NULLS LAST, rv.requirement_code
                """,
                purpose_version_id,
            )
        )

    # -- authoritative projection inputs -------------------------------------
    async def load_calculation_rows(
        self,
        *,
        organization_id: str,
        reporting_year: int,
        scope_hint: Optional[str] = None,
    ) -> list[dict]:
        """Authoritative snapshot rows shaped for the projection engine."""
        return _rows(
            await self._fetch_all(
                """
                SELECT cs.id AS natural_key, cs.id AS calculation_snapshot_id,
                       cs.co2e_kg AS co2e_kg, cs.quantity AS quantity,
                       cs.quantity_unit AS unit, cs.scope AS scope,
                       cs.activity_type AS activity_type
                FROM public.calculation_snapshots cs
                WHERE cs.organization_id = $1
                  AND cs.reporting_year = $2
                  AND ($3::text IS NULL OR cs.scope = $3)
                ORDER BY cs.calculated_at NULLS LAST, cs.id
                """,
                organization_id,
                reporting_year,
                scope_hint,
            )
        )

    async def load_emissions_rows(
        self,
        *,
        organization_id: str,
        period_start: Any,
        period_end: Any,
        scope_hint: Optional[str] = None,
    ) -> list[dict]:
        return _rows(
            await self._fetch_all(
                """
                SELECT el.id AS natural_key, el.snapshot_id AS calculation_snapshot_id,
                       el.calculated_kg_co2e AS co2e_kg, el.raw_quantity AS quantity,
                       el.unit AS unit, el.scope AS scope
                FROM public.emissions_logs el
                WHERE el.organization_id = $1
                  AND el.start_date >= $2::date AND el.start_date <= $3::date
                  AND ($4::text IS NULL OR el.scope = $4)
                ORDER BY el.start_date, el.id
                """,
                organization_id,
                period_start,
                period_end,
                scope_hint,
            )
        )

    async def load_rows_for(
        self,
        *,
        source_kind: str,
        organization_id: str,
        reporting_year: int,
        period_start: Any = None,
        period_end: Any = None,
        scope_hint: Optional[str] = None,
    ) -> list[dict]:
        """Rows for a producer kind. Non-row producers return ``[]`` (honestly)."""
        if source_kind == "CALCULATION_AGGREGATE":
            return await self.load_calculation_rows(
                organization_id=organization_id,
                reporting_year=reporting_year,
                scope_hint=scope_hint,
            )
        if source_kind == "EMISSIONS_LOG_AGGREGATE":
            if period_start is None or period_end is None:
                return []
            return await self.load_emissions_rows(
                organization_id=organization_id,
                period_start=period_start,
                period_end=period_end,
                scope_hint=scope_hint,
            )
        # FACTOR_PROVENANCE / EVIDENCE_COMPLETENESS / ENERGY_ACTIVITY /
        # INTENSITY_RATIO / PRIOR_PERIOD_VALUE / ORG_PROFILE_FACT / CUSTOMER_INPUT
        # are not row projections in this increment: returning [] produces an
        # honest UNRESOLVED value rather than a fabricated number.
        return []

    async def evidence_coverage(self, *, disclosure_value_id: str) -> dict:
        """Evidence counts + completeness for one disclosure value."""
        row = await self._fetch_one(
            """
            SELECT count(*) AS reference_count,
                   count(dve.source_line_item_id) AS line_linked_count,
                   count(dve.calculation_snapshot_id) AS snapshot_linked_count
            FROM public.disclosure_value_evidence dve
            WHERE dve.disclosure_value_id = $1
            """,
            disclosure_value_id,
        )
        if row is None:
            return {"reference_count": 0, "line_linked_count": 0, "snapshot_linked_count": 0}
        return {
            "reference_count": int(row["reference_count"]),
            "line_linked_count": int(row["line_linked_count"]),
            "snapshot_linked_count": int(row["snapshot_linked_count"]),
        }

    # -- value → line enumeration (the B2 join; DM-6 read model) -------------
    async def value_lines(self, *, report_version_id: str) -> list[dict]:
        """Enumerate a report version's discovery values down to source lines."""
        return _rows(
            await self._fetch_all(
                """
                SELECT dv.id AS disclosure_value_id, dv.requirement_version_id,
                       cs.id AS calculation_snapshot_id, eli.id AS evidence_line_item_id,
                       eli.line_number, eli.source_page, eli.raw_description,
                       eli.raw_quantity, eli.raw_unit, eli.materialisation_kind
                FROM public.disclosure_values dv
                LEFT JOIN public.disclosure_value_evidence dve
                       ON dve.disclosure_value_id = dv.id
                LEFT JOIN public.calculation_snapshots cs
                       ON cs.id = dve.calculation_snapshot_id
                LEFT JOIN public.evidence_line_items eli
                       ON eli.id = COALESCE(dve.source_line_item_id, cs.source_line_item_id)
                WHERE dv.report_version_id = $1
                ORDER BY dv.created_at, dv.id, eli.line_number NULLS LAST
                """,
                report_version_id,
            )
        )

    # -- intensity catalogue / selection -------------------------------------
    async def list_intensity_catalogue(self, *, active_only: bool = True) -> list[dict]:
        return _rows(
            await self._fetch_all(
                """
                SELECT id, code, name, denominator_kind, unit_hint, support_class, is_active
                FROM public.disclosure_intensity_denominator_types
                WHERE ($1::boolean IS FALSE OR is_active)
                ORDER BY code
                """,
                active_only,
            )
        )

    async def list_framework_treatment(self, *, denominator_type_id: str) -> list[dict]:
        """Framework-specific claims for a denominator (empty = no claim recorded)."""
        return _rows(
            await self._fetch_all(
                """
                SELECT l.id, l.treatment, l.evidence_basis, l.source_tier,
                       l.official_reference, l.verified_at, l.framework_version_id
                FROM public.disclosure_intensity_denominator_framework_links l
                WHERE l.denominator_type_id = $1
                ORDER BY l.treatment
                """,
                denominator_type_id,
            )
        )

    async def upsert_intensity_ratio(
        self,
        *,
        organization_id: str,
        report_version_id: str,
        denominator_type_id: str,
        selection_basis: str,
        denominator_value: Any = None,
        denominator_unit: Optional[str] = None,
        numerator_value: Any = None,
        selection_source: str = "CUSTOMER_SELECTED",
        confirmed_by: Optional[str] = None,
        numerator_disclosure_value_id: Optional[str] = None,
    ) -> Optional[dict]:
        """Upsert an org-scoped intensity selection (one per version+denominator)."""
        row = await self._fetch_one(
            """
            INSERT INTO public.disclosure_intensity_ratios
                (organization_id, report_version_id, denominator_type_id,
                 numerator_disclosure_value_id, denominator_value, denominator_unit,
                 ratio_value, selection_basis, selection_source, confirmed_by, confirmed_at)
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5::numeric, $6,
                    CASE WHEN $5::numeric IS NULL OR $5::numeric <= 0 THEN NULL
                         WHEN $7::numeric IS NULL THEN NULL
                         ELSE ($7::numeric / $5::numeric) END,
                    $8, $9, $10::uuid,
                    CASE WHEN $10::uuid IS NULL THEN NULL ELSE now() END)
            ON CONFLICT (organization_id, report_version_id, denominator_type_id)
            DO UPDATE SET denominator_value = EXCLUDED.denominator_value,
                          denominator_unit = EXCLUDED.denominator_unit,
                          ratio_value = EXCLUDED.ratio_value,
                          selection_basis = EXCLUDED.selection_basis,
                          selection_source = EXCLUDED.selection_source,
                          confirmed_by = EXCLUDED.confirmed_by,
                          confirmed_at = CASE WHEN EXCLUDED.confirmed_by IS NULL
                                              THEN public.disclosure_intensity_ratios.confirmed_at
                                              ELSE now() END,
                          updated_at = now()
            RETURNING id, organization_id, report_version_id, denominator_type_id,
                      denominator_value, denominator_unit, ratio_value,
                      selection_basis, selection_source, confirmed_by, confirmed_at
            """,
            organization_id,
            report_version_id,
            denominator_type_id,
            numerator_disclosure_value_id,
            denominator_value,
            denominator_unit,
            numerator_value,
            selection_basis,
            selection_source,
            confirmed_by,
        )
        return dict(row) if row is not None else None

    # -- producer mappings (ratified content only; B3 authors none) ----------
    async def list_requirement_mappings(self, requirement_version_id: str) -> list[dict]:
        """Current producer mapping rows for a requirement (may legitimately be none)."""
        return _rows(
            await self._fetch_all(
                """
                SELECT id, requirement_version_id, source_kind, aggregation,
                       source_selector, is_current
                FROM public.disclosure_requirement_mappings
                WHERE requirement_version_id = $1 AND is_current
                ORDER BY id
                """,
                requirement_version_id,
            )
        )

    # -- API read helpers ----------------------------------------------------
    async def get_value(self, value_id: str) -> Optional[dict]:
        """One disclosure value (org-scoped authorization happens in the API)."""
        row = await self._fetch_one(
            """
            SELECT id, organization_id, report_version_id, requirement_version_id,
                   effective_class, value_status, value_kind, numeric_value,
                   value_unit, text_value, reporting_year, source_kind, reason,
                   computed_at, created_at, updated_at
            FROM public.disclosure_values
            WHERE id = $1
            """,
            value_id,
        )
        return dict(row) if row is not None else None

    async def list_values(self, *, report_version_id: str) -> list[dict]:
        return _rows(
            await self._fetch_all(
                """
                SELECT id, requirement_version_id, effective_class, value_status,
                       value_kind, numeric_value, value_unit, text_value,
                       source_kind, reason, computed_at, created_at, updated_at
                FROM public.disclosure_values
                WHERE report_version_id = $1
                ORDER BY created_at, id
                """,
                report_version_id,
            )
        )

    async def list_applicability(
        self, *, organization_id: str, reporting_year: Optional[int] = None
    ) -> list[dict]:
        """Recorded applicability assessments for an organisation (newest first)."""
        return _rows(
            await self._fetch_all(
                """
                SELECT id, organization_id, framework_version_id, reporting_year,
                       reporting_period_start, reporting_period_end, assessed_status,
                       basis, determined_by, determined_at, version, created_at
                FROM public.disclosure_applicability_assessments
                WHERE organization_id = $1
                  AND ($2::int IS NULL OR reporting_year = $2::int)
                ORDER BY reporting_year DESC, version DESC, created_at DESC
                """,
                organization_id,
                reporting_year,
            )
        )

    async def list_intensity_ratios(self, *, report_version_id: str) -> list[dict]:
        return _rows(
            await self._fetch_all(
                """
                SELECT r.id, r.denominator_type_id, t.code AS denominator_code,
                       t.name AS denominator_name, t.unit_hint,
                       r.denominator_value, r.denominator_unit, r.ratio_value,
                       r.selection_basis, r.selection_source, r.confirmed_by,
                       r.confirmed_at, r.created_at
                FROM public.disclosure_intensity_ratios r
                JOIN public.disclosure_intensity_denominator_types t
                     ON t.id = r.denominator_type_id
                WHERE r.report_version_id = $1
                ORDER BY t.code
                """,
                report_version_id,
            )
        )
