"""Phase 8 B3/B4 — disclosure API surface (contract §12.2, B4 §10).

Exposes the ratified disclosure read models, the three authorised B3 write paths
(projection run, intensity selection, applicability assessment) and the B4
narrative/finalisation paths.

Governance enforced here, server-side (the UI is never the boundary):

* reads require an organisation member of the owning organisation;
* writes require organisation **Owner/Admin** (B4-D1 for approval/finalisation);
* Processing-Entity staff and CarbonTally internal staff are denied both
  (report lifecycle authority is the organisation's own — the S3 boundary);
* drill-down (evidence lines) is governed by the ratified **DM-6** matrix;
* an absent/unknown catalogue row, report, version or value returns a
  **meaningful 4xx** — never a raw database error;
* no endpoint may write a calculated value.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from api.dependencies import (
    ensure_org_access,
    get_current_user,
    get_pool,
    get_repositories,
    require_org_member,
)
from auth import AuthUser
from core.logging import get_logger
from data.disclosure import DisclosureCatalogRepository, DisclosureRepository
from data.disclosure_projection import DisclosureProjectionRepository
from domain.capability_catalogue import (
    project_capability_catalogue,
    select_governed_catalogue_version,
)
from domain.disclosure import DisclosureViolation
from domain.disclosure_exposure import (
    assert_drilldown_allowed,
    exposure_for_role,
    project_lines,
)
from domain.disclosure_projection import validate_applicability_basis
from services.disclosure_finalisation import (
    ArtefactRequired,
    DisclosureFinalisationService,
    FinalisationBlocked,
)
from services.disclosure_narrative import DisclosureNarrativeService
from services.disclosure_projection import DisclosureProjectionService
from services.report_artefact_storage import get_report_artefact_storage

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v3", tags=["V3 — Disclosure"])


def get_report_artefact_storage_dep() -> Any:
    """FastAPI dependency for the frozen-artefact storage adapter (B4-D6).

    Tests override this instead of touching real storage; production resolves the
    private-bucket adapter.
    """
    return get_report_artefact_storage()


def _branded_pdf_producer(repos: Any, current_user: AuthUser, report: dict) -> Any:
    """Build the frozen-artefact renderer for one report (B4-D5).

    Reuses the **existing** white-label renderer and branding resolver — the same
    code path as the live-render route (``GET /reports/{id}/pdf``, retained for
    drafts per `A15`) — rather than introducing a second renderer.
    """

    async def _produce() -> bytes:
        from api.consultant_branding import resolve_report_branding
        from engines.pdf_render import render_branded_pdf

        full = await repos.reports.get_full(report["id"])
        content = (full or {}).get("generated_content") or {}
        if not content:
            raise DisclosureViolation("report has no generated content to freeze")
        brand = await resolve_report_branding(repos, current_user, report["organization_id"])
        return render_branded_pdf(
            report={
                "report_type": (full or {}).get("report_type"),
                "reporting_year": (full or {}).get("reporting_year"),
            },
            content=content,
            brand=brand,
        )

    return _produce

#: The organisation roles that may perform B3 writes (B1 posture: p8_disclosure_is_org_admin).
_ORG_WRITE_ROLES: tuple[str, ...] = ("owner", "admin")

_SELECTION_SOURCES: tuple[str, ...] = (
    "CUSTOMER_SELECTED",
    "CUSTOMER_CONFIRMED",
    "CARBONTALLY_RECOMMENDED",
)


# ---------------------------------------------------------------------------
# Authorization (server-side, never the UI)
# ---------------------------------------------------------------------------
def _org_role(current_user: AuthUser) -> str:
    """Normalise the caller's organisation role (``org_owner`` -> ``owner``)."""
    role = (getattr(current_user, "role_name", None) or current_user.role or "").lower()
    if role.startswith("org_"):
        role = role[len("org_") :]
    return role


