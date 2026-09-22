"""V3 Source Evidence surface — shared Source Evidence Viewer backend (PO authorization, 2026-09-22).

One bounded, read-only resolution path for an **evidence line item**:

    GET /api/v3/evidence/line-items/{line_item_id}

Scope discipline:

* it introduces **no new evidence model** — it reads the authoritative B2
  ``public.evidence_line_items`` row, its parent extraction item, its source
  document and the calculations that reference it;
* it exposes an **allowlist only** (never arbitrary columns, never raw storage
  internals);
* it applies the **existing** authorization at read time: organisation isolation
  (``ensure_org_access``) plus the ratified **DM-6** drill-down depth. A stored
  line id is a locator, never a grant: every read re-authorizes, and the document
  pointer (the signed URL) is issued at FULL depth only;
* Processing-Entity and CarbonTally internal staff remain denied, exactly as they
  are on the disclosure drill-down route.

It is deliberately **not** an I3 tool: the closed four-tool catalogue is unchanged,
and the I3 surface keeps its own projections.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    RepositoryBundle,
    ensure_org_access,
    get_repositories,
    require_org_member,
)
from auth import AuthUser
from domain.disclosure import DisclosureViolation
from domain.disclosure_exposure import (
    assert_drilldown_allowed,
    exposure_for_role,
    project_lines,
)
from domain.evidence import derive_line_location, resolve_source_page

router = APIRouter(
    prefix="/api/v3/evidence",
    tags=["V3 — Source Evidence"],
)

#: Document-identity fields that are always returned for the caller's own line
#: (non-pointer identity: what the document *is*, never how to fetch it).
_DOCUMENT_IDENTITY_FIELDS = ("name", "file_type", "size_bytes", "uploaded_at")

#: Snapshot fields the viewer may show (bounded calculation context).
_SNAPSHOT_REF_FIELDS = (
    "id",
    "source_item_id",
    "source_line_item_id",
    "activity",
    "activity_type",
    "quantity",
    "quantity_unit",
    "co2e_kg",
    "scope",
    "date",
    "reporting_year",
    "methodology",
    "algorithm_version",
    "content_hash",
    "calculated_at",
)


def _json_safe(value: Any) -> Any:
    """JSON-safe scalar (Decimal → str preserves precision; dates → ISO)."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _role_of(current_user: AuthUser) -> str:
    """The caller's organisation role (``org_owner`` → ``owner``)."""
    role = (getattr(current_user, "role_name", None) or current_user.role or "").lower()
    if role.startswith("org_"):
        role = role[len("org_"):]
    return role


def exposure_for(current_user: AuthUser):
    """Resolve the ratified DM-6 exposure for this caller (single source of truth)."""
    return exposure_for_role(
        _role_of(current_user),
        is_entity_staff=bool(getattr(current_user, "is_entity_staff", False)),
        is_internal_staff=bool(getattr(current_user, "is_internal_staff", False)),
    )


@router.get("/line-items/{line_item_id}")
async def get_evidence_line(
    line_item_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Resolve one evidence line item for the shared Source Evidence Viewer.

    Returns the allowlisted provenance an authorized caller needs to see the
    original source document beside the extracted/mapped evidence: the line's own
    identity, the document identity, the derived source location (only when it is
    authoritative) and the bounded calculations that reference the line.

    Authorization is re-applied on every read; the response never contains a
    storage pointer below FULL depth.
    """
    from domain.audit import AuditEntry

    exposure = exposure_for(current_user)
    try:
        assert_drilldown_allowed(exposure, what="source evidence")
    except DisclosureViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    line = await repos.evidence_line_items.get(line_item_id)
    if line is None:
        raise HTTPException(status_code=404, detail="evidence line not found")
    # Organisation isolation: a line outside the caller's organisation is refused.
    ensure_org_access(current_user, line["organization_id"])

    extracted_data: Optional[dict] = None
    source_item = None
    source_item_id = line.get("source_item_id")
    if source_item_id:
        source_item = await repos.manual_extraction.get_item(str(source_item_id))
        if source_item is not None:
            extracted_data = getattr(source_item, "extracted_data", None)

    # Source document: prefer the line's own structural link, then the extraction
    # item's link, then the canonical path fallback (historical rows).
    file_row = None
    if line.get("source_file_id"):
        file_row = await repos.files.get(str(line["source_file_id"]))
    if file_row is None and source_item is not None:
        file_id = getattr(source_item, "file_id", None)
        if file_id:
            file_row = await repos.files.get(file_id)
        if file_row is None:
            file_row = await repos.files.get_by_path(getattr(source_item, "file_url", None))

    # DM-6: the signed URL is a storage pointer — FULL depth only.
    signed_url = ""
    if file_row is not None and exposure.allow_document_refs:
        from services.storage import path_from_url, storage_signed_url

        signed_url = storage_signed_url(path_from_url(file_row.path))

    # The line projection is the EXISTING DM-6 allowlist — no second policy and no
    # second evidence model.
    projected_line = {
        key: _json_safe(value)
        for key, value in project_lines([line], exposure)[0].items()
    }

    if exposure.allow_document_refs:
        location = {
            key: _json_safe(value)
            for key, value in derive_line_location(
                line=line, extracted_data=extracted_data
            ).items()
        }
    else:
        # A page/sheet/row is a document reference: below FULL it is withheld (not
        # nulled) and the state is explained honestly.
        location = {
            "state": "restricted",
            "display": "Exact source location is not available for your access level.",
        }

    document: Optional[dict] = None
    if file_row is not None:
        document = {
            field: _json_safe(getattr(file_row, field, None))
            for field in _DOCUMENT_IDENTITY_FIELDS
        }
        document["id"] = str(file_row.id)
        if exposure.allow_document_refs:
            document["path"] = file_row.path
            document["metadata"] = file_row.metadata
        document["signed_url"] = signed_url

    calculations: list[dict] = []
    try:
        rows = await repos.logs.list_for_line(
            str(line["id"]), str(line["organization_id"])
        )
    except Exception:  # noqa: BLE001 — context is non-essential to the read
        rows = []
    for row in rows:
        calculations.append(
            {field: _json_safe(row.get(field)) for field in _SNAPSHOT_REF_FIELDS if field in row}
        )

    # D33.1 precedent — append-only evidence access audit (ids only, never URLs).
    try:
        await repos.audit.record(
            AuditEntry(
                id=str(uuid.uuid4()),
                correlation_id=str(line["id"]),
                entity_type="evidence_line_items",
                entity_id=str(line["id"]),
                action="evidence.line_access",
                actor=current_user.user_id,
                occurred_at=datetime.now(timezone.utc),
                changed_fields={
                    "organization_id": str(line["organization_id"]),
                    "source_item_id": str(source_item_id) if source_item_id else None,
                    "source_file_id": (
                        str(line["source_file_id"]) if line.get("source_file_id") else None
                    ),
                    "drill_down_depth": exposure.depth,
                },
                reason="source evidence line viewed",
            )
        )
    except Exception:  # noqa: BLE001 — audit must never break the read path
        pass

    return {
        "evidence_line_item_id": str(line["id"]),
        "source_item_id": str(source_item_id) if source_item_id else None,
        "materialisation_kind": line.get("materialisation_kind"),
        "line": projected_line,
        "location": location,
        "document": document,
        "document_available": file_row is not None,
        "calculations": calculations,
        "access": {
            "drill_down_depth": exposure.depth,
            "drill_down_rationale": exposure.rationale,
            "document_references_available": bool(exposure.allow_document_refs),
        },
    }
