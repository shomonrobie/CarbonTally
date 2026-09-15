"""Phase 8 B3 — disclosure projection service (orchestration).

Projects a report version's disclosure values from already-authoritative data
and persists them through the B1 repository (which enforces tenant isolation,
report-version immutability and per-value audit).

Ratified behaviour implemented here:

* applicability is read from the recorded assessment; **no assessment means
  ``UNDETERMINED``** — never a silent default (`APPL`/D13);
* a requirement with **no producer mapping** yields an honest ``UNRESOLVED``
  value with an explicit reason — B3 authors no mapping content (`B3-D8`);
* re-running is idempotent: the B1 upsert keys on
  ``(report_version_id, requirement_version_id)``;
* failure of one requirement is recorded as ``UNRESOLVED`` with the error
  summarised, so a single bad mapping cannot abort a whole projection run and
  no value is ever fabricated.
"""
from __future__ import annotations

from typing import Any, Optional

import asyncpg

from core.logging import get_logger
from data.disclosure import DisclosureRepository
from data.disclosure_projection import DisclosureProjectionRepository
from domain.disclosure import DisclosureViolation
from domain.disclosure_projection import decide_projection, unmapped_decision

logger = get_logger(__name__)

#: Applicability recorded as unknown when no assessment exists (APPL/D13).
DEFAULT_APPLICABILITY_STATUS = "UNDETERMINED"


class DisclosureProjectionService:
    """Orchestrates projection of a report version's disclosure values."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool
        self._repo = DisclosureProjectionRepository(pool)
        self._disclosure = DisclosureRepository(pool)

    async def _applicability_status(self, binding: dict) -> str:
        assessment_id = binding.get("applicability_assessment_id")
        if not assessment_id:
            return DEFAULT_APPLICABILITY_STATUS
        assessment = await self._disclosure.get_applicability_assessment(str(assessment_id))
        if assessment is None:
            return DEFAULT_APPLICABILITY_STATUS
        return str(assessment["assessed_status"])

    async def project_report_version(
        self,
        *,
        report_version_id: str,
        actor: Optional[str] = None,  # noqa: ARG002 - reserved for future run-level audit
    ) -> dict:
        """Project every requirement of the version's purpose; idempotent."""
        ctx = await self._repo.report_context(report_version_id)
        if ctx is None:
            raise DisclosureViolation("unknown report version")

        binding = await self._disclosure.get_instance_binding(ctx["report_id"])
        if binding is None:
            raise DisclosureViolation(
                "report version has no disclosure instance binding; bind a purpose first"
            )

        applicability_status = await self._applicability_status(binding)
        requirements = await self._repo.list_purpose_requirements(
            str(binding["purpose_version_id"])
        )

        resolved = 0
        unresolved = 0
        results: list[dict] = []

        for requirement in requirements:
            requirement_version_id = str(requirement["requirement_version_id"])
            requirement_class = str(requirement["requirement_class"])
            capability = str(requirement["carbontally_capability"])
            value_kind = str(requirement["value_kind"])

            mappings = await self._repo.list_requirement_mappings(requirement_version_id)
            mapping: Optional[dict] = mappings[0] if mappings else None

            try:
                if mapping is None:
                    decision = unmapped_decision(
                        requirement_class=requirement_class,
                        carbontally_capability=capability,
                        applicability_status=applicability_status,
                    )
                else:
                    source_kind = str(mapping["source_kind"])
                    selector = mapping.get("source_selector") or {}
                    selector_scope = (
                        selector.get("scope") if isinstance(selector, dict) else None
                    )
                    scope_hint = selector_scope or requirement.get("scope_hint")
                    rows = await self._repo.load_rows_for(
                        source_kind=source_kind,
                        organization_id=ctx["organization_id"],
                        reporting_year=ctx["reporting_year"],
                        period_start=binding.get("reporting_period_start"),
                        period_end=binding.get("reporting_period_end"),
                        scope_hint=str(scope_hint) if scope_hint else None,
                    )
                    decision = decide_projection(
                        requirement_class=requirement_class,
                        carbontally_capability=capability,
                        applicability_status=applicability_status,
                        source_kind=source_kind,
                        aggregation=mapping.get("aggregation"),
                        rows=rows,
                    )
            except Exception as exc:  # noqa: BLE001 - record, never fabricate
                logger.warning(
                    "disclosure projection failed for requirement %s: %s",
                    requirement_version_id,
                    exc,
                )
                results.append(
                    {
                        "requirement_version_id": requirement_version_id,
                        "value_status": "UNRESOLVED",
                        "reason": f"projection error: {type(exc).__name__}",
                        "persisted": False,
                    }
                )
                unresolved += 1
                continue

            record = await self._disclosure.upsert_disclosure_value(
                organization_id=ctx["organization_id"],
                report_version_id=report_version_id,
                requirement_version_id=requirement_version_id,
                requirement_mapping_id=str(mapping["id"]) if mapping else None,
                effective_class=decision.effective_class,
                value_kind=value_kind,
                reporting_year=ctx["reporting_year"],
                value_status=decision.value_status,
                numeric_value=decision.numeric_value,
                value_unit=decision.value_unit,
                source_kind=decision.source_kind,
                reason=decision.reason,
            )

            if decision.value_status == "RESOLVED":
                resolved += 1
            else:
                unresolved += 1
            results.append(
                {
                    "requirement_version_id": requirement_version_id,
                    "disclosure_value_id": str(record["id"]),
                    "value_status": decision.value_status,
                    "effective_class": decision.effective_class,
                    "source_kind": decision.source_kind,
                    "numeric_value": str(decision.numeric_value) if decision.numeric_value is not None else None,
                    "value_unit": decision.value_unit,
                    "reason": decision.reason,
                    "persisted": True,
                }
            )

        summary = {
            "report_version_id": report_version_id,
            "organization_id": ctx["organization_id"],
            "applicability_status": applicability_status,
            "requirement_count": len(requirements),
            "resolved": resolved,
            "unresolved": unresolved,
            "values": results,
        }
        logger.info(
            "disclosure projection complete for report version %s: %s resolved / %s unresolved",
            report_version_id,
            resolved,
            unresolved,
        )
        return summary