def _authorize_read(current_user: AuthUser, organization_id: str) -> None:
    if current_user.is_entity_staff:
        raise HTTPException(status_code=403, detail="Processing Entity staff cannot read customer disclosures")
    if current_user.is_internal_staff:
        raise HTTPException(status_code=403, detail="CarbonTally staff cannot read customer disclosures")
    ensure_org_access(current_user, organization_id)


def _authorize_write(current_user: AuthUser, organization_id: str) -> None:
    _authorize_read(current_user, organization_id)
    if _org_role(current_user) not in _ORG_WRITE_ROLES:
        raise HTTPException(
            status_code=403,
            detail="This disclosure action requires organisation owner/admin access",
        )


def _field(row: Any, name: str, default: Any = None) -> Any:
    """Read a field from an asyncpg Record/dict or an object (defensive)."""
    if row is None:
        return default
    if isinstance(row, dict):
        return row.get(name, default)
    try:
        return row[name]
    except Exception:  # noqa: BLE001 - fall back to attribute access
        return getattr(row, name, default)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class ProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_version_id: Optional[str] = Field(
        default=None, description="Project this version; defaults to the report's current version"
    )


class IntensityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    denominator_type_id: str = Field(min_length=1)
    selection_basis: str = Field(min_length=1)
    denominator_value: Optional[float] = Field(default=None, gt=0)
    denominator_unit: Optional[str] = None
    numerator_value: Optional[float] = Field(default=None, ge=0)
    numerator_disclosure_value_id: Optional[str] = None
    selection_source: str = "CUSTOMER_SELECTED"
    report_version_id: Optional[str] = None


class ApplicabilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    framework_version_id: str = Field(min_length=1)
    reporting_year: int = Field(ge=1990, le=2200)
    reporting_period_start: str = Field(min_length=1)
    reporting_period_end: str = Field(min_length=1)
    assessed_status: str = Field(min_length=1)
    basis: str = Field(min_length=1)
    characteristic_snapshot: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Resolution helpers
