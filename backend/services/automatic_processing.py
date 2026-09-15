"""Automatic document-processing pipeline service (V3 Phase A / CL-56).

The execution engine between the durable job store
(:class:`data.document_processing.DocumentProcessingRepository`) and the
existing business engines (extraction, matching, validation, calculation).
It is intentionally stateless per job: every decision is derived from the
persisted job row, so the background worker can crash and resume safely.

Stage model (see :mod:`domain.automatic_processing`)::

    enqueued -> ingesting -> extracting -> mapping -> validating
    -> calculating -> review -> completed
    (blocked = manual-review gate, re-enters at enqueued after human action)

Idempotency
-----------
A stage's persisted output is its resume marker. ``process_job`` skips any
stage whose marker already exists, and the calculation stage derives a
deterministic ``match_request_id`` per job and reuses an existing snapshot with
that request id (no duplicate calculations even across crashes).

Gates
-----
* extraction completeness below ``AUTO_EXTRACT_CONFIDENCE_MIN`` -> blocked;
* any line without a confident factor match -> blocked;
* blocking validation findings -> blocked;
* every successful pipeline run stops at ``review`` for the distinct customer/
  owner verification (D5) before ``completed``.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date as _Date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from core.logging import get_logger
from domain.automatic_processing import (
    AUTO_EXTRACT_CONFIDENCE_MIN,
    AUTO_MAPPING_CONFIDENCE_MIN,
    REQUIRED_EXTRACT_FIELDS,
    RUNNABLE_STAGES,
    AutomaticProcessingJob,
)
from engines.calculation import CalculationEngine, CalculationRequest
from engines.calculation import CalculationEngine
from engines.processing_workflow import has_blocking_findings, validate_processing_item
from infra.ai_runtime import configured_ai_attribution
from infra.event_bus import EventBus
from infra.supabase import get_service_client
from services.automatic_extraction import (
    completeness_score,
    extract_document,
    extract_document_text,
)
from services.storage import DOCUMENTS_BUCKET, path_from_url

logger = get_logger(__name__)

#: Cap on in-memory source bytes the worker will ingest.
_MAX_INGEST_BYTES = 60 * 1024 * 1024

#: Worker/system actor id recorded on synced manual-extraction items.
_SYSTEM_ACTOR = "00000000-0000-0000-0000-000000000000"

#: WS4 Gate 5 (task T4) — machine actor label for the automatic-processing
#: extraction audit event (design 5.3). A machine label, NOT a user/PE/role/D38
#: identity and never an authorization principal.
_AUTOMATION_ACTOR = "automatic_pipeline"


def _calc_payload_digest(
    extracted: Optional[dict], mapped: Optional[dict]
) -> str:
    """Deterministic digest of the authoritative working data at calculate time.

    WS4 Gate 6 (workstream W4 / gap G6-D): the per-line calculation request id
    is keyed on this digest so (a) a crashed re-run with IDENTICAL data reuses
    the exact snapshot (no duplicate calculations), while (b) a human-corrected
    payload produces a DIFFERENT request id and therefore a NEW snapshot instead
    of silently reusing the pre-correction snapshot. Canonical JSON keeps the
    digest stable across value ordering.
    """
    canonical = json.dumps(
        {"e": extracted, "m": mapped},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _parse_date(value: Any) -> Optional[_Date]:
    """Parse common invoice-date formats into a ``date`` (never raises)."""
    if value is None:
        return None
    if isinstance(value, _Date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %B %Y", "%d %b %Y", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _methodology_for(factor_kind: str, unit: Optional[str]) -> str:
    """Map a matched factor to a valid :class:`CalculationMethodology`.

    ``MatchResult.methodology`` carries the matching-stage name (e.g.
    ``keyword_search``), which is NOT a calculation methodology — mapping it
    straight into :class:`CalculationRequest` fails the enum validation. The
    methodology is derived from the factor's nature instead:
    * a customer factor with a currency unit is ``spend_based``;
    * a distance unit is ``distance_based``;
    * everything else is ``direct_multiply``.
    """
    if factor_kind == "customer_factor" and unit:
        if unit.strip().upper() in ("GBP", "EUR", "USD"):
            return "spend_based"
    if unit and str(unit).strip().lower() in ("km", "miles", "mile"):
        return "distance_based"
    return "direct_multiply"


def _missing_required(extracted: dict) -> list[str]:
    """Unresolved canonical pipeline fields in ``extracted`` (for gate reasons).

    Mirrors the completeness semantics: for a single-line document the required
    top-level fields are checked; for a tabular document the union of the fields
    still missing across every line is returned.
    """
    data = extracted or {}
    lines = data.get("line_items") or []
    if lines:
        missing: set[str] = set()
        for line in lines:
            if not isinstance(line, dict):
                continue
            for field in ("activity", "quantity", "unit"):
                if not str(line.get(field) or "").strip():
                    missing.add(field)
        return sorted(missing)
    return [
        field
        for field in ("activity", "quantity", "unit")
        if not str(data.get(field) or "").strip()
    ]


def _merge_extraction_candidates(deterministic: dict, ai: dict) -> dict:
    """Merge an AI candidate under deterministic authority (Phase 2).

    Fields the deterministic extractor already resolved are preserved verbatim;
    AI fills only what deterministic left unresolved. When deterministic
    produced no table but AI did, the AI table is the only candidate. The merge
    never overwrites source evidence — it composes two candidate passes before
    the deterministic gate.
    """
    out = dict(deterministic or {})
    if not ai:
        return out
    det_lines = out.get("line_items") or []
    ai_lines = ai.get("line_items") or []
    if det_lines:
        merged_lines: list[dict] = []
        for idx, line in enumerate(det_lines):
            if not isinstance(line, dict):
                continue
            merged = dict(line)
            other = (
                ai_lines[idx]
                if idx < len(ai_lines) and isinstance(ai_lines[idx], dict)
                else {}
            )
            for field in (
                "activity", "quantity", "unit", "date",
                "supplier", "amount", "currency", "invoice_number",
            ):
                if not str(merged.get(field) or "").strip() and str(
                    other.get(field) or ""
                ).strip():
                    merged[field] = other[field]
            merged_lines.append(merged)
        out["line_items"] = merged_lines
        return out
    if ai.get("line_items"):
        return dict(ai)
    for field in (
        "activity", "quantity", "unit", "date",
        "supplier", "amount", "currency", "invoice_number",
    ):
        if not str(out.get(field) or "").strip() and str(
            ai.get(field) or ""
        ).strip():
            out[field] = ai[field]
    return out


class AutomaticProcessingService:
    """Runs one durable job through the automatic pipeline stages."""

    def __init__(
        self,
        repos,
        *,
        event_bus: Optional[EventBus] = None,
        audit_logger=None,
        matching_engine=None,
        calculation_engine: Optional[CalculationEngine] = None,
        ai_extraction_engine=None,
    ) -> None:
        self._repos = repos
        self._event_bus = event_bus
        self._audit_logger = audit_logger
        self._matching_engine = matching_engine
        self._calculation_engine = calculation_engine
        self._ai_extraction_engine = ai_extraction_engine
        self._content_cache: dict[str, bytes] = {}

    @property
    def ai_extraction_engine(self):
        """The optional candidate AI extraction engine (None = deterministic)."""
        return self._ai_extraction_engine

    @property
    def repos(self):
        """The repository bundle the service persists through."""
        return self._repos

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    async def process_job(
        self, job: AutomaticProcessingJob, lock_token: str
    ) -> AutomaticProcessingJob:
        """Advance ``job`` through every runnable stage it is eligible for.

        Idempotent: stages whose persisted output already exists are skipped.
        The claim is released when the job reaches a human gate (``blocked`` /
        ``review``) or a terminal state (``completed``/``failed``).
        """
        guard = 0
        current = job
        while current is not None and current.stage in RUNNABLE_STAGES and guard < 30:
            guard += 1
            target = await self._run_stage(current, lock_token)
            if target == "blocked":
                # The stage already persisted the manual-review gate + reason;
                # reload and skip the fallback so the specific reason survives.
                after = await self._repos.processing.get(current.id)
                if after is not None and after.stage == "blocked":
                    current = after
                    break
                await self._repos.processing.mark_blocked(
                    current.id,
                    reason=current.manual_review_reason or "manual review required",
                    lock_token=lock_token,
                )
                current = await self._repos.processing.get(current.id)
                break
            if target == "failed":
                await self._repos.processing.mark_failed(
                    current.id,
                    last_error=current.last_error or "automatic processing failed",
                    lock_token=lock_token,
                    attempt_count=current.attempt_count,
                )
                current = await self._repos.processing.get(current.id)
                break
            next_job = await self._repos.processing.get(current.id)
            if next_job is None:
                break
            # Safety net: no progress (same stage, no new outputs) must not spin.
            if next_job.stage == current.stage and guard > 1:
                logger.error(
                    "job %s made no progress at stage %s (guard %d)",
                    current.id, current.stage, guard,
                )
                break
            current = next_job
        if current is not None:
            await self._repos.processing.release_lock(current.id, lock_token)
        self._content_cache.pop(job.id, None)
        return current or job

    async def _run_stage(self, job: AutomaticProcessingJob, lock_token: str) -> str:
        """Execute one stage and return the next stage name (or gate/terminal)."""
        stage = job.stage or "enqueued"
        try:
            if stage in ("enqueued", "ingesting"):
                return await self._ingest(job, lock_token)
            if stage == "extracting":
                return await self._extract(job, lock_token)
            if stage == "mapping":
                return await self._map(job, lock_token)
            if stage == "validating":
                return await self._validate(job, lock_token)
            if stage == "calculating":
                return await self._calculate(job, lock_token)
        except Exception as exc:  # noqa: BLE001 — failures become failed jobs
            logger.exception("automatic processing failed for job %s", job.id)
            await self._repos.processing.mark_failed(
                job.id,
                last_error=f"{type(exc).__name__}: {exc}"[:1000],
                lock_token=lock_token,
                attempt_count=job.attempt_count + 1,
            )
            return "failed"
        # Human gates and terminal stages are not worker-runnable.
        return stage

    # ------------------------------------------------------------------
    # Stage: ingest
    # ------------------------------------------------------------------

    async def _ingest(self, job: AutomaticProcessingJob, lock_token: str) -> str:
        """Read the source object from private storage (idempotent read)."""
        content = self._content_cache.get(job.id)
        if content is None:
            content = await self._download(job)
        if content is None:
            await self._repos.processing.mark_blocked(
                job.id,
                reason="source document could not be read from storage",
                lock_token=lock_token,
            )
            return "blocked"
        self._content_cache[job.id] = content
        await self._repos.processing.advance_stage(
            job.id,
            target_stage="extracting",
            lock_token=lock_token,
            page_count=job.metadata.get("page_count") or 0,
        )
        return "extracting"

    async def _download(self, job: AutomaticProcessingJob) -> Optional[bytes]:
        """Download the source object server-side (never leaks to clients)."""
        path = path_from_url(job.file_url)
        if not path:
            return None
        try:
            obj = get_service_client().storage.from_(DOCUMENTS_BUCKET).download(path)
            data = obj if isinstance(obj, bytes) else bytes(getattr(obj, "read", lambda: b"")())
            if len(data) > _MAX_INGEST_BYTES:
                logger.warning("job %s exceeds ingest cap (%d bytes)", job.id, len(data))
                return None
            return data
        except Exception as exc:  # noqa: BLE001
            logger.warning("storage download failed for job %s: %r", job.id, exc)
            return None

    # ------------------------------------------------------------------
    # Stage: extracting
    # ------------------------------------------------------------------

    async def _extract(self, job: AutomaticProcessingJob, lock_token: str) -> str:
        """Extract structured data; low completeness routes to manual review."""
        if job.extracted_data:
            await self._repos.processing.advance_stage(
                job.id,
                target_stage="mapping",
                lock_token=lock_token,
            )
            return "mapping"  # resume marker already exists (idempotent resume)
        content = self._content_cache.get(job.id) or await self._download(job)
        if content is None:
            await self._repos.processing.mark_blocked(
                job.id,
                reason="source document could not be read from storage",
                lock_token=lock_token,
            )
            return "blocked"
        result = extract_document(content, job.file_name, job.metadata.get("mime") or "")
        extracted = result.get("extracted_data") or {}
        method = result.get("method") or "unknown"
        if result.get("status") not in ("ok",):
            await self._repos.processing.mark_blocked(
                job.id,
                reason=(
                    f"extraction {result.get('status')}: "
                    f"{result.get('detail') or 'no usable data'}"
                ),
                lock_token=lock_token,
                last_error=result.get("detail"),
            )
            return "blocked"
        confidence = float(result.get("confidence") or 0.0)
        method_stamp = method
        # ------------------------------------------------------------------
        # Phase 2 — optional candidate AI extraction. Runs only when an AI
        # engine is configured AND the deterministic pass is below the auto
        # completeness threshold (manual-review rescue) or the job explicitly
        # requests AI (prefer_ai / ai_required). AI output is candidate data:
        # deterministic fields win, the deterministic gate still applies, and
        # mapping/validation/calculation consume the merged result unchanged.
        # ------------------------------------------------------------------
        ai_meta: Optional[dict] = None
        if self._ai_extraction_engine is not None and (
            confidence < AUTO_EXTRACT_CONFIDENCE_MIN
            or job.metadata.get("prefer_ai")
            or job.metadata.get("force_ai")
            or job.metadata.get("ai_required")
        ):
            ai_meta, extracted, confidence, method_stamp = (
                await self._run_ai_candidate(
                    job, content, extracted, confidence, method
                )
            )
            if ai_meta is not None and ai_meta.get("status") != "ok":
                if (
                    job.metadata.get("ai_required")
                    or confidence < AUTO_EXTRACT_CONFIDENCE_MIN
                ):
                    # Durable failure: the job is blocked for human review with
                    # the AI failure reason — never silently successful.
                    await self._repos.processing.mark_blocked(
                        job.id,
                        reason=(
                            f"AI extraction failed: {ai_meta.get('detail') or 'error'} "
                            f"(deterministic completeness {confidence:.2f} below "
                            f"{AUTO_EXTRACT_CONFIDENCE_MIN:.2f} threshold)"
                        ),
                        lock_token=lock_token,
                        last_error=str(ai_meta.get("detail"))[:1000],
                    )
                    return "blocked"
                logger.warning(
                    "AI extraction failed for job %s but deterministic data "
                    "already cleared the gate (proceeding)",
                    job.id,
                )
        if confidence < AUTO_EXTRACT_CONFIDENCE_MIN:
            missing = _missing_required(extracted)
            await self._repos.processing.mark_blocked(
                job.id,
                reason=(
                    f"extraction completeness {confidence:.2f} below "
                    f"{AUTO_EXTRACT_CONFIDENCE_MIN:.2f} threshold — unresolved: "
                    f"{', '.join(missing) or 'no usable data'}"
                ),
                lock_token=lock_token,
            )
            return "blocked"
        # Sync the manual-extraction item so the existing workspace stays live.
        if job.source_item_id:
            try:
                await self._repos.manual_extraction.save_extracted_data(
                    job.source_item_id, extracted, _SYSTEM_ACTOR
                )
            except Exception:  # noqa: BLE001 — item sync must not break the job
                logger.exception("item extraction sync failed for job %s", job.id)
        ai_extraction_result = None
        ai_extracted_at = None
        ai_processing_time_ms = None
        if ai_meta is not None:
            ai_extracted_at = datetime.now(timezone.utc)
            ai_processing_time_ms = int(ai_meta.get("processing_time_ms") or 0)
            ai_extraction_result = {
                "status": ai_meta.get("status"),
                "method": ai_meta.get("method"),
                "model": ai_meta.get("model"),
                "confidence": ai_meta.get("confidence"),
                "unresolved": ai_meta.get("unresolved") or [],
                "detail": ai_meta.get("detail"),
            }
        # WS4 Gate 5 (task T3) — write-once automated-execution attribution.
        # Only a CONTRIBUTING AI pass (status ok) records provider/model/version;
        # deterministic-only outputs and failed-AI attempts leave the block NULL
        # (truthful provenance). Facts come from the accepted T2 helper and are
        # written via COALESCE (first-write-wins) in the repository.
        automation_attribution: dict = {}
        if ai_meta is not None and ai_meta.get("status") == "ok":
            try:
                automation_attribution = configured_ai_attribution()
            except Exception:  # noqa: BLE001 - attribution must never break the job
                logger.exception(
                    "AI attribution facts unavailable for job %s", job.id
                )
        await self._repos.processing.advance_stage(
            job.id,
            target_stage="mapping",
            lock_token=lock_token,
            extracted_data=extracted,
            attempt_count=job.attempt_count + 1,
            page_count=result.get("page_count") or 0,
            ai_confidence_score=confidence,
            ai_extraction_method=method_stamp,
            metadata={"ai_extraction": ai_meta} if ai_meta is not None else None,
            ai_extraction_result=ai_extraction_result,
            ai_extracted_at=ai_extracted_at,
            ai_processing_time_ms=ai_processing_time_ms,
            automation_provider=automation_attribution.get("provider"),
            automation_model=automation_attribution.get("model"),
            automation_model_version=automation_attribution.get("model_version"),
            # WS4 Gate 6 (workstream W1 / gap G6-A) — preserve the ORIGINAL
            # machine-produced extraction output at the same write-once advance
            # that first persists it. Deterministic-only runs are eligible (the
            # automatic pipeline produced the output); the automation_* block
            # above stays NULL for them. Human edits of `extracted_data` later
            # can never replace or delete this preserved original.
            automation_extracted_data=extracted,
        )
        # WS4 Gate 5 (task T4) — append-only extraction audit event with the
        # machine actor, fired AFTER the persisted advance (best-effort; audit
        # failure never breaks the job).
        await self._audit_extraction(
            job,
            method_stamp=method_stamp,
            automation_attribution=automation_attribution,
            ai_meta=ai_meta,
            confidence=confidence,
        )
        return "mapping"

    async def _run_ai_candidate(
        self,
        job: AutomaticProcessingJob,
        content: bytes,
        extracted: dict,
        confidence: float,
        deterministic_method: str,
    ) -> tuple[Optional[dict], dict, float, str]:
        """Run one candidate AI extraction pass over the deterministic text.

        Returns ``(ai_meta, extracted, confidence, method_stamp)``. On success
        the deterministic and AI candidates are merged (deterministic wins) and
        the merged completeness is returned. Every failure path returns an
        ``error`` ai_meta so the durable caller can represent it durably.
        """
        # WS4 Gate 5 (task T3, G5) — failure envelopes must record the model id
        # that was actually attempted (the engine's configured model) instead of
        # ``None``, so the durable record can answer "which model was attempted?"
        # truthfully. Never a credential.
        def _attempted_model() -> Optional[str]:
            try:
                return self._ai_extraction_engine.llm_client.model
            except Exception:  # noqa: BLE001 - attribution must never break the job
                return None

        try:
            from time import monotonic

            text_layer = extract_document_text(
                content, job.file_name, job.metadata.get("mime") or ""
            )
            if text_layer.get("status") != "ok":
                return (
                    {
                        "status": "error",
                        "method": "ai",
                        "model": _attempted_model(),
                        "detail": text_layer.get("detail")
                        or f"no text layer ({text_layer.get('status')})",
                    },
                    extracted,
                    confidence,
                    deterministic_method,
                )
            started = monotonic()
            candidate = await self._ai_extraction_engine.extract_candidate(
                text_layer.get("text") or "",
                filename=job.file_name,
                method=text_layer.get("method") or deterministic_method,
            )
            elapsed_ms = int((monotonic() - started) * 1000)
        except Exception as exc:  # noqa: BLE001 — AI failure is a durable event
            logger.exception("AI extraction crashed for job %s", job.id)
            return (
                {
                    "status": "error",
                    "method": "ai",
                    "model": _attempted_model(),
                    "detail": f"{type(exc).__name__}: {exc}"[:300],
                },
                extracted,
                confidence,
                deterministic_method,
            )
        model = candidate.get("model") or _attempted_model()
        ai_method = candidate.get("method") or "ai"
        if candidate.get("status") != "ok":
            return (
                {
                    "status": "error",
                    "method": ai_method,
                    "model": model,
                    "detail": candidate.get("detail") or candidate.get("status"),
                    "processing_time_ms": elapsed_ms,
                },
                extracted,
                confidence,
                deterministic_method,
            )
        merged = _merge_extraction_candidates(
            extracted, candidate.get("extracted_data") or {}
        )
        merged_confidence = completeness_score(merged)
        ai_meta = {
            "status": "ok",
            "method": ai_method,
            "model": model,
            "confidence": round(float(candidate.get("confidence") or 0.0), 4),
            "merged_confidence": round(merged_confidence, 4),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "processing_time_ms": elapsed_ms,
            "unresolved": candidate.get("unresolved") or [],
        }
        method_stamp = f"{deterministic_method}+{ai_method}"
        return ai_meta, merged, merged_confidence, method_stamp

    async def _audit_extraction(
        self,
        job: AutomaticProcessingJob,
        *,
        method_stamp: str,
        automation_attribution: dict,
        ai_meta: Optional[dict],
        confidence: float,
    ) -> None:
        """Best-effort append-only audit of one persisted automated extraction.

        WS4 Gate 5 (task T4, design 5.3): one ``automatic_processing:extracted``
        event per persisted extraction execution, correlated directly to the
        durable job (``entity_id``/``correlation_id`` = job id) and carrying the
        machine-attribution block plus the machine actor label. The audit trail
        is append-only/deny-by-default and service-role written. Audit failures
        are logged and never break the job.
        """
        if self._audit_logger is None:
            return
        try:
            await self._audit_logger.log_action(
                action="automatic_processing:extracted",
                entity_type="document_processing_queue",
                entity_id=job.id,
                correlation_id=job.id,
                actor=_AUTOMATION_ACTOR,
                after={
                    "method": method_stamp,
                    "pipeline_version": job.pipeline_version,
                    "provider": automation_attribution.get("provider"),
                    "model": automation_attribution.get("model"),
                    "model_version": automation_attribution.get("model_version"),
                    "confidence": round(float(confidence), 4),
                    "attempt_count": job.attempt_count + 1,
                    "source_item_id": job.source_item_id,
                    "ai_status": (ai_meta or {}).get("status"),
                },
            )
        except Exception:  # noqa: BLE001 - audit must never break the job
            logger.exception(
                "automatic-extraction audit failed for job %s", job.id
            )

    # ------------------------------------------------------------------
    # Stage: mapping
    # ------------------------------------------------------------------

    async def _map(self, job: AutomaticProcessingJob, lock_token: str) -> str:
        """Auto-map activity/unit to an emission factor (D-cf-5 precedence)."""
        if job.mapped_data:
            await self._repos.processing.advance_stage(
                job.id,
                target_stage="validating",
                lock_token=lock_token,
            )
            return "validating"  # resume marker exists
        if self._matching_engine is None:
            await self._repos.processing.mark_blocked(
                job.id,
                reason="matching engine unavailable",
                lock_token=lock_token,
            )
            return "blocked"
        from domain.matching import MatchRequest

        extracted = job.extracted_data or {}
        line_items = extracted.get("line_items") or []
        targets = line_items if line_items else [dict(extracted)]
        mapped_lines: list[dict[str, Any]] = []
        reasons: list[str] = []
        reporting_year = datetime.now().year
        parsed_date = _parse_date(extracted.get("date"))
        if parsed_date is not None:
            reporting_year = parsed_date.year
        for idx, line in enumerate(targets):
            activity = str(line.get("activity") or "").strip()
            unit = str(line.get("unit") or "").strip() or None
            if unit is not None:
                from core.units import normalize_unit

                normalized = normalize_unit(unit)
                if normalized:
                    unit = normalized
            if not activity:
                reasons.append(f"line {idx + 1}: activity missing")
                continue
            request_id = str(
                uuid.uuid5(uuid.NAMESPACE_DNS, f"{job.id}::map::{idx}")
            )
            try:
                request = MatchRequest(
                    id=request_id,
                    activity=activity,
                    country="GB",
                    reporting_year=reporting_year,
                    unit=unit,
                    organization_id=job.organization_id,
                    max_stages=6,
                )
                result = await self._matching_engine.match(request)
                result = await self._prefer_aggregate_factor(
                    activity, unit, result
                )
            except Exception as exc:  # noqa: BLE001
                reasons.append(f"line {idx + 1}: matching failed ({exc})")
                continue
            if result.status != "matched" or result.confidence < AUTO_MAPPING_CONFIDENCE_MIN:
                reasons.append(
                    f"line {idx + 1}: no confident factor for "
                    f"{activity!r} {unit or ''} (status={result.status}, "
                    f"confidence={result.confidence:.2f})"
                )
                continue
            factor_id = (
                result.customer_factor_id
                if result.factor_kind == "customer_factor"
                else result.factor.id if result.factor is not None else None
            )
            if factor_id is None:
                reasons.append(f"line {idx + 1}: matched factor has no id")
                continue
            mapped_lines.append(
                {
                    "factor_id": factor_id,
                    "factor_kind": result.factor_kind,
                    "mapping_confidence": round(result.confidence, 4),
                    "activity": activity,
                    "unit": unit or "",
                    "methodology": result.methodology,
                    "stages_executed": list(result.stages_executed),
                }
            )
        if reasons:
            await self._repos.processing.mark_blocked(
                job.id,
                reason="mapping could not auto-resolve: " + "; ".join(reasons[:6]),
                lock_token=lock_token,
            )
            return "blocked"
        if line_items:
            mapped_data: dict[str, Any] = {"line_items": mapped_lines}
        else:
            mapped_data = mapped_lines[0] if mapped_lines else {}
        emission_factor_used = (
            mapped_data.get("factor_id") if not line_items else None
        )
        if job.source_item_id:
            try:
                await self._repos.manual_extraction.save_mapped_data(
                    job.source_item_id,
                    mapped_data,
                    None,
                    None,
                    None,
                    emission_factor_used,
                )
            except Exception:  # noqa: BLE001
                logger.exception("item mapping sync failed for job %s", job.id)
        best_confidence = max(
            (float(m.get("mapping_confidence") or 0.0) for m in mapped_lines),
            default=0.0,
        )
        await self._repos.processing.advance_stage(
            job.id,
            target_stage="validating",
            lock_token=lock_token,
            mapped_data=mapped_data,
            emission_factor_used=emission_factor_used,
            ai_mapping_confidence=best_confidence,
        )
        return "validating"

    # ------------------------------------------------------------------
    # Stage: validating
    # ------------------------------------------------------------------

    async def _validate(self, job: AutomaticProcessingJob, lock_token: str) -> str:
        """Run item-level validation; blocking findings route to manual review."""
        if job.validation_result and job.validation_result.get("status") == "passed":
            await self._repos.processing.advance_stage(
                job.id,
                target_stage="calculating",
                lock_token=lock_token,
            )
            return "calculating"  # resume marker exists
        from domain.partners import ManualExtractionItem

        item = ManualExtractionItem(
            id=job.source_item_id or job.id,
            batch_id=job.id,
            file_name=job.file_name,
            file_url=job.file_url,
            page_count=0,
            status="validating",
            extracted_data=job.extracted_data,
            mapped_data=job.mapped_data,
            calculated_emissions_kg_co2e=None,
        )
        findings = validate_processing_item(item)
        from dataclasses import asdict

        findings_list = [asdict(f) for f in findings]
        if has_blocking_findings(findings):
            await self._repos.processing.advance_stage(
                job.id,
                target_stage="validating",
                lock_token=lock_token,
                validation_result={"status": "failed", "findings": findings_list},
            )
            await self._repos.processing.mark_blocked(
                job.id,
                reason=(
                    "validation found blocking findings: "
                    + "; ".join(
                        f"{f['code']} ({f.get('field') or 'item'})"
                        for f in findings_list[:5]
                    )
                ),
                lock_token=lock_token,
            )
            return "blocked"
        if job.source_item_id:
            try:
                await self._repos.manual_extraction.set_item_status(
                    job.source_item_id, "validated"
                )
            except Exception:  # noqa: BLE001
                logger.exception("item validation sync failed for job %s", job.id)
        await self._repos.processing.advance_stage(
            job.id,
            target_stage="calculating",
            lock_token=lock_token,
            validation_result={"status": "passed", "findings": findings_list},
        )
        return "calculating"

    async def _prefer_aggregate_factor(self, activity: str, unit: Optional[str], result):
        """Prefer the aggregate CO2e/CO2 factor over sub-gas component factors.

        The matching pipeline can resolve an activity to a sub-contribution
        factor (e.g. ``Natural gas (kg CO2e of CH4 per unit)``) whose
        multiplier only covers one greenhouse-gas component. For automatic
        mapping, the deterministic ``find_by_activity`` candidates are
        re-scored: the first unit-compatible candidate that is NOT a
        per-component sub-factor is preferred, mirroring the factor a human
        mapper would pick. Only downgrades component-factor matches; never
        fabricates a candidate.
        """
        marker = ("of CH4 per unit", "of N2O per unit", "of CO2 per unit", "of CO2e per unit")
        if result.status != "matched" or result.factor is None:
            return result
        if not any(m in result.factor.activity_type for m in marker):
            return result  # already an aggregate/whole-gas factor
        try:
            # P2 EF-E (PO D-A(b), D-B T2): a qualified aggregate factor must be
            # discoverable, otherwise a component-only factor is retained.
            candidates = await self._repos.factors.find_by_activity(
                activity, unit=unit, limit=20, unit_qualifier_tolerant=True
            )
            aggregate = next(
                (f for f in candidates if not any(m in f.activity_type for m in marker)),
                None,
            )
            if aggregate is not None:
                from dataclasses import replace

                return replace(result, factor=aggregate)
        except Exception:  # noqa: BLE001 — preference must never break mapping
            logger.exception("aggregate-factor preference failed for %r", activity)
        return result

    # ------------------------------------------------------------------
    # Notifications / status updates
    # ------------------------------------------------------------------


        item = ManualExtractionItem(
            id=job.source_item_id or job.id,
            batch_id=job.id,
            file_name=job.file_name,
            file_url=job.file_url,
            page_count=0,
            status="validating",
            extracted_data=job.extracted_data,
            mapped_data=job.mapped_data,
            calculated_emissions_kg_co2e=None,
        )
        findings = validate_processing_item(item)
        from dataclasses import asdict

        findings_list = [asdict(f) for f in findings]
        if has_blocking_findings(findings):
            await self._repos.processing.advance_stage(
                job.id,
                target_stage="validating",
                lock_token=lock_token,
                validation_result={"status": "failed", "findings": findings_list},
            )
            await self._repos.processing.mark_blocked(
                job.id,
                reason=(
                    "validation found blocking findings: "
                    + "; ".join(
                        f"{f['code']} ({f.get('field') or 'item'})"
                        for f in findings_list[:5]
                    )
                ),
                lock_token=lock_token,
            )
            return "blocked"
        if job.source_item_id:
            try:
                await self._repos.manual_extraction.set_item_status(
                    job.source_item_id, "validated"
                )
            except Exception:  # noqa: BLE001
                logger.exception("item validation sync failed for job %s", job.id)
        await self._repos.processing.advance_stage(
            job.id,
            target_stage="calculating",
            lock_token=lock_token,
            validation_result={"status": "passed", "findings": findings_list},
        )
        return "calculating"

    # ------------------------------------------------------------------
    # Stage: calculating (authoritative, no-duplicate-guarded)
    # ------------------------------------------------------------------

    async def _calculate(self, job: AutomaticProcessingJob, lock_token: str) -> str:
        """Run the authoritative calculation -> snapshot + emissions + evidence."""
        if job.calculation_snapshot_id:
            await self._repos.processing.advance_stage(
                job.id,
                target_stage="review",
                lock_token=lock_token,
            )
            return "review"  # resume marker exists
        if self._calculation_engine is None:
            await self._repos.processing.mark_blocked(
                job.id,
                reason="calculation engine unavailable",
                lock_token=lock_token,
            )
            return "blocked"
        extracted = job.extracted_data or {}
        line_items = extracted.get("line_items") or []
        targets = line_items if line_items else [dict(extracted)]

        # Deterministic request ids per job+data-generation: a crashed re-run
        # with identical data reuses the exact snapshot already persisted for
        # this request (no duplicate calculations), while human-corrected data
        # (G6-D) yields a different digest -> a NEW request id -> a NEW snapshot
        # is calculated instead of silently reusing the pre-correction one.
        calc_digest = _calc_payload_digest(extracted, job.mapped_data)
        request_ids = [
            str(
                uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    f"{job.id}::calc::{idx}::c1::{calc_digest}",
                )
            )
            for idx in range(len(targets))
        ]
        if request_ids:
            existing = await self._repos.logs.find_snapshot_by_request_id(
                request_ids[0]
            )
            if existing is not None:
                await self._repos.processing.advance_stage(
                    job.id,
                    target_stage="review",
                    lock_token=lock_token,
                    calculation_snapshot_id=str(existing["id"]),
                )
                return "review"

        total_co2e = Decimal("0")
        snapshot_ids: list[str] = []
        first_error: Optional[str] = None
        parsed_date = _parse_date(extracted.get("date")) or _Date.today()
        for idx, line in enumerate(targets):
            try:
                snapshot_id, co2e = await self._calculate_line(
                    job,
                    line,
                    idx,
                    request_ids[idx] if request_ids else "",
                    parsed_date,
                    extracted,
                )
            except Exception as exc:  # noqa: BLE001
                first_error = f"line {idx + 1}: {exc}"
                break
            if snapshot_id is None:
                first_error = f"line {idx + 1}: calculation produced no snapshot"
                break
            total_co2e += co2e
            snapshot_ids.append(snapshot_id)
        if first_error is not None:
            await self._repos.processing.mark_blocked(
                job.id,
                reason=f"calculation blocked: {first_error}",
                lock_token=lock_token,
                last_error=first_error,
            )
            return "blocked"
        # Persist the item result and advance to the review gate.
        if job.source_item_id:
            try:
                await self._repos.manual_extraction.save_calculation(
                    job.source_item_id,
                    float(total_co2e),
                    job.mapped_data if line_items else None,
                )
            except Exception:  # noqa: BLE001
                logger.exception("item calculation sync failed for job %s", job.id)
        await self._repos.processing.advance_stage(
            job.id,
            target_stage="review",
            lock_token=lock_token,
            calculation_snapshot_id=snapshot_ids[0],
        )
        # G6-D: a correction-driven recalculation reaches review again; notify
        # only on the job's first completion so reprocessing never spams the
        # owners/admins with duplicate "processed" notifications.
        if job.notified_at is None:
            await self._notify(
                job,
                "processing.completed",
                "Document processed automatically",
                (
                    f"{job.file_name} was automatically extracted, mapped, "
                    f"validated and calculated ({float(total_co2e):g} kg CO2e). "
                    f"Review and approve it to record the emissions."
                ),
            )
        return "review"

    async def _calculate_line(
        self,
        job: AutomaticProcessingJob,
        line: dict[str, Any],
        idx: int,
        request_base: str,
        parsed_date: _Date,
        header: dict[str, Any],
    ) -> tuple[Optional[str], Decimal]:
        """Calculate one line (or the single-line document) via the engine."""
        mapped = job.mapped_data or {}
        extracted = job.extracted_data or {}
        is_tabular = bool(extracted.get("line_items"))
        if is_tabular:
            mapped_lines = mapped.get("line_items") or []
            mapped_line = (
                mapped_lines[idx] if idx < len(mapped_lines) else {}
            )
        else:
            # Single-line documents: ``mapped`` IS the mapping decision.
            mapped_line = mapped
        factor_id = mapped_line.get("factor_id")
        if not factor_id:
            raise ValueError("no factor mapped for this line")
        factor = await self._repos.factors.get(factor_id)
        customer_factor = None
        if factor is None:
            customer_factor = await self._repos.customer_factors.get(factor_id)
            if customer_factor is None:
                raise ValueError("mapped factor not found")
            if customer_factor.status != "active":
                raise ValueError("mapped customer factor is not active")
        raw_qty = line.get("quantity")
        if raw_qty in (None, ""):
            raise ValueError("quantity missing")
        try:
            quantity = Decimal(str(raw_qty))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("quantity not numeric") from exc
        if quantity < 0:
            raise ValueError("quantity must be >= 0")
        quantity_unit = str(line.get("unit") or "").strip()
        if not quantity_unit:
            raise ValueError("unit missing")
        # CL-3 / PRC-2 — unit-alias resolution: ``m3`` against a ``cubic
        # metres`` factor (and ``L`` against ``litres``) is legitimate input.
        # Genuine mismatches pass through unchanged and the engine rejects them.
        from core.units import resolve_unit_for_factor

        quantity_unit = resolve_unit_for_factor(
            quantity_unit,
            (factor.unit if factor is not None else customer_factor.unit),
        )
        activity = str(line.get("activity") or "").strip() or str(
            header.get("activity") or ""
        )
        activity_type = mapped_line.get("activity") or activity
        scope = (
            mapped_line.get("scope")
            or (factor.scope if factor is not None else customer_factor.scope)
        )
        reporting_year = parsed_date.year
        match_request_id = request_base
        methodology = _methodology_for(
            mapped_line.get("factor_kind") or "emission_factor",
            str(mapped_line.get("unit") or quantity_unit),
        )
        request = CalculationRequest(
            match_request_id=match_request_id,
            organization_id=job.organization_id,
            quantity=quantity,
            quantity_unit=quantity_unit,
            date=parsed_date,
            reporting_year=reporting_year,
            activity=activity,
            activity_type=activity_type,
            scope=scope,
            methodology=methodology,
            source_file=job.file_name,
            source_page=job.metadata.get("page_count"),
            source_item_id=job.source_item_id,
            factor=factor,
            customer_factor=customer_factor,
        )
        result = await self._calculation_engine.calculate(request)
        return result.snapshot.id, result.snapshot.co2e_kg

    # ------------------------------------------------------------------
    # Notifications / status updates
    # ------------------------------------------------------------------

    async def _notify(
        self,
        job: AutomaticProcessingJob,
        notification_type: str,
        title: str,
        message: str,
    ) -> None:
        """Create an in-app notification for the org's owners/admins (best-effort)."""
        try:
            members = await self._repos.organizations.get_members(
                job.organization_id
            )
            for member in members:
                if getattr(member, "role", None) in ("owner", "admin"):
                    await self._repos.notifications.create(
                        member.user_id,
                        notification_type=notification_type,
                        title=title,
                        message=message,
                        priority=1,
                        link=f"/processing/jobs/{job.id}",
                    )
            await self._repos.processing.mark_notified(job.id)
        except Exception:  # noqa: BLE001 — notifications must never break the job
            logger.exception("notification failed for job %s", job.id)
