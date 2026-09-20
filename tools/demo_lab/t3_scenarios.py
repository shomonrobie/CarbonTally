#!/usr/bin/env python3
"""DEMO-T3-IMP-001 — audit-grade Demo Lab scenario tooling.

Runs the **real** CarbonTally document journeys in the local Demo Lab only:

    external generator (offline corpus producer, pinned commit)
        -> curated corpus (PDF + ground-truth JSON, outside the repo)
        -> this driver -> real upload API -> real pipeline
        -> real extraction/mapping/validation/calculation -> real evidence

Subcommands
-----------
``sync-corpus``  select + copy the curated corpus from the pinned external
                 repository checkout into the lab state dir, with provenance.
``seed``         upload every scenario through the real CarbonTally API, enqueue
                 the automatic pipeline and record evidence.
``verify``       compare the external ground truth against CarbonTally's own
                 extracted/evidence/calculation state.
``reset``        lab-scoped removal of the T3 corpus artefacts (never identities,
                 factors, orgs or members).

The external generator is NEVER imported, executed or vendored by CarbonTally
runtime: this tool only *reads* the pinned checkout and copies generated
*documents* (data) into the lab state directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402

TASK_ID = "DEMO-T3-IMP-001"

#: The only database this tool may ever write to (enforced, never inferred).
TARGET_DB = "carbontally_demo_local"

#: Pinned external corpus producer (8A/8B audit), treated as immutable.
GENERATOR_REPO = "https://github.com/shomonrobie/carbon_tally_synthetic_documents_generator"
GENERATOR_COMMIT = "8ade2bf778d518d59924905849ab114ab2d0820a"
GENERATOR_SEED = 42

#: Curated corpus identifier (bump when the selection changes).
CORPUS_ID = "t3-uk-curated-v1"
CORPUS_DIR = lab.STATE_DIR / "corpus" / CORPUS_ID
EVIDENCE_NAME = "t3_scenarios_latest.json"
UPLOAD_PREFIX = "t3imp"


class GuardError(RuntimeError):
    """Raised when the target is not provably the Demo Lab."""


def manifest() -> dict:
    path = pathlib.Path(__file__).resolve().parent / "t3_manifest.json"
    return json.loads(path.read_text())


def assert_lab_database() -> str:
    """HARD FAIL unless the only reachable database is the Demo Lab."""
    name = lab.psql_scalar("SELECT current_database()")
    if name != TARGET_DB:
        raise GuardError(f"refusing to run against {name!r}: {TASK_ID} may only use "
                         f"{TARGET_DB!r}")
    return name


# ---------------------------------------------------------------------------
# corpus curation
# ---------------------------------------------------------------------------
_UNIT_TOKENS = ("kwh", "kilowatt", "litre", "liter", "m3", "cubic", "tonne",
                "kg", "units")


def _text_quality(pdf: pathlib.Path) -> dict:
    """Score a generated PDF's text layer for deterministic parsing.

    Some generator layouts interleave or glue the quantity/unit columns (8A audit).
    Clean documents are required for the initial T3 corpus, so candidates are
    scored on: extractable text, a separable quantity+unit pair, and no glued
    unit tokens (e.g. ``10549.7000kilowatt``).
    """
    score = {"text_chars": 0, "unit_found": False, "glued": False, "score": 0}
    try:
        import pdfplumber  # local, already a release dependency
    except Exception as exc:  # pragma: no cover
        score["error"] = f"pdfplumber unavailable: {exc}"
        return score
    try:
        with pdfplumber.open(str(pdf)) as doc:
            text = "\n".join((page.extract_text() or "") for page in doc.pages)
    except Exception as exc:  # noqa: BLE001
        score["error"] = str(exc)[:120]
        return score
    lowered = text.lower()
    score["text_chars"] = len(text)
    score["unit_found"] = any(tok in lowered for tok in _UNIT_TOKENS)
    score["glued"] = bool(re.search(r"\d(?:kwh|kilowatt|litre|tonne|cubic|kg)\b", lowered))
    score["score"] = (0 if score["glued"] else 1) + (1 if score["unit_found"] else 0) \
        + (1 if score["text_chars"] > 200 else 0)
    score["sample"] = text[:200].replace("\n", " | ")
    return score


def sync_corpus(source: pathlib.Path, dry_run: bool = False) -> dict:
    """Select + copy the curated corpus from the pinned external checkout."""
    assert_lab_database()
    spec = manifest()
    if not (source / "generator").is_dir():
        raise SystemExit(f"external generator checkout not found at {source} "
                         f"(expected a clone of {GENERATOR_REPO} at {GENERATOR_COMMIT})")
    summary = {"corpus_id": CORPUS_ID, "source": str(source),
               "generator": {"repo": GENERATOR_REPO, "commit": GENERATOR_COMMIT,
                             "seed": GENERATOR_SEED},
               "documents": [], "dry_run": dry_run}
    if not dry_run:
        CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    for scenario in spec["scenarios"]:
        selection = scenario["corpus"]
        candidates = sorted(source.glob(selection["glob"]))
        if not candidates:
            summary["documents"].append({"scenario": scenario["id"],
                                         "error": "no candidate matched the glob"})
            continue
        scored = [(_text_quality(pdf), pdf)
                  for pdf in candidates[: selection.get("candidates", 4)]]
        scored.sort(key=lambda item: (-item[0]["score"], str(item[1])))
        quality, pdf = scored[0]
        truth = pdf.with_suffix(".json")
        entry = {"scenario": scenario["id"], "source_pdf": str(pdf),
                 "source_truth": str(truth) if truth.exists() else None,
                 "quality": quality, "candidates_considered": len(candidates)}
        if truth.exists():
            try:
                entry["generation_seed"] = json.loads(truth.read_text()).get("generation_seed")
            except Exception:  # noqa: BLE001
                entry["generation_seed"] = None
        if not dry_run:
            target_pdf = CORPUS_DIR / f"{UPLOAD_PREFIX}_{scenario['id']}__{pdf.name}"
            target_truth = CORPUS_DIR / f"{UPLOAD_PREFIX}_{scenario['id']}__{truth.name}"
            shutil.copy2(pdf, target_pdf)
            entry["corpus_pdf"] = str(target_pdf)
            entry["sha256"] = hashlib.sha256(target_pdf.read_bytes()).hexdigest()
            if truth.exists():
                shutil.copy2(truth, target_truth)
                entry["corpus_truth"] = str(target_truth)
        summary["documents"].append(entry)
    if not dry_run:
        (CORPUS_DIR / "corpus_provenance.json").write_text(
            json.dumps(summary, indent=2, default=str) + "\n")
    return summary


# ---------------------------------------------------------------------------
# real API client (lab GoTrue password grant — the documented lab path)
# ---------------------------------------------------------------------------
def base_url() -> str:
    return f"http://127.0.0.1:{lab.BACKEND_PORT}"


def gateway_url() -> str:
    return f"http://127.0.0.1:{lab.GATEWAY_PORT}"


def login(actor_key: str, state: dict, spec: dict) -> str:
    """Password grant against the lab GoTrue; returns an access token."""
    actor = next(a for a in spec["actors"] if a["key"] == actor_key)
    record = state["actors"][actor_key]
    status, payload, _raw = lab.http_json(
        f"{gateway_url()}/auth/v1/token?grant_type=password", method="POST",
        headers={"apikey": state["stack_anon_key"], "Content-Type": "application/json"},
        body={"email": record["email"], "password": state["demo_password"]})
    token = (payload or {}).get("access_token") if isinstance(payload, dict) else None
    if status != 200 or not token:
        raise RuntimeError(f"login failed for {actor_key}: status={status}")
    return token


def _multipart(fields: dict, filename: str, content: bytes) -> tuple[bytes, str]:
    boundary = "----ctt3boundary"
    parts = b""
    for key, value in fields.items():
        parts += (f"--{boundary}\r\nContent-Disposition: form-data; "
                  f'name="{key}"\r\n\r\n{value}\r\n').encode()
    parts += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
              f'filename="{filename}"\r\nContent-Type: application/pdf\r\n\r\n').encode()
    parts += content + f"\r\n--{boundary}--\r\n".encode()
    return parts, f"multipart/form-data; boundary={boundary}"


def api(method: str, path: str, token: str, *, body=None, headers=None) -> tuple[int, dict]:
    request = urllib.request.Request(
        f"{base_url()}{path}", data=body, method=method,
        headers={"Authorization": f"Bearer {token}", **(headers or {})})
    try:
        response = urllib.request.urlopen(request, timeout=300)
        raw = response.read().decode()
        code = response.status
    except urllib.error.HTTPError as exc:
        raw, code = exc.read().decode(), exc.code
    try:
        return code, json.loads(raw)
    except Exception:  # noqa: BLE001
        return code, {"raw": raw[:400]}


# ---------------------------------------------------------------------------
# Demo Lab state probes (read-only)
# ---------------------------------------------------------------------------
def _scalar(sql: str) -> str:
    return lab.psql_scalar(sql)


def org_id_by_name(name: str) -> str:
    value = _scalar(f"SELECT id FROM organizations WHERE name = '{name}'")
    if not value:
        raise SystemExit(f"organisation not found in the Demo Lab: {name}")
    return value


def client_id_by_org_name(name: str) -> str:
    value = _scalar("SELECT cc.id FROM consultant_clients cc JOIN organizations o "
                    f"ON o.id = cc.organization_id WHERE o.name = '{name}'")
    if not value:
        raise SystemExit(f"consultant-client engagement not found for: {name}")
    return value


def scenario_state(scenario_id: str) -> dict:
    like = f"{UPLOAD_PREFIX}_{scenario_id}__%"
    return {
        "files": int(_scalar(f"SELECT count(*) FROM organization_files "
                             f"WHERE name LIKE '{like}'") or 0),
        "items": int(_scalar(f"SELECT count(*) FROM manual_extraction_items "
                             f"WHERE file_name LIKE '{like}'") or 0),
        "jobs": int(_scalar(f"SELECT count(*) FROM document_processing_queue "
                            f"WHERE file_name LIKE '{like}'") or 0),
    }


def job_state(scenario_id: str) -> dict:
    like = f"%{UPLOAD_PREFIX}_{scenario_id}__%"
    row = lab.psql(
        "SELECT id || '|' || status || '|' || COALESCE(stage,'') || '|' || "
        "COALESCE(calculation_snapshot_id::text,'') || '|' || "
        "COALESCE(emission_factor_used::text,'') || '|' || "
        "COALESCE(source_item_id::text,'') || '|' || "
        "COALESCE(manual_review_reason,'') || '|' || COALESCE(last_error,'') || '|' || "
        "COALESCE(attempt_count::text,'') FROM document_processing_queue "
        f"WHERE file_name LIKE '{like}' ORDER BY created_at DESC LIMIT 1")
    lines = [line for line in (row.stdout or "").splitlines() if line.strip()]
    if not lines:
        return {}
    parts = lines[0].split("|")
    if len(parts) != 9:
        return {"raw": lines[0]}
    keys = ["job_id", "status", "stage", "calculation_snapshot_id", "emission_factor_used",
            "source_item_id", "manual_review_reason", "last_error", "attempt_count"]
    return dict(zip(keys, parts))


def extracted_state(scenario_id: str) -> dict:
    """CarbonTally's own extracted/mapped/validated data for the scenario job."""
    like = f"%{UPLOAD_PREFIX}_{scenario_id}__%"
    out = {}
    for label, column, table in (("extracted", "extracted_data", "document_processing_queue"),
                                 ("mapped", "mapped_data", "document_processing_queue"),
                                 ("validated", "validation_result",
                                  "document_processing_queue")):
        raw = lab.psql(f"SELECT COALESCE({column}::text,'') FROM {table} "
                       f"WHERE file_name LIKE '{like}' ORDER BY created_at DESC LIMIT 1")
        text = (raw.stdout or "").strip()
        if text:
            try:
                out[label] = json.loads(text)
            except Exception:  # noqa: BLE001
                out[label] = {"raw": text[:300]}
    return out