# ---------------------------------------------------------------------------
async def _report_or_404(repos: Any, report_id: str) -> dict:
    report = await repos.reports.get_full(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


async def _current_version_or_404(repos: Any, report_id: str) -> str:
    version = await repos.report_versions.get_current(report_id)
    version_id = _field(version, "id")
    if not version_id:
        raise HTTPException(status_code=404, detail="Report has no current version")
    return str(version_id)


# ---------------------------------------------------------------------------
# GET /api/v3/reports/{report_id}/disclosure
# ---------------------------------------------------------------------------
@router.get("/reports/{report_id}/disclosure")
async def get_report_disclosure(
    report_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: Any = Depends(get_repositories),
    pool: Any = Depends(get_pool),
) -> dict:
    report = await _report_or_404(repos, report_id)
    organization_id = str(report["organization_id"])
    _authorize_read(current_user, organization_id)
    version_id = await _current_version_or_404(repos, report_id)

    proj = DisclosureProjectionRepository(pool)
    values = await proj.list_values(report_version_id=version_id)
    counts: dict[str, int] = {}
    for row in values:
        key = str(row["value_status"])
        counts[key] = counts.get(key, 0) + 1
    return {
        "report_id": report_id,
        "report_version_id": version_id,
        "organization_id": organization_id,
        "count": len(values),
        "count_by_status": counts,
        "values": values,
    }


# ---------------------------------------------------------------------------
# GET /api/v3/reports/{report_id}/disclosure/{value_id}/lines  (DM-6 read model)
# ---------------------------------------------------------------------------
@router.get("/reports/{report_id}/disclosure/{value_id}/lines")
async def get_disclosure_value_lines(
    report_id: str,
    value_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: Any = Depends(get_repositories),
    pool: Any = Depends(get_pool),
) -> dict:
    report = await _report_or_404(repos, report_id)
    organization_id = str(report["organization_id"])
    _authorize_read(current_user, organization_id)

    proj = DisclosureProjectionRepository(pool)
    value = await proj.get_value(value_id)
    if value is None or str(value["organization_id"]) != organization_id:
        # Do not leak the existence of another tenant's value.
        raise HTTPException(status_code=404, detail="Disclosure value not found for this report")
    context = await proj.report_context(str(value["report_version_id"]))
    if context is None or str(context["report_id"]) != str(report_id):
        raise HTTPException(status_code=404, detail="Disclosure value not found for this report")

    rows = [
        row
        for row in await proj.value_lines(report_version_id=str(value["report_version_id"]))
        if str(row["disclosure_value_id"]) == str(value_id)
    ]
    # DM-6 (ratified): drill-down depth is per role. Denied callers get a 403
    # rather than a partially redacted answer; allowed callers get the line set
    # projected to their depth (hidden fields are removed, never nulled).
    rule = exposure_for_role(
        _org_role(current_user),
        is_entity_staff=current_user.is_entity_staff,
        is_internal_staff=current_user.is_internal_staff,
    )
    try:
        assert_drilldown_allowed(rule)
    except DisclosureViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    projected = project_lines(rows, rule)
    return {
        "report_id": report_id,
        "report_version_id": str(value["report_version_id"]),
        "disclosure_value_id": value_id,
        "requirement_version_id": str(value["requirement_version_id"]),
        "value_status": value["value_status"],
        "effective_class": value["effective_class"],
        "drill_down_depth": rule.depth,
        "drill_down_rationale": rule.rationale,
        "count": len(projected),
        "lines": projected,
    }


# ---------------------------------------------------------------------------
# POST /api/v3/reports/{report_id}/disclosure/project
# ---------------------------------------------------------------------------
@router.post("/reports/{report_id}/disclosure/project")
async def project_report_disclosure(
    report_id: str,
    payload: Optional[ProjectRequest] = None,
    current_user: AuthUser = Depends(require_org_member()),
    repos: Any = Depends(get_repositories),
    pool: Any = Depends(get_pool),
) -> dict:
    report = await _report_or_404(repos, report_id)
    organization_id = str(report["organization_id"])
    _authorize_write(current_user, organization_id)

    version_id = (
        payload.report_version_id if payload and payload.report_version_id else None
    ) or await _current_version_or_404(repos, report_id)

    service = DisclosureProjectionService(pool)
    try:
        summary = await service.project_report_version(report_version_id=version_id)
    except DisclosureViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return summary


# ---------------------------------------------------------------------------
# GET / POST /api/v3/reports/{report_id}/intensity
# ---------------------------------------------------------------------------
@router.get("/reports/{report_id}/intensity")
async def get_report_intensity(
    report_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: Any = Depends(get_repositories),
    pool: Any = Depends(get_pool),
) -> dict:
    report = await _report_or_404(repos, report_id)
    organization_id = str(report["organization_id"])
    _authorize_read(current_user, organization_id)
    version_id = await _current_version_or_404(repos, report_id)

    proj = DisclosureProjectionRepository(pool)
    catalogue = await proj.list_intensity_catalogue()
    selected = await proj.list_intensity_ratios(report_version_id=version_id)
    return {
        "report_id": report_id,
        "report_version_id": version_id,
        # Generic CarbonTally capabilities. No framework/statutory claim is made
        # or implied here (PO direction 2026-09-13; D17).
        "catalogue": catalogue,
        "selected": selected,
        "framework_claims_recorded": False,
    }


@router.post("/reports/{report_id}/intensity")
async def select_report_intensity(
    report_id: str,
    payload: IntensityRequest,
    current_user: AuthUser = Depends(require_org_member()),
    repos: Any = Depends(get_repositories),
    pool: Any = Depends(get_pool),
) -> dict:
    report = await _report_or_404(repos, report_id)
    organization_id = str(report["organization_id"])
    _authorize_write(current_user, organization_id)

    if payload.selection_source not in _SELECTION_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"selection_source must be one of {list(_SELECTION_SOURCES)}",
        )
    if not payload.selection_basis.strip():
        raise HTTPException(status_code=400, detail="selection_basis must explain the choice")

    version_id = payload.report_version_id or await _current_version_or_404(repos, report_id)

    proj = DisclosureProjectionRepository(pool)
    catalogue = await proj.list_intensity_catalogue()
    match = next((row for row in catalogue if str(row["id"]) == str(payload.denominator_type_id)), None)
    if match is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Unknown or inactive intensity denominator. Choose one from the controlled "
                "catalogue returned by GET /api/v3/reports/{report_id}/intensity."
            ),
        )

    confirmed_by = (
        current_user.user_id if payload.selection_source == "CUSTOMER_CONFIRMED" else None
    )
    row = await proj.upsert_intensity_ratio(
        organization_id=organization_id,
        report_version_id=str(version_id),
        denominator_type_id=str(payload.denominator_type_id),
        selection_basis=payload.selection_basis.strip(),
        denominator_value=payload.denominator_value,
        denominator_unit=payload.denominator_unit,
        numerator_value=payload.numerator_value,
        numerator_disclosure_value_id=payload.numerator_disclosure_value_id,
        selection_source=payload.selection_source,
        confirmed_by=confirmed_by,
    )
    if row is None:  # pragma: no cover - upsert always returns a row
        raise HTTPException(status_code=502, detail="Intensity selection could not be stored")
    return {"report_id": report_id, "report_version_id": str(version_id), "selection": row}


