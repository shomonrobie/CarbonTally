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
)

#: The core processing workflow stages, in pipeline order.
WORKFLOW_STAGES: tuple[str, ...] = (
    "source", "extraction", "mapping", "validation",
    "calculation", "review", "approval",
)

#: Maps each workflow stage to the item statuses that belong to it.
WORKFLOW_STAGE_STATUSES: dict[str, tuple[str, ...]] = {
    "source": ("pending",),
    "extraction": ("extracting", "extracted"),
    "mapping": ("mapping", "mapped"),
    "validation": ("validating", "validated"),
    "calculation": ("calculating", "calculated"),
    "review": ("customer_review",),
    "approval": ("approved", "rejected"),
    "qc": ("qc_approved", "qc_rejected"),
}

#: Permitted item status transitions (the workflow state machine). Validation
#: failures and customer rejections route items back to ``mapping``/``extracting``
#: (rework loop) instead of introducing new statuses.
ITEM_STATUS_FLOW: dict[str, tuple[str, ...]] = {
    "pending": ("extracting", "extracted"),
    "extracting": ("extracted", "pending"),
    "extracted": ("mapping", "mapped", "qc_approved"),
    "mapping": ("mapped", "extracted", "extracting"),
    "mapped": ("validating", "validated", "mapping"),
    "validating": ("validated", "mapping"),
    "validated": ("calculating", "mapping"),
    "calculating": ("calculated", "validated"),
    "calculated": ("customer_review", "approved", "rejected", "mapping"),
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
    client_access: list = field(default_factory=list)
    invited_at: Optional[datetime] = None
    joined_at: Optional[datetime] = None


#: ``consultant_clients.status`` lifecycle vocabulary (D27/D19 — the RLS/API
#: enforcement layer; the schema column stays free-varchar for data safety).
#: Only ``active`` grants consultant access (D15); ``suspended`` / ``ended``
#: carry no access; ``inactive`` is the legacy soft-deactivate value.
CLIENT_LIFECYCLE_STATUSES: tuple[str, ...] = (
    "active", "suspended", "ended", "inactive",
)

#: Allowed lifecycle transitions (D27/D19 Part 4):
#:   active -> suspended (temporary loss of access)
#:   active -> ended     (permanent loss of access)
#:   suspended -> active (restore)
#:   suspended -> ended  (make permanent)
#:   ended -> active     (a NEW explicit grant reactivation — the firm may
#:                        re-grant only with a new explicit act)
CLIENT_LIFECYCLE_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "active": ("suspended", "ended"),
    "suspended": ("active", "ended"),
    "ended": ("active",),
    "inactive": ("active", "suspended", "ended"),
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
