"""Unit tests for domain.document."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from domain.document import (
    Document,
    ExtractionField,
    ExtractionResult,
    ExtractedPage,
    ExtractedTable,
)


def utc_now() -> datetime:
    return datetime(2025, 6, 1, 9, 0, 0, tzinfo=timezone.utc)


class TestDocument:
    def test_constructs(self) -> None:
        doc = Document(
            id="doc-1",
            organization_id="org-1",
            filename="invoice.pdf",
            storage_path="org-1/invoice.pdf",
            file_type="pdf",
            status="uploaded",
            uploaded_at=utc_now(),
            uploaded_by="user-1",
        )
        assert doc.file_type == "pdf"

    def test_is_immutable(self) -> None:
        doc = Document(
            id="doc-1",
            organization_id="org-1",
            filename="invoice.pdf",
            storage_path="org-1/invoice.pdf",
            file_type="pdf",
            status="uploaded",
            uploaded_at=utc_now(),
            uploaded_by="user-1",
        )
        with pytest.raises(FrozenInstanceError):
            doc.status = "extracted"  # type: ignore[misc]


class TestExtractionResult:
    def _result(self, confidence: float = 0.9) -> ExtractionResult:
        return ExtractionResult(
            raw_text="hello",
            pages=(
                ExtractedPage(page_number=1, text="hello", confidence=0.95),
            ),
            tables=(
                ExtractedTable(page_number=1, rows=(("Diesel", "100", "litres"),)),
            ),
            metadata={"pages": 1},
            confidence=confidence,
        )

    def test_constructs(self) -> None:
        result = self._result()
        assert result.pages[0].text == "hello"
        assert result.tables[0].headers == ()
        assert result.metadata == {"pages": 1}

    def test_rejects_bad_aggregate_confidence(self) -> None:
        with pytest.raises(ValueError):
            self._result(confidence=1.5)

    def test_rejects_bad_page_confidence(self) -> None:
        with pytest.raises(ValueError):
            ExtractionResult(
                raw_text="x",
                pages=(ExtractedPage(page_number=1, text="x", confidence=-0.1),),
            )

    def test_extraction_field(self) -> None:
        field = ExtractionField(
            field_name="supplier", value="ACME", confidence=0.9, source="ai"
        )
        assert field.source == "ai"