# ---------------------------------------------------------------------------
# GET / POST /api/v3/organizations/{organization_id}/applicability
# ---------------------------------------------------------------------------
@router.get("/organizations/{organization_id}/applicability")
async def list_applicability(
    organization_id: str,
    reporting_year: Optional[int] = Query(default=None),
    current_user: AuthUser = Depends(require_org_member()),
    pool: Any = Depends(get_pool),
) -> dict:
    _authorize_read(current_user, organization_id)
    proj = DisclosureProjectionRepository(pool)
    assessments = await proj.list_applicability(
        organization_id=organization_id, reporting_year=reporting_year
    )
    return {
        "organization_id": organization_id,
        "count": len(assessments),
        "assessments": assessments,
        # CarbonTally records an assessment with a basis; it never gives legal advice.
        "legal_determination": False,
    }


@router.post("/organizations/{organization_id}/applicability")
async def create_applicability(
    organization_id: str,
    payload: ApplicabilityRequest,
    current_user: AuthUser = Depends(require_org_member()),
    pool: Any = Depends(get_pool),
) -> dict:
    _authorize_write(current_user, organization_id)

    try:
        basis = validate_applicability_basis(payload.basis, payload.assessed_status)
    except DisclosureViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    disclosure = DisclosureRepository(pool)
    try:
        row = await disclosure.create_applicability_assessment(
            organization_id=organization_id,
            framework_version_id=payload.framework_version_id,
            reporting_year=payload.reporting_year,
            reporting_period_start=payload.reporting_period_start,
            reporting_period_end=payload.reporting_period_end,
            characteristic_snapshot=payload.characteristic_snapshot,
            assessed_status=payload.assessed_status,
            basis=basis,
            determined_by=current_user.user_id,
        )
    except DisclosureViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"organization_id": organization_id, "assessment": row}


# ---------------------------------------------------------------------------
# B4 narrative overlay (A1/A3/P3/D15)
#   GET /api/v3/reports/{report_id}/disclosure/narrative            (member read)
#   PUT /api/v3/reports/{report_id}/disclosure/narrative/{requirement_version_id}
# ---------------------------------------------------------------------------
class NarrativeWriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: str = Field(description="Plain text (no markup). No arbitrary length limit (A3).")
    narrative_kind: str = Field(
        default="CUSTOMER_COMMENTARY",
        description="CUSTOMER_COMMENTARY | METHODOLOGY_NOTE | EXPLANATION",
    )
    report_version_id: Optional[str] = Field(
        default=None, description="Write against this version; defaults to the current version"
    )


