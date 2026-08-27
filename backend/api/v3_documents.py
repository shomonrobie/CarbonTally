"""V3 document surface (V3 legacy-capability reimplementation).

Upload, documents and batches. Upload writes to Supabase Storage and records
the ``organization_files`` row; batches group uploads in ``upload_batches``.
"""
from __future__ import annotations

from datetime import datetime
import re
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from api.dependencies import (
    RepositoryBundle,
    ensure_org_access,
    get_repositories,
)
from auth import AuthUser, require_org_member
from infra.supabase import get_service_client
from services.storage import DOCUMENTS_BUCKET, path_from_url, storage_signed_url

router = APIRouter(prefix="/api/v3", tags=["V3 — Documents"])


#: Minimum usable text length below which extraction is treated as "no text".
_OCR_MIN_TEXT = 20

#: Cap on OCR text persisted/surfaced per file (raw text stays on the object;
#: the JSONB copy is for the review workspace pre-fill).
_OCR_TEXT_CAP = 200_000


def _extract_document_text(content: bytes, filename: str, mime: str) -> dict:
    """Best-effort text/OCR extraction using the existing extraction engine.

    The engine (``pdf_engine.PDFExtractor``) performs:
      - PDF: pdfplumber text extraction, falling back to Tesseract OCR for
        scanned pages (the historical recovery fixes);
      - JPG/PNG: PIL decode + Tesseract OCR.

    When text is extracted, a DETERMINISTIC field-suggestion pass
    (``services.extraction_suggestions.suggest``) is also applied. Suggestions
    are for human-review pre-fill only — they are never written into
    ``manual_extraction_items.extracted_data`` automatically.

    Returns a JSON-safe summary — never raises. OCR failure must never fail an
    upload; the item still enters the manual-extraction queue for human review.

    Output shape::

        {"status": "ok"|"no_text"|"unsupported"|"error",
         "method": "pdf_text"|"tesseract_ocr"|None,
         "text": str, "page_count": int, "detail": str|None,
         "suggested_data": dict|None, "unresolved": list[str]|None}
    """
    try:
        from pdf_engine import PDFExtractor

        extractor = PDFExtractor()
        ftype = _classify(filename, mime)
        if ftype == "PDF":
            text = extractor._extract_text_direct(content)
            method = "pdf_text"
            if not text or len(text.strip()) < _OCR_MIN_TEXT:
                ocr = extractor._extract_text_ocr(content)
                if ocr and len(ocr.strip()) >= _OCR_MIN_TEXT:
                    text, method = ocr, "tesseract_ocr"
            page_count = extractor._get_page_count(content)
        elif ftype == "IMAGE":
            text = extractor.extract_image_text(content)
            method = "tesseract_ocr"
            page_count = 1
        else:
            return {
                "status": "unsupported",
                "method": None,
                "text": "",
                "page_count": 0,
                "detail": f"unsupported file type {ftype}",
            }
    except Exception as exc:  # pragma: no cover - defensive; never fails upload
        print(f"⚠️ OCR/extraction failed for {filename}: {exc!r}")
        return {
            "status": "error",
            "method": None,
            "text": "",
            "page_count": 0,
            "detail": str(exc)[:500],
        }
    if not text or len(text.strip()) < _OCR_MIN_TEXT:
        return {
            "status": "no_text",
            "method": method,
            "text": "",
            "page_count": page_count,
            "detail": "no usable text extracted (blank page, or image too low quality)",
        }
    truncated = len(text) > _OCR_TEXT_CAP
    clipped = text[:_OCR_TEXT_CAP]
    result = {
        "status": "ok",
        "method": method,
        "text": clipped,
        "page_count": page_count,
        "truncated": truncated,
        "detail": None,
    }
    # Deterministic suggestion pass (human-review pre-fill; never auto-approved).
    try:
        from services.extraction_suggestions import suggest

        suggestion = suggest(clipped)
        result["suggested_data"] = suggestion.get("suggested_data") or {}
        result["unresolved"] = suggestion.get("unresolved") or []
    except Exception as exc:  # pragma: no cover - defensive
        print(f"⚠️ field-suggestion pass failed for {filename}: {exc!r}")
        result["suggested_data"] = {}
        result["unresolved"] = []
    return result


