"""AI-assisted field extraction (Backend v2.1 §7, prep-pack Phase 7).

Uses an :class:`infra.llm_client.LLMClient` to extract structured key/value
fields from document text. The prompt, JSON parsing and confidence validation
are deterministic — the LLM is the only non-deterministic input. Failures
surface as :class:`core.exceptions.AIExtractionFailedError` (HTTP 502); empty
input surfaces as :class:`core.exceptions.ExtractionFailedError` (HTTP 422).

The engine uses the document repository only for status transitions and never
touches the database directly.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from core.exceptions import AIExtractionFailedError, ExtractionFailedError
from core.logging import get_logger
from domain.document import Document, ExtractionField
from domain.workflow import DomainEvent, FieldsExtracted
from engines.extraction import DocumentSink
from infra.audit_logger import AuditLogger
from infra.event_bus import EventBus
from infra.llm_client import LLMClient

logger = get_logger(__name__)

#: Default field vocabulary for AI extraction (a common invoice set; the caller
#: may supply its own via the constructor).
DEFAULT_FIELDS: tuple[str, ...] = (
    "supplier",
    "invoice_number",
    "date",
    "currency",
    "net_amount",
    "gross_amount",
    "vat_amount",
)

#: Bounds the prompt text so token usage stays bounded for long documents.
DEFAULT_MAX_TEXT_CHARS = 20_000

_SYSTEM_PROMPT = (
    "You are a precise document field-extraction assistant. "
    "Return only JSON."
)


class AIExtractionEngine:
    """Extracts key/value fields from document text through an LLM.

    Args:
        documents_repo: Repository used for document status transitions.
        llm_client: The LLM client used for extraction.
        event_bus: Optional bus receiving ``FieldsExtracted`` (fire-and-forget).
        audit_logger: Optional logger that records the extraction outcome.
        fields: Field names requested from the LLM.
        max_text_chars: Maximum document characters sent to the LLM.
    """

    def __init__(
        self,
        documents_repo: DocumentSink,
        llm_client: LLMClient,
        *,
        event_bus: Optional[EventBus] = None,
        audit_logger: Optional[AuditLogger] = None,
        fields: tuple[str, ...] = DEFAULT_FIELDS,
        max_text_chars: int = DEFAULT_MAX_TEXT_CHARS,
    ) -> None:
        if documents_repo is None:
            raise ValueError("documents_repo must not be None")
        if llm_client is None:
            raise ValueError("llm_client must not be None")
        if not fields:
            raise ValueError("fields must not be empty")
        if max_text_chars < 1:
            raise ValueError("max_text_chars must be >= 1")
        self._documents_repo = documents_repo
        self._llm_client = llm_client
        self._event_bus = event_bus
        self._audit_logger = audit_logger
        self._fields = fields
        self._max_text_chars = max_text_chars

    @property
    def fields(self) -> tuple[str, ...]:
        """The field names requested from the LLM."""
        return self._fields

    @property
    def max_text_chars(self) -> int:
        """The document-character bound sent to the LLM."""
        return self._max_text_chars

    async def extract_fields(
        self, document: Document, text: str
    ) -> tuple[ExtractionField, ...]:
        """Extract fields from ``text`` via the LLM.

        Transitions the document ``processing`` → ``processed`` on success and
        ``processing`` → ``failed`` (re-raising) on failure.
        """
        await self._set_status(document.id, "processing")
        try:
            fields = await self._call_llm(text)
        except Exception:  # noqa: BLE001 - mark failed then propagate
            await self._set_status(document.id, "failed")
            raise
        await self._set_status(document.id, "processed")
        confidence = (
            sum(field.confidence for field in fields) / len(fields)
            if fields
            else 0.0
        )
        if fields:
            await self._publish(
                FieldsExtracted(
                    event_id=str(uuid.uuid4()),
                    occurred_at=datetime.now(timezone.utc),
                    correlation_id=document.id,
                    document_id=document.id,
                    fields={field.field_name: field.value for field in fields},
                    confidence=confidence,
                ),
                document.id,
            )
        await self._audit(document, fields, confidence)
        return fields

    async def _call_llm(self, text: str) -> tuple[ExtractionField, ...]:
        if not text.strip():
            raise ExtractionFailedError("no document text to extract from")
        chunk = text[: self._max_text_chars]
        prompt = self._build_prompt(chunk)
        response = await self._llm_client.complete(prompt, system=_SYSTEM_PROMPT)
        return self._parse_response(response)

    def _build_prompt(self, chunk: str) -> str:
        fields = ", ".join(self._fields)
        return (
            "Extract the following fields from the document text:\n"
            f"Fields: {fields}\n\n"
            "Document text:\n"
            f"{chunk}\n\n"
            "Respond with a single JSON object where each key is one of the "
            'requested fields and each value is an object with "value" and '
            '"confidence" (0..1), for example:\n'
            '{"supplier": {"value": "Acme Corp", "confidence": 0.99}}\n'
            "Omit fields that are not present."
        )

    def _parse_response(self, response_text: str) -> tuple[ExtractionField, ...]:
        cleaned = _strip_code_fence(response_text)
        try:
            data = json.loads(cleaned)
        except ValueError as exc:
            raise AIExtractionFailedError(
                "LLM returned invalid JSON",
                details={"body": response_text[:500]},
            ) from exc
        if not isinstance(data, dict):
            raise AIExtractionFailedError(
                "LLM response must be a JSON object"
            )
        fields: list[ExtractionField] = []
        for field_name in self._fields:
            item = data.get(field_name)
            if item is None:
                continue
            if not isinstance(item, dict) or "value" not in item:
                raise AIExtractionFailedError(
                    f"LLM field {field_name!r} is malformed",
                    details={"item": str(item)[:200]},
                )
            raw_value = item["value"]
            raw_confidence = item.get("confidence", 1.0)
            try:
                confidence = float(raw_confidence)
            except (TypeError, ValueError):
                raise AIExtractionFailedError(
                    f"LLM field {field_name!r} confidence is not a number"
                ) from None
            if not 0.0 <= confidence <= 1.0:
                raise AIExtractionFailedError(
                    f"LLM field {field_name!r} confidence is out of range"
                )
            fields.append(
                ExtractionField(
                    field_name=field_name,
                    value=str(raw_value),
                    confidence=confidence,
                    source="ai",
                )
            )
        return tuple(fields)

    async def _set_status(self, doc_id: str, status: str) -> None:
        await self._documents_repo.update_status(doc_id, status)

    async def _publish(self, event: DomainEvent, correlation_id: str) -> None:
        if self._event_bus is None:
            return
        try:
            await self._event_bus.publish(event)
        except Exception:  # noqa: BLE001 - side effects must not break extraction
            logger.exception(
                "failed to publish %s for correlation %s",
                type(event).__name__,
                correlation_id,
            )

    async def _audit(
        self,
        document: Document,
        fields: tuple[ExtractionField, ...],
        confidence: float,
    ) -> None:
        if self._audit_logger is None:
            return
        try:
            await self._audit_logger.log_action(
                action="ai_extraction:completed",
                entity_type="document",
                entity_id=document.id,
                correlation_id=document.id,
                actor="ai_extraction_engine",
                after={
                    "field_count": len(fields),
                    "fields": {field.field_name: field.value for field in fields},
                    "confidence": confidence,
                },
            )
        except Exception:  # noqa: BLE001 - audit must not break extraction
            logger.exception(
                "failed to audit ai extraction for document %s", document.id
            )


def _strip_code_fence(text: str) -> str:
    """Remove a surrounding Markdown code fence from an LLM response."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()

