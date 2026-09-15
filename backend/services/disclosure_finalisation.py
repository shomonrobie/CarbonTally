"""Phase 8 B4 — approval and finalisation service (contract §8, §10, §23).

Enforces, server-side:

* **`B4-D1` (PO ratified, Option A):** only a Customer **Owner/Admin** may approve
  or finalise; consultants and CarbonTally internal staff may **never** do so.
* **`DM-5`:** a report cannot be finalised while a required
  ``CUSTOMER_INPUT_REQUIRED`` item is unresolved; a required ``NOT_SUPPORTED``
  item is **surfaced** (allowed to proceed) and never presented as satisfied;
  the two are never collapsed.
* **`B4-D5`/`B4-D6`/`B4-D7`:** finalisation is impossible without the **frozen
  artefact** — the immutable PDF is rendered, stored in the private bucket and
  recorded (SHA-256, append-only) *before* the version becomes ``FINAL``.
* **S3 state machine + `D15`:** transitions go through the ratified rule table and
  the atomic expected-state guard (a stale/concurrent caller gets a conflict, not
  a clobbered state); an immutable version is never re-transitioned.

No calculation, no narrative write, no authoritative-value write.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import asyncpg

from core.logging import get_logger
from data.audit import AuditRepository
from data.disclosure_projection import DisclosureProjectionRepository
from data.report_artefacts import ReportArtefactRepository
from data.report_versions import ReportVersionsRepository
from domain.audit import AuditEntry
from domain.disclosure import DisclosureViolation
from domain.disclosure_narrative import (
    FinalisationAssessment,
    assert_author_role,
    assert_states_are_not_collapsed,
    evaluate_finalisation,
)
from domain.report_artefact import (
    FrozenArtefact,
    assert_artefact_matches,
    build_artefact,
)
from domain.report_lifecycle import (
    APPROVE,
    FINALIZE,
    TransitionNotAllowed,
    is_terminal,
    resolve_transition,
)
from services.report_artefact_storage import (
    SIGNED_URL_TTL_SECONDS,
    ReportArtefactStorage,
    get_report_artefact_storage,
)

logger = get_logger(__name__)


#: B4-D5: finalisation is refused outright when no renderer is wired — there is
#: deliberately no "finalise without an artefact" path.
_NO_PRODUCER = (
    "B4 artefact (B4-D5): the frozen artefact is mandatory at finalisation, but no "
    "PDF producer was supplied - finalisation is refused"
)


class ArtefactRequired(DisclosureViolation):
    """The mandatory frozen artefact could not be produced or stored (B4-D5)."""


class FinalisationBlocked(DisclosureViolation):
    """The DM-5 gate refused finalisation. Carries the structured assessment."""

    def __init__(self, assessment: FinalisationAssessment) -> None:
        self.assessment = assessment
        reasons = ", ".join(
            f"{item.requirement_version_id}:{item.effective_class}" for item in assessment.blocking
        )
        super().__init__(f"finalisation blocked by unresolved required disclosures ({reasons})")


class FinalisationConflict(DisclosureViolation):
    """The atomic expected-state guard did not match (stale or concurrent caller)."""


class DisclosureFinalisationService:
    """Approval and finalisation for a disclosure-backed report version."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool
        self._projection = DisclosureProjectionRepository(pool)
        self._versions = ReportVersionsRepository(pool)
        self._artefacts = ReportArtefactRepository(pool)
        self._audit = AuditRepository(pool)

    # -- B4-D11: auditability (append-only audit_trail; never a signed URL) ---
    async def _audit_artefact(
        self,
        *,
        action: str,
        entity_id: str,
        organization_id: Optional[str],
        actor: Optional[str],
        after: Optional[dict] = None,
        reason: Optional[str] = None,
        entity_type: str = "report_version_artifacts",
    ) -> bool:
        """Append one audit entry. Never raises: audit must not break an action.

        The ``after`` payload deliberately carries only non-secret provenance
        (object key, hash, TTL, state change) — **never** a signed URL (AGENTS §68/§78).
        """
        entry = AuditEntry(
            id=str(uuid4()),
            correlation_id=str(uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor or "system",
            occurred_at=datetime.now(timezone.utc),
            before=None,
            after=after,
            reason=reason,
            organization_id=organization_id,
        )
        try:
            await self._audit.record(entry)
            return True
        except Exception:  # noqa: BLE001 — audited action must still succeed
            logger.exception("B4 artefact audit (%s) failed for %s", action, entity_id)
            return False

    async def _context(self, report_version_id: str) -> dict:
        ctx = await self._projection.report_context(report_version_id)
        if ctx is None:
            raise DisclosureViolation("unknown report version")
        return ctx

    async def assess(self, *, report_version_id: str) -> dict:
        """The DM-5 gate preview — no side effects, no transition."""
        ctx = await self._context(report_version_id)
        values = await self._projection.list_values(report_version_id=report_version_id)
        assessment = evaluate_finalisation(values)
        assert_states_are_not_collapsed(assessment)
        return {
            "report_version_id": report_version_id,
            "report_id": ctx["report_id"],
            "organization_id": ctx["organization_id"],
            "version_status": ctx["status"],
            "can_finalise": assessment.can_finalise,
            "blocking": [self._item(i) for i in assessment.blocking],
            "surfaced_limitations": [self._item(i) for i in assessment.surfaced],
            "information_only": [self._item(i) for i in assessment.informational],
        }

    @staticmethod
    def _item(item: Any) -> dict:
        return {
            "requirement_version_id": item.requirement_version_id,
            "effective_class": item.effective_class,
            "value_status": item.value_status,
            "reason": item.reason,
        }

    async def _transition(
        self,
        *,
        report_version_id: str,
        action: str,
        actor_role: str,
        actor_id: Optional[str] = None,
    ) -> dict:
        ctx = await self._context(report_version_id)
        current = str(ctx["status"])
        try:
            target = resolve_transition(action, current)
        except TransitionNotAllowed as exc:
            raise DisclosureViolation(str(exc)) from exc
        updated = await self._versions.set_status(
            ctx["report_id"],
            report_version_id,
            expected_status=current,
            new_status=target,
        )
        if updated is None:
            raise FinalisationConflict(
                f"state changed concurrently (expected {current}); reload and retry"
            )
        logger.info(
            "report version %s transitioned %s -> %s by %s", report_version_id, current, target, actor_role
        )
        # A10: every lifecycle transition is audited (append-only audit_trail).
        action_verb = "approved" if action == APPROVE else "finalised"
        await self._audit_artefact(
            action=f"report_version.{action_verb}",
            entity_id=report_version_id,
            organization_id=str(ctx["organization_id"]),
            actor=actor_id,
            after={"status_from": current, "status_to": target, "actor_role": actor_role},
            reason=f"B4 {action_verb} transition",
            entity_type="report_versions",
        )
        # The repository returns a version object; expose only primitives so the
        # response is serialisable regardless of the row shape.
        version = None
        if updated is not None:
            version = {
                "id": str(getattr(updated, "id", report_version_id)),
                "status": str(getattr(updated, "status", target)),
                "version_number": getattr(updated, "version_number", None),
            }
        return {
            "report_version_id": report_version_id,
            "previous_status": current,
            "version_status": target,
            "actor_role": actor_role,
            "version": version,
        }

    async def approve(
        self,
        *,
        report_version_id: str,
        actor_role: Optional[str],
        actor_id: Optional[str] = None,
    ) -> dict:
        """REVIEWED -> APPROVED. Owner/Admin only (B4-D1); never staff/consultant."""
        role = assert_author_role(actor_role)
        return await self._transition(
            report_version_id=report_version_id,
            action=APPROVE,
            actor_role=role,
            actor_id=actor_id,
        )

    async def finalise(
        self,
        *,
        report_version_id: str,
        actor_role: Optional[str],
        pdf_producer: Optional[Any] = None,
        storage: Optional[ReportArtefactStorage] = None,
        actor_id: Optional[str] = None,
    ) -> dict:
        """APPROVED -> FINAL, gated by `DM-5` **and** the mandatory frozen artefact.

        PO `B4-D5`: the immutable PDF artefact must be produced and stored *before*
        the version becomes `FINAL`; if it cannot be, finalisation fails and the
        version stays `APPROVED`. Owner/Admin only (`B4-D1`).
        """
        role = assert_author_role(actor_role)
        ctx = await self._context(report_version_id)
        # A terminal version is never re-transitioned: FINAL is corrected by a NEW
        # version (T9/T10/T17), never by mutating the finalised one.
        if is_terminal(ctx["status"]):
            raise DisclosureViolation(
                f"report version is already terminal ({ctx['status']}); create a new version instead"
            )
        assessment = evaluate_finalisation(
            await self._projection.list_values(report_version_id=report_version_id)
        )
        assert_states_are_not_collapsed(assessment)
        if not assessment.can_finalise:
            raise FinalisationBlocked(assessment)

        # S5 (B4-D5/D6/D7): freeze first, transition second. Any failure in here
        # propagates as a refusal — the version is left APPROVED.
        frozen = await self.freeze_artefact(
            report_version_id=report_version_id,
            pdf_producer=pdf_producer,
            storage=storage,
            actor_id=actor_id,
        )

        result = await self._transition(
            report_version_id=report_version_id,
            action=FINALIZE,
            actor_role=role,
            actor_id=actor_id,
        )
        result["surfaced_limitations"] = [self._item(i) for i in assessment.surfaced]
        result["frozen_artefact"] = frozen
        return result

    # -- S5 frozen artefact --------------------------------------------------
    async def freeze_artefact(
        self,
        *,
        report_version_id: str,
        pdf_producer: Optional[Any],
        storage: Optional[ReportArtefactStorage] = None,
        actor_id: Optional[str] = None,
    ) -> dict:
        """Render, upload and record the frozen artefact (idempotent per version).

        A version that already has an artefact is **never** rewritten: the stored
        bytes must hash to the recorded SHA-256, otherwise the call is refused.
        """
        if pdf_producer is None:
            raise ArtefactRequired(_NO_PRODUCER)

        ctx = await self._context(report_version_id)
        existing = await self._artefacts.get_for_version(report_version_id)

        try:
            produced = pdf_producer()
            payload = await produced if hasattr(produced, "__await__") else produced
        except DisclosureViolation:
            raise
        except Exception as exc:  # noqa: BLE001 — renderer internals never reach the user
            raise ArtefactRequired(
                f"B4 artefact (B4-D5): PDF rendering failed ({type(exc).__name__}); "
                "finalisation is refused"
            ) from exc

        frozen = build_artefact(
            organization_id=ctx["organization_id"],
            report_id=ctx["report_id"],
            report_version_id=report_version_id,
            payload=payload,
        )

        if existing is not None:
            assert_artefact_matches(
                FrozenArtefact(
                    organization_id=str(existing["organization_id"]),
                    report_id=str(existing["report_id"]),
                    report_version_id=str(existing["report_version_id"]),
                    storage_bucket=str(existing["storage_bucket"]),
                    object_key=str(existing["object_key"]),
                    content_sha256=str(existing["content_sha256"]),
                    byte_size=int(existing["byte_size"]),
                    content_type=str(existing["content_type"]),
                ),
                payload,
            )
            logger.info("B4 artefact already frozen for version %s - reusing it", report_version_id)
            return existing

        store = storage or get_report_artefact_storage()
        try:
            if not store.exists(object_key=frozen.object_key):
                store.upload(object_key=frozen.object_key, payload=payload)
        except Exception as exc:  # noqa: BLE001 — a storage failure must block FINAL
            raise ArtefactRequired(
                "B4 artefact (B4-D5): storing the frozen artefact failed "
                f"({type(exc).__name__}); finalisation is refused"
            ) from exc

        record = await self._artefacts.create(frozen.as_record(produced_by=actor_id))
        if record is None:
            record = await self._artefacts.get_for_version(report_version_id) or {}
        else:
            await self._audit_artefact(
                action="frozen_artefact.created",
                entity_id=str(record.get("id") or report_version_id),
                organization_id=str(ctx["organization_id"]),
                actor=actor_id,
                after={
                    "object_key": frozen.object_key,
                    "content_sha256": frozen.content_sha256,
                    "byte_size": frozen.byte_size,
                    "storage_bucket": frozen.storage_bucket,
                },
            )
        return record

    async def artefact_status(self, *, report_version_id: str) -> dict:
        """Metadata for the frozen artefact. Never returns a URL.

        `B4-D11`: also reports **data as of** and a **staleness flag**. Staleness is
        *reported*, never actioned — a finalised version is never auto-invalidated.
        """
        ctx = await self._context(report_version_id)
        record = await self._artefacts.get_for_version(report_version_id)
        values = await self._projection.list_values(report_version_id=report_version_id)
        changes = [
            value.get("updated_at") or value.get("computed_at")
            for value in values
            if value.get("updated_at") or value.get("computed_at")
        ]
        latest = max(changes).isoformat() if changes else None
        produced_at = (record or {}).get("produced_at")
        stale = bool(
            record is not None and latest and produced_at is not None and latest > str(produced_at)
        )
        return {
            "report_version_id": report_version_id,
            "report_id": ctx["report_id"],
            "organization_id": ctx["organization_id"],
            "version_status": ctx["status"],
            "frozen": record is not None,
            "artefact": record,
            "data_as_of": latest,
            "stale": stale,
            "staleness_action": (
                "reported only - never auto-invalidated; corrections create a new version (D15/DM-7)"
            ),
        }
        return {
            "report_version_id": report_version_id,
            "report_id": ctx["report_id"],
            "organization_id": ctx["organization_id"],
            "version_status": ctx["status"],
            "frozen": record is not None,
            "artefact": record,
        }

    async def artefact_download_url(
        self,
        *,
        report_version_id: str,
        storage: Optional[ReportArtefactStorage] = None,
        actor_id: Optional[str] = None,
    ) -> dict:
        """A short-lived signed URL, issued **after** authorization (B4-D6).

        Authorization is the API layer's responsibility; this method refuses when
        no frozen artefact exists, so a draft can never be served from the frozen
        bucket (drafts use the live-render route, `A15`).

        `B4-D11`: the issuance is audited. The audit payload carries the object key,
        hash and TTL — **never** the signed URL (AGENTS §68/§78).
        """
        record = await self._artefacts.get_for_version(report_version_id)
        if record is None:
            raise DisclosureViolation(
                "B4 artefact: this report version has no frozen artefact "
                "(drafts are served by the live-render route)"
            )
        ctx = await self._context(report_version_id)
        store = storage or get_report_artefact_storage()
        url = store.signed_url(
            object_key=str(record["object_key"]), expires_in=SIGNED_URL_TTL_SECONDS
        )
        await self._audit_artefact(
            action="frozen_artefact.signed_url_issued",
            entity_id=str(record.get("id") or report_version_id),
            organization_id=str(ctx["organization_id"]),
            actor=actor_id,
            after={
                "object_key": record["object_key"],
                "content_sha256": record["content_sha256"],
                "expires_in": SIGNED_URL_TTL_SECONDS,
            },
            reason="frozen artefact download URL issued",
        )
        logger.info(
            "B4 artefact: signed URL issued for version %s (ttl %ss)",
            report_version_id,
            SIGNED_URL_TTL_SECONDS,
        )
        return {
            "report_version_id": report_version_id,
            "object_key": record["object_key"],
            "content_sha256": record["content_sha256"],
            "byte_size": record["byte_size"],
            "expires_in": SIGNED_URL_TTL_SECONDS,
            "signed_url": url,
        }
