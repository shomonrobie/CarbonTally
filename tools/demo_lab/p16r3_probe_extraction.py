#!/usr/bin/env python3
"""P16-R2/R3 diagnosis — what does the deterministic extraction actually return
for the canonical PDFs?  Read-only probe of the real service (no DB writes).

Answers the RD-2 question precisely: are `line_items` present, and do they carry
activity/quantity/unit?
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

BACKEND = pathlib.Path("/home/shomonrobie/ct_93d5cdd/backend")
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

CORPUS_DOCS = pathlib.Path.home() / "ct_local_env/demo_lab/corpus/p12-canonical-demo-v1/documents"

from services.automatic_extraction import completeness_score  # noqa: E402


def main() -> int:
    from services import extraction_suggestions

    for pdf in sorted(CORPUS_DOCS.glob("*.pdf")):
        content = pdf.read_bytes()
        text, method, pages = extraction_suggestions._pdf_text(content) \
            if hasattr(extraction_suggestions, "_pdf_text") else (None, None, None)
        if not text:
            # fall back to the shared helper in automatic_extraction
            from services.automatic_extraction import _pdf_text  # type: ignore
            text, method, pages = _pdf_text(content)

        sug = extraction_suggestions.suggest(text[:200_000])
        data = sug.get("suggested_data") or {}
        lines = data.get("line_items") or []
        print(f"== {pdf.name} ==")
        print(f"   text_method={method} pages={pages} chars={len(text or '')}")
        print(f"   keys={sorted(k for k in data if k != 'extraction_evidence')}")
        print(f"   line_items={len(lines)}  completeness={completeness_score(data)}")
        print(f"   unresolved={sug.get('unresolved')}")
        for i, line in enumerate(lines[:6], 1):
            print(f"     line {i}: activity={line.get('activity')!r} "
                  f"qty={line.get('quantity')!r} unit={line.get('unit')!r} "
                  f"desc={str(line.get('description'))[:38]!r}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
