"""Document extraction engine (Backend v2.1 §7, prep-pack Phase 7).

Deterministically converts document **text** into the structured
:class:`domain.document.ExtractionResult`: pages (split on a configurable page
separator), tables (delimiter-delimited runs of rows) and key/value fields
(generic ``key: value`` lines plus configurable named patterns). The extracted
fields are published through the ``FieldsExtracted`` workflow event.

The engine uses the document repository **only** for status transitions
(``processing`` → ``processed`` / ``failed``) and never touches the database
directly. Extraction failures surface as
:class:`core.exceptions.ExtractionFailedError` (HTTP 422).

Dependency rules: this module imports from ``core`` (errors, logging),
``domain`` (document + workflow) and ``infra`` (event bus, audit logger).
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Mapping, Optional, Protocol

from core.exceptions import ExtractionFailedError
from core.logging import get_logger
from domain.document import (
    Document,
    ExtractedPage,
    ExtractedTable,
    ExtractionField,
    ExtractionResult,
)
from domain.workflow import (
    DomainEvent,
    ExtractionCompleted,
    ExtractionRequested,
    FieldsExtracted,
)
from infra.audit_logger import AuditLogger
from infra.event_bus import EventBus

logger = get_logger(__name__)

#: Matches a ``Key: value`` line (also accepts the full-width colon).
_KEY_VALUE_RE = re.compile(
    r"(?im)^\s*([a-z][a-z0-9 _\-/]{1,60}?)\s*[:：]\s*(.+?)\s*$"
)

#: Named field patterns applied after the generic key/value pass.
_DEFAULT_FIELD_PATTERNS: Mapping[str, re.Pattern[str]] = {
    "supplier": re.compile(r"(?im)^\s*supplier\s*[:：]\s*(.+?)\s*$"),
    "invoice_number": re.compile(
        r"(?im)^\s*invoice\s*(?:number|no\.?|#)?\s*[:：]\s*(.+?)\s*$"
    ),
    "date": re.compile(r"(?im)^\s*(?:invoice\s+)?date\s*[:：]\s*(.+?)\s*$"),
    "net_amount": re.compile(
        r"(?im)^\s*net\s*(?:amount|total)?\s*[:：]\s*(.+?)\s*$"
    ),
    "gross_amount": re.compile(
        r"(?im)^\s*gross\s*(?:amount|total)?\s*[:：]\s*(.+?)\s*$"
    ),
}


class DocumentSink(Protocol):
    """The repository surface used for document status transitions.

    Satisfied structurally by :class:`data.documents.DocumentsRepository`.
    """

    async def update_status(self, doc_id: str, status: str) -> Document: ...


class DocumentExtractionEngine:
    """Text → :class:`ExtractionResult` pipeline for one document.

    Args:
        documents_repo: Repository used for status transitions.
        event_bus: Optional bus receiving ``ExtractionRequested``,
            ``ExtractionCompleted`` and ``FieldsExtracted`` events
            (fire-and-forget).
        audit_logger: Optional logger that records the extraction outcome.
        page_separator: Character/string splitting pages (default: form feed).
        table_delimiter: Column delimiter used for table detection.
        field_patterns: Named field patterns; defaults to a small invoice set.
    """

    def __init__(
        self,
        documents_repo: DocumentSink,
        *,
        event_bus: Optional[EventBus] = None,
        audit_logger: Optional[AuditLogger] = None,
        page_separator: str = "\f",
        table_delimiter: str = "\t",
        field_patterns: Optional[Mapping[str, re.Pattern[str]]] = None,
    ) -> None:
        if documents_repo is None:
            raise ValueError("documents_repo must not be None")
        if not page_separator:
            raise ValueError("page_separator must not be empty")
        if not table_delimiter:
            raise ValueError("table_delimiter must not be empty")
        self._documents_repo = documents_repo
        self._event_bus = event_bus
        self._audit_logger = audit_logger
        self._page_separator = page_separator
        self._table_delimiter = table_delimiter
        self._field_patterns = dict(
            field_patterns
            if field_patterns is not None
            else _DEFAULT_FIELD_PATTERNS
        )

    @property
    def page_separator(self) -> str:
        """The configured page separator."""
        return self._page_separator

    @property
    def table_delimiter(self) -> str:
        """The configured table column delimiter."""
        return self._table_delimiter

    async def extract(self, document: Document, text: str) -> ExtractionResult:
        """Extract pages/tables/fields from ``text`` and publish the events.

        Transitions the document ``processing`` → ``processed`` on success and
        ``processing`` → ``failed`` (re-raising) on extraction failure.

        Raises:
            ExtractionFailedError: When ``text`` contains no usable content.
        """
        await self._set_status(document.id, "processing")
        await self._publish(
            ExtractionRequested(
                event_id=str(uuid.uuid4()),
                occurred_at=datetime.now(timezone.utc),
                correlation_id=document.id,
                document_id=document.id,
            ),
            document.id,
        )
        try:
            result = self._build_result(text)
        except ExtractionFailedError:
            await self._set_status(document.id, "failed")
            raise
        await self._set_status(document.id, "processed")
        await self._publish(
            ExtractionCompleted(
                event_id=str(uuid.uuid4()),
                occurred_at=datetime.now(timezone.utc),
                correlation_id=document.id,
                document_id=document.id,
                page_count=len(result.pages),
                confidence=result.confidence,
            ),
            document.id,
        )
        if result.metadata.get("field_count", 0) > 0:
            await self._publish(
                FieldsExtracted(
                    event_id=str(uuid.uuid4()),
                    occurred_at=datetime.now(timezone.utc),
                    correlation_id=document.id,
                    document_id=document.id,
                    fields=result.metadata.get("fields", {}),
                    confidence=result.confidence,
                ),
                document.id,
            )
        await self._audit(document, result)
        return result

    def _build_result(self, text: str) -> ExtractionResult:
        if not text.strip():
            raise ExtractionFailedError("extraction produced no usable content")
        pages = tuple(
            ExtractedPage(page_number=index + 1, text=chunk, confidence=1.0)
            for index, chunk in enumerate(text.split(self._page_separator))
        )
        tables = self._extract_tables(pages)
        fields = self._extract_fields(text)
        confidence = (
            sum(page.confidence for page in pages) / len(pages)
            if pages
            else 0.0
        )
        return ExtractionResult(
            raw_text=text,
            pages=pages,
            tables=tables,
            metadata={
                "page_count": len(pages),
                "table_count": len(tables),
                "field_count": len(fields),
                "fields": {field.field_name: field.value for field in fields},
                "engine": "document_extraction",
            },
            confidence=confidence,
        )

    def _extract_tables(
        self, pages: tuple[ExtractedPage, ...]
    ) -> tuple[ExtractedTable, ...]:
        tables: list[ExtractedTable] = []
        for page in pages:
            current: list[tuple[str, ...]] = []
            for line in page.text.splitlines():
                if self._table_delimiter in line:
                    columns = tuple(
                        cell.strip() for cell in line.split(self._table_delimiter)
                    )
                    if current and len(columns) != len(current[0]):
                        self._emit_table(tables, page.page_number, current)
                        current = []
                    current.append(columns)
                elif current:
                    self._emit_table(tables, page.page_number, current)
                    current = []
            if current:
                self._emit_table(tables, page.page_number, current)
        return tuple(tables)

    @staticmethod
    def _emit_table(
        tables: list[ExtractedTable],
        page_number: int,
        rows: list[tuple[str, ...]],
    ) -> None:
        if len(rows) >= 2:
            tables.append(
                ExtractedTable(
                    page_number=page_number,
                    headers=rows[0],
                    rows=tuple(rows[1:]),
                )
            )

    def _extract_fields(self, text: str) -> tuple[ExtractionField, ...]:
        fields: dict[str, ExtractionField] = {}
        for line in text.splitlines():
            match = _KEY_VALUE_RE.match(line)
            if match:
                name = match.group(1).strip().casefold().replace(" ", "_")
                fields.setdefault(
                    name,
                    ExtractionField(
                        field_name=name,
                        value=match.group(2).strip(),
                        confidence=1.0,
                        source="regex",
                    ),
                )
        for field_name, pattern in self._field_patterns.items():
            match = pattern.search(text)
            if match:
                fields[field_name] = ExtractionField(
                    field_name=field_name,
                    value=match.group(1).strip(),
                    confidence=1.0,
                    source="regex",
                )
        return tuple(fields.values())

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

    async def _audit(self, document: Document, result: ExtractionResult) -> None:
        if self._audit_logger is None:
            return
        try:
            await self._audit_logger.log_action(
                action="document_extraction:completed",
                entity_type="document",
                entity_id=document.id,
                correlation_id=document.id,
                actor="document_extraction_engine",
                after={
                    "page_count": len(result.pages),
                    "table_count": len(result.tables),
                    "field_count": result.metadata.get("field_count", 0),
                    "confidence": result.confidence,
                },
            )
        except Exception:  # noqa: BLE001 - audit must not break extraction
            logger.exception(
                "failed to audit extraction for document %s", document.id
            )