def snapshot_state(scenario_id: str) -> dict:
    like = f"%{UPLOAD_PREFIX}_{scenario_id}__%"
    raw = lab.psql(
        "SELECT s.id || '|' || s.activity || '|' || s.quantity::text || '|' || "
        "COALESCE(s.quantity_unit,'') || '|' || s.co2e_kg::text || '|' || "
        "COALESCE(s.factor_id::text,'') || '|' || COALESCE(s.factor_set,'') || '|' || "
        "COALESCE(s.country,'') || '|' || COALESCE(s.scope,'') || '|' || "
        "COALESCE(s.methodology,'') || '|' || COALESCE(s.content_hash,'') || '|' || "
        "COALESCE(s.source_item_id::text,'') FROM calculation_snapshots s "
        "JOIN document_processing_queue j ON j.calculation_snapshot_id = s.id "
        f"WHERE j.file_name LIKE '{like}' LIMIT 1")
    lines = [line for line in (raw.stdout or "").splitlines() if line.strip()]
    if not lines:
        return {}
    parts = lines[0].split("|")
    keys = ["snapshot_id", "activity", "quantity", "quantity_unit", "co2e_kg",
            "factor_id", "factor_set", "country", "scope", "methodology",
            "content_hash", "source_item_id"]
    return dict(zip(keys, parts + [""] * (len(keys) - len(parts))))


