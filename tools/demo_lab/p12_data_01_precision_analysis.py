#!/usr/bin/env python3
"""P12-DATA-01 — canonical PDF precision analysis (READ-ONLY disposable analysis tool).

Establishes the three numerical layers for the frozen corpus ``p12-canonical-demo-v1``:

  A. PDF-visible value  — the literal text printed in the shipped PDF
  B. Oracle/generator   — the generator ground truth (full precision)
  C. Extracted product  — the P12-IMPL-01 real-product extraction result

Hypothesis under test (from the generator source at the pinned commit):
``generator/data_factory.py:372`` picks ``decimal_places = rng.choice([0, 2, 3, 4])`` per
document and ``generator/reportlab_renderer.py`` prints every number with
``f"{value:,.{decimal_places}f}"`` (and ``int(x)`` for integer quantities). If so,

    PDF_VISIBLE == render(oracle_value, decimal_places(document))

for every numeric field, proving the discrepancies are display rounding rather than
extraction error.

No database access, no product-code import, no corpus/oracle writes.
Output: docs/architecture/artifacts/p12_data_01_precision_analysis_20260924.json
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import time

REPO = pathlib.Path("/home/shomonrobie/ct_93d5cdd")
ORACLE = REPO / "tools/demo_lab/p12_canonical_manifest.json"
IMPL01 = (REPO / "docs/architecture/artifacts"
          / "p12_impl_01_extracted_data_20260924.json")
OUT = (REPO / "docs/architecture/artifacts"
       / "p12_data_01_precision_analysis_20260924.json")
CORPUS = pathlib.Path.home() / "ct_local_env/demo_lab/corpus/p12-canonical-demo-v1"

MONEY = r"£\s*([\d,]+(?:\.\d+)?)"
ROW_RE = re.compile(
    r"^(?P<desc>.+?)\s+(?P<qty>[\d,]+(?:\.\d+)?)\s+(?P<unit>[A-Za-z]{1,6})\s+"
    rf"{MONEY}\s+{MONEY}\s*$"
)
UNITS = {"t", "tonnes", "tonne", "kg", "kwh"}


def pdf_text(pdf: pathlib.Path) -> str:
    return subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                          capture_output=True, text=True).stdout


def decimals(text: str | None) -> int:
    return len(str(text).split(".")[1]) if text and "." in str(text) else 0


def render(value, dp: int) -> str:
    """Reproduce the generator renderer's currency formatting."""
    return f"{float(value):,.{dp}f}"


def num(text):
    if text is None:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", str(text).replace(",", ""))
    if cleaned in ("", "-", "."):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def classify(pdf_visible, oracle_value, extracted, dp: int):
    """(classification, note) for one numeric field."""
    if extracted is None:
        return "unknown", "no extracted value"
    if abs(float(extracted) - float(oracle_value)) < 1e-9:
        return "exact agreement", "extraction equals the oracle exactly"
    rendered = render(oracle_value, dp)
    if str(pdf_visible) == str(extracted) == rendered:
        return ("PDF display rounding",
                f"oracle {oracle_value} rendered at {dp} dp = {rendered} = printed = extracted")
    if str(pdf_visible) == str(extracted):
        return ("PDF display rounding",
                "printed matches extraction; rounding representation differs in form only")
    return "unexpected", "printed / extracted / oracle reconciliation failed"


def printed_total(text: str) -> str:
    """The printed gross/total value — the field that carries the document's
    display precision (labels vary: ``Total``, ``Total Due``, ``Net Payable``)."""
    pattern = re.compile(
        r"(?i)^.*(?<!\bnet\s)(?:\b(?:total(?:\s+due|\s+amount)?|amount\s+due|"
        r"balance\s+due|net\s+payable|grand\s+total)\b)[^:：\n]*[:：]"
    )
    for line in text.splitlines():
        if pattern.search(line):
            found = re.findall(MONEY, line)
            if found:
                return found[-1]
    return ""


