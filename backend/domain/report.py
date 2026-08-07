"""Report generation domain objects (Backend v2.1 §9, ADR-10).

Pure Python, immutable frozen dataclasses. ``ReportTemplate`` describes the
skeleton of a report; ``GeneratedReport`` is the produced artefact.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class ReportSection:
    """A single section within a report."""

    section_id: str
    title: str
    content: str
    order: int


@dataclass(frozen=True, slots=True)
class ReportTemplate:
    """A named report skeleton listing its sections in order."""

    id: str
    name: str
    report_type: str
    structure: tuple[ReportSection, ...]


@dataclass(frozen=True, slots=True)
class ReportRequest:
    """A request to generate a report."""

    organization_id: str
    report_type: str
    reporting_year: int
    template_id: Optional[str] = None
    sections: tuple[ReportSection, ...] = ()
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (1990 <= self.reporting_year <= 2100):
            raise ValueError(
                f"reporting_year {self.reporting_year} outside supported range 1990-2100"
            )


@dataclass(frozen=True, slots=True)
class GeneratedReport:
    """A successfully generated, stored report artefact."""

    id: str
    organization_id: str
    report_type: str
    reporting_year: int
    storage_url: str
    file_size_bytes: int
    generated_at: datetime
    page_count: int

    def __post_init__(self) -> None:
        if self.file_size_bytes < 0:
            raise ValueError("file_size_bytes must be >= 0")
        if self.page_count < 0:
            raise ValueError("page_count must be >= 0")
