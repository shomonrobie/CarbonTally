"""WP-8 — migration drift gate tests (pure; no database, no production)."""
from __future__ import annotations

import json
from pathlib import Path

from tools.migration_drift import (
    EXIT_DRIFT,
    EXIT_OK,
    DriftReport,
    MigrationFile,
    assert_safe_dsn,
    compare,
    exit_code,
    load_repository_migrations,
    main,
    parse_ledger,
    render_markdown,
    write_evidence,
)


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "supabase" / "migrations").is_dir():
            return parent
    raise AssertionError("could not locate repo root")


def _seed_repo(tmp_path: Path, names: list[str]) -> Path:
    migrations = tmp_path / "supabase" / "migrations"
    migrations.mkdir(parents=True, exist_ok=True)
    for name in names:
        (migrations / name).write_text("-- test migration\n", encoding="utf-8")
    return tmp_path


class TestRepositorySide:
    def test_real_repository_is_clean_and_ordered(self) -> None:
        migrations, anomalies = load_repository_migrations(_repo_root())
        assert anomalies == []
        assert len(migrations) >= 69  # release set (69) + this task's migrations
        versions = [m.version for m in migrations]
        assert versions == sorted(versions)
        assert len(set(versions)) == len(versions)

    def test_naming_anomaly_is_detected(self, tmp_path: Path) -> None:
        root = _seed_repo(tmp_path, ["20260101000000_ok.sql", "not-a-migration.sql"])
        _, anomalies = load_repository_migrations(root)
        assert any("naming anomaly" in a for a in anomalies)

    def test_duplicate_version_is_detected(self, tmp_path: Path) -> None:
        root = _seed_repo(
            tmp_path, ["20260101000000_first.sql", "20260101000000_second.sql"]
        )
        _, anomalies = load_repository_migrations(root)
        assert any("duplicate migration version" in a for a in anomalies)


class TestLedgerComparison:
    def test_classifies_pending_and_unexpected(self) -> None:
        migrations = [
            MigrationFile("20260101000000", "a", "20260101000000_a.sql"),
            MigrationFile("20260102000000", "b", "20260102000000_b.sql"),
        ]
        report = compare(migrations, ["20260101000000", "20250101000000"])
        assert report.pending == ["20260102000000"]
        assert report.unexpected == ["20250101000000"]
        assert report.applied == ["20260101000000"]
        assert report.drift is True

    def test_fully_applied_is_not_drift(self) -> None:
        migrations = [MigrationFile("20260101000000", "a", "20260101000000_a.sql")]
        report = compare(migrations, ["20260101000000"])
        assert report.drift is False

    def test_ledger_duplicates_are_an_anomaly(self) -> None:
        report = compare([], ["20260101000000", "20260101000000"])
        assert any(
            "duplicate entries in the migration ledger" in a for a in report.anomalies
        )

    def test_parse_ledger_normalises_rows(self) -> None:
        assert parse_ledger(["20260101000000_a", "20260102000000", "  "]) == [
            "20260101000000",
            "20260102000000",
        ]


class TestReleaseGate:
    def test_drift_hard_fails_without_override(self) -> None:
        report = DriftReport(repository=["2"], pending=["2"])
        assert exit_code(report) == EXIT_DRIFT

    def test_override_downgrades_to_warning_but_is_recorded(self) -> None:
        report = DriftReport(repository=["2"], pending=["2"], override="CT-123")
        assert exit_code(report) == EXIT_OK
        assert report.override == "CT-123"
        assert "CT-123" in render_markdown(report, target="test")

    def test_no_drift_is_ok(self) -> None:
        assert exit_code(DriftReport(repository=["1"], applied=["1"])) == EXIT_OK


class TestSafetyAndEvidence:
    def test_production_looking_dsn_is_refused(self, monkeypatch) -> None:
        monkeypatch.delenv("CARBONTALLY_MIGRATION_DRIFT_ALLOW", raising=False)
        for dsn in (
            "postgresql://u:p@prod-db:5432/x",
            "postgresql://u:p@live.internal/x",
            "postgresql://u:p@demo-host/x",
        ):
            try:
                assert_safe_dsn(dsn)
            except SystemExit as exc:
                assert "refusing DSN" in str(exc)
            else:  # pragma: no cover - explicit failure path
                raise AssertionError(f"DSN was not refused: {dsn}")

    def test_explicit_non_production_acknowledgement_allows(self, monkeypatch) -> None:
        monkeypatch.setenv("CARBONTALLY_MIGRATION_DRIFT_ALLOW", "non-production")
        assert_safe_dsn("postgresql://u:p@qa-clone:5432/x")  # no raise

    def test_evidence_artefacts_are_written(self, tmp_path: Path) -> None:
        report = compare([], [], ledger_source="repo-only")
        json_path, md_path = write_evidence(
            report, target="unit-test", out_dir=tmp_path / "drift"
        )
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert payload["drift"] is False
        assert payload["ledger_source"] == "repo-only"
        assert "Migration drift report" in md_path.read_text(encoding="utf-8")


class TestCli:
    def test_repo_only_mode_exits_zero(self, tmp_path: Path) -> None:
        code = main(
            ["--repo-root", str(_repo_root()), "--repo-only", "--out-dir", str(tmp_path)]
        )
        assert code == EXIT_OK
        assert list(tmp_path.glob("migration_drift_*.json"))

    def test_pending_ledger_blocks_the_release(self, tmp_path: Path) -> None:
        ledger = tmp_path / "ledger.txt"
        ledger.write_text("20260101000000\n", encoding="utf-8")
        code = main(
            [
                "--repo-root",
                str(_repo_root()),
                "--ledger-file",
                str(ledger),
                "--out-dir",
                str(tmp_path / "drift"),
            ]
        )
        assert code == EXIT_DRIFT

    def test_override_unblocks_with_evidence(self, tmp_path: Path) -> None:
        ledger = tmp_path / "ledger.txt"
        ledger.write_text("20260101000000\n", encoding="utf-8")
        code = main(
            [
                "--repo-root",
                str(_repo_root()),
                "--ledger-file",
                str(ledger),
                "--override",
                "CT-FIN-001",
                "--out-dir",
                str(tmp_path / "drift"),
            ]
        )
        assert code == EXIT_OK
        payload = json.loads(
            sorted((tmp_path / "drift").glob("*.json"))[0].read_text(encoding="utf-8")
        )
        assert payload["override"] == "CT-FIN-001"
        assert payload["drift"] is True