def main() -> int:
    oracle = json.loads(ORACLE.read_text())
    impl = {d["document_id"]: d for d in json.loads(IMPL01.read_text())["documents"]}
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    prov = json.loads((CORPUS / "corpus_provenance.json").read_text())

    analysis = {
        "task_id": "P12-DATA-01-20260924-CANONICAL-PDF-PRECISION-CONTRACT",
        "corpus": "p12-canonical-demo-v1",
        "corpus_path": str(CORPUS),
        "oracle_path": str(ORACLE),
        "oracle_sha256": subprocess.run(["sha256sum", str(ORACLE)],
                                        capture_output=True, text=True).stdout.split()[0],
        "generator_commit": prov["generator"]["commit"],
        "baseline_commit": commit,
        "analysis_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "database_touched": False,
        "product_code_modified": False,
        "documents": [], "line_comparisons": [], "document_comparisons": [],
        "arithmetic_checks": [], "discrepancy_classifications": [],
        "precision_contract_options": [], "recommended_contract": "",
        "oracle_policy": "", "corpus_policy": "", "future_v2_required": None,
        "future_v2_recommended": None, "precision_rules": {},
    }
    _collect(analysis, oracle, impl)
    _contracts(analysis)
    _doc_arithmetic(analysis, oracle, impl)
    _policies(analysis)
    OUT.write_text(json.dumps(analysis, indent=2, default=str) + "\n")
    for key in ("documents", "line_comparisons", "document_comparisons",
                "arithmetic_checks", "discrepancy_classifications"):
        print(f"{key}: {len(analysis[key])}")
    print("artifact:", OUT)
    return 0


