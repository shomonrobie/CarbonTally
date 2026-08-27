# backend/routes/admin/__init__.py
"""
Admin Routes Package
All admin-related endpoints.
"""

from . import staff
from . import defra
from . import extraction
from . import reviews
from . import assignments
from . import permissions
from . import workload
from . import beta
from . import audit
from . import review_history
from . import logs as admin_logs
from . import bulk as admin_bulk
from . import email_templates
from . import analytics as admin_analytics
from . import settings  # ✅ New import

__all__ = [
    'staff',
    'defra',
    'extraction',
    'reviews',
    'assignments',
    'permissions',
    'workload',
    'beta',
    'audit',
    'review_history',
    'admin_logs',
    'admin_bulk',
    'email_templates',
    'admin_analytics',
    'settings',  # ✅ New
]