#!/usr/bin/env python3
"""P12-DOC-03 — canonical synthetic PDF corpus for the investor demo.

Generates a small, reproducible, multi-year set of realistic supplier PDF
invoices for the canonical investor-demo relationship:

    supplier  Robinsons Recycling Services Ltd
    customer  Sustainable Direct Group

DESIGN CONSTRAINTS (P12-DOC-03):
  * The external generator repository is used strictly as a LIBRARY and is
    NEVER modified.  This driver lives in the CarbonTally Demo Lab tooling,
    reads a pinned generator checkout, and writes the corpus OUTSIDE both
    repositories (the Demo Lab state directory).
  * Everything except the two canonical business names is generator-produced:
    line items, quantities, units, unit prices, VAT, gross amounts, totals,
    addresses, invoice numbers, billing periods, layouts and difficulties.
  * The only binding applied here is the canonical supplier/customer NAME
    (the generator's name pools cannot yield `Robinsons Recycling Services
    Ltd`; see the P12-DOC-03 report section D).  No field is invented and no
    extracted CarbonTally data is touched.
  * Billing periods are *selected*, not edited: candidate document ids are
    searched deterministically until their generator-derived period falls in
    the target reporting year (2025 / 2026).

Usage:
    myenv/bin/python p12_canonical_corpus.py --generator-root <checkout> \
        [--output-dir <state>/corpus/p12-canonical-demo-v1]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

CANONICAL_SUPPLIER = "Robinsons Recycling Services Ltd"
CANONICAL_CUSTOMER = "Sustainable Direct Group"
CANONICAL_CORPUS_ID = "p12-canonical-demo-v1"
GENERATOR_REPO = "https://github.com/shomonrobie/carbon_tally_synthetic_documents_generator"
BASE_SEED = 42
PERIOD_YEARS = (2025, 2026)
PER_YEAR = 3


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _period_year_for(document_id: str, base_seed: int) -> int:
    """Replicate the generator's own date derivation for a document id.

    Mirrors ``SeedManager.get_document_seed`` (sha256 of ``"{seed}:doc:{id}"``)
    followed by ``DataFactory.create_dates`` (``year = 2025 + randint(0, 1)``).
    """
    digest = hashlib.sha256(f"{base_seed}:doc:{document_id}".encode()).digest()
    seed = int.from_bytes(digest[:4], "big")
    return 2025 + random.Random(seed + 4000).randint(0, 1)


def _select_document_ids(base_seed: int, limit: int = 400):
    """Pick deterministic ids so that each target year gets PER_YEAR documents."""
    chosen: dict[int, list[str]] = {y: [] for y in PERIOD_YEARS}
    index = 1
    while index <= limit and any(len(v) < PER_YEAR for v in chosen.values()):
        candidate = f"p12canon_waste_{index:03d}"
        year = _period_year_for(candidate, base_seed)
        if year in chosen and len(chosen[year]) < PER_YEAR:
            chosen[year].append(candidate)
        index += 1
    for year, ids in chosen.items():
        if len(ids) != PER_YEAR:
            raise RuntimeError(f"could not find {PER_YEAR} documents for {year}: {ids}")
    return chosen


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    generator_root = Path(args.generator_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    generator_dir = generator_root / "generator"
    if not (generator_dir / "main.py").is_file():
        print(f"ERROR: pinned generator not found at {generator_dir}")
        return 2

    sys.path.insert(0, str(generator_dir))
    from main import DocumentGenerator  # noqa: E402
    from schemas import (  # noqa: E402
        DocumentCategory, DifficultyLevel, DocumentSpec, DocumentVariations,
    )
    from data_factory import DataFactory  # noqa: E402
    from document_builder import DocumentBuilder  # noqa: E402

    class CanonicalNameDataFactory(DataFactory):
        """DataFactory that binds the two canonical business names.

        Only ``supplier`` / ``customer`` are overridden.  Every other field --
        addresses, invoice number, period, line items, quantities, units,
        unit prices, VAT and totals -- remains generator-produced.
        """

        def create_document(self, spec):
            data = super().create_document(spec)
            data.supplier = CANONICAL_SUPPLIER
            data.customer = CANONICAL_CUSTOMER
            return data

    output_dir.mkdir(parents=True, exist_ok=True)
    selection = _select_document_ids(BASE_SEED)

    difficulties = [
        (DifficultyLevel.CLEAN, 3),
        (DifficultyLevel.REALISTIC, 4),
        (DifficultyLevel.REALISTIC, 2),
        (DifficultyLevel.CLEAN, 5),
        (DifficultyLevel.REALISTIC, 3),
        (DifficultyLevel.DIFFICULT, 4),
    ]
    counter = 0
    specs = []
    for year in PERIOD_YEARS:
        for document_id in selection[year]:
            difficulty, line_items = difficulties[counter % len(difficulties)]
            counter += 1
            specs.append(
                DocumentSpec(
                    document_id=document_id,
                    category=DocumentCategory.WASTE,
                    difficulty=difficulty,
                    pages=1,
                    line_items=line_items,
                    has_scan=False,
                    description=(
                        f"{CANONICAL_SUPPLIER} -> {CANONICAL_CUSTOMER} "
                        f"(FY{year} recycling services)"
                    ),
                    variations=DocumentVariations(
                        currency_symbol="GBP",
                        decimal_places=2,
                        table_variant=(counter % 12) + 1,
                    ),
                )
            )

    generator = DocumentGenerator(output_dir=str(output_dir), seed=BASE_SEED)
    generator.data_factory = CanonicalNameDataFactory(generator.seed_manager)
    generator.document_builder = DocumentBuilder(
        generator.seed_manager, generator.data_factory
    )

    print(f"generating {len(specs)} canonical documents into {output_dir}")
    for spec in specs:
        generator.generate_document(spec)
    return _write_artifacts(output_dir, specs, generator_root)


def _write_artifacts(output_dir: Path, specs, generator_root: Path) -> int:
    from subprocess import run as _run

    documents = []
    for spec in specs:
        pdf = output_dir / "documents" / f"{spec.document_id}.pdf"
        truth = output_dir / "ground_truth" / f"{spec.document_id}.json"
        gt = json.loads(truth.read_text())
        documents.append(
            {
                "document_id": spec.document_id,
                "pdf": str(pdf),
                "pdf_sha256": _sha256(pdf),
                "pdf_bytes": pdf.stat().st_size,
                "ground_truth": str(truth),
                "ground_truth_sha256": _sha256(truth),
                "supplier": gt["supplier"],
                "customer": gt["customer"],
                "invoice_number": gt["invoice_number"],
                "invoice_date": gt["invoice_date"],
                "billing_period_start": gt["billing_period_start"],
                "billing_period_end": gt["billing_period_end"],
                "reporting_year": int(gt["billing_period_start"][:4]),
                "currency": gt["currency"],
                "difficulty": gt["difficulty"],
                "line_item_count": gt["line_item_count"],
                "line_items": gt["line_items"],
                "net_total": gt["net_total"],
                "vat_total": gt["vat_total"],
                "gross_total": gt["gross_total"],
                "document_generation_seed": gt["generation_seed"],
            }
        )

    (output_dir / "canonical_manifest.json").write_text(
        json.dumps(
            {
                "corpus_id": CANONICAL_CORPUS_ID,
                "task": "P12-DOC-03-20260924-CANONICAL-SYNTHETIC-PDF-CORPUS",
                "canonical_supplier": CANONICAL_SUPPLIER,
                "canonical_customer": CANONICAL_CUSTOMER,
                "years": list(PERIOD_YEARS),
                "document_count": len(documents),
                "documents": documents,
            },
            indent=2,
        )
        + "\n"
    )

    commit = _run(
        ["git", "-C", str(generator_root), "rev-parse", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()
    dirty = bool(
        _run(
            ["git", "-C", str(generator_root), "status", "--porcelain"],
            capture_output=True, text=True,
        ).stdout.strip()
    )
    (output_dir / "corpus_provenance.json").write_text(
        json.dumps(
            {
                "corpus_id": CANONICAL_CORPUS_ID,
                "generator": {
                    "repo": GENERATOR_REPO,
                    "checkout": str(generator_root),
                    "commit": commit,
                    "dirty_at_generation": dirty,
                    "base_seed": BASE_SEED,
                    "used_as": "library only; repository never modified",
                },
                "binding": {
                    "method": "CanonicalNameDataFactory(DataFactory) bound at "
                              "generate time",
                    "bound_fields": ["supplier", "customer"],
                    "everything_else": "generator-produced (line items, units, "
                                       "rates, VAT, totals, addresses, invoice "
                                       "numbers, periods, layouts)",
                    "why": "generator name pools cannot yield "
                           "'Robinsons Recycling Services Ltd'",
                },
                "period_selection": {
                    "method": "deterministic document-id search over the "
                              "generator's own create_dates derivation; periods "
                              "selected, never edited",
                },
                "documents": {d["document_id"]: d["pdf_sha256"] for d in documents},
            },
            indent=2,
        )
        + "\n"
    )

    print(f"documents : {len(documents)}")
    print(f"manifest  : {output_dir / 'canonical_manifest.json'}")
    print(f"generator : {commit[:12]} dirty={dirty}")
    for d in documents:
        print(
            f"  {d['document_id']}  FY{d['reporting_year']}  "
            f"{d['invoice_number']:>14}  items={d['line_item_count']}  "
            f"gross={d['gross_total']:>9}  sha={d['pdf_sha256'][:12]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
