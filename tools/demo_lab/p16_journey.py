#!/usr/bin/env python3
"""P16 — core accounting journey driver (real application path).

Drives the release API exactly as an operator would:

    upload -> enqueue -> automatic processing -> workspace/ambiguity
           -> clarification OR mapping (+ supplier) -> calculation
           -> snapshot -> emissions -> evidence -> reporting

Nothing here writes to the database directly: every state change is an HTTP call
against the running release backend, authenticated with a lab-signed token for a
real provisioned actor. The script prints the status and body of every call so a
failed step is diagnosable rather than mysterious.

Usage:
    python3 tools/demo_lab/p16_journey.py --probe
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402

ORG_A = "3fd0f325-16a1-5b53-8fb8-27929cf218fa"  # Demo Lab Organisation A (from lab state)

BACKEND = f"http://127.0.0.1:{lab.BACKEND_PORT}"
GATEWAY = f"http://127.0.0.1:{lab.GATEWAY_PORT}"
CORPUS = pathlib.Path.home() / "ct_local_env/demo_lab/corpus/p12-canonical-demo-v1"
CORPUS_DOCS = CORPUS / "documents"
CORPUS_GT = CORPUS / "ground_truth"
EVIDENCE_DIR = pathlib.Path.home() / "ct_local_env/demo_lab/evidence"
MANIFEST = pathlib.Path(__file__).resolve().parent / "manifest.json"


def _show(label: str, status: int, payload, limit: int = 900) -> None:
    body = payload if isinstance(payload, str) else json.dumps(payload)
    print(f"  [{status}] {label}\n        {body[:limit]}")


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def login(key: str) -> tuple[str | None, str]:
    """Authenticate a provisioned lab actor; password grant, then minted fallback."""
    state = lab.load_state()
    record = (state.get("actors") or {}).get(key) or {}
    email = record.get("email")
    if not email:
        manifest = _manifest()
        for actor in manifest.get("actors", []):
            if actor.get("key") == key:
                email = f"{actor['local_part']}@{manifest['email_domain']}"
                break
    if not email:
        return None, f"no identity for actor key {key!r}"
    status, payload, _ = lab.http_json(
        f"{GATEWAY}/auth/v1/token?grant_type=password", method="POST",
        headers={"apikey": lab.anon_key()},
        body={"email": email, "password": state.get("demo_password")})
    if status == 200 and isinstance(payload, dict) and payload.get("access_token"):
        return payload["access_token"], f"{key} via password_grant"
    token = lab.mint_token(record.get("user_id", ""), email, state["jwt_secret"])
    return token, f"{key} via minted_token (password grant -> {status})"


def call(path: str, token: str, method: str = "GET", body: dict | None = None,
         label: str | None = None) -> tuple[int, object]:
    status, payload, _raw = lab.http_json(
        f"{BACKEND}{path}", method=method,
        headers={"Authorization": f"Bearer {token}"}, body=body)
    _show(label or f"{method} {path}", status, payload)
    return status, payload


def upload(token: str, path: pathlib.Path, org_id: str, data_type: str) -> tuple[int, object]:
    """Multipart upload against the real release route."""
    out = subprocess.run([
        "curl", "-s", "-w", "\n%{http_code}", "-X", "POST", f"{BACKEND}/api/v3/uploads",
        "-H", f"Authorization: Bearer {token}",
        "-F", f"organization_id={org_id}",
        "-F", f"data_type={data_type}",
        "-F", f"file=@{path}",
    ], capture_output=True, text=True, timeout=300).stdout
    head, _, code = out.rpartition("\n")
    try:
        payload = json.loads(head)
    except Exception:  # noqa: BLE001 — surface the raw body for diagnosis
        payload = head
    _show(f"UPLOAD {path.name} -> /api/v3/uploads", int(code or 0), payload)
    return int(code or 0), payload


def _first_id(payload, *keys) -> str | None:
    """Pull the first plausible id out of a list-or-dict API payload."""
    def _pick(node):
        if not isinstance(node, dict):
            return None
        for key in keys:
            if node.get(key):
                return node[key]
        return None

    if isinstance(payload, list):
        for node in payload:
            got = _pick(node)
            if got:
                return got
        return None
    if isinstance(payload, dict):
        got = _pick(payload)
        if got:
            return got
        for container in ("items", "data", "results", "batches", "jobs", "organizations"):
            inner = payload.get(container)
            if isinstance(inner, list):
                found = _first_id(inner, *keys)
                if found:
                    return found
    return None


def discover_item(token: str) -> str | None:
    """Find the extraction item that automatic processing produced for the upload."""
    print("\n== item discovery ==")
    for path in ("/api/v3/ops/queues/operator", "/api/v3/ops/next-item",
                 "/api/v3/manual-extraction/batches"):
        status, payload = call(path, token, label=f"GET {path}")
        if status == 200:
            found = _first_id(payload, "item_id", "id")
            if found:
                print(f"    -> candidate id from {path}: {found}")
    # batches -> items
    status, payload = call("/api/v3/manual-extraction/batches", token)
    batch_id = _first_id(payload, "batch_id", "id") if status == 200 else None
    if batch_id:
        status, payload = call(f"/api/v3/manual-extraction/batches/{batch_id}/items", token,
                               label=f"GET batches/{batch_id}/items")
        item_id = _first_id(payload, "item_id", "id") if status == 200 else None
        print(f"    -> batch {batch_id} item: {item_id}")
        return item_id
    return None


def probe() -> int:
    state = lab.load_state()
    manifest = _manifest()

    print("== resolved lab context ==")
    print(f"  backend port : {lab.BACKEND_PORT}   gateway port: {lab.GATEWAY_PORT}")
    print(f"  lab database : {state.get('database')}")
    print(f"  actor keys   : {sorted((state.get('actors') or {}).keys())}")
    entities = state.get("entities") or {}
    print(f"  entity keys  : {sorted(entities.keys())[:12]}")
    for name, block in list(entities.items())[:6]:
        if isinstance(block, dict):
            print(f"    {name}: {json.dumps({k: v for k, v in list(block.items())[:4]})[:150]}")
    print("  manifest organizations:")
    for org in manifest.get("organizations", []):
        print(f"    {json.dumps(org)[:170]}")
    print("  manifest processing_entities:")
    for pe in manifest.get("processing_entities", []):
        print(f"    {json.dumps(pe)[:170]}")

    token, how = login("internal_operator")
    print(f"\n== auth: {how} ==")
    if not token:
        print("BLOCKED: operator auth unavailable")
        return 1
    call("/api/v3/me/context", token, label="GET /api/v3/me/context")
    call("/api/v3/ops/me", token, label="GET /api/v3/ops/me")

    org_id = None
    _status, payload = call("/api/v3/ops/organizations", token,
                            label="GET /api/v3/ops/organizations")
    items = payload if isinstance(payload, list) else (
        (payload or {}).get("items") or (payload or {}).get("organizations") or [])
    if items:
        org_id = items[0].get("id") or items[0].get("organization_id")
        print(f"  candidate orgs: {len(items)}; first -> {json.dumps(items[0])[:200]}")
    print(f"\n  resolved org_id for journey: {org_id}")

    print("\n== canonical corpus ==")
    pdfs = sorted(CORPUS_DOCS.glob("*.pdf")) if CORPUS_DOCS.exists() else []
    for pdf in pdfs:
        print(f"    {pdf.name}  ({pdf.stat().st_size} bytes)")
    print(f"    total canonical PDFs: {len(pdfs)}")
    if not pdfs:
        print(f"    MISSING under {CORPUS_DOCS}")

    print("\n== upload + enqueue probe (first canonical PDF) ==")
    if pdfs:
        status, payload = upload(token, pdfs[0], ORG_A, "pdf")
        file_id = None
        if isinstance(payload, dict):
            file_id = (payload.get("id") or payload.get("file_id")
                       or (payload.get("data") or {}).get("id")
                       or (payload.get("file") or {}).get("id"))
        print(f"    resolved file_id: {file_id}")
        if file_id:
            call(f"/api/v3/processing/documents/{file_id}/enqueue", token, method="POST",
                 body={"processing_type": "automatic"}, label="POST enqueue")
            for attempt in range(1, 7):
                time.sleep(10)
                status, payload = call("/api/v3/processing/jobs", token,
                                       label=f"GET /api/v3/processing/jobs (poll {attempt})")
    return 0


def journey() -> int:
    """IA-01/02/03/04/05 real-path journey: upload -> extraction -> clarification/mapping
    (+supplier) -> calculation -> snapshot -> emissions -> evidence."""
    evidence: dict = {"journey": "p16-core-accounting", "steps": []}

    def record(step: str, status: int, payload, extra: dict | None = None) -> None:
        evidence["steps"].append({"step": step, "status": status,
                                  "payload": payload, "extra": extra or {}})

    owner_token, how_owner = login("org_a_owner")
    op_token, how_op = login("internal_operator")
    print(f"== actors ==\n  uploader: {how_owner}\n  operator: {how_op}")
    if not owner_token or not op_token:
        return 1

    pdfs = sorted(CORPUS_DOCS.glob("*.pdf"))
    if not pdfs:
        print("BLOCKED: no canonical PDFs")
        return 1

    print("\n== STEP 1: upload as organisation member ==")
    status, payload = upload(owner_token, pdfs[0], ORG_A, "pdf")
    record("upload", status, payload, {"file": pdfs[0].name, "as": "org_a_owner"})
    file_id = _first_id(payload, "file_id", "id") if isinstance(payload, dict) else None
    if not file_id and isinstance(payload, dict):
        file_id = (payload.get("data") or {}).get("id")
    print(f"  file_id: {file_id}")
    if not (200 <= status < 300) or not file_id:
        print("BLOCKED at upload")
        _write(evidence)
        return 1

    print("\n== STEP 2: enqueue automatic processing ==")
    status, payload = call(f"/api/v3/processing/documents/{file_id}/enqueue", op_token,
                           method="POST", body={"processing_type": "automatic"},
                           label="POST enqueue (as operator)")
    record("enqueue", status, payload)

    print("\n== STEP 3: wait for extraction ==")
    for attempt in range(1, 7):
        time.sleep(10)
        status, payload = call("/api/v3/processing/jobs", op_token,
                               label=f"GET jobs (poll {attempt})")
        record(f"poll_{attempt}", status, payload)

    item_id = discover_item(op_token)
    evidence["item_id"] = item_id
    if item_id:
        call(f"/api/v3/ops/items/{item_id}/workspace", op_token, label="GET workspace")
        call(f"/api/v3/ops/items/{item_id}/mapping-options", op_token,
             label="GET mapping-options")
        call("/api/v3/activity-clarifications/options", op_token,
             label="GET clarification options")
    else:
        print("  item not discovered via batch/queue routes")

    _write(evidence)
    print(f"\n== evidence written ==")
    return 0


def _write(evidence: dict) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    out = EVIDENCE_DIR / "p16_journey_latest.json"
    out.write_text(json.dumps(evidence, indent=1, default=str))
    print(f"  -> {out}")


def item_probe(item_id: str, org_id: str = ORG_A) -> int:
    """Inspect one extraction item through the real operator workspace routes."""
    op_token, how = login("internal_operator")
    print(f"== operator auth: {how} ==")
    if not op_token:
        return 1
    print("\n== item workspace ==")
    call(f"/api/v3/ops/items/{item_id}/workspace", op_token)
    call(f"/api/v3/ops/items/{item_id}/mapping-options", op_token, label="GET mapping-options")
    print("\n== clarification plane ==")
    call("/api/v3/activity-clarifications/options", op_token, label="GET clarification options")
    call(f"/api/v3/activity-clarifications/effective?organization_id={org_id}", op_token,
         label="GET clarifications effective")
    call(f"/api/v3/issues?organization_id={org_id}", op_token, label="GET issues")
    call(f"/api/v3/processing/jobs?organization_id={org_id}", op_token, label="GET jobs")
    return 0


def resolve(item_id: str, clarification_id: str = "waste disposal|landfill|") -> int:
    """IA-03/IA-04: operator resolves the clarification, maps (with supplier) and calculates."""
    op_token, how = login("internal_operator")
    print(f"== operator: {how} ==")
    if not op_token:
        return 1

    print("\n== STEP A: resolve the clarification for each canonical line ==")
    for line in (1, 2, 3):
        status, payload = call(
            "/api/v3/activity-clarifications/clarifications", op_token, method="POST",
            body={"organization_id": ORG_A, "activity": "Waste",
                  "clarification": clarification_id, "item_id": item_id},
            label=f"POST clarify (line {line})")
    print("\n== STEP B: re-read workspace / options after resolution ==")
    call(f"/api/v3/ops/items/{item_id}/workspace", op_token)
    call(f"/api/v3/ops/items/{item_id}/mapping-options", op_token, label="GET mapping-options")
    call(f"/api/v3/activity-clarifications/effective?item_id={item_id}&activity=Waste",
         op_token, label="GET effective clarification")
    return 0


def mapcalc(item_id: str, factor_id: str) -> int:
    """IA-04/IA-05: map the item with the selected factor + a supplier, then calculate."""
    op_token, how = login("internal_operator")
    print(f"== operator: {how} ==")
    if not op_token:
        return 1

    # a supplier already exists in org A (mapping-options): British Gas
    supplier_id = "2fd4072c-0dfc-4c2b-86c6-59797f49898b"
    print("\n== STEP C: map with selected factor + supplier attribution ==")
    status, payload = call(
        f"/api/v3/ops/items/{item_id}/map", op_token, method="POST",
        body={
            "mapped_data": {"activity": "Waste", "activity_type": "Waste disposal",
                            "factor_id": factor_id, "unit": "tonnes",
                            "factor_kind": "emission_factor",
                            "methodology": "direct_multiply"},
            "mapped_facility_id": "e05b5cc8-4a6d-4ca1-9b62-8f2662ff4505",
            "mapped_asset_id": None,
            "mapped_supplier_id": supplier_id,
            "emission_factor_used": factor_id,
        },
        label="POST /ops/items/{id}/map")
    print("\n== STEP D: calculate ==")
    status, payload = call(
        f"/api/v3/ops/items/{item_id}/calculate", op_token, method="POST",
        body={"date": "2025-03-31", "activity": "Waste",
              "activity_type": "Waste disposal", "scope": "Scope 3",
              "methodology": "direct_multiply",
              "facility_id": "e05b5cc8-4a6d-4ca1-9b62-8f2662ff4505"},
        label="POST /ops/items/{id}/calculate")
    print("\n== STEP E: re-read workspace ==")
    call(f"/api/v3/ops/items/{item_id}/workspace", op_token)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--journey", action="store_true")
    ap.add_argument("--item", default=None, help="inspect one extraction item id")
    ap.add_argument("--resolve", default=None, help="resolve clarification for one item id")
    ap.add_argument("--clarification", default="waste disposal|landfill|")
    ap.add_argument("--mapcalc", default=None, help="item id to map+calculate")
    ap.add_argument("--factor", default="33696860-fa7e-469b-970e-7ebc159afa6b")
    args = ap.parse_args()
    if args.mapcalc:
        return mapcalc(args.mapcalc, args.factor)
    if args.resolve:
        return resolve(args.resolve, args.clarification)
    if args.item:
        return item_probe(args.item)
    if args.journey:
        return journey()
    return probe()


if __name__ == "__main__":
    raise SystemExit(main())
