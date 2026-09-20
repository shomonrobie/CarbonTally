#!/usr/bin/env python3
"""DEMO-T3-REM-001 (B-1) — candidate parseability probe.

Runs **CarbonTally's own deterministic extractor** over candidate documents and
prints one JSON line per candidate, so corpus selection can be based on the real
extraction path instead of superficial text heuristics.

Must be executed with the backend interpreter (it imports the release's
extraction service)::

    backend/.venv/bin/python tools/demo_lab/t3_extract_probe.py <pdf> [<pdf> ...]

Exit codes
----------
0  probe produced a verdict for every candidate
3  the extractor could not be imported/run (the caller must FAIL LOUDLY)
"""
from __future__ import annotations

import json
import pathlib
import sys

#: Required pipeline fields (backend/domain/automatic_processing.REQUIRED_EXTRACT_FIELDS).
REQUIRED = ("activity", "quantity", "unit")


def _load_extractor():
    """Import the release extractor from the backend package root."""
    backend_root = pathlib.Path(__file__).resolve().parents[2] / "backend"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    from services.automatic_extraction import (  # noqa: PLC0415
        completeness_score,
        extract_document,
    )
    return extract_document, completeness_score


def _safe_float(value):
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def probe(paths: list[str]) -> list[dict]:
    extract_document, completeness_score = _load_extractor()
    results = []
    for raw_path in paths:
        path = pathlib.Path(raw_path)
        entry = {"path": str(path), "filename": path.name}
        try:
            content = path.read_bytes()
            result = extract_document(content, path.name, "application/pdf") or {}
        except Exception as exc:  # noqa: BLE001 — never raises out of the probe
            entry.update({"probe_error": str(exc)[:200], "ok": False})
            results.append(entry)
            continue
        data = result.get("extracted_data") or {}
        items = data.get("line_items") if isinstance(data, dict) else None
        first = items[0] if isinstance(items, list) and items else (
            data if isinstance(data, dict) else {})
        activity = str(first.get("activity") or first.get("description") or "").strip()
        unit = str(first.get("unit") or "").strip()
        quantity = _safe_float(first.get("quantity"))
        resolved = {
            field: bool(str(first.get(field) or "").strip()) for field in REQUIRED
        }
        resolved["quantity"] = quantity is not None and quantity > 0
        completeness = completeness_score(result)
        completeness_payload = completeness_score(data)
        entry.update({
            "status": result.get("status"),
            "method": result.get("method"),
            "page_count": result.get("page_count"),
            "confidence": result.get("confidence"),
            "unresolved": result.get("unresolved"),
            "completeness": completeness,
            "completeness_payload": completeness_payload,
            "line_item_count": len(items) if isinstance(items, list) else (1 if data else 0),
            "extracted_activity": activity or None,
            "extracted_quantity": quantity,
            "extracted_unit": unit or None,
            "resolved": resolved,
            "ok": (result.get("status") == "ok" and all(resolved.values())),
        })
        results.append(entry)
    return results


def main(argv: list[str]) -> int:
    if not argv:
        print(json.dumps({"error": "no candidate paths supplied"}), file=sys.stderr)
        return 3
    try:
        results = probe(argv)
    except Exception as exc:  # noqa: BLE001 — dependency/import failure
        print(json.dumps({
            "error": f"extractor unavailable: {exc}",
            "hint": "run this probe with the backend interpreter: "
                    "backend/.venv/bin/python tools/demo_lab/t3_extract_probe.py <pdf> …",
        }), file=sys.stderr)
        return 3
    for entry in results:
        print(json.dumps(entry, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