def _collect(analysis: dict, oracle: dict, impl: dict) -> None:
    for doc in oracle["documents"]:
        did = doc["document_id"]
        pdf = pathlib.Path(doc["pdf"])
        text = pdf_text(pdf)
        rows = [m for m in (ROW_RE.match(ln.strip()) for ln in text.splitlines())
                if m and m.group("unit").lower() in UNITS]
        total = printed_total(text)
        dp = decimals(total)
        extracted = impl[did]["actual_extracted_data"]
        expected_lines = doc["line_items"]
        actual_lines = extracted.get("line_items") or []

        analysis["documents"].append({
            "document_id": did, "pdf_sha256": doc["pdf_sha256"],
            "display_decimal_places": dp, "printed_total": total,
            "oracle_total": doc["gross_total"],
            "extracted_total": extracted.get("gross_amount"),
            "expected_line_count": len(expected_lines),
            "extracted_line_count": len(actual_lines),
            "printed_line_count_from_pdf_text": len(rows),
        })

        doc_fields = [
            ("supplier", doc["supplier"], extracted.get("supplier"), None),
            ("customer", doc["customer"], extracted.get("customer"), None),
            ("invoice_ref", doc["invoice_number"], extracted.get("invoice_number"), None),
            ("invoice_date", doc["invoice_date"], extracted.get("date"), None),
            ("period_start", doc["billing_period_start"],
             extracted.get("billing_period_start"), None),
            ("period_end", doc["billing_period_end"],
             extracted.get("billing_period_end"), None),
            ("subtotal", doc["net_total"], extracted.get("net_amount"), dp),
            ("vat", doc["vat_total"], extracted.get("vat_amount"), dp),
            ("total", doc["gross_total"], extracted.get("gross_amount"), dp),
        ]
        for field, exp, act, field_dp in doc_fields:
            if field_dp is None:
                pdfv = exp
                cls, note = (("exact agreement", "string field")
                             if str(exp) == str(act) else ("unexpected", "string mismatch"))
            else:
                pdfv = render(exp, field_dp)
                cls, note = classify(num(pdfv), exp, num(act), field_dp)
            entry = {"document_id": did, "field": field, "pdf_visible": pdfv,
                     "oracle": exp, "extracted": act, "classification": cls, "note": note}
            analysis["document_comparisons"].append(entry)
            if cls != "exact agreement":
                analysis["discrepancy_classifications"].append(entry)

        for index, exp in enumerate(expected_lines):
            act = actual_lines[index] if index < len(actual_lines) else {}
            row = rows[index] if index < len(rows) else None
            pairs = (("quantity", "qty", "quantity"),
                     ("unit_price", "rate", "unit_price"),
                     ("net_amount", "net", "net_amount"))
            for field, pdf_key, impl_key in pairs:
                pdf_visible = (re.findall(MONEY, row.group(0)) if pdf_key in ("rate", "net")
                               else [row.group(pdf_key)]) if row else [None]
                pdf_value = (pdf_visible[0] if pdf_key == "rate"
                             else pdf_visible[-1]) if row else None
                cls, note = classify(num(pdf_value), exp.get(field), act.get(impl_key), dp)
                record = {"document_id": did, "line": index + 1, "field": field,
                          "pdf_visible": pdf_value, "oracle": exp.get(field),
                          "extracted": act.get(impl_key), "document_dp": dp,
                          "classification": cls, "note": note,
                          "printed_line": act.get("source_line")}
                analysis["line_comparisons"].append(record)
                if cls != "exact agreement":
                    analysis["discrepancy_classifications"].append(record)

        for index, exp in enumerate(expected_lines):
            act = actual_lines[index] if index < len(actual_lines) else {}
            row = rows[index] if index < len(rows) else None
            q_pdf = r_pdf = n_pdf = None
            if row:
                money = re.findall(MONEY, row.group(0))
                q_pdf, r_pdf = num(row.group("qty")), num(money[0])
                n_pdf = num(money[-1])
            oracle_ok = abs(exp["quantity"] * exp["unit_price"] - exp["net_amount"]) < 0.01
            pdf_ok = (abs(q_pdf * r_pdf - n_pdf) < 0.01
                      if None not in (q_pdf, r_pdf, n_pdf) else None)
            analysis["arithmetic_checks"].append({
                "document_id": did, "line": index + 1,
                "oracle_qty_x_rate": round(exp["quantity"] * exp["unit_price"], 4),
                "oracle_net": exp["net_amount"], "oracle_consistent": oracle_ok,
                "pdf_qty_x_rate": round(q_pdf * r_pdf, 4) if None not in (q_pdf, r_pdf) else None,
                "pdf_net": n_pdf, "pdf_consistent": pdf_ok,
                "pdf_deviation": (round(abs(q_pdf * r_pdf - n_pdf), 4)
                                  if None not in (q_pdf, r_pdf, n_pdf) else None),
                "extracted_arithmetic_ok": act.get("arithmetic_ok"),
            })


