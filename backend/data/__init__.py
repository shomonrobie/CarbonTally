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
from .issues import IssuesRepository
from .organizations import OrganizationsRepository
from .processing_entities import ProcessingEntitiesRepository
from .reports import ReportsRepository

__all__ = [
    "AbstractRepository",
    "AuditRepository",
    "CustomerFactorsRepository",
    "DocumentsRepository",
    "EmissionFactorsRepository",
    "EmissionsLogsRepository",
    "EventsRepository",
    "FactorAliasesRepository",
    "ImportsRepository",
    "IssuesRepository",
    "OrganizationsRepository",
    "ProcessingEntitiesRepository",
    "ReportsRepository",
]