# ---------------------------------------------------------------------------
# seeding (real APIs only)
# ---------------------------------------------------------------------------
def _corpus_index() -> dict:
    path = CORPUS_DIR / "corpus_provenance.json"
    if not path.exists():
        raise SystemExit(f"corpus not synced yet — run: sync-corpus "
                         f"(expected {path})")
    data = json.loads(path.read_text())
    return {entry["scenario"]: entry for entry in data["documents"]}


def seed(dry_run: bool = False, only: list | None = None, wait_seconds: int = 120) -> dict:
    """Upload every scenario through the real API and enqueue the real pipeline."""
    assert_lab_database()
    spec, state = manifest(), lab.load_state()
    corpus = _corpus_index()
    summary = {"task": TASK_ID, "corpus_id": CORPUS_ID, "dry_run": dry_run,
               "generator": {"repo": GENERATOR_REPO, "commit": GENERATOR_COMMIT,
                             "seed": GENERATOR_SEED},
               "scenarios": [], "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                            time.gmtime())}
    for scenario in spec["scenarios"]:
        sid = scenario["id"]
        if only and sid not in only:
            continue
        entry = {"scenario": sid, "kind": scenario["kind"], "actor": scenario["actor"],
                 "expected": scenario["expected"]}
        before = scenario_state(sid)
        entry["state_before"] = before
        if before["files"] > 0 and not scenario.get("repeatable"):
            entry["skipped"] = "already seeded (idempotent)"
            summary["scenarios"].append(entry)
            continue
        asset = corpus.get(sid)
        if not asset or not asset.get("corpus_pdf"):
            entry["error"] = "corpus document missing — run sync-corpus"
            summary["scenarios"].append(entry)
            continue
        pdf = pathlib.Path(asset["corpus_pdf"])
        token = login(scenario["actor"], state, spec)
        data_type = scenario.get("data_type", "utility")
        if scenario["kind"] == "consultant":
            client_id = client_id_by_org_name(scenario["client_organization"])
            body, ctype = _multipart({"data_type": data_type}, pdf.name, pdf.read_bytes())
            code, payload = api("POST", f"/api/v3/consultants/clients/{client_id}/documents",
                                token, body=body, headers={"Content-Type": ctype})
        else:
            organization_id = org_id_by_name(scenario["organization"])
            body, ctype = _multipart({"organization_id": organization_id,
                                      "data_type": data_type}, pdf.name, pdf.read_bytes())
            code, payload = api("POST", "/api/v3/uploads", token, body=body,
                                headers={"Content-Type": ctype})
        entry["upload_status"] = code
        document = payload
        if isinstance(payload, dict) and isinstance(payload.get("document"), dict):
            document = payload["document"]
        file_id = document.get("id") if isinstance(document, dict) else None
        if not file_id and isinstance(document, dict):
            file_id = document.get("file_id")
        entry["file_id"] = file_id
        if code != 201 or not file_id:
            entry["error"] = f"upload failed: {json.dumps(payload)[:300]}"
            summary["scenarios"].append(entry)
            continue
        if dry_run:
            entry["enqueue_status"] = "skipped (dry run)"
            summary["scenarios"].append(entry)
            continue
        enqueue_code, enqueue_payload = api(
            "POST", f"/api/v3/processing/documents/{file_id}/enqueue", token)
        entry["enqueue_status"] = enqueue_code
        entry["enqueue_response"] = (json.dumps(enqueue_payload)[:200]
                                     if enqueue_code not in (200, 201) else "ok")
        deadline = time.time() + wait_seconds
        state_snapshot = job_state(sid)
        while time.time() < deadline:
            state_snapshot = job_state(sid)
            if state_snapshot.get("status") in ("completed", "failed") or \
                    state_snapshot.get("stage") in ("review", "blocked", "failed"):
                break
            time.sleep(2)
        entry["job"] = state_snapshot
        entry["extracted"] = extracted_state(sid)
        entry["snapshot"] = snapshot_state(sid)
        entry["state_after"] = scenario_state(sid)
        summary["scenarios"].append(entry)
    lab.ensure_dirs()
    (lab.EVIDENCE_DIR / EVIDENCE_NAME).write_text(
        json.dumps(summary, indent=2, default=str) + "\n")
    summary["evidence"] = str(lab.EVIDENCE_DIR / EVIDENCE_NAME)
    return summary


# ---------------------------------------------------------------------------
# ground-truth verification (external truth is an oracle, never a data source)
# ---------------------------------------------------------------------------
def _first_line(payload) -> dict:
    """Best-effort extraction of a single line-item dict from a payload."""
    if not isinstance(payload, dict):
        return {}
    lines = payload.get("line_items")
    if isinstance(lines, list) and lines and isinstance(lines[0], dict):
        return lines[0]
    if payload.get("activity") or payload.get("quantity") or payload.get("unit"):
        return payload
    return {}


def verify() -> dict:
    """Compare external ground truth with CarbonTally's own state."""
    assert_lab_database()
    spec, corpus = manifest(), _corpus_index()
    report = {"task": TASK_ID, "corpus_id": CORPUS_ID,
              "generator": {"repo": GENERATOR_REPO, "commit": GENERATOR_COMMIT,
                            "seed": GENERATOR_SEED},
              "compared_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "scenarios": []}
    counts = {"compared": 0, "activity_match": 0, "quantity_match": 0,
              "unit_match": 0, "snapshot_present": 0, "skipped": 0}
    for scenario in spec["scenarios"]:
        sid = scenario["id"]
        asset = corpus.get(sid) or {}
        entry = {"scenario": sid, "kind": scenario["kind"]}
        truth_path = asset.get("corpus_truth")
        if not truth_path or not pathlib.Path(truth_path).exists():
            entry["status"] = "skipped — no ground truth sidecar"
            counts["skipped"] += 1
            report["scenarios"].append(entry)
            continue
        truth_doc = json.loads(pathlib.Path(truth_path).read_text())
        truth_lines = truth_doc.get("line_items") or []
        truth_first = truth_lines[0] if truth_lines else {}
        ct_extracted = extracted_state(sid)
        ct_first = _first_line(ct_extracted.get("extracted"))
        job = job_state(sid)
        snapshot = snapshot_state(sid)
        entry.update({
            "truth_document_id": truth_doc.get("document_id"),
            "truth_document_type": truth_doc.get("document_type"),
            "truth_generation_seed": truth_doc.get("generation_seed"),
            "truth_first_line": {k: truth_first.get(k) for k in
                                 ("activity_type", "description", "quantity", "unit")},
            "carbontally_extracted": ct_extracted.get("extracted") or None,
            "carbontally_first_line": {k: ct_first.get(k) for k in
                                       ("activity", "description", "quantity", "unit")},
            "job": job, "snapshot": snapshot,
        })
        counts["compared"] += 1
        truth_unit = str(truth_first.get("unit") or "").strip().lower()
        ct_unit = str(ct_first.get("unit") or "").strip().lower()
        entry["unit_match"] = bool(ct_unit) and (
            ct_unit == truth_unit or ct_unit.rstrip("s") == truth_unit.rstrip("s"))
        try:
            tq, cq = float(truth_first.get("quantity")), float(ct_first.get("quantity"))
            entry["quantity_delta"] = round(cq - tq, 4)
            entry["quantity_match"] = abs(cq - tq) <= max(0.01, abs(tq) * 0.01)
        except (TypeError, ValueError):
            entry["quantity_match"] = False
            entry["quantity_delta"] = None
        truth_activity = (truth_first.get("activity_type") or "").lower()
        ct_activity = (ct_first.get("activity") or ct_first.get("description") or "").lower()
        entry["activity_match"] = bool(ct_activity) and (
            truth_activity.replace("_", " ") in ct_activity
            or ct_activity in truth_activity)
        entry["snapshot_present"] = bool(snapshot)
        entry["evidence_link"] = bool(job.get("source_item_id")) or bool(
            snapshot.get("source_item_id"))
        for key in ("activity_match", "quantity_match", "unit_match"):
            if entry.get(key):
                counts[key] += 1
        if snapshot:
            counts["snapshot_present"] += 1
        report["scenarios"].append(entry)
    report["summary"] = counts
    lab.ensure_dirs()
    (lab.EVIDENCE_DIR / "t3_ground_truth_latest.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n")
    report["evidence"] = str(lab.EVIDENCE_DIR / "t3_ground_truth_latest.json")
    return report


# ---------------------------------------------------------------------------
# reset (lab-scoped, corpus artefacts only) + CLI
# ---------------------------------------------------------------------------
def reset(dry_run: bool = False) -> dict:
    """Remove only T3 corpus artefacts; never identities, factors or members."""
    assert_lab_database()
    like = f"{UPLOAD_PREFIX}_%"
    invariants = {
        "organizations": int(_scalar("SELECT count(*) FROM organizations") or 0),
        "organization_members": int(_scalar("SELECT count(*) FROM organization_members") or 0),
        "emission_factors": int(_scalar("SELECT count(*) FROM emission_factors") or 0),
        "import_batches": int(_scalar("SELECT count(*) FROM import_batches") or 0),
    }
    targets = {
        "organization_files": f"name LIKE '{like}'",
        "manual_extraction_items": f"file_name LIKE '{like}'",
        "document_processing_queue": f"file_name LIKE '{like}'",
    }
    counts = {table: int(_scalar(f"SELECT count(*) FROM {table} WHERE {clause}") or 0)
              for table, clause in targets.items()}
    counts["storage.objects"] = int(_scalar(
        "SELECT count(*) FROM storage.objects WHERE bucket_id='documents' "
        f"AND name LIKE '%{UPLOAD_PREFIX}_%'") or 0)
    summary = {"task": TASK_ID, "dry_run": dry_run, "scope": "corpus artefacts only",
               "affected": counts, "invariants_before": invariants}
    if not dry_run and any(counts.values()):
        statements = ["BEGIN;"]
        for table, clause in targets.items():
            statements.append(f"DELETE FROM {table} WHERE {clause};")
        statements.append("DELETE FROM storage.objects WHERE bucket_id='documents' "
                          f"AND name LIKE '%{UPLOAD_PREFIX}_%';")
        statements.append("COMMIT;")
        result = lab.psql("".join(statements))
        if "ERROR" in (result.stderr or ""):
            raise SystemExit(f"reset failed: {result.stderr.strip()[:300]}")
    summary["invariants_after"] = {
        "organizations": int(_scalar("SELECT count(*) FROM organizations") or 0),
        "organization_members": int(_scalar("SELECT count(*) FROM organization_members") or 0),
        "emission_factors": int(_scalar("SELECT count(*) FROM emission_factors") or 0),
        "import_batches": int(_scalar("SELECT count(*) FROM import_batches") or 0),
    }
    summary["invariants_preserved"] = summary["invariants_after"] == invariants
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="t3_scenarios.py",
                                     description=f"{TASK_ID} — audit-grade Demo Lab scenarios")
    parser.add_argument("command", choices=("sync-corpus", "seed", "verify", "reset",
                                            "status"))
    parser.add_argument("--source", default="/tmp/extgen",
                        help="path to the pinned external generator checkout")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", default=None,
                        help="comma-separated scenario ids (seed/status)")
    parser.add_argument("--wait", type=int, default=120,
                        help="seconds to wait for each job to reach a terminal stage")
    args = parser.parse_args(argv)
    only = args.only.split(",") if args.only else None
    try:
        if args.command == "sync-corpus":
            payload = sync_corpus(pathlib.Path(args.source), dry_run=args.dry_run)
        elif args.command == "seed":
            payload = seed(dry_run=args.dry_run, only=only, wait_seconds=args.wait)
        elif args.command == "verify":
            payload = verify()
        elif args.command == "reset":
            payload = reset(dry_run=args.dry_run)
        else:
            spec = manifest()
            payload = {"database": assert_lab_database(), "corpus_id": CORPUS_ID,
                       "corpus_synced": (CORPUS_DIR / "corpus_provenance.json").exists(),
                       "storage": {"schema": lab.psql_scalar(
                           "SELECT count(*) FROM pg_namespace WHERE nspname='storage'"),
                           "container": lab.container_state(lab.STORAGE_CONTAINER)},
                       "scenarios": [{"id": s["id"], "kind": s["kind"],
                                      "actor": s["actor"], **scenario_state(s["id"])}
                                     for s in spec["scenarios"]]}
    except GuardError as exc:
        print(f"GUARD BLOCKED — {exc}", file=sys.stderr)
        return 3
    print(json.dumps(payload, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
