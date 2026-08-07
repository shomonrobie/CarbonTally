"""Unit tests for domain.provider."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from domain.provider import (
    DiscoveredSheet,
    DiscoveryResult,
    ImportBatch,
    ImportError,
    ImportResult,
    NormalisedFactor,
    ProviderInfo,
    ProviderVersion,
    RawFactorRow,
)


def make_batch(**overrides: object) -> ImportBatch:
    values: dict[str, object] = {
        "id": "batch-1",
        "provider_key": "defra",
        "provider_version": "2025.1",
        "source_file": "DEFRA-2025.xlsx",
        "source_checksum": "sha256:abc",
        "reporting_year": 2025,
        "status": "importing",
        "rows_total": 100,
        "rows_imported": 0,
        "rows_skipped": 0,
        "rows_duplicate": 0,
        "errors": (),
        "is_active": False,
        "created_at": datetime(2025, 4, 1, tzinfo=timezone.utc),
        "created_by": "system",
        "rolled_back_from": None,
    }
    values.update(overrides)
    return ImportBatch(**values)  # type: ignore[arg-type]


class TestProviderInfo:
    def test_constructs(self) -> None:
        info = ProviderInfo(
            key="defra",
            name="UK Government GHG Conversion Factors",
            jurisdiction="UK",
            country_codes=("GB",),
            website="https://www.gov.uk/",
            license="Open Government Licence",
            latest_version="2025.1",
            publisher="UK Government (DEFRA/DESNZ)",
            language="en",
            documentation_url="https://www.gov.uk/government/collections/ghg-conversion-factors",
        )
        assert info.country_codes == ("GB",)


class TestImportBatch:
    def test_constructs(self) -> None:
        batch = make_batch()
        assert batch.status == "importing"
        assert batch.is_active is False

    def test_rejects_unknown_status(self) -> None:
        with pytest.raises(ValueError):
            make_batch(status="shipped")

    def test_rejects_negative_row_count(self) -> None:
        with pytest.raises(ValueError):
            make_batch(rows_total=-1)

    def test_activate_returns_active_copy(self) -> None:
        batch = make_batch()
        active = batch.activate()
        assert active.is_active is True
        assert active.status == "completed"
        assert active.id == batch.id
        assert batch.is_active is False  # original untouched

    def test_rollback_marks_rolled_back(self) -> None:
        batch = make_batch()
        rolled = batch.rollback(replaced_by="batch-2")
        assert rolled.status == "rolled_back"
        assert rolled.is_active is False
        assert rolled.rolled_back_from == "batch-2"
        assert batch.status == "importing"

    def test_is_immutable(self) -> None:
        batch = make_batch()
        with pytest.raises(FrozenInstanceError):
            batch.status = "completed"  # type: ignore[misc]


class TestImportError:
    def test_constructs(self) -> None:
        err = ImportError(row_number=5, field="unit", message="missing", severity="error")
        assert err.severity == "error"

    def test_rejects_unknown_severity(self) -> None:
        with pytest.raises(ValueError):
            ImportError(row_number=5, field="unit", message="x", severity="fatal")

    def test_rejects_row_zero(self) -> None:
        with pytest.raises(ValueError):
            ImportError(row_number=0, field="unit", message="x", severity="warning")


class TestDiscovery:
    def test_discovery_requires_sheets(self) -> None:
        with pytest.raises(ValueError):
            DiscoveryResult(
                provider_key="defra",
                provider_version="2025.1",
                source_path="x.xlsx",
                source_checksum="sha256:abc",
                reporting_year=2025,
                sheets=(),
            )

    def test_discovery_constructs(self) -> None:
        sheet = DiscoveredSheet(
            name="Conversion factors",
            sheet_type="factors",
            max_row=200,
            max_col=8,
            header_row=6,
            columns=("Activity", "Unit", "kgCO2e"),
        )
        result = DiscoveryResult(
            provider_key="defra",
            provider_version="2025.1",
            source_path="x.xlsx",
            source_checksum="sha256:abc",
            reporting_year=2025,
            sheets=(sheet,),
        )
        assert result.sheets[0].columns[0] == "Activity"

    def test_raw_row(self) -> None:
        row = RawFactorRow(
            sheet_name="Conversion factors",
            row_number=7,
            cells={"Activity": "Diesel", "Unit": "litres"},
        )
        assert row.cells["Activity"] == "Diesel"

    def test_normalised_factor(self) -> None:
        factor = NormalisedFactor(
            provider_key="defra",
            reporting_year=2025,
            activity_type="Diesel",
            co2e_multiplier=2.52,
            unit="litres",
        )
        assert factor.metadata == {}

    def test_normalised_factor_rejects_negative_multiplier(self) -> None:
        with pytest.raises(ValueError):
            NormalisedFactor(
                provider_key="defra",
                reporting_year=2025,
                activity_type="Diesel",
                co2e_multiplier=-1.0,
            )


class TestImportResult:
    def test_constructs(self) -> None:
        batch = make_batch(status="completed", rows_imported=98, rows_skipped=2)
        result = ImportResult(
            batch=batch,
            rows_imported=98,
            rows_skipped=2,
            rows_duplicate=0,
            errors=(),
            artifacts={"imported_file": "DEFRA-2025.xlsx"},
        )
        assert result.batch.status == "completed"
        assert result.rows_imported == 98


class TestProviderVersion:
    def test_constructs(self) -> None:
        version = ProviderVersion(
            provider_key="defra",
            version="2025.1",
            release_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            status="active",
            import_batch_id="batch-1",
            row_count=1000,
            checksum="sha256:abc",
        )
        assert version.row_count == 1000

