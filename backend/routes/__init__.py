# backend/routes/__init__.py
"""
CarbonTally API Routes Package
"""

from . import emissions
from . import waitlist
from . import upload
from . import reports
from . import glossary
from . import users
from . import notifications
from . import documents_main      # ✅ Direct import (no documents folder)
from . import document_activity   # ✅ Direct import (no documents folder)
from . import drafts
from . import reference
from . import logs
from . import feedback
from . import drafts_enhanced
from . import customer_documents
from .admin import staff, defra, extraction, reviews, assignments, workload, beta, audit, review_history
from .admin import logs as admin_logs
from .admin import bulk as admin_bulk
from .admin import email_templates
from .admin import analytics as admin_analytics
from .admin import settings

from .organizations import (
    management,
    members,
    assets,
    data,
    analytics,
    dashboard,
    files,
    team,
    metadata,
    exports,
    bulk as org_bulk,
)

__all__ = [
    # Public/General routes
    'emissions',
    'waitlist',
    'upload',
    'reports',
    'glossary',
    'users',
    'notifications',
    'feedback',
    'documents_main',      # ✅ Direct
    'document_activity',   # ✅ Direct
    'drafts',
    'drafts_enhanced',
    'reference',
    'logs',
    
    # Admin routes
    'staff',
    'defra',
    'extraction',
    'reviews',
    'assignments',
    'workload',
    'beta',
    'audit',
    'review_history',
    'admin_logs',
    'admin_bulk',
    'email_templates',
    'admin_analytics',
    'settings',
    
    # Organization routes
    'management',
    'members',
    'assets',
    'data',
    'analytics',
    'dashboard',
    'files',
    'team',
    'metadata',
    'exports',
    'org_bulk',
]