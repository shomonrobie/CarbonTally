"""CarbonTally repository layer (Backend v2.1 §10).

Every repository maps database rows to immutable domain objects, contains
persistence logic only (no business, matching, calculation or workflow rules),
uses explicit column lists (never ``SELECT *``) and exposes async methods.
"""
from .audit import AuditRepository
from .base import AbstractRepository
from .customer_factors import CustomerFactorsRepository
from .documents import DocumentsRepository
from .emission_factors import EmissionFactorsRepository
from .emissions_logs import EmissionsLogsRepository
from .events import EventsRepository
from .factor_aliases import FactorAliasesRepository
from .imports import ImportsRepository
from .invitations import InvitationsRepository
from .issues import IssuesRepository
from .organizations import OrganizationsRepository
from .processing_entities import ProcessingEntitiesRepository
from .reports import ReportsRepository
from .report_versions import ReportVersionsRepository
from .exports import ExportsRepository
from .notifications import NotificationsRepository
from .organization_files import OrganizationFilesRepository
from .queue_settings import QueueSettingsRepository
from .review_queue import ReviewQueueRepository
from .roles import RolesRepository
from .tenant import TenantRepository
from .upload_batches import UploadBatchesRepository
from .verifications import VerificationsRepository
from .consultants import ConsultantsRepository
from .manual_extraction import ManualExtractionRepository
from .suppliers import SuppliersRepository

__all__ = [
    "AbstractRepository",
    "AuditRepository",
    "ConsultantsRepository",
    "CustomerFactorsRepository",
    "DocumentsRepository",
    "EmissionFactorsRepository",
    "EmissionsLogsRepository",
    "EventsRepository",
    "ExportsRepository",
    "FactorAliasesRepository",
    "ImportsRepository",
    "InvitationsRepository",
    "IssuesRepository",
    "ManualExtractionRepository",
    "NotificationsRepository",
    "OrganizationFilesRepository",
    "OrganizationsRepository",
    "ProcessingEntitiesRepository",
    "QueueSettingsRepository",
    "ReportsRepository",
    "ReportVersionsRepository",
    "ReviewQueueRepository",
    "RolesRepository",
    "SuppliersRepository",
    "TenantRepository",
    "UploadBatchesRepository",
    "VerificationsRepository",
]

