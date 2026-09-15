"""Phase 8 B2 — evidence line-item repository (contract §11, §12, §17).

Insert-only materialisation plus the read surface for
``public.evidence_line_items``. This module is the *only* place B2 writes
evidence-line rows, and it writes them exactly two ways:

* **forward** — best-effort, from the data-layer choke point
  (:meth:`data.manual_extraction.ManualExtractionRepository.save_extracted_data`
  / ``update_item``), never blocking the extraction save (B2-D6);
* **backfill** — the explicitly-invoked, batched, resumable, idempotent
  Class-1 operation (``materialisation_kind='BACKFILL'``, §11.4).

Invariants enforced here (contract §7.6, §11.3, §12.3, B2-D2, B2-D11):

* **no UPDATE and no DELETE statement for ``evidence_line_items`` exists** —
  the table is append-only evidence; reruns are ``ON CONFLICT DO NOTHING``;
  a hash difference is *detected and reported*, never reconciled in place;
* **no retention / soft-delete / purge / anonymisation** mechanism exists;
* **no extraction, OCR, LLM or parser is called** and neither ``mapped_data``
  nor any calculation is read or written — line identity derives only from the
  persisted ``extracted_data.line_items[]`` (§11.4);
* ``organization_id`` is resolved **server-side** from the parent batch, never
  caller-supplied (the item has no ``organization_id`` — F-B2-8).

Audit (contract §17, B2-D5): one event per source document on forward
materialisation, one summary event per backfill **run**, and one event per item
whose ordinals diverged. Emission is best-effort, mirroring ``data/disclosure``:
audit never breaks a materialisation, and the run report records whether the
summary audit was actually written.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

import asyncpg

from core.logging import get_logger
from data.audit import AuditRepository
from data.base import AbstractRepository, loads_jsonb
from domain.audit import ACTOR_SYSTEM, AuditEntry
from domain.line_items import (
    ACTION_DIVERGENCE,
    ACTION_INSERT,
    AUDIT_LINE_ITEMS_BACKFILLED,
    AUDIT_LINE_ITEMS_DIVERGENCE_DETECTED,
    AUDIT_LINE_ITEMS_MATERIALISED,
    INELIGIBLE_LINE_COUNT,
    MATERIALISATION_BACKFILL,
    MATERIALISATION_FORWARD,
    MATERIALISATION_KINDS,
    UNKNOWN_EXTRACTION_METHOD,
    decide_ordinals,
    derive_line_candidates,
)

logger = get_logger(__name__)

_SYSTEM_ACTOR = "00000000-0000-0000-0000-000000000000"
_ZERO_UUID = "00000000-0000-0000-0000-000000000000"

#: Explicit column list — never ``SELECT *`` (repository convention).
_COLUMNS = (
    "id, organization_id, source_item_id, source_file_id, line_number, "
    "source_page, row_reference, raw_description, raw_quantity, raw_unit, "
    "payload_hash, extraction_method, materialisation_kind, created_at"
)

#: `manual_extraction_items` has no organization_id (F-B2-8): the tenant is
#: resolved server-side from the parent batch; the document-level extraction
#: method stamp lives on the queue row (F-B2-15).
_CONTEXT_SQL = """
    SELECT i.id                 AS source_item_id,
           b.organization_id    AS organization_id,
           i.file_id            AS source_file_id,
           q.ai_extraction_method AS queue_extraction_method
      FROM public.manual_extraction_items i
      LEFT JOIN public.manual_extraction_batches b ON b.id = i.batch_id
      LEFT JOIN public.document_processing_queue q
             ON q.id = i.document_processing_queue_id
     WHERE i.id = $1