def _pdf_page_count(content: bytes) -> int:
    """Best-effort PDF page count (pdfplumber, then raw-structure fallback)."""
    try:
        import io

        import pdfplumber

        with pdfplumber.open(io.BytesIO(content)) as pdf:
            return len(pdf.pages)
    except Exception:  # pragma: no cover - dependency/parse fallback
        pass
    try:
        text = content[:200_000].decode("latin-1")
        match = re.search(r"/Count\s+(\d+)", text)
        if match:
            return max(1, int(match.group(1)))
        return max(1, text.count("/Type /Page"))
    except Exception:  # pragma: no cover - non-decodable content
        return 1


class BatchCreate(BaseModel):
    batch_name: str
    metadata: dict = {}


def _classify(filename: str, mime: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf" or "pdf" in mime:
        return "PDF"
    if ext in ("jpg", "jpeg", "png", "gif", "webp") or "image" in mime:
        return "IMAGE"
    if ext in ("csv", "xlsx", "xls"):
        return "SPREADSHEET"
    return "OTHER"


@router.post("/uploads", status_code=201)
async def upload_document(
    organization_id: str = Form(...),
    data_type: str = Form("utility"),
    file: UploadFile = File(...),
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Upload a document to Supabase Storage and record it in organization_files."""
    ensure_org_access(current_user, organization_id)
    filename = file.filename or "untitled"
    content = await file.read()
    file_type = _classify(filename, file.content_type or "")
    day = datetime.utcnow().strftime("%Y/%m/%d")
    path = f"uploads/{organization_id}/{day}/{uuid4().hex}_{filename}"
    client = get_service_client()
    try:
        client.storage.from_("documents").upload(
            path,
            content,
            file_options={"content-type": file.content_type or "application/octet-stream"},
        )
    except Exception as exc:  # pragma: no cover - storage failure path
        raise HTTPException(status_code=500, detail=f"storage upload failed: {exc}")
    # D32 (P0): the documents bucket is PRIVATE. Only short-lived signed URLs
    # are ever produced — never a public URL. The canonical PATH is stored on
    # the record; consumers request a fresh signed URL per view.
    file_url = storage_signed_url(path)
    record = await repos.files.create(
        org_id=organization_id,
        name=filename,
        path=path,
        size_bytes=len(content),
        file_type=file_type,
        mime_type=file.content_type or "application/octet-stream",
        bucket="documents",
        uploaded_by=current_user.user_id,
        metadata={"data_type": data_type, "file_url": file_url},
    )

    # D23 (P0 fix): every uploaded document enters the manual-extraction
    # pipeline so CarbonTally operators/entities see it in the processing
    # queue. A single reusable "Uploads" batch per organisation groups the
    # uploads; each file becomes a pending extraction item. Enqueue failures
    # never fail the upload itself.
    try:
        batches = await repos.manual_extraction.list_batches(organization_id)
        upload_batch = next(
            (
                b
                for b in batches
                if b.batch_name == "Uploads"
                and b.status in ("open", "in_progress")
            ),
            None,
        )
        if upload_batch is None:
            upload_batch = await repos.manual_extraction.create_batch(
                org_id=organization_id,
                batch_name="Uploads",
                total_documents=1,
                total_pages=1,
                total_cost=0.0,
                currency="GBP",
                batch_description="Auto-created from document uploads",
                price_per_page=None,
                created_by=current_user.user_id,
            )
        page_count = _pdf_page_count(content) if file_type == "PDF" else 1
        await repos.manual_extraction.create_item(
            upload_batch.id,
            filename,
            path,  # D32: store the canonical PATH (non-expiring); responses sign it
            page_count,
            file_type.lower() if file_type != "OTHER" else None,
            "pending",
            file_id=record.id,  # D33: authoritative item → source-document link
        )
    except Exception as exc:  # pragma: no cover - enqueue is best-effort
        print(f"⚠️ extraction enqueue failed: {exc}")

    # OCR/extraction wiring: best-effort, deterministic, server-side. The
    # extracted text is persisted on the organization_files metadata JSONB (no
    # schema change) and surfaced in the item workspace for human review. OCR
    # failure never fails the upload — the item stays pending for manual entry.
    try:
        ocr = _extract_document_text(content, filename, file.content_type or "")
        if ocr["status"] in ("ok", "no_text"):
            await repos.files.update_metadata(record.id, {**record.metadata, "ocr": ocr})
    except Exception as exc:  # pragma: no cover - defensive
        print(f"⚠️ OCR persistence failed for {filename}: {exc!r}")

    return record


@router.post("/uploads/{file_id}/ocr")
async def run_ocr(
    file_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Run (or re-run) deterministic text/OCR extraction on an uploaded file.

    Organisation-scoped: the caller must be a member of the owning organisation.
    Reads the private storage object server-side (never returns the object; only
    the extraction summary). Persists the result on ``organization_files.metadata``
    and returns it for immediate surfacing.
    """
    doc = await repos.files.get(file_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    ensure_org_access(current_user, doc.organization_id)
    client = get_service_client()
    try:
        content = client.storage.from_(DOCUMENTS_BUCKET).download(path_from_url(doc.path))
    except Exception as exc:  # pragma: no cover - storage read failure
        raise HTTPException(status_code=404, detail=f"document object not found: {exc}")
    if isinstance(content, bytes):
        raw = content
    else:
        raw = bytes(getattr(content, "read", lambda: b"")()) if hasattr(content, "read") else b""
    ocr = _extract_document_text(raw, doc.name, doc.mime_type)
    merged = {**doc.metadata, "ocr": ocr}
    await repos.files.update_metadata(file_id, merged)
    return {"file_id": file_id, "ocr": ocr}


@router.get("/documents")
async def list_documents(
    organization_id: str,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    return {
        "documents": await repos.files.list_for_org(organization_id, status, limit, offset)
    }


@router.get("/documents/{file_id}")
async def get_document(
    file_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    doc = await repos.files.get(file_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    ensure_org_access(current_user, doc.organization_id)
    return doc


@router.get("/documents/{file_id}/signed-url")
async def get_document_signed_url(
    file_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Return a short-lived signed URL for one document (org member only).

    D32 (P0): the documents bucket is private — documents are never served via
    public URLs. This endpoint is the only way viewers obtain access, and it is
    authorization-gated per organisation.
    """
    doc = await repos.files.get(file_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    ensure_org_access(current_user, doc.organization_id)
    from services.storage import path_from_url

    url = storage_signed_url(path_from_url(doc.path))
    if not url:
        raise HTTPException(status_code=404, detail="document object not found in storage")
    return {"url": url, "expires_in_seconds": 3600}


@router.get("/documents/{file_id}/emissions")
async def document_emissions(
    file_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """D33 — reverse lookup: every emission result derived from this document.

    Chain: organization_files.id <- manual_extraction_items.file_id
    <- calculation_snapshots.source_item_id <- emissions_logs.snapshot_id.
    Org-scoped (the caller must be a member of the document's organisation).
    """
    doc = await repos.files.get(file_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    ensure_org_access(current_user, doc.organization_id)
    rows = await repos.logs.list_for_file(file_id)

    # D33.1 — append-only evidence-access audit (ids only; never URLs/secrets).
    from datetime import datetime, timezone

    from domain.audit import AuditEntry

    try:
        await repos.audit.record(
            AuditEntry(
                id=str(uuid4()),
                correlation_id=file_id,
                entity_type="organization_files",
                entity_id=file_id,
                action="evidence.reverse_lookup",
                actor=current_user.user_id,
                occurred_at=datetime.now(timezone.utc),
                changed_fields={
                    "organization_id": str(doc.organization_id),
                    "emissions_returned": len(rows),
                },
                reason="reverse document -> emissions lookup",
            )
        )
    except Exception:  # noqa: BLE001 — audit must never break the read path
        pass

    from data.base import to_jsonable

    return {
        "document_id": file_id,
        "document_name": doc.name,
        "organization_id": str(doc.organization_id),
        "emissions": [to_jsonable(dict(r)) for r in rows],
    }


@router.post("/batches", status_code=201)
async def create_batch(
    organization_id: str,
    payload: BatchCreate,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    return await repos.batches.create(
        organization_id, payload.batch_name, current_user.user_id, payload.metadata
    )


@router.get("/batches")
async def list_batches(
    organization_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, organization_id)
    return {"batches": await repos.batches.list_for_org(organization_id)}


@router.get("/batches/{batch_id}")
async def get_batch(
    batch_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    batch = await repos.batches.get(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    ensure_org_access(current_user, batch.organization_id)
    return batch
