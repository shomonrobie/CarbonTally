"""Partner & operations domain objects (V3 new capabilities).

Immutable dataclasses for consultants (firms, members, clients, tasks),
manual-extraction batches/items, and suppliers. Mirrors the RC2 tables.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional

#: Batch lifecycle vocabulary for ``manual_extraction_batches.status``.
BATCH_STATUSES: tuple[str, ...] = (
    "open", "in_progress", "qc_in_progress", "qc_passed",
    "completed", "cancelled", "failed",
)

#: Item workflow vocabulary for ``manual_extraction_items.status``. The core
#: pipeline is Source → Extraction → Mapping → Validation → Calculation →
#: Review → Approval (``WORKFLOW_STAGES``). QC (``qc_approved``/``qc_rejected``)
#: is an orthogonal CarbonTally-staff gate applied after extraction.
ITEM_STATUSES: tuple[str, ...] = (
    "pending", "extracting", "extracted", "mapping", "mapped",
    "validating", "validated", "calculating", "calculated",
    "customer_review", "approved", "rejected",
    "qc_approved", "qc_rejected", "failed",
    # P6-2B-1 — Consultant Review completion (readiness control). Distinguishable
    # from internal `reviewed`, PE review/QC, CarbonTally QC and Customer Review.
    "consultant_reviewed",
)

#: The core processing workflow stages, in pipeline order.
WORKFLOW_STAGES: tuple[str, ...] = (
    "source", "extraction", "mapping", "validation",
    "calculation", "review", "qc", "pe_review", "pe_qc",
    "carbon_tally_qc", "approval",
)

#: Maps each workflow stage to the item statuses that belong to it.
#: ``review`` keeps its legacy ``customer_review`` member so existing by-stage
#: reporting is unchanged; new V1.2 statuses are additive.
WORKFLOW_STAGE_STATUSES: dict[str, tuple[str, ...]] = {
    "source": ("pending",),
    "extraction": ("extracting", "extracted"),
    "mapping": ("mapping", "mapped"),
    "validation": ("validating", "validated"),
    "calculation": ("calculating", "calculated"),
    "review": ("review", "reviewed", "customer_review", "consultant_reviewed"),
    "qc": ("qc_approved", "qc_rejected"),  # legacy early extraction-QC markers
    "pe_review": ("pe_review", "pe_reviewed", "pe_review_rejected"),
    "pe_qc": ("pe_qc", "pe_qc_approved", "pe_qc_rejected"),
    "carbon_tally_qc": ("ct_qc", "ct_qc_approved", "ct_qc_rejected"),
    "approval": ("approved", "rejected"),
}

#: Permitted item status transitions (the workflow state machine). Validation
#: failures and customer rejections route items back to ``mapping``/``extracting``
#: (rework loop) instead of introducing new statuses.
#:
#: V1.2 (CT-QC-001..005) — dual-origin canonical paths:
#:   CARBONTALLY_INTERNAL: … → calculated → review → reviewed → ct_qc →
#:       ct_qc_approved → customer_review → approved
#:   PROCESSING_ENTITY:    … → calculated → pe_review → pe_reviewed → pe_qc →
#:       pe_qc_approved → ct_qc → ct_qc_approved → customer_review → approved
#: Legacy early-QC statuses (qc_approved/qc_rejected) remain valid as historical
#: markers and are never reinterpreted as CarbonTally QC.
ITEM_STATUS_FLOW: dict[str, tuple[str, ...]] = {
    "pending": ("extracting", "extracted"),
    "extracting": ("extracted", "pending"),
    "extracted": ("mapping", "mapped", "qc_approved"),
    "mapping": ("mapped", "extracted", "extracting"),
    "mapped": ("validating", "validated", "mapping"),
    "validating": ("validated", "mapping"),
    "validated": ("calculating", "mapping"),
    "calculating": ("calculated", "validated"),
    "calculated": (
        "customer_review", "approved", "rejected", "mapping",
        "reviewed", "pe_review",
        # P6-2B-1 — Consultant Review (readiness control) may follow Consultant
        # processing; it never reaches ct_qc_*/approved by itself.
        "consultant_reviewed",
    ),
    # P6-2B-1/2 — Consultant Review completion. The item is submitted by the
    # P6-2B-2 `can_submit` action into the existing CarbonTally QC intake state
    # (`reviewed` — the internal-reviewed hand-off state that feeds the CT-QC
    # pending queue and CT-QC decision endpoint). Ops rework is the fallback
    # path out of this state (mapping/calculated); Consultants cannot re-enter
    # review once reviewed (endpoint requires status='calculated').
    "consultant_reviewed": ("mapping", "calculated", "reviewed"),
    # V1.2 canonical review / QC stages.
    # P6-2B-4 — `reviewed` is the awaiting-CT-QC intake for MANUAL work and may
    # only advance to the CarbonTally QC gate (or rework). The legacy
    # `reviewed -> customer_review` escape is REMOVED: manual work must pass
    # CT-QC (reviewed -> ct_qc -> ct_qc_approved) before any customer surface.
    "review": ("reviewed", "ct_qc", "calculated", "mapping"),
    "reviewed": ("ct_qc", "mapping", "calculated"),
    "pe_review": ("pe_reviewed", "pe_review_rejected", "mapping"),
    "pe_reviewed": ("pe_qc", "mapping", "calculated"),
    "pe_review_rejected": ("mapping", "extracting"),
    "pe_qc": ("pe_qc_approved", "pe_qc_rejected", "mapping"),
    "pe_qc_approved": ("ct_qc", "mapping"),
    "pe_qc_rejected": ("mapping", "extracting"),
    "ct_qc": ("ct_qc_approved", "ct_qc_rejected", "mapping"),
    # V1.2 — CarbonTally QC approval releases the item to the customer review
    # surface. Customers decide from `ct_qc_approved` (guard: PE-origin work must
    # have passed CT QC) or the legacy `customer_review` handoff state.
    "ct_qc_approved": ("customer_review", "mapping", "approved", "rejected"),
    "ct_qc_rejected": ("mapping", "extracting"),
    "customer_review": ("approved", "rejected", "calculated"),
    "approved": ("customer_review",),
    "rejected": ("mapping", "extracting"),
    "qc_approved": ("mapping", "mapped"),
    "qc_rejected": ("extracting", "mapping"),
    "failed": ("pending", "extracting"),
}


def can_transition_item_status(current: Optional[str], target: str) -> bool:
    """Return ``True`` when ``current`` may advance to ``target``.

    ``None``/unknown current statuses are treated as ``pending`` (fresh items).
    """
    if current == target:
        return True
    base = current if current in ITEM_STATUS_FLOW else "pending"
    return target in ITEM_STATUS_FLOW.get(base, ())


@dataclass(frozen=True, slots=True)
class ConsultantProfile:
    """A consultant firm profile (``consultant_profiles``)."""

    id: str
    user_id: str
    company_name: str
    brand_name: Optional[str] = None
    email_from: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    vat_number: Optional[str] = None
    partner_status: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class ConsultantFirmMember:
    """A member of a consultant firm (``consultant_firm_members``).

    ``role`` is the display role; the ``can_*`` boolean columns are the actual
    consultant authorization surface (Phase 7 uses them for action gates).
    """

    id: str
    firm_id: str
    user_id: str
    role: str
    is_active: bool = True
    can_manage_clients: bool = False
    can_upload_documents: bool = False
    can_generate_reports: bool = False
    can_manage_team: bool = False
    # P6-2A — consultant processing capability flags (deny-by-default; the
    # server-side authorization surface for consultant processing actions).
    can_extract: bool = False
    can_map: bool = False
    can_validate: bool = False
    can_calculate: bool = False
    can_confirm_automation: bool = False
    can_submit: bool = False
    client_access: list = field(default_factory=list)
    invited_at: Optional[datetime] = None
    joined_at: Optional[datetime] = None


#: ``consultant_clients.status`` lifecycle vocabulary (D27/D19 + P6-1C — the
#: RLS/API enforcement layer; the schema column stays free-varchar for data
#: safety). Only ``active`` grants consultant access (D15); ``pending`` /
#: ``rejected`` / ``suspended`` / ``ended`` / ``inactive`` / ``onboarding``
#: carry NO access.
CLIENT_LIFECYCLE_STATUSES: tuple[str, ...] = (
    "active", "pending", "rejected", "suspended", "ended", "inactive",
    "onboarding",
)

#: Origin of a consultant↔organisation relationship (P6-1C provenance).
#:   * ``consultant_created_customer`` — the firm CREATED the client org via the
#:     approved provisioning flow (Case A); the active grant is legitimate
#:     without a separate customer acceptance step.
#:   * ``engagement_request`` — the firm requested an engagement with an
#:     ALREADY-EXISTING organisation (Case B); customer acceptance is the
#:     required authorization boundary (status: pending -> active).
#:   * ``legacy`` — rows that predate P6-1C (kept active per ratified data).
RELATIONSHIP_ORIGINS: tuple[str, ...] = (
    "legacy", "consultant_created_customer", "engagement_request",
)

#: Raw (actor-agnostic) state machine used by the existing lifecycle checker.
#: ``None``/unknown statuses remain ``active``-compatible for legacy rows.
CLIENT_LIFECYCLE_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "active": ("suspended", "ended"),
    "suspended": ("active", "ended"),
    "ended": ("active", "pending"),
    "inactive": ("active", "suspended", "ended"),
    "pending": ("active", "rejected", "ended"),
    "rejected": ("pending",),
}


def can_transition_client_lifecycle(current: Optional[str], target: str) -> bool:
    """Return ``True`` when a client relationship may move to ``target``.

    ``None``/unknown current statuses are treated as ``active``-compatible
    (legacy rows created without a status, or rows that predate D19, default to
    the grant being active — matching the pre-D19 behaviour).
    """
    if current == target:
        return True
    base = current if current in CLIENT_LIFECYCLE_TRANSITIONS else "active"
    return target in CLIENT_LIFECYCLE_TRANSITIONS.get(base, ())


def can_transition_consultant_engagement(
    current: Optional[str],
    target: str,
    *,
    actor_side: str,
    origin: Optional[str] = "consultant_created_customer",
) -> bool:
    """P6-1C — the CANONICAL engagement transition policy.

    ``actor_side`` is ``'customer'`` (an authorized representative of the
    client organisation) or ``'consultant'`` (an authorized firm actor).

    Customer side (the required authorization boundary for pre-existing
    organisations): only a PENDING engagement may be accepted (-> active) or
    rejected (-> rejected). Customer approval is the ONLY path from pending to
    active.

    Consultant side:
    * Legacy / consultant-created relationships keep the D19 firm lifecycle
      (active <-> suspended, active/... -> ended, ended -> active reactivation,
      inactive -> active/suspended/ended).
    * ``engagement_request`` relationships: the firm may withdraw a pending
      request (-> ended), RE-REQUEST after rejection/termination
      (rejected/ended/inactive -> pending), and use the normal active/
      suspended/ended lifecycle once accepted. The firm can NEVER move a row
      to ``active`` from ``pending``/``rejected`` — that requires customer
      acceptance.
    """
    if origin in ("engagement_request",):
        if actor_side == "customer":
            # Customer acceptance/rejection is the authorized decision on a
            # pending engagement — the ONLY pending -> active path.
            return str(current) == "pending" and target in ("active", "rejected")
        allowed = {
            "pending": ("ended",),          # firm may withdraw a request
            "rejected": ("pending",),       # firm may re-request
            "ended": ("pending",),          # re-request after termination
            "inactive": ("pending",),       # legacy deactivate -> re-request
            "active": ("suspended", "ended"),
            "suspended": ("active", "ended"),
        }
        return target in allowed.get(str(current or "pending"), ())
    # legacy + consultant_created_customer keep the ratified D19 firm lifecycle.
    if actor_side == "customer":
        return str(current) == "pending" and target in ("active", "rejected")
    return can_transition_client_lifecycle(current, target)


@dataclass(frozen=True, slots=True)
class ConsultantClient:
    """A consultant↔organisation grant (``consultant_clients``)."""

    id: str
    consultant_id: str
    organization_id: str
    client_name: str
    client_industry: Optional[str] = None
    client_contact_email: Optional[str] = None
    client_contact_name: Optional[str] = None
    status: Optional[str] = None
    billing_plan: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    # D27/D19 lifecycle provenance columns.
    suspended_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    ended_by: Optional[str] = None
    lifecycle_updated_at: Optional[datetime] = None
    #: Server-authoritative creator of the grant (authenticated actor).
    created_by: Optional[str] = None
    # P6-1C — engagement provenance.
    relationship_origin: Optional[str] = "consultant_created_customer"
    engagement_requested_at: Optional[datetime] = None
    engagement_decided_by: Optional[str] = None
    engagement_decided_at: Optional[datetime] = None



@dataclass(frozen=True, slots=True)
class ConsultantTask:
    """A consultant task (``consultant_tasks``)."""

    id: str
    consultant_id: str
    task_title: str
    client_id: Optional[str] = None
    task_type: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)
    created_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class ManualExtractionBatch:
    """A manual-extraction batch (``manual_extraction_batches``)."""

    id: str
    organization_id: str
    batch_name: str
    batch_description: Optional[str] = None
    entity_id: Optional[str] = None
    total_documents: int = 0
    total_pages: int = 0
    total_cost: float = 0.0
    price_per_page: Optional[float] = None
    currency: str = "GBP"
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_by: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    qc_approved: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    estimated_completion_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    sla_breached: bool = False
    assigned_at: Optional[datetime] = None
    qc_by: Optional[str] = None
    qc_at: Optional[datetime] = None
    qc_notes: Optional[str] = None
    customer_notes: Optional[str] = None
    staff_notes: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class ManualExtractionItem:
    """A manual-extraction work item (``manual_extraction_items``)."""

    id: str
    batch_id: str
    file_name: str
    file_url: str
    page_count: int
    file_id: Optional[str] = None
    document_type: Optional[str] = None
    status: Optional[str] = None
    extracted_data: Optional[dict] = None
    mapped_data: Optional[dict] = None
    mapped_facility_id: Optional[str] = None
    mapped_asset_id: Optional[str] = None
    mapped_supplier_id: Optional[str] = None
    calculated_emissions_kg_co2e: Optional[float] = None
    extracted_by: Optional[str] = None
    qc_by: Optional[str] = None
    qc_at: Optional[datetime] = None
    qc_notes: Optional[str] = None
    quality_score: Optional[int] = None
    created_at: Optional[datetime] = None
    document_processing_queue_id: Optional[str] = None
    emission_factor_used: Optional[str] = None
    extracted_at: Optional[datetime] = None
    customer_reviewed_by: Optional[str] = None
    customer_reviewed_at: Optional[datetime] = None
    customer_approved: Optional[bool] = None
    customer_rejection_reason: Optional[str] = None
    customer_notes: Optional[str] = None
    updated_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class Supplier:
    """A supplier record (``suppliers``)."""

    id: str
    organization_id: str
    name: str
    type: Optional[str] = None
    supplier_category_id: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    country: Optional[str] = None
    vat_number: Optional[str] = None
    website: Optional[str] = None
    supplier_type: Optional[str] = None
    annual_emissions: Optional[float] = None
    supplier_rating: Optional[float] = None
    is_certified: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)