@router.get("/reports/{report_id}/disclosure/narrative")
async def list_report_narrative(
    report_id: str,
    requirement_version_id: Optional[str] = Query(default=None),
    current_user: AuthUser = Depends(require_org_member()),
    repos: Any = Depends(get_repositories),
    pool: Any = Depends(get_pool),
) -> dict:
    """The requirement-bound narrative for the report's current version."""
    report = await _report_or_404(repos, report_id)
    organization_id = str(report["organization_id"])
    _authorize_read(current_user, organization_id)
    version_id = await _current_version_or_404(repos, report_id)
    try:
        return await DisclosureNarrativeService(pool).list_narrative(report_version_id=version_id)
    except DisclosureViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/reports/{report_id}/disclosure/narrative/{requirement_version_id}")
async def write_report_narrative(
    report_id: str,
    requirement_version_id: str,
    payload: NarrativeWriteRequest,
    current_user: AuthUser = Depends(require_org_member()),
    repos: Any = Depends(get_repositories),
    pool: Any = Depends(get_pool),
) -> dict:
    """Author narrative against one requirement (A1) — Owner/Admin only.

    The requirement must belong to this report version's requirement set; an
    ``APPROVED``/``FINAL`` version refuses authoring (D15).
    """
    report = await _report_or_404(repos, report_id)
    organization_id = str(report["organization_id"])
    _authorize_write(current_user, organization_id)
    version_id = payload.report_version_id or await _current_version_or_404(repos, report_id)
    try:
        return await DisclosureNarrativeService(pool).write_narrative(
            report_version_id=version_id,
            requirement_version_id=requirement_version_id,
            narrative_kind=payload.narrative_kind,
            body=payload.body,
            actor_role=_org_role(current_user),
            actor_id=current_user.user_id,
        )
    except DisclosureViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# POST /api/v3/reports/{report_id}/approve      (B4-D1: Owner/Admin only)
# POST /api/v3/reports/{report_id}/finalise     (B4-D1 + DM-5 gate)
# GET  /api/v3/reports/{report_id}/finalisation-check
# ---------------------------------------------------------------------------
class TransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_version_id: Optional[str] = Field(
        default=None, description="Transition this version; defaults to the report's current version"
    )


@router.get("/reports/{report_id}/finalisation-check")
async def get_finalisation_check(
    report_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: Any = Depends(get_repositories),
    pool: Any = Depends(get_pool),
) -> dict:
    """The DM-5 gate preview. Read-only: it never transitions anything."""
    report = await _report_or_404(repos, report_id)
    organization_id = str(report["organization_id"])
    _authorize_read(current_user, organization_id)
    version_id = await _current_version_or_404(repos, report_id)
    service = DisclosureFinalisationService(pool)
    try:
        return await service.assess(report_version_id=version_id)
    except DisclosureViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/reports/{report_id}/approve")
async def approve_report_version(
    report_id: str,
    payload: Optional[TransitionRequest] = None,
    current_user: AuthUser = Depends(require_org_member()),
    repos: Any = Depends(get_repositories),
    pool: Any = Depends(get_pool),
) -> dict:
    """REVIEWED -> APPROVED. B4-D1: organisation Owner/Admin only.

    Consultants and CarbonTally internal staff are denied (server-side); the role
    is re-checked inside the service as defence in depth.
    """
    report = await _report_or_404(repos, report_id)
    organization_id = str(report["organization_id"])
    _authorize_write(current_user, organization_id)  # Owner/Admin only, PE/staff denied
    version_id = (payload.report_version_id if payload and payload.report_version_id else None) or (
        await _current_version_or_404(repos, report_id)
    )
    service = DisclosureFinalisationService(pool)
    try:
        return await service.approve(
            report_version_id=version_id,
            actor_role=_org_role(current_user),
            actor_id=current_user.user_id,
        )
    except DisclosureViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/reports/{report_id}/finalise")
