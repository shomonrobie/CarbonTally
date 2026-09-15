"""Phase 8 B4 — narrative overlay service (authoring rules, A1/A3/P3/D15).

Composes the ratified policy spine with persistence:

* ``A1`` — the entry is bound to a ``requirement_version_id`` that must be part of
  this report version's requirement set; report-wide narrative is impossible;
* ``A1``/``P3`` — authoring requires a Customer Owner/Admin actor (re-checked here,
  so a future caller cannot bypass the API);
* ``A3`` — plain text, non-empty, **no arbitrary length limit**;
* ``D15`` — never author against an ``APPROVED``/``FINAL`` version.

No calculation, no artefact, no AI.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import asyncpg

from core.logging import get_logger
from data.audit import AuditRepository
from data.disclosure_narrative import DisclosureNarrativeRepository
from data.disclosure_projection import DisclosureProjectionRepository
from domain.audit import AuditEntry
from domain.disclosure import DisclosureViolation
from domain.disclosure_narrative import (
    assert_author_role,
    assert_can_author,
    assert_narrative_binding,
    validate_narrative_body,
    validate_narrative_kind,
)

logger = get_logger(__name__)


class DisclosureNarrativeService:
    """Read and author the requirement-bound narrative overlay."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool
        self._entries = DisclosureNarrativeRepository(pool)
        self._projection = DisclosureProjectionRepository(pool)
        self._audit = AuditRepository(pool)

    async def _audit_narrative(
        self,
        *,
        action: str,
        entity_id: str,
        organization_id: str,
        actor: Optional[str],
        after: Optional[dict] = None,
    ) -> bool:
        """A10: append one audit entry. Never raises; the body text is never audited.

        Only the binding, kind, state and length are recorded — the customer's prose
        stays in its own table rather than being duplicated into the audit trail.
        """
        entry = AuditEntry(
            id=str(uuid4()),
            correlation_id=str(uuid4()),
            entity_type="disclosure_narrative_entries",
            entity_id=entity_id,
            action=action,
            actor=actor or "system",
            occurred_at=datetime.now(timezone.utc),
            before=None,
            after=after,
            reason="B4 narrative overlay written",
            organization_id=organization_id,
        )
        try:
            await self._audit.record(entry)
            return True
        except Exception:  # noqa: BLE001 — the write must still succeed
            logger.exception("B4 narrative audit (%s) failed for %s", action, entity_id)
            return False

    async def _context(self, report_version_id: str) -> dict:
        ctx = await self._projection.report_context(report_version_id)
        if ctx is None:
            raise DisclosureViolation("unknown report version")
        return ctx

    async def list_narrative(self, *, report_version_id: str) -> dict:
        ctx = await self._context(report_version_id)
        entries = await self._entries.list_entries(report_version_id)
        return {
            "report_version_id": report_version_id,
            "report_id": ctx["report_id"],
            "organization_id": ctx["organization_id"],
            "version_status": ctx["status"],
            "authoring_allowed": not ctx["status"] in ("APPROVED", "FINAL"),
            "count": len(entries),
            "entries": entries,
        }

    async def write_narrative(
        self,
        *,
        report_version_id: str,
        requirement_version_id: Optional[str],
        narrative_kind: str,
        body: Optional[str],
        actor_role: Optional[str],
        actor_id: Optional[str] = None,
    ) -> dict:
        role = assert_author_role(actor_role)
        ctx = await self._context(report_version_id)
        assert_can_author(ctx["status"])
        binding = assert_narrative_binding(requirement_version_id)
        kind = validate_narrative_kind(narrative_kind)
        text = validate_narrative_body(body)

        values = await self._projection.list_values(report_version_id=report_version_id)
        matching = [v for v in values if str(v["requirement_version_id"]) == binding]
        if not matching:
            raise DisclosureViolation(
                "B4 narrative: requirement is not part of this report version "
                "(A1 binding refused)"
            )

        entry = await self._entries.upsert(
            organization_id=str(ctx["organization_id"]),
            report_version_id=report_version_id,
            requirement_version_id=binding,
            narrative_kind=kind,
            body=text,
            authored_by=actor_id,
            disclosure_value_id=str(matching[0]["id"]) if matching[0].get("id") else None,
        )
        logger.info(
            "B4 narrative upserted for version %s requirement %s kind %s by role %s",
            report_version_id,
            binding,
            kind,
            role,
        )
        await self._audit_narrative(
            action="disclosure_narrative.written",
            entity_id=str(entry.get("id") or binding),
            organization_id=str(ctx["organization_id"]),
            actor=actor_id,
            after={
                "report_version_id": report_version_id,
                "requirement_version_id": binding,
                "narrative_kind": kind,
                "state": entry.get("state", "DRAFT"),
                "body_length": len(text),
            },
        )
        return {
            "report_version_id": report_version_id,
            "requirement_version_id": binding,
            "narrative_kind": kind,
            "state": entry.get("state", "DRAFT"),
            "actor_role": role,
            "entry": entry,
        }
