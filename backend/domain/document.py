"""Document-extraction domain objects (Backend v2.1 §9, ADR-10).

Represent a customer document and the output of its extraction pipeline.
Pure Python, immutable frozen dataclasses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class Document:
    """A customer-uploaded document referenced by the ``documents`` table."""

    id: str
    organization_id: str
    filename: str
    storage_path: str
    file_type: str
    status: str
    uploaded_at: datetime
    uploaded_by: str


@dataclass(frozen=True, slots=True)
class ExtractedPage:
    """Text content of a single extracted page."""

    page_number: int
    text: str
    confidence: float


@dataclass(frozen=True, slots=True)
class ExtractedTable:
    """A tabular structure found inside an extracted document."""

    page_number: int
    rows: tuple[tuple[str, ...], ...]
    headers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExtractionField:
    """A key/value pair extracted from a document (e.g. ``supplier``)."""

    field_name: str
    value: str
    confidence: float
    source: str


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """The full output of the extraction pipeline for one document.

    Attributes:
        raw_text: Concatenated text of all pages.
        pages: Per-page text with confidence.
        tables: Tabular structures found (empty when none).
        metadata: Free-form pipeline metadata (chunk count, OCR stats, ...).
        confidence: Aggregate extraction confidence in ``[0, 1]``.
    """

    raw_text: str
    pages: tuple[ExtractedPage, ...]
    tables: tuple[ExtractedTable, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        for page in self.pages:
            if not 0.0 <= page.confidence <= 1.0:
                raise ValueError(
                    f"page {page.page_number} confidence must be in [0, 1]"
                )