async def finalise_report_version(
    report_id: str,
    payload: Optional[TransitionRequest] = None,
    current_user: AuthUser = Depends(require_org_member()),
    repos: Any = Depends(get_repositories),
    pool: Any = Depends(get_pool),
    artefact_storage: Any = Depends(get_report_artefact_storage_dep),
) -> dict:
    """APPROVED -> FINAL, gated by `DM-5` **and** the mandatory frozen artefact.

    B4-D1: Owner/Admin only. B4-D5: the immutable PDF artefact is rendered, stored
    in the private bucket and recorded **before** the transition — if it cannot be
    produced or stored, finalisation fails (503) and the version stays APPROVED.
    A blocked `DM-5` gate returns 409 with the blocking requirement ids; a
    concurrent state change returns 409 rather than clobbering the version.
    """
    report = await _report_or_404(repos, report_id)
    organization_id = str(report["organization_id"])
    _authorize_write(current_user, organization_id)
    version_id = (payload.report_version_id if payload and payload.report_version_id else None) or (
        await _current_version_or_404(repos, report_id)
    )
    producer = _branded_pdf_producer(repos, current_user, report)
    service = DisclosureFinalisationService(pool)
    try:
        return await service.finalise(
            report_version_id=version_id,
            actor_role=_org_role(current_user),
            pdf_producer=producer,
            storage=artefact_storage,
            actor_id=current_user.user_id,
        )
    except FinalisationBlocked as exc:
        blocking = ", ".join(
            f"{item.requirement_version_id} ({item.effective_class})" for item in exc.assessment.blocking
        )
        raise HTTPException(
            status_code=409,
            detail=(
                "Finalisation blocked: unresolved required disclosures "
                f"[{blocking}]. Resolve them or supply the required customer input, "
                "then retry. See GET /api/v3/reports/{report_id}/finalisation-check."
            ),
        ) from exc
    except ArtefactRequired as exc:
        # The frozen artefact is mandatory (B4-D5): no FINAL without it.
        raise HTTPException(
            status_code=503,
            detail=f"{exc} The report version remains APPROVED; retry once the artefact can be produced.",
        ) from exc
    except DisclosureViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# S5 frozen artefact (B4-D5/D6/D7)
#   GET  /api/v3/reports/{report_id}/frozen-artefact             (member read)
#   POST /api/v3/reports/{report_id}/frozen-artefact/signed-url
# ---------------------------------------------------------------------------
@router.get("/reports/{report_id}/frozen-artefact")
async def get_frozen_artefact(
    report_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: Any = Depends(get_repositories),
    pool: Any = Depends(get_pool),
) -> dict:
    """Metadata for the frozen artefact (bucket, derived key, SHA-256, size).

    Never returns a URL: the object is private and only reachable through the
    signed-URL route below.
    """
    report = await _report_or_404(repos, report_id)
    organization_id = str(report["organization_id"])
    _authorize_read(current_user, organization_id)
    version_id = await _current_version_or_404(repos, report_id)
    try:
        return await DisclosureFinalisationService(pool).artefact_status(
            report_version_id=version_id
        )
    except DisclosureViolation as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/reports/{report_id}/frozen-artefact/signed-url")
async def get_frozen_artefact_signed_url(
    report_id: str,
    payload: Optional[TransitionRequest] = None,
    current_user: AuthUser = Depends(require_org_member()),
    repos: Any = Depends(get_repositories),
    pool: Any = Depends(get_pool),
    artefact_storage: Any = Depends(get_report_artefact_storage_dep),
) -> dict:
    """Issue a **short-lived** signed URL for the frozen artefact (B4-D6).

    Authorization happens first (organisation member of the owning organisation;
    Processing-Entity and CarbonTally staff are denied by ``_authorize_read``).
    A version with no frozen artefact returns 404 — drafts are served by the
    live-render route (`A15`), never from the frozen bucket.
    """
    report = await _report_or_404(repos, report_id)
    organization_id = str(report["organization_id"])
    _authorize_read(current_user, organization_id)
    version_id = (payload.report_version_id if payload and payload.report_version_id else None) or (
        await _current_version_or_404(repos, report_id)
    )
    try:
        return await DisclosureFinalisationService(pool).artefact_download_url(
            report_version_id=version_id, storage=artefact_storage, actor_id=current_user.user_id
        )
    except DisclosureViolation as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# P17-L — the governed capability truth surface