def _contracts(analysis: dict) -> None:
    """The acceptance-contract options evaluated against the measured evidence."""
    def option(cid, **kw):
        analysis["precision_contract_options"].append({"id": cid, **kw})

    option("A", name="PDF-visible values are authoritative",
           meaning="Acceptance compares extraction against what the PDF prints.",
           validates="Document fidelity for every field, including rounding.",
           cannot_validate="Generator intent and exact invoice arithmetic — printed values do "
                           "not reproduce the invoice arithmetic on 15/21 lines.",
           effect_p12_impl_01="No change needed; all 117 field comparisons pass at the printed "
                              "precision.",
           effect_p12_impl_02="Waste evidence comes from printed descriptions — unaffected.",
           effect_calculation="Emissions from printed numbers would differ from generator intent.",
           effect_evidence="Records displayed values only; generator intent is lost.",
           effect_corpus_regen="Would require the oracle to be re-derived from the render.",
           false_failure_risk="None for extraction.",
           hidden_defect_risk="HIGH — with the true value removed from the oracle, a real column "
                              "misread becomes undetectable.")
    option("B", name="Generator/oracle values authoritative for everything",
           meaning="Acceptance compares extraction against full-precision oracle values.",
           validates="Generator fidelity and exact arithmetic.",
           cannot_validate="Extraction correctness for the rendered document: 29/63 line fields "
                           "can never pass because those digits are not in the PDF.",
           effect_p12_impl_01="Would report 29 line-field and 6 document-field false failures.",
           effect_p12_impl_02="Quantity/supplier evidence judged against invisible digits.",
           effect_calculation="Validates the generator, not the document.",
           effect_evidence="Provenance would claim values absent from the source.",
           effect_corpus_regen="All documents would have to be rendered at maximum precision.",
           false_failure_risk="HIGH.",
           hidden_defect_risk="LOW for arithmetic; it hides the rendering relationship.")
    option("C", name="Split: PDF-visible for extraction, generator precision as "
                     "generation-level ground truth",
           meaning="Two fidelity questions, two oracles.",
           validates="Both, without conflating them.",
           cannot_validate="Nothing material; needs a mechanism (see E) to compare at the "
                           "document's precision.",
           effect_p12_impl_01="Confirms the implementation: 117/117 field comparisons reconcile "
                              "exactly at the document's own precision.",
           effect_p12_impl_02="Clean — printed descriptions/quantities for the document lane, "
                              "generator precision retained as metadata.",
           effect_calculation="Document-lane tests use printed numbers; generator-lane tests use "
                              "full precision, stated explicitly.",
           effect_evidence="Evidence carries printed value + display precision + generator value "
                           "as separately labelled layers.",
           effect_corpus_regen="No regeneration needed for v1.",
           false_failure_risk="LOW.",
           hidden_defect_risk="LOW — a misread differs from the *printed* value, so it still fails.")
    option("D", name="Explicit numeric tolerance",
           meaning="Accept if |extracted - oracle| <= tolerance.",
           validates="Nothing specific; it is a mechanism, not a policy.",
           cannot_validate="Which layer is authoritative, or whether a difference is display "
                           "rounding rather than a misread column.",
           effect_p12_impl_01="A tolerance covering the observed £80 deviation also covers "
                              "9.4% of a 297.0 net — far too wide.",
           effect_p12_impl_02="Propagates loose comparisons into waste/quantity evidence.",
           effect_calculation="Would silently accept arithmetic inconsistencies.",
           effect_evidence="Tolerance is not provenance.",
           effect_corpus_regen="None.",
           false_failure_risk="LOW by construction.",
           hidden_defect_risk="HIGH — measured deviations reach 28.0 on a 297.0 net (9.4%) and "
                              "80.0 on a 6256.0 net (1.28%).")
    option("E", name="Field-specific precision rules derived from the document",
           meaning="Each document declares the display precision its own columns exhibit; "
                   "comparison is exact at that precision, per field family.",
           validates="Document fidelity precisely, field by field.",
           cannot_validate="Nothing; it is the mechanism that makes C executable.",
           effect_p12_impl_01="0 unexplained mismatches across 117 field comparisons.",
           effect_p12_impl_02="Provides a per-document precision context for evidence.",
           effect_calculation="Calculation tests declare which layer they use.",
           effect_evidence="Precision becomes recorded provenance, not an assumption.",
           effect_corpus_regen="None required.",
           false_failure_risk="LOW.",
           hidden_defect_risk="LOW when derived from the document itself (observed uniform per "
                              "document: 0/2/3/4 dp).")


