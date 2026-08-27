"""Operations domain objects (V3 legacy-capability reimplementation).

Immutable dataclasses mirroring the RC2 operations tables used by the
reimplemented legacy capabilities: organization_files, upload_batches,
manual_review_queue, queue_settings, notifications, verifications and the
tenant write surface (members/facilities/assets).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class MemberRecord:
    """A row of ``organization_members`` used by the V3 member surface."""

    id: str
    organization_id: str
    user_id: str
    role: str
    is_active: bool = True
    joined_at: Optional[datetime] = None
    last_active: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class FacilityDetail:
    """A row of ``facilities`` (richer than domain.organization.Facility)."""

    id: str
    organization_id: str
    name: str
    postcode: Optional[str] = None
    country: str = "GB"
    type: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AssetDetail:
    """A row of ``assets`` (richer than domain.organization.Asset)."""

    id: str
    organization_id: str
    facility_id: Optional[str]
    name: str
    type: Optional[str] = None
    description: Optional[str] = None
    serial_number: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VehicleDetail:
    """A row of ``vehicles`` (D17 organisation master data)."""

    id: str
    organization_id: str
    name: str
    registration: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    fuel_type: Optional[str] = None
    vehicle_type: Optional[str] = None
    capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OrganizationFile:
    """A row of ``organization_files`` (upload/document record)."""

    id: str
    organization_id: str
    name: str
    path: str
    size_bytes: int
    file_type: str
    mime_type: str
    bucket: str
    status: str
    uploaded_by: str
    uploaded_at: Optional[datetime] = None
    is_active: bool = True
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class UploadBatch:
    """A row of ``upload_batches``."""

    id: str
    organization_id: str
    batch_name: str
    total_files: int
    processed_files: int
    status: str
    created_by_user_id: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReviewItem:
    """A row of ``manual_review_queue``."""

    id: str
    organization_id: str
    file_name: str
    status: str
    priority: int = 1
    priority_score: float = 0.0
    entity_id: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_by: Optional[str] = None
    batch_id: Optional[str] = None
    file_id: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    data_type: Optional[str] = None
    customer_notes: Optional[str] = None
    staff_notes: Optional[str] = None
    auto_extraction_result: Optional[dict] = None
    manual_extraction_result: Optional[dict] = None
    sla_deadline: Optional[str] = None
    sla_breached: bool = False
    escalation_level: int = 0
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    review_time_seconds: Optional[int] = None


@dataclass(frozen=True, slots=True)
class QueueSettings:
    """A row of ``queue_settings``."""

    max_reviews_per_staff: int
    sla_hours: int
    auto_assign_enabled: bool
    escalation_hours: int
    priority_weights: dict = field(default_factory=dict)
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


@dataclass(frozen=True, slots=True)
class Notification:
    """A row of ``notifications`` (real schema: per-recipient rows).

    The table carries ``recipient_type``/``recipient_id`` (e.g. ``user`` /
    auth user id) plus the display fields ``notification_type``, ``title``,
    ``message`` and ``link``. D25 aligned the repository/API to this schema
    (the previous implementation referenced a non-existent ``user_id`` column).
    """

    id: str
    recipient_type: str = "user"
    recipient_id: str = ""
    notification_type: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    priority: int = 0
    link: Optional[str] = None
    is_read: bool = False
    created_at: Optional[datetime] = None



@dataclass(frozen=True, slots=True)
class Verification:
    """A customer verification decision over a document's result."""

    document_id: str
    organization_id: str
    status: str
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None
    extraction: Optional[dict] = None