#   GET /api/v3/capabilities
# ---------------------------------------------------------------------------


@router.get("/capabilities")
async def get_capability_catalogue(
    current_user: AuthUser = Depends(get_current_user),
    pool: Any = Depends(get_pool),
) -> dict:
    """What CarbonTally currently supports — **product-level** truth (`P17-L`).

    This is the one canonical read model behind both capability surfaces
    (`DECISION-03 §6`): the customer product surface and the investor surface
    consume this same payload, so a governed value cannot differ between them
    (`CS-2`).

    Governance enforced here:

    * **Authenticated, tenant-free.** Authentication is required
      (`DECISION-03 §16`), and *no* tenant context is read or accepted: the
      endpoint takes no tenant parameter, performs no tenant query, and answers
      identically for every caller (`CS-1`, `SEC-1`, `SEC-3`, `AG-5`). It is a
      product fact, so it is safe to serve without a tenant context.
    * **Server-authoritative.** The payload is derived from persisted
      `disclosure_requirement_versions` rows through the existing governed
      projection engine; nothing is hardcoded and no value is computed here.
    * **Identity-anchored selection.** The catalogue version is chosen by
      governed *identity* — the version whose rows are the complete governed
      requirement identity set — never by `status`, `source_tier` or
      `version_label` ordering (`P17-M2`, `DEF-1`). A competing version carrying
      a governed-looking requirement code therefore cannot replace the governed
      catalogue or upgrade a claim.
    * **Fails closed.** If the catalogue is not provisioned, if two versions both
      claim the governed identity set (an ambiguous catalogue), or if the
      projection cannot be stated honestly, the endpoint returns **503** and no
      claim — never a partial or upgraded one (`CS-3`, `IV-4`).

    It answers *"what does CarbonTally support?"*. It deliberately does **not**
    answer *"which Scope 3 categories apply to this customer?"* — there is no
    applicability model (`PO-3`, `F-1`), no tenant state (`§13`), and no Axis-A
    architecture status (`IV-1`, `AG-3`).
    """
    catalog = DisclosureCatalogRepository(pool)

    # Which framework version is the governed capability catalogue? By GOVERNED
    # IDENTITY, never by ordering luck (P17-M2 / DEF-1): the version whose
    # requirement rows are the complete governed identity set. A framework may
    # legitimately have several versions, and a database may contain requirement
    # rows that are not a capability catalogue at all — merging them, or letting a
    # competitor carry one governed-looking code, would widen or narrow a claim.
    candidates = await catalog.capability_catalogue_candidates()
    try:
        selected = select_governed_catalogue_version(candidates)
    except DisclosureViolation as exc:
        # More than one version claims the catalogue identity: an ambiguous
        # governed state yields NO claim, never a chosen one.
        logger.error("capability surface: ambiguous governed catalogue (%s)", exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "The governed capability catalogue is ambiguous, so no capability "
                "statement can be made until it is resolved."
            ),
        ) from exc
    if selected is None:
        logger.error(
            "capability surface: no framework version carries a governed requirement catalogue"
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "The governed capability catalogue is not provisioned, so no "
                "capability statement can be made."
            ),
        )

    framework_code = str(selected.get("framework_code") or "")
    framework = await catalog.get_framework_by_code(framework_code)
    if framework is None:
        logger.error("capability surface: framework %s is absent", framework_code)
        raise HTTPException(
            status_code=503,
            detail=(
                "The governed capability catalogue is not provisioned, so no "
                "capability statement can be made."
            ),
        )

    rows = await catalog.list_capability_catalogue_requirements(str(selected["id"]))
    try:
        return project_capability_catalogue(
            framework=framework,
            framework_version=selected,
            requirement_rows=rows,
        )
    except DisclosureViolation as exc:
        # A projection that cannot be stated within the frozen wording yields no
        # claim at all: the surface shows less, never something stronger.
        logger.error("capability surface: projection refused (%s)", exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "Unable to produce the governed capability statement. No claim is "
                "made rather than an unverified one."
            ),
        ) from exc

