"""CarbonTally repository layer (Backend v2.1 §10).

Every repository maps database rows to immutable domain objects, contains
persistence logic only (no business, matching, calculation or workflow rules),
uses explicit column lists (never ``SELECT *``) and exposes async methods.
"""
from .audit import AuditRepository
from .base import AbstractRepository
from .documents import DocumentsRepository
from .emission_factors import EmissionFactorsRepository
from .emissions_logs import EmissionsLogsRepository
from .events import EventsRepository
from .factor_aliases import FactorAliasesRepository
from .imports import ImportsRepository
from .organizations import OrganizationsRepository
from .reports import ReportsRepository

__all__ = [
    "AbstractRepository",
    "AuditRepository",
    "DocumentsRepository",
    "EmissionFactorsRepository",
    "EmissionsLogsRepository",
    "EventsRepository",
    "FactorAliasesRepository",
    "ImportsRepository",
    "OrganizationsRepository",
    "ReportsRepository",
]