"""

#: Insert-if-absent — never an UPDATE (contract §11.3, B2-D2).
_INSERT_SQL = """
    INSERT INTO public.evidence_line_items (
        organization_id, source_item_id, source_file_id, line_number,
        source_page, row_reference, raw_description, raw_quantity, raw_unit,
        payload_hash, extraction_method, materialisation_kind
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    ON CONFLICT (source_item_id, line_number) DO NOTHING
    RETURNING id
"""

#: Keyset-paginated Class-1 scan (§11.4). ``extracted_data`` is only fetched for
#: items that actually carry a non-empty ``line_items`` array, and
#: ``line_count`` distinguishes the §11.1 skip categories without a second scan.
_BACKFILL_SQL = f"""
    SELECT i.id              AS source_item_id,
           b.organization_id AS organization_id,
           i.file_id         AS source_file_id,
           q.ai_extraction_method AS queue_extraction_method,
           CASE
             WHEN jsonb_typeof(i.extracted_data -> 'line_items') = 'array'
                  AND jsonb_array_length(i.extracted_data -> 'line_items') >= 1
             THEN i.extracted_data
             ELSE NULL
           END AS extracted_data,
           CASE
             WHEN jsonb_typeof(i.extracted_data -> 'line_items') = 'array'
             THEN jsonb_array_length(i.extracted_data -> 'line_items')
             ELSE {INELIGIBLE_LINE_COUNT}
           END AS line_count
      FROM public.manual_extraction_items i
      LEFT JOIN public.manual_extraction_batches b ON b.id = i.batch_id
      LEFT JOIN public.document_processing_queue q
             ON q.id = i.document_processing_queue_id
     WHERE i.id > $1
     ORDER BY i.id
     LIMIT $2
"""


def _row_to_line(row: Any) -> dict:
    """Map one ``evidence_line_items`` row to a plain dict (ids as strings)."""
    data = dict(row)
    for key in ("id", "organization_id", "source_item_id", "source_file_id"):
        if data.get(key) is not None:
            data[key] = str(data[key])
    if data.get("created_at") is not None:
        data["created_at"] = data["created_at"].isoformat()
    return data


def resolve_extraction_method(
    *,
    caller_supplied: Optional[str],
    per_line_override: Optional[str],
    document_level: Optional[str],
) -> str:
    """Extraction-method attribution (§11.2, §11.7).

    Priority: the element's own ``extraction_method`` key (per-line override,
    §11.7) → the value supplied by the write site (FORWARD) or the document-level
    stamp resolved by the operation (BACKFILL) → ``unknown``. The vocabulary is
    deliberately open (B2-D7) and ``unknown`` is the honest default.
    """
    for candidate in (per_line_override, caller_supplied, document_level):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return UNKNOWN_EXTRACTION_METHOD


@dataclass
class MaterialisationOutcome:
    """Per-item result of a materialisation attempt (§11.3 counts)."""

    source_item_id: str
    materialisation_kind: str
    eligible: bool
    materialised: int = 0
    skipped_exists: int = 0
    skipped_empty: int = 0
    skipped_malformed: int = 0
    skipped_no_lines: int = 0
    divergent_ordinals: tuple[int, ...] = ()
    line_item_ids: tuple[str, ...] = ()
    first_line_item_id: Optional[str] = None
    payload_digests: dict[str, str] = field(default_factory=dict)

    @property
    def wrote_rows(self) -> bool:
        return self.materialised > 0


@dataclass
class BackfillReport:
    """Run report of one Class-1 backfill invocation (§11.4)."""

    run_id: str
    dry_run: bool
    scanned_items: int = 0
    eligible_items: int = 0
    materialised_rows: int = 0
    skipped_empty: int = 0
    skipped_malformed: int = 0
    skipped_no_lines: int = 0
    divergences: int = 0
    errors: int = 0
    started_at: str = ""
    finished_at: str = ""
    audit_written: bool = False

    def as_payload(self) -> dict[str, Any]:
        """Audit payload (§17 backfill summary — counts and timestamps only)."""
        return {
            "dry_run": self.dry_run,
            "scanned_items": self.scanned_items,
            "eligible_items": self.eligible_items,
            "materialised_rows": self.materialised_rows,
            "skipped_empty": self.skipped_empty,
            "skipped_malformed": self.skipped_malformed,
            "skipped_no_lines": self.skipped_no_lines,
            "divergences": self.divergences,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }




class EvidenceLineItemsRepository(AbstractRepository[dict]):
    """Insert-only materialisation and organisation-scoped reads (§12.2)."""

    # -- audit (contract §17) -------------------------------------------------
    async def _record_audit(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: Optional[str],
        organization_id: Optional[str] = None,
        after: Optional[dict[str, Any]] = None,
        actor: str = _SYSTEM_ACTOR,
    ) -> bool:
        """Append ONE audit entry, best-effort (never breaks materialisation).

        Payloads stay compact and non-sensitive: counts, ordinals, ids and
        payload hashes only — never line values, documents or signed URLs.
        """
        if not entity_id:
            return False
        identifier = str(entity_id)
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=identifier,
            entity_type=entity_type,
            entity_id=identifier,
            action=action,
            actor=actor,
            occurred_at=datetime.now(timezone.utc),
            before=None,
            after=after,
            actor_type=ACTOR_SYSTEM if actor == _SYSTEM_ACTOR else None,
            organization_id=organization_id,
        )
        try:
            await AuditRepository(self._pool).record(entry)
            return True
        except Exception:  # noqa: BLE001 — audit must never break a materialisation
            logger.exception(
                "B2 audit (%s) failed for %s %s", action, entity_type, identifier
            )
            return False

    # -- context / reads ------------------------------------------------------
    async def _resolve_context(self, source_item_id: str) -> Optional[dict]:
        """Resolve tenant/document/method context server-side (never caller-supplied)."""
        row = await self._fetch_one(_CONTEXT_SQL, source_item_id)
        if row is None:
            return None
        data = dict(row)
        return {
            "organization_id": (
                str(data["organization_id"]) if data.get("organization_id") else None
            ),
            "source_file_id": (
                str(data["source_file_id"]) if data.get("source_file_id") else None
            ),
            "queue_extraction_method": data.get("queue_extraction_method"),
        }

    async def _existing_ordinals(
        self, source_item_id: str
    ) -> dict[int, tuple[str, str]]:
        rows = await self._fetch_all(
            "SELECT line_number, id, payload_hash FROM public.evidence_line_items "
            "WHERE source_item_id = $1",
            source_item_id,
        )
        return {
            int(r["line_number"]): (str(r["id"]), str(r["payload_hash"])) for r in rows
        }

    async def list_for_item(
        self, organization_id: str, source_item_id: str
    ) -> list[dict]:
        """Line rows of one document, ordered by ``line_number`` (§12.2)."""
        rows = await self._fetch_all(
            f"SELECT {_COLUMNS} FROM public.evidence_line_items "
            "WHERE organization_id = $1 AND source_item_id = $2 "
            "ORDER BY line_number",
            organization_id,
            source_item_id,
        )
        return [_row_to_line(r) for r in rows]

    async def get(self, id: str) -> Optional[dict]:
        """One line by its addressable id (§12.2)."""
        row = await self._fetch_one(
            f"SELECT {_COLUMNS} FROM public.evidence_line_items WHERE id = $1", id
        )
        return _row_to_line(row) if row is not None else None

    async def get_by_ordinals(
        self, source_item_id: str, ordinals: Sequence[int]
    ) -> dict[int, str]:
        """Ordinal → line id resolve used by the calculation integration (§13.2)."""
        wanted = [int(o) for o in ordinals]
        if not wanted:
            return {}
        rows = await self._fetch_all(
            "SELECT line_number, id FROM public.evidence_line_items "
            "WHERE source_item_id = $1 AND line_number = ANY($2::int[])",
            source_item_id,
            wanted,
        )
        return {int(r["line_number"]): str(r["id"]) for r in rows}

    async def count_for_item(self, source_item_id: str) -> int:
        """Population/eligibility audit helper (§12.2)."""
        value = await self._fetch_one(
            "SELECT count(*)::int AS n FROM public.evidence_line_items "
            "WHERE source_item_id = $1",
            source_item_id,
        )
        return int(value["n"]) if value is not None else 0


    # -- materialisation (insert-only; §11.3, §12.1) --------------------------
    async def materialise_for_item(
        self,
        *,
        source_item_id: str,
        extracted_data: Any,
        materialisation_kind: str,
        extraction_method: Optional[str] = None,
        organization_id: Optional[str] = None,
        source_file_id: Optional[str] = None,
        actor: str = _SYSTEM_ACTOR,
        emit_audit: bool = True,
        persist: bool = True,
    ) -> MaterialisationOutcome:
        """Derive and insert the missing lines of one item (§11.1–§11.3).

        ``persist=False`` is the dry-run mode of the Class-1 operation: identical
        counts, **zero writes** (§11.4). ``emit_audit=False`` suppresses audit
        emission (dry runs perform no writes at all of any kind).
        """
        if materialisation_kind not in MATERIALISATION_KINDS:
            raise ValueError(
                f"unknown materialisation_kind {materialisation_kind!r}; "
                f"expected one of {MATERIALISATION_KINDS}"
            )
        derivation = derive_line_candidates(extracted_data)
        outcome = MaterialisationOutcome(
            source_item_id=str(source_item_id),
            materialisation_kind=materialisation_kind,
            eligible=derivation.eligible,
            skipped_empty=derivation.skipped_empty,
            skipped_malformed=derivation.skipped_malformed,
            skipped_no_lines=derivation.skipped_no_lines,
        )
        if not derivation.candidates:
            return outcome

        context: Optional[dict] = None
        if (
            organization_id is None
            or source_file_id is None
            or extraction_method is None
        ):
            context = await self._resolve_context(str(source_item_id))
        organization = organization_id or (context or {}).get("organization_id")
        if not organization:
            raise ValueError(
                "evidence-line materialisation requires the parent batch's "
                f"organization_id; it could not be resolved for item {source_item_id}"
            )
        file_id = (
            source_file_id
            if source_file_id is not None
            else (context or {}).get("source_file_id")
        )
        document_level = (context or {}).get("queue_extraction_method")

        existing = await self._existing_ordinals(str(source_item_id))
        decisions = decide_ordinals(derivation.candidates, existing)
        candidates = {c.line_number: c for c in derivation.candidates}

        inserted: list[str] = []
        divergent_ordinals: list[int] = []
        divergent_line_ids: list[str] = []
        for decision in decisions:
            if decision.action == ACTION_DIVERGENCE:
                divergent_ordinals.append(decision.line_number)
                if decision.line_id:
                    divergent_line_ids.append(decision.line_id)
                continue
            if decision.action != ACTION_INSERT:
                outcome.skipped_exists += 1
                continue
            candidate = candidates[decision.line_number]
            if not persist:
                outcome.materialised += 1
                outcome.payload_digests[str(decision.line_number)] = (
                    candidate.payload_hash
                )
                continue
            row = await self._fetch_one(
                _INSERT_SQL,
                organization,
                str(source_item_id),
                file_id,
                candidate.line_number,
                candidate.source_page,
                candidate.row_reference,
                candidate.raw_description,
                candidate.raw_quantity,
                candidate.raw_unit,
                candidate.payload_hash,
                resolve_extraction_method(
                    caller_supplied=extraction_method,
                    per_line_override=candidate.extraction_method_override,
                    document_level=document_level,
                ),
                materialisation_kind,
            )
            if row is None:
                # A concurrent writer already owns this identity: skip, never update.
                outcome.skipped_exists += 1
                continue
            inserted.append(str(row["id"]))
            outcome.materialised += 1
            outcome.payload_digests[str(decision.line_number)] = candidate.payload_hash

        outcome.divergent_ordinals = tuple(divergent_ordinals)
        outcome.line_item_ids = tuple(inserted)
        outcome.first_line_item_id = inserted[0] if inserted else None

        if emit_audit and divergent_ordinals:
            await self._record_audit(
                action=AUDIT_LINE_ITEMS_DIVERGENCE_DETECTED,
                entity_type="manual_extraction_items",
                entity_id=str(source_item_id),
                organization_id=organization,
                after={
                    "divergent_ordinals": divergent_ordinals,
                    "line_item_ids": divergent_line_ids,
                },
            )
        if emit_audit and materialisation_kind == MATERIALISATION_FORWARD and inserted:
            await self._record_audit(
                action=AUDIT_LINE_ITEMS_MATERIALISED,
                entity_type="manual_extraction_items",
                entity_id=str(source_item_id),
                organization_id=organization,
                actor=actor,
                after={
                    "materialised": outcome.materialised,
                    "skipped_empty": outcome.skipped_empty,
                    "skipped_malformed": outcome.skipped_malformed,
                    "first_line_item_id": outcome.first_line_item_id,
                    "payload_digests": outcome.payload_digests,
                },
            )
        return outcome


    # -- Class-1 backfill (§11.4, §12.1) --------------------------------------
    async def backfill(
        self,
        *,
        dry_run: bool = True,
        batch_size: int = 500,
        limit: Optional[int] = None,
        emit_audit: bool = True,
    ) -> BackfillReport:
        """Idempotent, batched, resumable Class-1 materialisation (§11.4).

        Read-only on every other table; inserts only missing evidence lines;
        never updates, deletes, renumbers, re-extracts or infers. A dry run
        produces the **identical counts with zero writes** — including zero
        audit writes, so "zero writes" is literally true. The run report is the
        evidence of the run; one summary audit event is written per real run
        (§17, B2-D5).
        """
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        write_audit = emit_audit and not dry_run
        report = BackfillReport(
            run_id=str(uuid.uuid4()),
            dry_run=dry_run,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        cursor = _ZERO_UUID
        while True:
            take = batch_size if limit is None else min(batch_size, limit)
            if take <= 0:
                break
            rows = await self._fetch_all(_BACKFILL_SQL, cursor, take)
            if not rows:
                break
            for row in rows:
                report.scanned_items += 1
                line_count = int(row["line_count"])
                if line_count == INELIGIBLE_LINE_COUNT:
                    continue  # ineligible: no line_items[] at all (§11.1)
                if line_count == 0:
                    report.skipped_no_lines += 1
                    continue
                report.eligible_items += 1
                try:
                    outcome = await self.materialise_for_item(
                        source_item_id=str(row["source_item_id"]),
                        extracted_data=loads_jsonb(row["extracted_data"]),
                        materialisation_kind=MATERIALISATION_BACKFILL,
                        organization_id=(
                            str(row["organization_id"])
                            if row.get("organization_id")
                            else None
                        ),
                        source_file_id=(
                            str(row["source_file_id"])
                            if row.get("source_file_id")
                            else None
                        ),
                        emit_audit=write_audit,
                        persist=not dry_run,
                    )
                except Exception:  # noqa: BLE001 — one bad item never aborts the run
                    report.errors += 1
                    logger.exception(
                        "B2 backfill: materialisation failed for item %s",
                        row["source_item_id"],
                    )
                    continue
                report.materialised_rows += outcome.materialised
                report.skipped_empty += outcome.skipped_empty
                report.skipped_malformed += outcome.skipped_malformed
                report.divergences += len(outcome.divergent_ordinals)
            cursor = str(rows[-1]["source_item_id"])
            if limit is not None:
                limit -= len(rows)
            if len(rows) < take:
                break

        report.finished_at = datetime.now(timezone.utc).isoformat()
        if write_audit:
            report.audit_written = await self._record_audit(
                action=AUDIT_LINE_ITEMS_BACKFILLED,
                entity_type="evidence_line_items",
                entity_id=report.run_id,
                after=report.as_payload(),
            )
        return report

    # -- AbstractRepository contract -----------------------------------------
    async def save(self, entity: dict) -> dict:
        """No authoring path exists: a line is *derived*, never authored (§12.3)."""
        return entity

    async def delete(self, id: str) -> None:
        """B2 has **no** delete path (B2-D11; retention is a separate workstream)."""
        raise NotImplementedError(
            "evidence_line_items are immutable provenance records: B2 defines no "
            "delete path (contract §12.3, B2-D11)."
        )
