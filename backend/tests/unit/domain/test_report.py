"""Unit tests for domain.report."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from domain.report import (
    GeneratedReport,
    ReportRequest,
    ReportSection,
    ReportTemplate,
)


def utc_now() -> datetime:
    return datetime(2025, 6, 1, 15, 0, 0, tzinfo=timezone.utc)


class TestReportSection:
    def test_constructs(self) -> None:
        section = ReportSection(
            section_id="s-1", title="Summary", content="text", order=1
        )
        assert section.order == 1


class TestReportTemplate:
    def test_constructs(self) -> None:
        template = ReportTemplate(
            id="t-1",
            name="Default",
            report_type="annual",
            structure=(
                ReportSection(section_id="s-1", title="Summary", content="", order=1),
            ),
        )
        assert template.structure[0].section_id == "s-1"


class TestReportRequest:
    def test_constructs(self) -> None:
        request = ReportRequest(
            organization_id="org-1", report_type="annual", reporting_year=2025
        )
        assert request.options == {}
        assert request.template_id is None

    def test_rejects_implausible_year(self) -> None:
        with pytest.raises(ValueError):
            ReportRequest(organization_id="org-1", report_type="annual", reporting_year=1800)

    def test_is_immutable(self) -> None:
        request = ReportRequest(
            organization_id="org-1", report_type="annual", reporting_year=2025
        )
        with pytest.raises(FrozenInstanceError):
            request.report_type = "quarterly"  # type: ignore[misc]


class TestGeneratedReport:
    def test_constructs(self) -> None:
        report = GeneratedReport(
            id="r-1",
            organization_id="org-1",
            report_type="annual",
            reporting_year=2025,
            storage_url="s3://reports/r-1.pdf",
            file_size_bytes=1024,
            generated_at=utc_now(),
            page_count=4,
        )
        assert report.page_count == 4

    def test_rejects_negative_size(self) -> None:
        with pytest.raises(ValueError):
            GeneratedReport(
                id="r-1",
                organization_id="org-1",
                report_type="annual",
                reporting_year=2025,
                storage_url="s3://reports/r-1.pdf",
                file_size_bytes=-1,
                generated_at=utc_now(),
                page_count=1,
            )

    def test_rejects_negative_page_count(self) -> None:
        with pytest.raises(ValueError):
            GeneratedReport(
                id="r-1",
                organization_id="org-1",
                report_type="annual",
                reporting_year=2025,
                storage_url="s3://reports/r-1.pdf",
                file_size_bytes=1,
                generated_at=utc_now(),
                page_count=-1,
            )