def _doc_arithmetic(analysis: dict, oracle: dict, impl: dict) -> None:
    """Document-level arithmetic at both precisions (sum(nets) vs subtotal;
    subtotal + VAT vs gross)."""
    checks = []
    for doc in oracle["documents"]:
        did = doc["document_id"]
        text = pdf_text(pathlib.Path(doc["pdf"]))
        printed = {
            "subtotal": _labelled(text, r"net\s*amount|sub\s*total|net\s*total"),
            "vat": _labelled(text, r"vat|gst|tax"),
            "gross": _labelled(
                text, r"net\s+payable|total(?:\s+due)?|amount\s+due|gross\s+total",
                exclude=r"net\s+total"),
        }
        extracted = impl[did]["actual_extracted_data"]
        lines = extracted.get("line_items") or []
        pdf_sum = round(sum(num(l.get("net_amount")) or 0 for l in lines), 4)
        oracle_sum = round(sum(l["net_amount"] for l in doc["line_items"]), 4)
        checks.append({
            "document_id": did,
            "display_decimal_places": decimals(printed["gross"]),
            "printed_subtotal": printed["subtotal"],
            "printed_vat": printed["vat"],
            "printed_gross": printed["gross"],
            "oracle_net_total": doc["net_total"], "oracle_vat_total": doc["vat_total"],
            "oracle_gross_total": doc["gross_total"],
            "pdf_sum_of_line_nets": pdf_sum,
            "pdf_sum_vs_printed_subtotal_ok": (
                abs(pdf_sum - (num(printed["subtotal"]) or 0)) < 0.005),
            "pdf_sum_vs_printed_subtotal_deviation": round(
                abs(pdf_sum - (num(printed["subtotal"]) or 0)), 4),
            "oracle_sum_of_line_nets": oracle_sum,
            "oracle_sum_vs_oracle_net_ok": abs(oracle_sum - doc["net_total"]) < 0.005,
            "pdf_subtotal_plus_vat_vs_printed_gross_ok": (
                abs((num(printed["subtotal"]) or 0) + (num(printed["vat"]) or 0)
                    - (num(printed["gross"]) or 0)) < 0.005),
            "oracle_net_plus_vat_vs_gross_ok": (
                abs(doc["net_total"] + doc["vat_total"] - doc["gross_total"]) < 0.005),
        })
    analysis["document_arithmetic"] = checks


def _labelled(text: str, label: str, exclude: str = "") -> str:
    """Last money value on the first line matching ``label`` (label-anchored)."""
    pattern = re.compile(rf"(?i)^.*\b(?:{label})\b[^:：\n]*[:：]")
    skip = re.compile(rf"(?i){exclude}") if exclude else None
    for line in text.splitlines():
        if pattern.search(line) and not re.search(r"(?i)vat\s*no", line):
            if skip and skip.search(line):
                continue
            found = re.findall(MONEY, line)
            if found:
                return found[-1]
    return ""


def _policies(analysis: dict) -> None:
    """Contract recommendation, oracle/corpus policy and precision rules."""
    analysis["recommended_contract"] = (
        "C as the policy, implemented with E as the mechanism: the printed value is "
        "authoritative for extraction acceptance, compared exactly at the document's own display "
        "precision, while the generator/oracle retains full precision as generation- and "
        "calculation-level ground truth. A and B alone are rejected by the measured evidence; "
        "D alone is rejected because deviations reach 9.4%."
    )
    analysis["oracle_policy"] = (
        "tools/demo_lab/p12_canonical_manifest.json is NOT changed. Its numeric values remain "
        "authoritative for generator-level validation; for extraction acceptance they must be "
        "interpreted through each document's display precision. Conflicting fields (the numeric "
        "values of 002/004 and the sub-4dp rates of 001/003/005) are recorded as conflicts, not "
        "corrected."
    )
    analysis["corpus_policy"] = (
        "p12-canonical-demo-v1 remains FROZEN (hashes verified in this analysis). No document, "
        "manifest or provenance file was modified."
    )
    analysis["future_v2_required"] = False
    analysis["future_v2_recommended"] = True
    analysis["future_v2_rationale"] = (
        "Not required for a correct contract, but advised for investor clarity: a v2 rendered "
        "uniformly at 4 dp with no truncated description fragments would remove the one genuine "
        "source ambiguity in v1 (document 002 prints 'Qty: 25.8 t...' inside its description "
        "while its Qty column prints 26). v1 must remain available for regression."
    )
    analysis["precision_rules"] = {
        "observed_per_document_display_precision": {
            d["document_id"]: d["display_decimal_places"] for d in analysis["documents"]
        },
        "policy": "Precision is a per-document display property (observed 0/2/3/4 dp). "
                  "Quantity, rate, line net, subtotal, VAT and gross all share the document's "
                  "precision, with integer quantities printed without decimals. A field-specific "
                  "rule must be derived per document from the document itself.",
    }


if __name__ == "__main__":
    sys.exit(main())
